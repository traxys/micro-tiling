#!/usr/bin/python
import pyinotify
import json
import os

WATCH_DIR = '/home/traxys/unitator_files'


def translation(segments, job_id):
    """Creates replicas of the segments in the eight directions
    """
    pass


def listen(watch_dir):
    """Listen for new files in *watch_dir* and reads them, translates the
    segments and forwards them
    """
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CREATE

    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CREATE(self, event):
            segment_file = open(event.pathname, "r")
            segments = json.loads(segment_file.read())
            segment_file.close()
            translation(segments, event.name)
            os.remove(event.pathname)

    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)

    wm.add_watch(watch_dir, mask)
    notifier.loop()

#listen(watch_dir)
