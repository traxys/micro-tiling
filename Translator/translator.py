import pyinotify
import json
from matrix_client.client import MatrixClient

def get_room():
    client = MatrixClient("http://localhost:8008")

    matrix_param_file = open("../matrix_user.json","r")
    matrix_param = json.loads(matrix_param_file.read())
    matrix_param_file.close()

    token = client.login(username=matrix_param["username"], password=matrix_param["password"])
    return client.join_room(matrix_param["room"]);

ROOM = get_room()

def translation(segments, job_id):
    ROOM.send_text('@' + json.dumps({
        "msg": "Read segments",
        "service": "translator",
        "id": job_id
    }))
    print(job_id, segments)

def listen():
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CREATE

    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CREATE(self, event):
            segment_file = open(event.pathname, "r")
            segments = json.loads(segment_file.read())
            segment_file.close()
            translation(segments, event.name)

    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)

    wm.add_watch('/home/traxys/unitator_files', mask)
    notifier.loop()

listen()
