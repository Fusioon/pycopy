# Allow direct pasting from phone without the need to press keyboard shortcut
ALLOW_DIRECT_PASTE = True
# Maximum time to wait for a response from phone (in seconds)
MAX_WAIT_TIME_S = 4.0
# Maximum time the data is considered valid (in seconds)
MAX_DATA_AGE_S = 10.0
# We are using same notification channel for copy and paste so this literal is used when we want to retrieve data fromn phone
COPY_MESSAGE_TEXT = "#%$copy$%#"

# Port used for interprocess communication
PORT = 32145
# Copy & Paste can only be triggered by sending events through socket
# No hotkeys will be registered by application
ONLY_SYSTEM_HOTKEYS = False
COPY_HOTKEY = '<alt>+c'
PASTE_HOTKEY = '<alt>+x'

FIREBASE_URL = ""
FIREBASE_SECRET = ""

AUTOMATE_ENDPOINT = "https://llamalab.com/automate/cloud/message"
AUTOMATE_APIKEY = ""
AUTOMATE_EMAIL = ""