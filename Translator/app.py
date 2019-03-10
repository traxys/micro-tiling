import os
import subprocess

from flask import Flask
from flask import request


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    subprocess.Popen(["python3", "inotify-serv.py"])

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/', methods=("POST",))
    def write_to_file():
        f = open("../jobs/{}".format(request.form['job']), "w")
        f.write(request.form['message'])
        f.close()

        return ""

    return app

app = create_app()
