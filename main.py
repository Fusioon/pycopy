from datetime import datetime, timezone
from time import sleep
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Controller
import pyperclip
import requests
from firebasedb import FirebaseDB
from threading import Event

from conf import *

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

def copyHotkey():
    print("copy")
    kb.release(Key.alt)
    kb.release("C")
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

def pasteHotkey():
    print("paste")
    kb.release(Key.alt)
    kb.release("X")
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

with keyboard.GlobalHotKeys({
        COPY_HOTKEY: copyHotkey,
        PASTE_HOTKEY: pasteHotkey}) as h:
    h.join()