#!/usr/bin/python
#
# Freezer: AWS Glacier interface
#
# The Freezer programs allows users to freeze archives into the AWS Glacier storage and melt them
# back into your filesystem.
# The program uses an SQLite database that can (and needs!) to be backed up easily to facilitate the
# Glacier interface
#
# Copyright Muis IT 2011 - 2016


import threading
import sys, os, os.path
dname = os.path.dirname(__file__)
sys.path.append(dname)
sys.path.append(os.path.join(dname,"debug"))
sys.path.append(os.path.join(dname,"gui"))
sys.path.append(os.path.join(dname,"controller"))
sys.path.append(os.path.join(dname,"interfaces"))
sys.path.append(os.path.join(dname,"model"))

import globals
import gui
import debug
import config
import controller
import db
import actionfactory
import awsinterface
import time

globals.Config.setOption("nogui",globals.Config.Option("-g","--no-gui","Run headless interface",None,False))

class ViewThread (threading.Thread):
    def run(self):
         globals.GUI.MainLoop()

def header():
    print "Freezer: AWS Glacier Manager\nCopyright 2011 - 2016 (c) Muis IT"

def usage():
    print "Usage: freezer <options>"
    globals.Config.printOptions()

if __name__ == "__main__":
    try:
        files=globals.Config.readArguments(sys.argv[1:],header,usage)
        globals.Reporter.message("Started Freezer")
        globals.Controller.run()
        globals.DB.initiate()

        # initiate the SQLite database and read the core information
        # This will invoke a command in the GUI thread (displaying vault information)
        # which can only execute after we completed the GUI buildup
        globals.ActionFactory.initialise_db()

        hasgui = globals.Config.getValue("nogui")
        if hasgui == None:
            globals.GUI.mainLoop(dname)
        else:
            while True:
                time.sleep(20)
    except:
        globals.Reporter.error("caught exception on main thread",True)
        pass

    globals.Reporter.message("exitting Freezer")
    # send a signal to the controller to quit
    globals.Controller.signal("quit")

    # make sure the database exits as well
    globals.DB.activate(None)
    globals.DB.join()

