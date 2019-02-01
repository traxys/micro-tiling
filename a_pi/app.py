from flask import Flask
import sqlite3
import click
import random
import string
from flask import current_app, g, request
from flask.cli import with_appcontext
from werkzeug.exceptions import abort
import os

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

    @app.route('/', methods=('GET', 'POST'))
    def hello():
        digits = [str(i) for i in range(0, 10)]
        if request.method == 'POST':
            digit = request.form['digit']
            job = request.form['job']
            
            db = get_db()
            job_current = db.execute(
                'SELECT job.digits FROM job WHERE job.id = ?',
                (job,)
            ).fetchone()
            print(job_current)
            
            if digit not in digits:
                abort(400)
            
            if job_current is None and digit == '3':
                job_current = ''.join(random.choices(string.ascii_letters, k=20))
                db.execute(
                    'INSERT INTO job (id, digits)'
                    ' VALUES (?, ?)',
                    (job_current, 0)
                )
                db.commit()
                return job_current

            return 'Hello, World! : {} for {}'.format(digit, job)
        else:
            abort(400)
    
    init_app(app)

    return app

create_app()
