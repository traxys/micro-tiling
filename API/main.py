import os
import sqlite3
import string
import random
from flask import Flask
import init

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.exceptions import abort
from flask import jsonify

MAX_STATE = 42
A_PI_ADDRESS = os.environ['A_PI_ADDRESS'] or 'http://localhost:5000'


def get_public_state(state):
    return "started"


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


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
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

    @app.route('/<string:job_id>/state', methods=('GET',))
    def get_state(job_id):
        db = get_db()
        state = db.execute(
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
        address = db.execute(
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
        result = db.execute(
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
        db.execute(
            'INSERT INTO jobs (id, state)'
            ' VALUES (?, ?)',
            (job_id, 0)
        )
        db.commit()
        init.generate_segments(job_id, A_PI_ADDRESS)
        return jsonify({"id": job_id})

    return app

app = create_app()
