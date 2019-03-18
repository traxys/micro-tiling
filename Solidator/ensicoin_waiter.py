import socket
import ensicoin
import json
import solidator
import database
import os
import shutil

TCP_IP = "0.0.0.0"
TCP_PORT = 2442


def listen():
    listener = socket.socket()
    listener.bind((TCP_IP, TCP_PORT))
    listener.listen()

    while True:
        conn, _ = listener.accept()

        print("connection accepted")

        data = conn.recv(66).decode()

        print("data:", data)

        _, flags = ensicoin.wait_for_pubkey(data)

        print("flags: ", flags)

        segments = None
        job_id = None

        if flags[0][0] == "[":
            segments = json.loads(flags[0])
            job_id = flags[1]

        if flags[1][0] == "[":
            segments = json.loads(flags[1])
            job_id = flags[0]

        print("segments: ", segments)
        print("job_id: ", job_id)

        database.update_state(database.open_db(), 26, job_id)

        print("saving results")
        
        points = solidator.create_points(segments)
        os.mkdir(job_id)
        os.chdir(job_id)
        solidator.remove_deg_1(points, job_id, True)

        result = open("result.svg", "r")
        svg_data = result.read()
        result.close()

        os.chdir("..")
        shutil.rmtree(job_id)

        database.open_db().write("/{}/result".format(job_id), svg_data)
        database.update_state(database.open_db(), 31, job_id)

if __name__ == "__main__":
    print('starting solidator')
    listen()
