#!/usr/bin/python
import socket
import json
import pyautogui
import subprocess
from time import sleep

GOPHER_IP = '127.0.0.1'
GOPHER_PORT = 3333

SSH_HOST = "localhost"
SSH_DIR = "unitator_files"

TCP_PORT = 1337
TCP_IP = '127.0.0.1'

TERMINAL = "/usr/bin/kitty"


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
    write(TERMINAL, SSH_HOST, SSH_DIR, job_id, json.dumps(segments, indent=4))


def write(terminal, host, file_dir, job_id, text):
    """Writes a *text* by ssh to the *host*,
    in the directory *file_dir* in a file named *job_id*
    using the *terminal* provided
    """
    subprocess.Popen(terminal)
    sleep(2)
    pyautogui.typewrite('ssh ' + host + '\n')
    sleep(2)
    pyautogui.hotkey('ctrl', 'd')
    pyautogui.typewrite("cd " + file_dir + '\n', interval=0.1)
    pyautogui.typewrite('vim ' + job_id + '\n', interval=0.1)
    sleep(1)
    pyautogui.typewrite('a')
    pyautogui.press('capslock')
    for line in text.split('\n'):
        pyautogui.typewrite(line)
        pyautogui.press('enter')
    pyautogui.press('capslock')
    pyautogui.press('esc')
    pyautogui.typewrite(':x')
    pyautogui.press('enter')
    pyautogui.typewrite("exit\n")
    pyautogui.typewrite("exit\n")


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

#listen()
