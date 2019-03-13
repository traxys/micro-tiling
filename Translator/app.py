import os
import subprocess
import database
import translator
import gnupg
import json

from flask import Flask
from flask import request

SMTP_ADDR = "localhost"
if "SMTP_ADDR" in os.environ:
    SMTP_ADDR = os.environ['SMTP_ADDR']


def translation(segments, job_id, gpg):
    """Creates replicas of the segments in the eight directions
    """
    segments = translator.translate_segments(segments, True)

    database.update_state(database.open_db(), 16, job_id)

    send(SMTP_ADDR, segments, job_id, gpg)


def encrypt(string, gpg):
    """ Encrypt the *string* in pgp encoded using the context *gpg*
    """
    enc = gpg.encrypt(string, gpg.list_keys()[0]['fingerprint'])
    return str(enc)


def send(host, segments, job_id, gpg):
    """Sends the encoded *segments* to the next service by smtp
    throught *host* encrypted using the *gpg* context
    """
    import smtplib

    sender = "translator@micro-tiling.tk"
    receivers = ["cruxingator@micro-tiling.tk"]
    message = """{}|""".format(job_id)

    message += json.dumps(segments) + "\n"
    database.update_state(database.open_db(), 17, job_id)

    message = encrypt(message, gpg)
    database.update_state(database.open_db(), 18, job_id)

    smtpObj = smtplib.SMTP(host)
    smtpObj.sendmail(sender, receivers, message.encode())
    database.update_state(database.open_db(), 19, job_id)


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    subprocess.Popen(["python3", "inotify_serv.py"])

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    gpg = gnupg.GPG(gnupghome='.')
    pub_file = open("keys/pub.gpg", "r")
    gpg.import_keys(pub_file.read())
    pub_file.close()
    gpg.trust_keys("032F62203EC4B1A332D54B93932CE0D477126DC5",
                   "TRUST_ULTIMATE")

    # a simple page that says hello
    @app.route('/', methods=("POST",))
    def write_to_file():
        job_id = request.form['job']
        segments = json.loads(request.form['message'])

        database.update_state(database.open_db(), 14, request.form['job'])

        translation(segments, job_id, gpg)
        return ""

    return app


app = create_app()

print("starting translator")

app.run(host='0.0.0.0', port=80)
