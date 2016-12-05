#
# The ActionThread class is a generic class that executes threads in the Controller
# It finds its thread id in the Controller class and moves it from/to the active/idle thread
# lists
# The Action class is a stub to be used for commands for the ActionThread

import sys
sys.path.append("..")
import globals
import threading, time

class ActionThread(threading.Thread):
    def run(self):
        self.lock=threading.RLock()
        self.condition=threading.Condition(self.lock)
        self.command=None

        self.command=globals.Controller.moveThread(True)

        self.lock.acquire()
        while not globals.Controller.exitting:
            if self.command==None:
                globals.Reporter.message("waiting for an action", "control")
                self.condition.wait()
            if self.command!=None:
                globals.Reporter.message("thread activated", "control")
                self.lock.release()
                globals.Controller.moveThread(False)
                self.lock.acquire()
                try:
                    globals.Reporter.message("running action", "control")
                    self.command.run("backend")
                except:
                    globals.Reporter.error("error running command",True)
                globals.Reporter.message("thread idle again", "control")

                self.lock.release()
                self.command=globals.Controller.moveThread(True)
                self.lock.acquire()

        self.lock.release()
        globals.Controller.removeThread()

    def activate(self,action):
        retval=False
        self.lock.acquire()
        if self.command==None:
            self.command=action
            retval=True
        self.condition.notify()
        self.lock.release()
        return retval

class TimerThread(threading.Thread):
    def run(self):
        self.init()

        self.lock.acquire()
        while not globals.Controller.exitting:
            if len(self.commands)>0:
                now=time.time()
                removeindexes=[]
                earliest=-1.0
                for i in range(len(self.commands)):
                    if (not self.commands[i].when==None) and self.commands[i].when <=now:
                        self.commands[i].when=None
                        globals.Reporter.message("timer activates an action", "control")
                        globals.Controller.activate(self.commands[i])
                    elif (not self.commands[i].when==None):
                        if self.commands[i].when < earliest or earliest==-1:
                            earliest=self.commands[i].when

                    if self.commands[i].when==None:
                        removeindexes.append(i)

                for i in range(len(removeindexes)):
                    index=removeindexes[len(removeindexes)-i-1]
                    del self.commands[index]

            if len(self.commands)==0:
                self.condition.wait()
            else:
                # earliest must be set
                waitfortime=earliest - time.time()
                self.condition.wait(waitfortime)

        globals.Controller.timerthread=None

    def init(self):
        if not hasattr(self,'lock'):
            self.lock=threading.RLock()
            self.condition=threading.Condition(self.lock)
            self.commands=[]

    def activate(self,action):
        self.init()
        self.lock.acquire()
        self.commands.append(action)
        self.condition.notify()
        self.lock.release()

class Action(object):
    def __init__(self,callback):
        globals.Reporter.message("setting when attribute to None", "control")
        self.when=None
        self.callback=callback

    def run(self, callee, data=None):
        globals.Reporter.message("executing callback on action from callee '"+ str(callee) + "'","control")
        if self.callback != None:
            self.callback(self,callee, data)
        else:
            globals.Reporter.message("no callback available...","control")


        