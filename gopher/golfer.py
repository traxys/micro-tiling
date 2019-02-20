import socket

TCP_IP = '127.0.0.1'
HOST = 'Golfer'
TCP_PORT = 3333
FILE_DIR = 'files'

from os import listdir
from os.path import isfile, join
import os

def get_entries():
    """returns [(DirEntry)]
    """
    commands = ['newfile', 'notify', 'delete']
    for com in commands:
        yield ("!Command\t"
               + "!/" + com + "\t"
               + HOST + "\t"
               + str(TCP_PORT) + "\n")
    for entry in (("0" + f + "\t"
                   + "0/" + f + "\t"
                   + HOST + "\t"
                   + str(TCP_PORT) + "\n")
                  for f in listdir(FILE_DIR)
                  if isfile(join(FILE_DIR, f))):
        yield entry

def get_selectors():
    return ((f, "0/" + f)
            for f in listdir(FILE_DIR) if isfile(join(FILE_DIR, f)))
    
def main():
    listener = socket.socket()
    listener.bind((TCP_IP, TCP_PORT))
    listener.listen()
    print("Golfer started on port", TCP_PORT)

    notifications = []

    while True:
        conn, _ = listener.accept()
        data = ""
        while True:
            new_data = conn.recv(1)
            if not new_data or new_data == b'\n':
                break
            data += new_data.decode()
        
        if data == '':
            for entry in get_entries():
                conn.send(entry.encode())
        else:
            if data == "!/newfile":
                for notifier in notifications:
                    notifier.send(b"pssssst want some ?")
            
            
            if data.split()[0] == "!/notify":
                if len(data.split()) == 2 and len(data.split()[1].split(':')) == 2:
                    addr, port = data.split()[1].split(':')
                    try:
                        notifier = socket.create_connection((addr, port))
                        notifications.append(notifier)
                    except ConnectionRefusedError:
                        print("Can't connect to notifier")
                    except socket.gaierror:
                        print("Invalid notifier address")
            
            if data.split()[0] == "!/delete":
                if len(data.split()) == 2:
                    selector_requested = data.split()[1]
                    for file_name in map(lambda x: x[0],
                                         filter(lambda x: x[1] == selector_requested,
                                                get_selectors())):
                        os.remove(FILE_DIR+'/'+file_name)
            
            
            for file_name, selector in get_selectors():
                if selector == data:
                    selected_file = open(FILE_DIR+'/'+file_name, "r")
                    conn.send(selected_file.read().encode())
                    selected_file.close()
        conn.close()

main()
