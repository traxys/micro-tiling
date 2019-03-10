#!/usr/bin/python
import socket
import json
import subprocess
from time import sleep
import clipping

from pyvirtualdisplay import Display
from selenium import webdriver

GOPHER_IP = '127.0.0.1'
GOPHER_PORT = 3333

TCP_PORT = 1337
TCP_IP = '127.0.0.1'


def recv_data(conn):
    """Recv all data from a socket *conn*
    """
    data = ""
    while True:
        new_data = conn.recv(1)
        if not new_data:
            break
        data += new_data.decode()
    return data


def send(data, host, port):
    """Send *data* using a gopher connnection on *host*:*port*
    """
    gopher_conn = socket.create_connection((host, port))
    gopher_conn.send(data)
    return gopher_conn


def unit(segments, job_id):
    """Clip *segments* of the job *job_id* into a unit square and forwards them
    """
    segments = [clipping.segment(
                    clipping.p(segment[0][0], segment[0][1]),
                    clipping.p(segment[1][0], segment[1][1])
                ) for segment in segments]

    clipped_segments = clipping.clip_unit_square(segments)

    tuple_segments = [(
                        (segment.a.x, segment.a.y),
                        (segment.b.x, segment.b.y)
                      ) for segment in clipped_segments]
    write(job_id,
          json.dumps(tuple_segments, indent=4))


def write(job_id, text):
    """Writes a *text* by a html form
    """
    display = Display(visible=0, size=(1024, 768))
    display.start()

    browser = webdriver.Firefox()
    actions = webdriver.ActionChains(browser)
    browser.get("file:///app/test.html")
    message = browser.find_element_by_name("message")
    message.send_keys(text)
    job = browser.find_element_by_name("job")
    job.send_keys(job_id)
    job.submit()


def listen():
    """Start a Unitator server listening for notifications of
    a golfer server
    """
    notifier = socket.socket()
    notifier.bind((TCP_IP, TCP_PORT))

    send(b'!/notify '
         + (TCP_IP+':'+str(TCP_PORT)).encode()
         + b'\n', GOPHER_IP, GOPHER_PORT)

    notifier.listen()
    while True:
        conn, _ = notifier.accept()
        data = conn.recv(19)
        if data == b'pssssst want some ?':
            data = b""
            while True:
                new_data = conn.recv(1)
                if not new_data or new_data == b'#':
                    break
                data += new_data
            conn.close()

            data = data.decode()
            data = data.split('|')

            if len(data) == 2:
                host, ip = data[0].split(":")
                job_selector = data[1]

                job_conn = send(job_selector.encode()+b'\n', host, ip)
                raw = recv_data(job_conn)
                segments = json.loads(raw)

                send(b'!/delete '+job_selector.encode()+b'\n', host, ip)

                job_id = job_selector.split("/")[1]
                unit(segments, job_id)


if __name__ == "__main__":
    listen()
