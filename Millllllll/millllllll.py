import time
from concurrent import futures
import grpc
import json
import mill_pb2
import mill_pb2_grpc
from google.protobuf import json_format

GOPHER_PATH = '../gopher/files/'

from matrix_client.client import MatrixClient
client = MatrixClient("http://localhost:8008")

import json
matrix_param_file = open("../matrix_user.json","r")
matrix_param = json.loads(matrix_param_file.read())
matrix_param_file.close()

token = client.login(username=matrix_param["username"], password=matrix_param["password"])
room = client.join_room(matrix_param["room"]);

def write(job):
    room.send_text('@' + json.dumps({
        "msg": "Wrote to gopher server",
        "service": "millllllll",
        "id": job.id.id
    }))
    f = open(GOPHER_PATH + job.id.id, 'w')
    print(list(job.result))
    f.write(json.dumps(list(job.result)))
    f.close()

class MillServicer(mill_pb2_grpc.MillServicer):
    def Turn(self, request, context):
        write(request)
        room.send_text('@' + json.dumps({
            "msg": "Turned segments",
            "service": "millllllll",
            "id": request.id.id
        }))
        return mill_pb2.Response()

def serve():
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
