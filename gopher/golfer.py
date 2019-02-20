import socket

TCP_IP = '127.0.0.1'
HOST = 'Golfer'
TCP_PORT = 3333
FILE_DIR = 'files'

from os import listdir
from os.path import isfile, join

def get_entries():
    """returns [(DirEntry)]
    """
    return (("0" + f + "\t"
             + "0/" + f + "\t"
             + HOST + "\t"
             + str(TCP_PORT) + "\n")
            for f in listdir(FILE_DIR) if isfile(join(FILE_DIR, f)))

def get_selectors():
    return ((f, "0/" + f)
            for f in listdir(FILE_DIR) if isfile(join(FILE_DIR, f)))
    
def main():
    listener = socket.socket()
    listener.bind((TCP_IP, TCP_PORT))
    listener.listen()
    print("Golfer started on port", TCP_PORT)

    while True:
        conn, addr = listener.accept()
        data = ""
        while True:
            new_data = conn.recv(1)
            if not new_data or new_data == b'\n':
                break
            data += new_data.decode()
        if data == '':
            print("Listing files")
            for entry in get_entries():
                conn.send(entry.encode())
        for file_name, selector in get_selectors():
            if selector == data:
                selected_file = open(FILE_DIR+'/'+file_name, "r")
                conn.send(selected_file.read().encode())
                selected_file.close()
        conn.close()

main()
