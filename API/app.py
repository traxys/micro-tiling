import os
import etcd
import asyncio
import random
import requests
import string
from quart import Quart, jsonify, abort
from database import open_db, update_state

MAX_STATE = 42
A_PI_ADDRESS = os.environ['A_PI_ADDRESS']

def make_pi(total):
    q, r, t, k, m, x = 1, 0, 1, 1, 3, 3
    count = 0
    while True:
        if 4 * q + r - t < m * t:
            yield m
            count += 1
            if count > total:
                break
            q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k,\
                (10*(3*q+r))//t - 10*m, x
        else:
            q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1,\
                (q*(7*k+2)+r*x)//(t*x), x+2


MAX_SEGMENT = 20
MIN_SEGMENT = 5


async def generate_segments(db, job_id, address):
    """Generate segments for *job_id* using a_pi at host at *address*
    """

    print(0)

    pi = make_pi(random.randint(MIN_SEGMENT, MAX_SEGMENT))
    print(1)
    update_state(db, 1, job_id)

    print(2)

    for digit in pi:
        payload = {'digit': str(digit), 'job': job_id}
        print('-->', requests.post(address, data=payload))

    done = {'digit': 'π', 'job': job_id}
    print('->', requests.post(address, data=done))


    return job_id


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


app = Quart(__name__)

@app.route('/<string:job_id>/state', methods=('GET',))
async def get_state(job_id):
    try:
        state = open_db().read("/{}/state".format(job_id))
    except etcd.EtcdKeyNotFound:
        abort(404)

    return jsonify({"state": get_public_state(state),
                    "completion": round(state/MAX_STATE)})

@app.route('/<string:job_id>/address', methods=('GET',))
async def get_address(job_id):
    try:
        address = open_db().read("/{}/address".format(job_id))
    except etcd.EtcdKeyNotFound:
        abort(404)

    return jsonify({"address": address})

@app.route('/<string:job_id>/result', methods=('GET',))
async def get_result(job_id):
    result = None

    try:
        result = open_db().read("/{}/result".format(job_id))
    except etcd.EtcdKeyNotFound:
        abort(404)

    return jsonify({"result": result})

@app.route('/', methods=('POST',))
async def new_job():
    job_id = ''.join(random.choices(string.ascii_letters, k=20))

    db = open_db()

    db.write("/{}/state".format(job_id), 0)

    asyncio.ensure_future(generate_segments(db, job_id, A_PI_ADDRESS))

    return jsonify({"id": job_id})
