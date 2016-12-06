#
# Copyright Muis IT 2011 - 2016
#
# This file is part of AWS Freezer
#
# AWS Freezer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AWS Freezer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AWS Freezer (see the COPYING file).
# If not, see <http://www.gnu.org/licenses/>.

import time, sys, getopt, inspect, traceback, threading

import sys, codecs, locale
sys.path.append("..")
import globals
import logging

class LogHandler(logging.Handler):
    def handle(self,record):
        globals.Reporter.message("LOG: " + str(record.pathname) + ":" + str(record.lineno) + ":" + str(record.msg),record.name)

class Reporter(object):
    verbose=False
    trace={}

    def _init__(self):
        sys.stdout = codecs.getwriter(sys.stdout.encoding)(sys.stdout)

    def mark(self,msg):
        # generic, non-error, i-am-still-alive-message
        tt = time.localtime()
        sys.stdout.write("%04d-%02d-%02d %02d:%02d:%02d %s\r\n"%(tt[0],tt[1],tt[2],tt[3],tt[4],tt[5],msg.encode('utf-8','ignore')))

    def message(self,msg,trace=None):
        try:
            # messages that should only be shown when verbose output is on
            if self.verbose and (trace==None or len(self.trace)==0 or self.trace.has_key(trace)):
                tt = time.localtime()
                if trace==None:
                    sys.stdout.write("%02d%02d%02d [%s]: %s\r\n"%(tt[3],tt[4],tt[5],threading.currentThread().name,msg.encode('utf-8','ignore')))
                else:
                    sys.stdout.write("%02d%02d%02d [%s](%s): %s\r\n"%(tt[3],tt[4],tt[5],threading.currentThread().name,trace,msg.encode('utf-8','ignore')))
            sys.stdout.flush()
        except:
            self.error("Unable to print message",True)

    def error(self,msg, doexcept=True):
        try:
            # error messages, possibly with exception trace
            tt = time.localtime()
            sys.stderr.write("%02d%02d%02d [%s] ERROR: %s at %s:%d\r\n"%(tt[3],tt[4],tt[5],threading.currentThread().name, msg,inspect.stack()[1][1],inspect.stack()[1][2]))
        except:
            doexcept=True
        if doexcept:
                traceback.print_exc()

globals.Reporter=Reporter()
