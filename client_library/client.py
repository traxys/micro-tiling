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


def manage_state(host, ensicoin_adress, result):
    """Iterator on the completion of a job generation at *host*,
    using the *ensicoin_adress* as needed.

    Writes the mosaic in the list *result*
    """
    job_id = launch_job(host)
    while True:
        state = json.loads(requests.get(
                                host +
                                job_id +
                                "/state").text)
        if state["state"] == "finished":
            break
        if state["state"] == "error":
            job_id = launch_job(host)
            continue
        yield state["completion"]
        time.sleep(10)


def generate_mosaic(host, ensicoin_address):
    """Wraps **manage_state** to return a result
    """
    result = []
    for _ in manage_state(host, ensicoin_address, result):
        pass
    return result[0]


if __name__ == "__main__":
    import progressbar

    def wrap_bar(host, ensicoin_address):
        bar = progressbar.ProgressBar(max_value=100,
                                      widgets=["generating mosaic : ",
                                               progressbar.Bar(),
                                               progressbar.Timer()])
        bar.start()
        result = []
        for completion in manage_state(
                            host,
                            ensicoin_address,
                            result):
            bar.update(completion)

    import sys
    wrap_bar(sys.argv[1], sys.argv[2])
