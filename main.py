from datetime import datetime, timezone
from time import sleep
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Controller
import pyperclip
import requests
from firebasedb import FirebaseDB
from threading import Event

# Allow direct pasting from phone without the need to press keyboard shortcut
ALLOW_DIRECT_PASTE = True
# Maximum time to wait for a response from phone (in seconds)
MAX_WAIT_TIME_S = 4.0
# Maximum time the data is considered valid (in seconds)
MAX_DATA_AGE_S = 10.0
# We are using same notification channel for copy and paste so this literal is used when we want to retrieve data fromn phone
COPY_MESSAGE_TEXT = "#%$copy$%#"
COPY_HOTKEY = '<alt>+c'
PASTE_HOTKEY = '<alt>+x'

FIREBASE_URL = ""
FIREBASE_SECRET = ""

AUTOMATE_APIKEY = ""
AUTOMATE_EMAIL = ""
AUTOMATE_REQUEST = {
    "secret": AUTOMATE_APIKEY,
    "to": AUTOMATE_EMAIL,
    "device": None,
    "priority": "normal",
    "payload": None
}
AUTOMATE_ENDPOINT = "https://llamalab.com/automate/cloud/message"

rtdb = FirebaseDB(FIREBASE_URL, FIREBASE_SECRET)
kb = Controller()

dbData = {}
dataEvent = Event()

def isTimestampValid(timestamp: int) -> bool:
    now = datetime.utcnow().timestamp()
    now -= MAX_DATA_AGE_S
    print(f"now: {now} | {timestamp}")
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

def sendAutomateRequest(text: str):
    AUTOMATE_REQUEST["payload"] = text
    post_response = requests.post(AUTOMATE_ENDPOINT, json=AUTOMATE_REQUEST)

def copyHotkey():
    kb.release(Key.alt)
    with kb.pressed(Key.ctrl):
        kb.press('c')
        kb.release('c')  
    
    sleep(0.03)
    clip = pyperclip.paste()
    print(clip)
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
    dataEvent.clear()
    try:
        sendAutomateRequest(COPY_MESSAGE_TEXT)
        kb.release(Key.alt)
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