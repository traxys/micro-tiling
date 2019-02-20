import time
from concurrent import futures
import grpc
import json
import mill_pb2
import mill_pb2_grpc
from google.protobuf import json_format

GOPHER_PATH = '/srv/gopher/'

def write(job):
    f = open(GOPHER_PATH + job.id.id, 'w')
    print(list(job.result))
    f.write(json.dumps(list(job.result)))
    f.close()

class MillServicer(mill_pb2_grpc.MillServicer):
    def Turn(self, request, context):
        write(request)
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
