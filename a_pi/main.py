#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import random
import string
import os
import math
import click
from flask import Flask
from flask import current_app, g, request
from flask.cli import with_appcontext
from werkzeug.exceptions import abort

import grpc

import mill_pb2
import mill_pb2_grpc

from matrix_client.client import MatrixClient
client = MatrixClient('http://{}:{}'.format(os.environ['MATRIX_HOST'], os.environ['MATRIX_PORT']))

print(os.environ['MATRIX_HOST'])

import json
matrix_param_file = open("matrix_user.json", "r")
matrix_param = json.loads(matrix_param_file.read())
matrix_param_file.close()

token = client.login(username=matrix_param["username"], password=matrix_param["password"])
room = client.join_room(matrix_param["room"]);

MAX_PI = 1000
MILLLLLLLL_ADDR = os.environ['MILLLLLLLL_HOST'] + ':' + os.environ['MILLLLLLLL_PORT']

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    
def make_pi(total):
    q, r, t, k, m, x = 1, 0, 1, 1, 3, 3
    count = 0
    while True:
        if 4 * q + r - t < m * t:
            yield m
            count += 1
            if count > total:
                break
            q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k, (10*(3*q+r))//t - 10*m, x
        else:
            q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1, (q*(7*k+2)+r*x)//(t*x), x+2

def action(db, job_id, job_current):
    db.execute(
        'UPDATE job SET digits = ?'
        ' WHERE id = ?',
        (job_current + 1, job_id)
    )
    db.execute(
        'INSERT INTO segment (job_id, x1, y1, x2, y2)'
        ' VALUES (?, ?, ?, ?, ?)',
        (job_id, random.random(), random.random(), random.random(), random.random())
    )
    db.commit()

def terminate(db, job_id, mill_stub):
    # TODO add RPC call
    segments = db.execute(
        'SELECT x1, y1, x2, y2 FROM segment'
        ' WHERE job_id = ?',
        (job_id,)
    ).fetchall()

    segments = [mill_pb2.Segment(
                    a=mill_pb2.Point(
                        x=s['x1'],
                        y=s['y1']),
                    b=mill_pb2.Point(
                        x=s['x2'],
                        y=s['x2'])) for s in segments]
    
    room.send_text('@'+json.dumps({
        "msg": "Sent segments to mill",
        "service": "a_pi",
        "id": job_id}))

    mill_stub.Turn(
        mill_pb2.Job(
            id=mill_pb2.JobId(
                id=job_id),
            amount=8,
            segments=segments,
            result=segments
    ))
    
    db.execute(
        'DELETE FROM job'
        ' WHERE id = ?',
        (job_id,)
    )
    db.execute(
        'DELETE FROM segment'
        ' WHERE job_id = ?',
        (job_id,)
    )
    db.commit()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    channel = grpc.insecure_channel(MILLLLLLLL_ADDR)
    mill_stub = mill_pb2_grpc.MillStub(channel)

    pi = [str(d) for d in make_pi(MAX_PI)]

    @app.route('/', methods=('GET', 'POST'))
    def hello():
        valid = [str(i) for i in range(0, 10)]
        valid.append('π')
        
        if request.method == 'POST':
            digit = request.form['digit']
            job = request.form['job']

            db = get_db()
            job_current = db.execute(
                'SELECT job.digits FROM job WHERE job.id = ?',
                (job,)
            ).fetchone()
            
            if digit not in valid:
                print('unexpected :', digit)
                abort(400)
            
            if job_current is None:
                if digit == '3':
                    job_id = ''.join(random.choices(string.ascii_letters, k=20))
                    db.execute(
                        'INSERT INTO job (id, digits)'
                        ' VALUES (?, ?)',
                        (job_id, 1)
                    )
                    db.commit()
                    room.send_text('@'+json.dumps({
                        "msg": "Created job",
                        "service": "a_pi",
                        "id": job_id}))
                    return job_id
                else:
                    abort(400)
            else:
                job_current = job_current['digits']
                if digit == 'π':
                    terminate(db, job, mill_stub)
                    return 'OK THX'
                if pi[job_current] == digit and job_current < MAX_PI:
                    action(db, job, job_current)
                    return 'π'
                else:
                    abort(418)

            return 'Hello, World! : {} for {}'.format(digit, job)
        else:
            abort(400)
    
    init_app(app)

    return app

app = create_app()
