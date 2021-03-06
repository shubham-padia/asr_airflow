import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os
import json
from models.base import Session
from models.metadata_registry import MetadataRegistry
import uuid
import shutil

def parse_metadata(metadata_file_path):
    with open(metadata_file_path, "r") as stream:
        try:
            metadata = json.loads(stream)
        except ValueError as exc:
            print(exc)
    return metadata

def get_metadata_str(metadata_file_path):
    with open(metadata_file_path, "r") as stream:
	    return stream.read().replace('\n', '')
        
class Watcher:
    directory_to_watch = "/home/shubham/github/asr_airflow/metadata/"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.directory_to_watch,
                               recursive=True)

        #creates a new thread, each observer runs on a separate thread.
        self.observer.start()
        print("To stop the watcher please press ctrl-c")

        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
            print("\nWatcher has been stopped safely")
        
        # Blocks the thread in which you're making the call, until
        # `self.observer` stops running.
        self.observer.join()

def parse_json(metadata_file_path):
    metadata = None 
    with open(metadata_file_path, "r") as stream:
        try:
            metadata = json.loads(stream.read())
        except ValueError as exc:
            print(exc)
    
    return metadata

def move_file(file_path):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    new_file_path = "%s/metadata/%s-%s.json" % (os.getcwd(), file_name,
            str(uuid.uuid4()))
    shutil.move(file_path, new_file_path)
    return new_file_path

class Handler(FileSystemEventHandler):
    @staticmethod
    def on_created(event):
        print(event)
        file_path = event.src_path
        pipeline_info = parse_json(file_path)
        file_extension = os.path.splitext(os.path.basename(file_path))[1]
        print(file_extension)
        if file_extension == '.json':
            file_path = move_file(file_path)
            session = Session()
            metadata_entry = MetadataRegistry(file_path, pipeline_info.get('version', '0.0.1'), False)
            session.add(metadata_entry)
            session.commit()
            session.close()

if __name__ == '__main__':
    watcher = Watcher()
    watcher.run()
