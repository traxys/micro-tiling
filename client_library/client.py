#!/bin/python3

import requests
import json
import time


def launch_job(host):
    r = requests.post(host)
    return json.loads(r.text)["id"]


def manage_state(host, ensicoin_adress, result):
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
    result = []
    for _ in manage_state(host, ensicoin_address, result):
        pass
    return result


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
