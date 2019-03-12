import socket
from os import listdir
from os.path import isfile, join
import os

TCP_IP = '0.0.0.0'
HOST = 'Golfer'
TCP_PORT = 3333
FILE_DIR = '/olala/gopher/files'
DEFAULT_NOTIFIER = os.environ["DEFAULT_NOTIFIER"]
POD_IP = os.environ["POD_IP"]

def get_entries():
    """returns `[(DirEntry)]` as defined by the gopher protocol
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
    """returns a list of selectors for the known files
    """
    return ((f, "0/" + f)
            for f in listdir(FILE_DIR) if isfile(join(FILE_DIR, f)))


def main():
    """Starts the gopher server
    """
    listener = socket.socket()
    listener.bind((TCP_IP, TCP_PORT))
    listener.listen()
    print("Golfer started on port", TCP_PORT)

    notifications = [DEFAULT_NOTIFIER.split(':')]
    notifications[0][1] = int(notifications[0][1])

    print("Notifications:", notifications)

    while True:
        conn, addr = listener.accept()
        data = ""
        while True:
            new_data = conn.recv(1)
            if not new_data or new_data == b'\n':
                break
            data += new_data.decode()
        print(data, "from", addr)
        if data == '':
            for entry in get_entries():
                conn.send(entry.encode())
        else:
            data = data.split()
            if data[0] == "!/newfile":
                if len(data) == 2:
                    for addr in notifications:
                        try:
                            print('sending a notification to', addr)
                            notifier = socket.create_connection(addr)
                            notifier.send(b"pssssst want some ?" +
                                          POD_IP.encode() +
                                          b":" +
                                          str(TCP_PORT).encode() +
                                          b"|0/" +
                                          data[1].encode() +
                                          b"#")
                            notifier.close()
                        except ConnectionRefusedError:
                            print("Can't connect to notifier")
                        except socket.gaierror:
                            print("Invalid notifier address")
                    print("Notified")

            elif data[0] == "!/notify":
                print("Added hook: ", data)
                if len(data) == 2 and \
                   len(data[1].split(':')) == 2:
                    addr, port = data[1].split(':')
                    notifications.append((addr, port))

            elif data[0] == "!/delete":
                if len(data) == 2:
                    selector_requested = data[1]
                    for file_name in map(lambda x: x[0],
                                         filter(lambda x: x[1] == selector_requested,
                                                get_selectors())):
                        os.remove(FILE_DIR+'/'+file_name)


            for file_name, selector in get_selectors():
                if selector == data[0]:
                    selected_file = open(FILE_DIR+'/'+file_name, "r")
                    conn.send(selected_file.read().encode())
                    selected_file.close()
        conn.close()


if __name__ == "__main__":
    main()
