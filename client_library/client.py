#!/bin/python3
""" Module to generate mosaics using micro-tiling
"""

import requests
import json
import time


def launch_job(host):
    """Create a job for *host* and returns the **job_id**
    """
    r = requests.post(host)
    return json.loads(r.text)["id"]


def get_address(host, job_id):
    """Gets the ensicoin address needing fees for *job*
    """
    r = requests.get(host +
                     job_id +
                     "/address")
    if r.ok:
        return json.loads(r.text)["address"]
    else:
        return None


def manage_state(host, result):
    """Iterator on the completion of a job generation at *host*,

    Writes the mosaic in the list *result*
    """
    job_id = launch_job(host)
    while True:
        state = json.loads(requests.get(
                                host +
                                job_id +
                                "/state").text)
        if state["state"] == "finished":
            result.append(fetch_segments(host, job_id))
            break
        if state["state"] == "error":
            job_id = launch_job(host)
            continue
        yield (state["completion"], state["state"], job_id)
        time.sleep(10)


def generate_mosaic(host, on_invoice):
    """Wraps **manage_state** to return a result, uses *on_invoice* when
    needing to pay
    """
    result = []
    for _, state, job_id in manage_state(host, result):
        address = get_address(host, job_id)
        if address is not None:
            on_invoice(address)
    return result[0]


def fetch_segments(host, job_id):
    result = json.loads(requests.get(
                                host +
                                job_id +
                                "/result").text)
    return result["result"]


if __name__ == "__main__":
    import progressbar

    def wrap_bar(host):
        priv_key = input("Ensicoin private key to pay fees :")
        bar = progressbar.ProgressBar(max_value=100,
                                      widgets=["generating mosaic : ",
                                               progressbar.Bar(),
                                               progressbar.Timer()])
        bar.start()
        result = []
        for completion, state, _ in manage_state(host, result):
            bar.update(completion)
        f = open("output.svg", "w")
        f.write(result[0])
        f.close()

    import sys
    wrap_bar(sys.argv[1])
