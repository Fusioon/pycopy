import threading
import time
import requests
import json
from typing import Tuple

class DBListener:
    running: bool
    parent: "FirebaseDB"
    cb: callable(...)
    thread: "threading.Thread"
    url: str

    currentValue: any

    def __init__(self, parent: "FirebaseDB", path: str, cb: callable(any)):
        self.running = True
        self.thread = threading.Thread(target=self.proc)
        self.thread.start()
        self.url = f"{parent.dburl}{path}.json?{parent.auth}"
        self.cb = cb

    def stop(self):
        self.running = False

    def handleLine(self, line: str):
        DATA_LINE_START = "data: "
        if not line.startswith(DATA_LINE_START):
            return
        
        dataStr = line[len(DATA_LINE_START):]
        data = json.loads(dataStr)
        if not data:
            return
        
        if data['path'] == '/':
            self.currentValue = data['data']
        else:
            path = data[1:]
            self.currentValue[path] = data['data']
        
        self.cb(self.currentValue)

    def proc(self):
        header = {'Accept': 'text/event-stream'}
        while self.running:
            try:
                session = requests.Session()
                response = session.get(self.url, headers=header, stream=True, allow_redirects=True)

                for line in response.iter_lines(chunk_size=1, decode_unicode=True):
                    if line:
                        self.handleLine(line)
            except:
                time.sleep(1)

class FirebaseDB:
    dburl: str
    auth: str
    
    def __init__(self, url: str, secret: str):
        self.dburl = url
        self.auth = f"auth={secret}"

    def getPathUrl(self, path: str) -> str:
        return f"{self.dburl}{path}.json?{self.auth}"

    def ReadValue(self, path: str) -> Tuple[int, any]:
        headers = {"Accept": "application/json"}
        response = requests.get(self.getPathUrl(path), headers)
        if response.status_code == 200:
            return (response.status_code, json.loads(response.content))

        return (response.status_code, None)

    def PutValue(self, path: str, value : any) -> int:
        headers = {"Accept": "application/json"}
        response = requests.get(self.getPathUrl(path), headers)
        if response.status_code == 200:
            return json.loads(response.content)

        return response.status_code

    def Listen(self, path: str, cb : callable(any)) -> "DBListener": 
        return DBListener(self, path, cb)