import threading, sqlite3, datetime

import sys
import os,shutil
import globals
import config
import collections
import schema

import archivefile

class Database(threading.Thread):
    def close(self, force=False):
        if (force or globals.Config.getValue("nogui")) and self.connection != None:
            self.connection.close()
            self.connection=None

    def backup_database(self):
        try:
            fname = self.filename + ".bak"
            cnt=0
            while os.path.exists(fname):
                cnt+=1
                fname = self.filename + "." + str(cnt) + ".bak"
            shutil.copyfile(self.filename, fname)
            return fname
        except:
            return None

    def restore_database(self,fname):
        try:
            shutil.copyfile(fname, self.filename)
            return True
        except:
            return False

    def open(self):
        if self.connection == None:
            self.connection = sqlite3.connect(self.filename)
            self.connection.row_factory = sqlite3.Row

    def query(self,query):
        globals.Reporter.message("SQL: "+str(query),"db")
        result = self.connection.execute(query)
        self.connection.commit()
        return result

    def sanitise(self,val):
        keepcharacters = ('-','.','_')
        return "".join(c for c in val if c.isalnum() or c in keepcharacters).rstrip()

    def initiate(self):
        self.lock=threading.RLock()
        self.condition=threading.Condition(self.lock)
        self.queue = collections.deque()
        self.daemon=True
        self.name="DB Thread"
        self.connection=None
        self.start()

    def activate(self, cmd):
        globals.Reporter.message("pushing action on SQL queue list","db")
        if cmd!= None:
            self.queue.append(cmd)
        self.lock.acquire()
        self.condition.notify()
        self.lock.release()

    def run(self):
        self.filename = globals.Config.getValue("dbname")
        globals.Reporter.message("database name is " + str(self.filename),"db")

        self.lock.acquire()
        while not globals.Controller.exitting:
            if len(self.queue) == 0:
                globals.Reporter.message("waiting for an SQL action", "db")
                self.condition.wait()
            self.command=None
            if globals == None or globals.Controller == None or globals.Controller.exitting:
                return
            if len(self.queue) != 0:
                self.command = self.queue.popleft()
            if self.command!=None:
                globals.Reporter.message("SQL thread activated", "db")
                try:
                    globals.Reporter.message("running SQL action", "db")
                    self.command.run("db",self)
                except:
                    globals.Reporter.error("error running SQL command",True)
                globals.Reporter.message("SQL thread idle again", "db")

        globals.Reporter.message("Graciously exitting SQL thread", "db")
        self.lock.release()

    def update_schema(self):
        try:
            schema.update_schema(self.connection)
            return True
        except:
            return False

    def test_maintenance(self):
        globals.Reporter.message("counting orphan files","db")
        row = self.connection.execute("SELECT COUNT(*) as cnt FROM file f WHERE NOT EXISTS(SELECT * FROM archive_file af WHERE af.file_id=f.id)").fetchone()
        globals.Reporter.message("returned " + str(row),"db")
        if row != None:
            cnt = int(row['cnt'])
            globals.Reporter.message("count is " + str(cnt),"db")
            if cnt > 0:
                return "removing unused files"
        globals.Reporter.message("counting dirty files","db")
        row = self.connection.execute("SELECT COUNT(*) as cnt FROM file f WHERE is_dirty=1").fetchone()
        globals.Reporter.message("returned " + str(row),"db")
        if row != None:
            cnt = int(row['cnt'])
            globals.Reporter.message("count is " + str(cnt),"db")
            if cnt > 0:
                return "updating file cache ("+str(cnt) + " left)"
        globals.Reporter.message("No maintenance action to take","db")
        return None

    def run_maintenance(self):
        if self.maintenance_unusedfiles():
            return True
        if self.maintenance_dirtyfiles():
            return True
        return None

    def maintenance_unusedfiles(self):
        row = self.connection.execute("SELECT COUNT(*) as cnt FROM file f WHERE is_excluded=0 AND NOT EXISTS(SELECT * FROM archive_file af WHERE af.file_id=f.id)").fetchone()
        if row != None:
            cnt = int(row['cnt'])
            if cnt > 0:
                self.connection.execute("DELETE FROM file WHERE id IN (SELECT f.id FROM file f WHERE is_excluded=0 AND NOT EXISTS(SELECT * FROM archive_file af WHERE af.file_id=f.id))")
                return True
        return False

    def maintenance_dirtyfiles(self):
        files = archivefile.ArchiveFile.dirty_files(100)
        if len(files)>0:
            for f in files:
                archives = f.get_archives()
                if len(archives)>0:
                    f.in_archives=",".join(map(lambda x: str(x.id), archives))
                    f.lastupload = archives[0].created
                    f.is_dirty=0
                    f.save()
            return True
        return False

    def timestamp(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

globals.DB=Database()
globals.Config.setOption("dbname",globals.Config.Option("-d","--database","SQLite database file","freezer.db",True))
