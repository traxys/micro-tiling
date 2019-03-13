import os
import etcd

DATABASE_HOST = "http://localhost"
if "DATABASE_HOST" in os.environ:
    DATABASE_HOST = os.environ["DATABASE_HOST"]

DATABASE_PORT = "2379"
if "DATABASE_PORT" in os.environ:
    DATABASE_PORT = int(os.environ["DATABASE_PORT"])


def open_db():
    """Opens the database
    """
    return etcd.Client(host=DATABASE_HOST, port=DATABASE_PORT)


def update_state(db, new_state, job_id):
    """Update the state in *db* for the job *job_id*
    if it is less than *new_state*
    """
    key = '/{}/state'.format(job_id)
    old_state = int(db.read(key).value)
    if old_state < new_state:
        db.write(key, new_state)
