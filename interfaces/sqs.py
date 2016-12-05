import threading

import sys
import globals
import pyrebase

class FCM(threading.Thread):
    def initiate(self):
        self.lock=threading.RLock()
        self.condition=threading.Condition(self.lock)
        self.daemon=True
        self.name="Firebase CM Thread"
        self.start()

    def run(self):
        cfg = {
            'apikey': globals.Config.getValue("gcm_apikey"),
            'authDomain': globals.Config.getValue("gcm_authdomain"),
            "databaseURL": globals.Config.getValue("gcm_db"),
            "storageBucket": globals.Config.getValue("gcm_storage")
        }
        self.firebase = pyrebase.initialize_app(cfg)
        self.db = self.firebase.database
        my_stream = self.db.child("posts")

    def receive_notification(self, post):
        globals.Reporter.message("received GCM post " + str(post),"fcm")

globals.Firebase = FCM()
