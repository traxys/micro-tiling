import os
import database
import string
import random
from flask import Flask
import init

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.exceptions import abort
from flask import jsonify

import threading

MAX_STATE = 42
A_PI_ADDRESS = os.environ['A_PI_ADDRESS']


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


def init_db():
    with current_app.open_resource('schema.sql') as f:
        database.run_transaction(lambda conn: conn.cursor().execute(f.read().decode('utf8')))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.cli.add_command(init_db_command)


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )

    init_app(app)

    with app.app_context():
        init_db()

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
        state = None

        with database.open_db().cursor() as cur:
            cur.execute(
                'SELECT state FROM jobs WHERE jobs.id = %s',
                (job_id,)
            )

            state = cur.fetchone()

            print(state)

        if state is None:
            abort(418)

        state = state[0]

        return jsonify({"state": get_public_state(state),
                        "completion": round(state/MAX_STATE)})

    @app.route('/<string:job_id>/address', methods=('GET',))
    def get_address(job_id):
        address = None

        with database.open_db().cursor() as cur:
            address = cur.execute(
                'SELECT address FROM ensicoin WHERE id = %s',
                (job_id,)
            ).fetchone()

        if address is None:
            abort(404)

        address = address['address']

        return jsonify({"address": address})

    @app.route('/<string:job_id>/result', methods=('GET',))
    def get_result(job_id):
        result = None

        with database.open_db().cursor() as cur:
            result = cur.execute(
                'SELECT segments FROM result WHERE id = %s',
                (job_id,)
            ).fetchone()

        if result is None:
            abort(404)

        result = result['segments']

        return jsonify({"result": result})

    @app.route('/', methods=('POST',))
    def new_job():
        job_id = ''.join(random.choices(string.ascii_letters, k=20))

        def op(conn):
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO jobs (id, state)'
                    ' VALUES (%s, %s)',
                    (job_id, 0)
                )

        database.run_transaction(op)

        init.generate_segments(job_id, A_PI_ADDRESS)

        return jsonify({"id": job_id})

    return app

app = create_app()

