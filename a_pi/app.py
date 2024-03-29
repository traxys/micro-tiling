#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Flask a_pi executing an action on each digit of pi sent
"""

import etcd
import database
import os
from flask import Flask
from flask import g, request
from werkzeug.exceptions import abort
import json

import grpc

import mill_pb2
import mill_pb2_grpc

import segment_generator

MAX_PI = 1000
MILLLLLLLL_ADDR = "localhost:5001"
if "MILLLLLLLL_ADDR" in os.environ:
    MILLLLLLLL_ADDR = os.environ['MILLLLLLLL_ADDR']


def get_db():
    """Get the db associated with the application
    """
    if 'db' not in g:
        g.db = database.open_db()
    return g.db


def close_db(e=None):
    """Closes the DB
    """
    g.pop('db', None)


def make_pi(total):
    return list('3141592653589793238462643383279502884197169399375105820974944592307816406286')

def action(db, job_id, job_current):
    """Advances the state of the job *job_id* using the state *job_current* as
    inital state and executes an action, here `segment generation`_

    .. _segment generation: segment_generator.html#\
                            segment_generator.random_segment
    """

    db.write("/a_pi/{}/digit".format(job_id), job_current + 1)

    segments = json.loads(db.read("/a_pi/{}/segments".format(job_id)).value)
    if job_current == 0:
        segments.append(segment_generator.random_segment(1, 1))
    else:
        segments.append(segment_generator.random_segment(1.2, 1.2))
    db.write("/a_pi/{}/segments".format(job_id), json.dumps(segments))


def terminate(db, job_id, mill_stub):
    """Finishes the job *job_id* and forwards it to the *mill_stub*
    """
    database.update_state(database.open_db(), 2, job_id)

    segments = json.loads(db.read("/a_pi/{}/segments".format(job_id)).value)

    segments = [mill_pb2.Segment(
                    a=mill_pb2.Point(
                        x=s[0],
                        y=s[1]),
                    b=mill_pb2.Point(
                        x=s[2],
                        y=s[3])) for s in segments]

    mill_stub.Turn(mill_pb2.Job(id=job_id,
                                         segments=segments))
    database.update_state(database.open_db(), 3, job_id)

    db.delete("/a_pi/{}/segments".format(job_id))
    db.delete("/a_pi/{}/digit".format(job_id))


def create_app(test_config=None):
    """Generates the Flask application"""
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    channel = grpc.insecure_channel(MILLLLLLLL_ADDR)
    mill_stub = mill_pb2_grpc.MillStub(channel)

    pi = make_pi(MAX_PI)

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

            if digit not in valid:
                print('unexpected :', digit)
                abort(400)

            try:
                job_current = int(db.read("/a_pi/{}/digit".format(job)).value)
            except etcd.EtcdKeyNotFound:
                if digit == '3':
                    db.write("/a_pi/{}/digit".format(job), 1)
                    db.write("/a_pi/{}/segments".format(job), "[]")
                    action(db, job, 0)
                    return 'π'
                else:
                    abort(400)

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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
