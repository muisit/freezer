import threading, time, tempfile

import sys
import globals
# import ActionThread, TimerThread and the generic Action class
from action import *

globals.Config.setOption("maxthreads",globals.Config.Option("-t","--threads","maximum nr of threads",10,True))

class Controller(object):
    def __init__(self):
        self.lock=threading.RLock()
        self.condition=threading.Condition(self.lock)
        self.exitting=False

        self.timerthread=None
        self.activethreads={}
        self.idlethreads={}
        self.actions=[] # pending actions for which we have no more threads

    def moveThread(self, isidle):
        globals.Reporter.message("moving thread in pool : isidle:"+str(isidle), "control")
        retval=None
        threadid=threading.current_thread().ident
        self.lock.acquire()
        if isidle and self.activethreads.has_key(threadid):
            self.idlethreads[threadid]=self.activethreads[threadid]
            del self.activethreads[threadid]
        elif not isidle and self.idlethreads.has_key(threadid):
            self.activethreads[threadid]=self.idlethreads[threadid]
            del self.idlethreads[threadid]
        elif isidle:
            self.idlethreads[threadid]=threading.current_thread()
        else:
            self.activethreads[threadid]=threading.current_thread()

        # now see if we have any idle threads and actions
        globals.Reporter.message("checking for pending actions", "control")
        if not self.exitting and self.idlethreads.has_key(threadid) and len(self.actions)>0:
            globals.Reporter.message("action found, returned for activation", "control")
            retval=self.actions.pop(0)
        self.lock.release()
        return retval

    def removeThread(self):
        threadid=threading.current_thread().ident
        self.lock.acquire()
        if self.activethreads.has_key(threadid):
            del self.activethreads[threadid]
        elif self.idlethreads.has_key(threadid):
            del self.idlethreads[threadid]
        self.lock.release()

    def activate(self,action):
        if action.when==None:
            globals.Reporter.message("immediately performing action", "control")
            success=False
            self.lock.acquire()
            if len(self.idlethreads)>0:
                # the following will wait for the lock to be released
                globals.Reporter.message("idle thread found", "control")
                thr=self.idlethreads[self.idlethreads.keys()[0]]
                success=thr.activate(action)
                # the action run loop will release its own lock and try to lock this object, which waits
                # for the next release at the end of the parent IF block

            if not success:
                 # no idle thread left, push the action on the action list
                 globals.Reporter.message("pushing action for later execution", "control")
                 self.actions.append(action)

                 # see if we need to create a new thread to handle this action
                 maxthreads=int(globals.Config.getValue("maxthreads"))
                 if maxthreads>(len(self.activethreads)+len(self.idlethreads)):
                    globals.Reporter.message("auto creating a new thread", "control")
                    ac=ActionThread() # adds itself to the idle list
                    ac.name="ActionThread " + str(len(self.activethreads)+len(self.idlethreads)+1)
                    ac.daemon=True
                    ac.start()
                    # the locks and conditions of the ActionThread are only set at the start of the
                    # thread loop. Once initialised, it will mark itself as idle and the action
                    # will be executed later on
            self.lock.release()

        else:
            globals.Reporter.message("postponing action execution", "control")
            self.timerthread.activate(action)

    def run(self):
        # initiate the Timer thread
        self.timerthread=TimerThread()
        self.timerthread.start()

    def signal(self, msg):
        self.lock.acquire()
        if msg == "quit":
            self.quit()
        self.lock.release()

    def quit(self):
        globals.Reporter.message("graciously quitting", "control")
        # we arrive here in a locked condition
        self.exitting=True
        # signal all idle threads
        for t in self.idlethreads:
            self.idlethreads[t].activate(None)
        # active threads will check after they finished their action
        # signal the timer thread
        self.timerthread.activate(None)

        # now join the threads
        globals.Reporter.message("joining threads", "control")
        while len(self.idlethreads)>0:
            t=self.idlethreads[self.idlethreads.keys()[0]]
            self.lock.release()
            t.join()
            self.lock.acquire()
        globals.Reporter.message("idle threads joined", "control")
        if not self.timerthread==None:
            self.lock.release()
            globals.Reporter.message("activating and joining timer thread","control")
            self.timerthread.activate(None)
            self.timerthread.join()
            self.lock.acquire()
        globals.Reporter.message("joining remaining threads","control")
        while len(self.activethreads)>0 or len(self.idlethreads)>0:
            if len(self.idlethreads)>0:
                t=self.idlethreads[self.idlethreads.keys()[0]]
                self.lock.release()
                t.activate(None)
                t.join()
                self.lock.acquire()
            else:
                t=self.activethreads[self.activethreads.keys()[0]]
                self.lock.release()
                globals.Reporter.message("joining active thread","control")
                t.join()
                self.lock.acquire()
        globals.Reporter.message("end of controller thread", "control")

globals.Controller=Controller()
