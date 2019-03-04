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
SSH_DIR = "unitator_files"

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
    print(data)
    return data

def send(data):
    gopher_conn = socket.create_connection((GOPHER_IP, GOPHER_PORT))
    gopher_conn.send(data)
    return gopher_conn

def unit(segments, job_id):
    write(SSH_HOST, SSH_DIR, job_id, json.dumps(segments, indent=4))

def write(host, file_dir, job_id, text):
    subprocess.Popen('/usr/bin/kitty')
    sleep(3)
    pyautogui.typewrite('ssh ' + host + '\n')
    sleep(3)
    #pyautogui.hotkey('ctrl', 'd')
    pyautogui.typewrite("cd " + file_dir + '\n', interval=0.1)
    pyautogui.typewrite('vim ' + job_id + '\n', interval=0.1)
    sleep(1)
    pyautogui.typewrite('a')
    for line in text.split('\n'):
        pyautogui.typewrite(line, interval=0.05)
        pyautogui.press('enter')
    pyautogui.press('esc')
    pyautogui.typewrite(':x')
    pyautogui.press('enter')
    pyautogui.typewrite("exit\n")
    pyautogui.typewrite("exit\n")
    room.send_text('@' + json.dumps({
        "msg": "Wrote segments by ssh connection",
        "service": "unitator",
        "id": job_id
    }))

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
            print(data)
            
            if len(data) == 2:
                host = data[0]
                job_selector = data[1]

                job_conn = send(job_selector.encode()+b'\n')
                segments = json.loads(recv_data(job_conn))

                send(b'!/delete '+job_selector.encode()+b'\n')

                job_id = job_selector.split("/")[1]
                room.send_text('@' + json.dumps({
                    "msg": "Fetched segments",
                    "service": "unitator",
                    "id": job_id
                }))
                unit(segments, job_id)

listen()
