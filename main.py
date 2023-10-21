from datetime import datetime, timezone
from time import sleep
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Controller
import pyperclip
import requests
from firebasedb import FirebaseDB
from threading import Event, Thread
import queue
import sys
import socket

from conf import *

class EventType:
    COPY = 1
    PASTE = 2
    CLOSE = 3


if len(sys.argv) >= 2:
    arg = sys.argv[1].lower()
    eventType: EventType
    if (arg == "copy"):
        eventType = EventType.COPY
    elif (arg == "paste"):
        eventType = EventType.PASTE
    elif (arg == "close"):
        eventType = EventType.CLOSE
    else:
        print(f"Unknown argument '{arg}'")
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("127.0.0.1", PORT))
        s.send(eventType.to_bytes(1, 'big') )
    sys.exit(0)


eventQueue = queue.SimpleQueue()
running = False
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(("127.0.0.1", PORT))
soc.listen()

AUTOMATE_REQUEST = {
    "secret": AUTOMATE_APIKEY,
    "to": AUTOMATE_EMAIL,
    "device": None,
    "priority": "normal",
    "payload": None
}

rtdb = FirebaseDB(FIREBASE_URL, FIREBASE_SECRET)
kb = Controller()

dbData = {}
dataEvent = Event()

def isTimestampValid(timestamp: int) -> bool:
    now = datetime.utcnow().timestamp()
    now -= MAX_DATA_AGE_S
    return now < timestamp

def onNewData(value):
    global dbData
    fromHotkey = not dataEvent.is_set()
    dbData = value
    dataEvent.set()
    if not ALLOW_DIRECT_PASTE:
        return
    
    if fromHotkey:
        return

    if isTimestampValid(dbData['time']):
        pasteText(dbData['data'])

dblistener = rtdb.Listen("", onNewData)

def sendAutomateRequest(text: str) -> bool:
    AUTOMATE_REQUEST["payload"] = text
    post_response = requests.post(AUTOMATE_ENDPOINT, json=AUTOMATE_REQUEST)
    return post_response.status_code == 200

def triggerCopy():
    print("copy")
    with kb.pressed(Key.ctrl):
        kb.press('c')
        kb.release('c')  
    
    sleep(0.03)
    clip = pyperclip.paste()
    sendAutomateRequest(clip)

def getFirebaseResponse(timeoutMS: int) -> str:
    global dbData

    if not dataEvent.wait(MAX_WAIT_TIME_S):
        return None
    
    if isTimestampValid(dbData['time']):
        return dbData['data']
    
    return None

def pasteText(text: str):
    pyperclip.copy(text)
    with kb.pressed(Key.ctrl):
        kb.press('v')
        kb.release('v')

def triggerPaste():
    print("paste")
    try:
        dataEvent.clear()
        sendAutomateRequest(COPY_MESSAGE_TEXT)
        data = getFirebaseResponse(4000)
        if data:
            pasteText(data)
        else:
            print("Failed to retrieve data")
    except:
        pass  

def onCopy():
    global eventQueue
    kb.release(Key.alt)
    kb.release("C")
    eventQueue.put(EventType.COPY)
    

def onPaste():
    global eventQueue
    kb.release(Key.alt)
    kb.release("X")
    eventQueue.put(EventType.PASTE)

def processPipe():
    global soc, running, eventQueue
    while running:
        conn, addr = soc.accept()
        with conn:
            data = conn.recv(1)
            event = int.from_bytes(data, byteorder='big')
            eventQueue.put(event)
            print(f"Received event: {event}")

h = None
if not ONLY_SYSTEM_HOTKEYS:
    h = keyboard.GlobalHotKeys({
            COPY_HOTKEY: onCopy,
            PASTE_HOTKEY: onPaste})
    h.start()


running = True
pipeThread = Thread(target=processPipe)
pipeThread.start()
while running:
    item = eventQueue.get()
    if item == EventType.CLOSE:
        running = False
        break
    elif item == EventType.COPY:
        triggerCopy()
    elif item == EventType.PASTE:
        triggerPaste()

if h:
    h.stop()

dblistener.stop()
soc.close()
sys.exit(0)