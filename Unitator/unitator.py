#!/usr/bin/python
import socket
import json
import subprocess
from time import sleep
import database
import clipping

from pyvirtualdisplay import Display
from selenium import webdriver

TCP_PORT = 1337
TCP_IP = '0.0.0.0'


def recv_data(conn):
    """Receive all data from a socket *conn*
    """
    data = ""
    while True:
        new_data = conn.recv(1)
        if not new_data:
            break
        data += new_data.decode()
    return data


def send(data, host, port):
    """Sends *data* using a gopher connnection on *host*:*port*
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
    database.update_state(database.open_db(), 10, job_id)

    tuple_segments = [(
                        (segment.a.x, segment.a.y),
                        (segment.b.x, segment.b.y)
                      ) for segment in clipped_segments]
    write(job_id,
          json.dumps(tuple_segments, indent=4))


def write(job_id, text):
    """Writes a *text* by an html form
    """
    database.update_state(database.open_db(), 11, job_id)
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
    database.update_state(database.open_db(), 12, job_id)


def listen():
    """Start a Unitator server listening for notifications of
    a golfer server
    """
    notifier = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    notifier.bind((TCP_IP, TCP_PORT))

    notifier.listen()
    
    print('listening')
    
    while True:
        conn, _ = notifier.accept()
        print('accepted')
        
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

                print('>', host, ip, job_selector)

                job_conn = send(job_selector.encode()+b'\n', host, ip)
                raw = recv_data(job_conn)
                segments = json.loads(raw)

                send(b'!/delete '+job_selector.encode()+b'\n', host, ip)

                job_id = job_selector.split("/")[1]
                database.update_state(database.open_db(), 9, job_id)
                unit(segments, job_id)


if __name__ == "__main__":
    print('starting')

    listen()
