#!/bin/python3

import requests
import json
import time
import progressbar


def launch_job(host):
    r = requests.post(host)
    return json.loads(r.text)["id"]


def generate_mosaic(host, ensicoin_adress):
    job_id = launch_job(host)
    bar = progressbar.ProgressBar(max_value=100,
                                  widgets=["generating mosaic :",
                                           progressbar.Bar()])
    bar.update(0)
    while True:
        state = json.loads(requests.get(
                                host +
                                job_id +
                                "/state").text)
        bar.update(state["completion"])
        if state["state"] == "finished":
            break
        if state["state"] == "error":
            job_id = launch_job(host)
            continue
        time.sleep(10)


if __name__ == "__main__":
    import sys
    generate_mosaic(sys.argv[1], 0)
