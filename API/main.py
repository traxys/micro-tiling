import os
import database
import string
import random
from flask import Flask
import init
import etcd

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.exceptions import abort
from flask import jsonify

import threading

MAX_STATE = 42
A_PI_ADDRESS = os.environ['A_PI_ADDRESS'] or 'http://localhost:5000'


def get_public_state(state):
    if state == -1:
        return "error"
    elif state == 0:
        return "started"
    elif state <= 3:
        return "generating segments"
    elif state <= 7:
        return "rotating segments"
    elif state <= 12:
        return "clipping segments"
    elif state <= 19:
        return "translating segments"
    elif state <= 22:
        return "cutting segments"
    elif state == 23:
        return "waiting fees"


def get_db():
    if 'db' not in g:
        g.db = database.open_db()
    return g.db


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
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

    @app.route('/health', methods=('GET',))
    def health():
        return 'ok'

    @app.route('/<string:job_id>/state', methods=('GET',))
    def get_state(job_id):
        db = get_db()

        try:
            state = db.read("/{}/state".format(job_id))
        except etcd.EtcdKeyNotFound:
            abort(404)

        return jsonify({"state": get_public_state(state),
                        "completion": round(state/MAX_STATE)})

    @app.route('/<string:job_id>/address', methods=('GET',))
    def get_address(job_id):
        db = get_db()

        try:
            address = db.read("/{}/address".format(job_id))
        except etcd.EtcdKeyNotFound:
            abort(404)

        return jsonify({"address": address})

    @app.route('/<string:job_id>/result', methods=('GET',))
    def get_result(job_id):
        db = get_db()

        result = None

        try:
            result = db.read("/{}/result".format(job_id))
        except etcd.EtcdKeyNotFound:
            abort(404)

        return jsonify({"result": result})

    @app.route('/', methods=('POST',))
    def new_job():
        db = get_db()
        job_id = ''.join(random.choices(string.ascii_letters, k=20))

        db.write("/{}/state".format(job_id), 0)

        init.generate_segments(job_id, A_PI_ADDRESS)

        return jsonify({"id": job_id})

    return app

app = create_app()
