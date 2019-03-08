#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Flask a_pi executing an action on each digit of pi sent
"""

import sqlite3
import os
import click
from flask import Flask
from flask import current_app, g, request
from flask.cli import with_appcontext
from werkzeug.exceptions import abort

import grpc

import threading

import mill_pb2
import mill_pb2_grpc

import segment_generator

MAX_PI = 1000
MILLLLLLLL_ADDR = os.environ['MILLLLLLLL_ADDR']

def get_db():
    """Get the db associated with the application
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """Closes the DB
    """
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    """Generates a DB from a `schema.sql` file
    """
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables.

    Usable from the command line: `flask init-db`"""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    """Adds the database functions to the application *app*
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def make_pi(total):
    """Generates up to *total* digits of pi
    """
    q, r, t, k, m, x = 1, 0, 1, 1, 3, 3
    count = 0
    while True:
        if 4 * q + r - t < m * t:
            yield m
            count += 1
            if count > total:
                break
            q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k, \
                (10*(3*q+r))//t - 10*m, x
        else:
            q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1, \
                (q*(7*k+2)+r*x)//(t*x), x+2


def action(db, job_id, job_current):
    """Advances the state of the job *job_id* using the state *job_current* as
    inital state and executes an action, here `segment generation`_

    .. _segment generation: segment_generator.html#\
                            segment_generator.random_segment
    """
    db.execute(
        'UPDATE job SET digits = ?'
        ' WHERE id = ?',
        (job_current + 1, job_id)
    )
    db.execute(
        'INSERT INTO segment (job_id, x1, y1, x2, y2)'
        ' VALUES (?, ?, ?, ?, ?)',
        (job_id,) + segment_generator.random_segment(1, 1)
    )
    db.commit()


def terminate(db, job_id, mill_stub):
    """Finishes the job *job_id* and forwards it to the *mill_stub*
    """
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
                        y=s['y2'])) for s in segments]

    t = threading.Thread(target=mill_stub.Turn,
                         args=(mill_pb2.Job(
                                id=job_id,
                                segments=segments,
                            ), ))
    t.start()

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
    """Generates the Flask application"""
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

    @app.route('/health', methods=('GET',))
    def health():
        return 'ok'

    @app.route('/', methods=('POST',))
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
                    db.execute(
                        'INSERT INTO job (id, digits)'
                        ' VALUES (?, ?)',
                        (job, 1)
                    )
                    db.commit()
                    action(db, job, 0)
                    return 'π'
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

        else:
            abort(400)

    init_app(app)

    return app

app = create_app()
