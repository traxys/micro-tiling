import socket
import ensicoin
import json
import solidator
import database

TCP_IP = "127.0.0.1"
TCP_PORT = 2442


def listen():
    listener = socket.socket()
    listener.bind((TCP_IP, TCP_PORT))
    listener.listen()

    while True:
        conn, _ = listener.accept()
        data = conn.recv().decode()

        _, flags = ensicoin.wait_for_pubkey(data)

        if flags[0][0] == "[":
            segments = json.loads(flags[0])
            job_id = json.loads(flags[1])

        if flags[1][0] == "[":
            segments = json.loads(flags[1])
            job_id = json.loads(flags[0])

        points = solidator.create_points(segments)
        solidator.remove_deg_1(points)

        result = open("result.svg", "r")
        svg_data = result.read()
        result.close()

        database.open_db().write("/{}/result".format(job_id), svg_data)
