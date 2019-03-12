"""gRPC server to rotate segments
"""

import database
import time
from concurrent import futures
import grpc
import mill_pb2
import mill_pb2_grpc
import socket
from google.protobuf.json_format import MessageToDict
import rotate
import json


GOPHER_PATH = 'gopher/files/'
GOPHER_IP = '127.0.0.1'
GOPHER_PORT = 3333


def write(job, job_id):
    """Write a *job* to a gopher served directory
    while notifing a golfer server of the *job_id*
    """
    f = open(GOPHER_PATH + job_id, 'w')
    f.write(job)
    f.close()
    GOPHER_SOCKET = \
        socket.create_connection((GOPHER_IP, GOPHER_PORT))
    GOPHER_SOCKET.send(b'!/newfile ' + job_id.encode() + b'\n')
    GOPHER_SOCKET.close()


def segment_to_tuple(segment):
    """Transforms a *segment* from a dict to a tuple
    """
    return ((segment['a']['x'], segment['a']['y']),
            (segment['b']['x'], segment['b']['y']))


class MillServicer(mill_pb2_grpc.MillServicer):
    """Serves a Millllllll gRPC server
    """
    def Turn(self, request, context):
        """Turns segments contained in the RPC message *request*
        """
        print("DEEEEEEEEEE")
        status_db = database.open_db()
        database.update_state(status_db, 4, request.id)

        segments = MessageToDict(request)["segments"]
        segments = list(map(segment_to_tuple, segments))

        database.update_state(status_db, 5, request.id)
        rotated_segments = rotate.mirror_and_turn_segments(segments, True)
        database.update_state(status_db, 6, request.id)

        write(json.dumps(list(rotated_segments)), request.id)
        database.update_state(status_db, 7, request.id)

        return mill_pb2.Response()


def serve():
    """Start the Millllllll server
    """
    print('starting millllllll server...')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mill_pb2_grpc.add_MillServicer_to_server(
        MillServicer(), server)
    server.add_insecure_port('[::]:5001')
    server.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
