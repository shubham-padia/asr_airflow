import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os
import json

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

class Handler(FileSystemEventHandler):
    @staticmethod
    def on_created(event):
        file_path = event.src_path
        file_name = os.path.splitext(os.path.basename(file_path))[0]

        # metadata = parse_metadata(file_path)
        # conf_dict = {'metadata': metadata}
        conf_string = '{"metadata": %s}' % get_metadata_str(file_path) # json.dumps(conf_dict)
        # print("conf_string type: " + str(type(conf_string)))
        # print("file_name type: " + str(type(file_name)))

        my_env = os.environ.copy()
        my_env["AIRFLOW_HOME"] = "/home/shubham/github/asr_airflow"
        my_env["AIRFLOW_CONFIG"] = my_env["AIRFLOW_HOME"] + "/airflow.cfg"
        
        result = subprocess.run(["airflow", "trigger_dag", "-c", conf_string,
                                 file_name], env=my_env)
        # print(result.stdout)

if __name__ == '__main__':
    watcher = Watcher()
    watcher.run()
