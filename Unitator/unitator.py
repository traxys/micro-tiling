#!/usr/bin/python
import socket
import json
import os
import pyautogui
import subprocess
from matrix_client.client import MatrixClient
from time import sleep

GOPHER_IP = '127.0.0.1'
GOPHER_PORT = 3333

SSH_HOST = "localhost"

client = MatrixClient("http://localhost:8008")

matrix_param_file = open("../matrix_user.json","r")
matrix_param = json.loads(matrix_param_file.read())
matrix_param_file.close()

token = client.login(username=matrix_param["username"], password=matrix_param["password"])
room = client.join_room(matrix_param["room"]);

TCP_PORT = 1337
TCP_IP = '127.0.0.1'

def recv_data(conn):
    data = ""
    while True:
        new_data = conn.recv(1)
        if not new_data:
            break
        data += new_data.decode()
    return data

def send(data):
    gopher_conn = socket.create_connection((GOPHER_IP, GOPHER_PORT))
    gopher_conn.send(data)
    return gopher_conn

def unit(segments, job_id):
    pass

def write(host, job_id, text):
    subprocess.Popen('/usr/bin/kitty')
    sleep(3)
    pyautogui.typewrite('ssh ' + host + '\n')
    sleep(3)
    pyautogui.hotkey('ctrl', 'd')
    pyautogui.typewrite('vim ' + job_id + '\n', interval=0.1)
    sleep(1)
    pyautogui.typewrite('a')
    for line in text.split('\n'):
        pyautogui.typewrite(line, interval=0.05)
        pyautogui.press('enter')
    pyautogui.press('esc')
    pyautogui.typewrite(':x')
    pyautogui.press('enter')

def listen():
    notifier = socket.socket()
    notifier.bind((TCP_IP, TCP_PORT))

    send(b'!/notify '
         + (TCP_IP+':'+str(TCP_PORT)).encode()
         + b'\n')

    notifier.listen()
    while True:
        conn, _ = notifier.accept()
        data = conn.recv(19)
        conn.close()
        if data == b'pssssst want some ?':

            conn = send(b'\n')
            entries = recv_data(conn)

            for entry in entries.split('\n'):
                if len(entry.split('\t')) < 2:
                    continue
                selector = entry.split('\t')[1]
                if selector[0] == '0':
                    job_conn = send(selector.encode()+b'\n')
                    segments = json.loads(recv_data(job_conn))

                    send(b'!/delete '+selector.encode()+b'\n')

                    job_id = selector.split("/")[1]
                    room.send_text('@' + json.dumps({
                        "msg": "Fetched segments",
                        "service": "unitator",
                        "id": job_id
                    }))
                    unit(segments, job_id)

listen()
