import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

processo = [None]

def iniciar():
    if processo[0]:
        processo[0].kill()   
        processo[0].wait()   
        time.sleep(1)
    processo[0] = subprocess.Popen([sys.executable, "index.py"])

class Watcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("index.py"):
            print("Arquivo alterado, reiniciando...")
            iniciar()

iniciar()
observer = Observer()
observer.schedule(Watcher(), path=".", recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    if processo[0]:
        processo[0].kill()
observer.join()