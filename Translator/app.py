import os
import subprocess
import database

from flask import Flask
from flask import request


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    subprocess.Popen(["python3", "inotify_serv.py"])

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/', methods=("POST",))
    def write_to_file():
        f = open("/app/jobs/{}".format(request.form['job']), "w")
        print(request.form['message'])
        f.write(request.form['message'])

        database.update_state(database.open_db(), 14, request.form['job'])

        f.close()

        return ""

    return app

app = create_app()

print("starting translator")

app.run(host='0.0.0.0', port=80)
