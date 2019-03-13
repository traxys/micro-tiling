#!/usr/bin/python
import pyinotify
import json
import os
import gnupg
import translator
import database

WATCH_DIR = '/app/jobs'
SMTP_HOST = 'localhost:8025'


def translation(segments, job_id, gpg):
    """Creates replicas of the segments in the eight directions
    """
    segments = translator.translate_segments(segments, True)

    database.update_state(database.open_db(), 16, job_id)

    send(SMTP_HOST, segments, job_id, gpg)


def encode(string):
    """ Encode the *string* in the most frequent kanji encoding
    """
    f = open('kanji', "r")
    kanji = json.loads(f.read())
    return ''.join(map(lambda c: kanji[ord(c)], string))


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


def listen(watch_dir):
    """Listen for new files in *watch_dir* and reads them, translates the
    segments and forwards them
    """
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CREATE

    gpg = gnupg.GPG(gnupghome='.')
    pub_file = open("keys/pub.gpg", "r")
    gpg.import_keys(pub_file.read())
    pub_file.close()
    gpg.trust_keys("032F62203EC4B1A332D54B93932CE0D477126DC5",
                   "TRUST_ULTIMATE")

    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CREATE(self, event):
            database.update_state(database.open_db(), 15, event.name)

            segment_file = open(event.pathname, "r")
            
            print(segment_file.read())
           
            try:
                segments = json.loads(segment_file.read())
            except json.JSONDecodeError:
                key = '/{}/state'.format(event.name)
                database.open_db().write(key, "-1")
            
            segment_file.close()

            translation(segments, event.name, gpg)
            os.remove(event.pathname)

    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)

    wm.add_watch(watch_dir, mask)
    notifier.loop()


if __name__ == "__main__":
    listen(WATCH_DIR)
