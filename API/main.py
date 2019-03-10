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


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        database.run_transaction(db,
                                 lambda conn: conn.cursor().
                                 execute(f.read().decode('utf8')))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def get_db():
    if 'db' not in g:
        g.db = database.open_db()
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )

    init_app(app)

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

        state = None

        with db.cursor() as cur:
            state = cur.execute(
                'SELECT state FROM jobs WHERE jobs.id = ?',
                (job_id,)
            ).fetchone()

        if state is None:
            abort(404)

        state = state['state']

        return jsonify({"state": get_public_state(state),
                        "completion": round(state/MAX_STATE)})

    @app.route('/<string:job_id>/address', methods=('GET',))
    def get_address(job_id):
        db = get_db()

        address = None

        with db.cursor() as cur:
            address = cur.execute(
                'SELECT address FROM ensicoin WHERE id = ?',
                (job_id,)
            ).fetchone()

        if address is None:
            abort(404)

        address = address['address']

        return jsonify({"address": address})

    @app.route('/<string:job_id>/result', methods=('GET',))
    def get_result(job_id):
        db = get_db()

        result = None

        with db.cursor() as cur:
            result = cur.execute(
                'SELECT segments FROM result WHERE id = ?',
                (job_id,)
            ).fetchone()

        if result is None:
            abort(404)

        result = result['segments']

        return jsonify({"result": result})

    @app.route('/', methods=('POST',))
    def new_job():
        db = get_db()
        job_id = ''.join(random.choices(string.ascii_letters, k=20))

        def op(cur):
            cur.execute(
                'INSERT INTO jobs (id, state)'
                ' VALUES (?, ?)',
                (job_id, 0)
            )

        database.run_transaction(db, op)

        t = threading.Thread(target=init.generate_segments,
                             args=(job_id, A_PI_ADDRESS))
        t.start()

        return jsonify({"id": job_id})

    return app

app = create_app()
