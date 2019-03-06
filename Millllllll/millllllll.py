"""gRPC server to rotate segments
"""

import time
from concurrent import futures
import grpc
import mill_pb2
import mill_pb2_grpc
import socket
from google.protobuf.json_format import MessageToDict

GOPHER_PATH = '../gopher/files/'
GOPHER_IP = '127.0.0.1'
GOPHER_PORT = 3333


def write(job, job_id):
    """Write a *job* to a gopher served directory
    while notifing a golfer server of the *job_id*
    """
    f = open(GOPHER_PATH + job.id.id, 'w')
    f.write(job)
    f.close()
    GOPHER_SOCKET = \
        socket.create_connection((GOPHER_IP, GOPHER_PORT))
    GOPHER_SOCKET.send(b'!/newfile ' + job.id.id.encode() + b'\n')
    GOPHER_SOCKET.close()


class MillServicer(mill_pb2_grpc.MillServicer):
    """Serves a Millllllll gRPC server
    """
    def Turn(self, request, context):
        """Turns segments contained in the RPC message *request*
        """
        # write(request)
        return mill_pb2.Response()


def serve():
    """Start the Millllllll server
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mill_pb2_grpc.add_MillServicer_to_server(
        MillServicer(), server)
    server.add_insecure_port('[::]:5001')
    server.start()
    try:
        while True:
            time.sleep(1000000)
    except KeyboardInterrupt:
        server.stop(0)

serve()
