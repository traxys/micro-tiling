import socket
TCP_IP = '127.0.0.1'
TCP_PORT = 1111


def main():
    listener = socket.socket()
    listener.bind((TCP_IP, TCP_PORT))
    listener.listen()
    print("Golfer started")

    while True:
        conn, addr = listener.accept()
        data = ""
        while True:
            new_data = conn.recv(1)
            if not new_data or new_data == b'\n':
                conn.close()
                break
            data += new_data.decode()
        print("received data:", data)

main()
