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

import os, datetime, hashlib
import awsobj
import globals
import archive

class ArchiveFile(awsobj.Object):
    def __init__(self):
        self.name='NN'
        self.id=None
        self.path=''
        self.sha256=''
        self.size=''
        self.date=''
        self.is_dirty=0
        self.lastupload=''
        self.in_archives=''
        self.is_excluded=0

    @staticmethod
    def dirty_files(cnt=100):
        rows=globals.DB.connection.execute("SELECT f.* FROM file f WHERE is_dirty=1 LIMIT(" + str(cnt) + ")").fetchall()
        retval=[]
        for row in rows:
            a = ArchiveFile()
            a.read(row)
            retval.append(a)
        return retval

    @staticmethod
    def by_archive(archive):
        rows=globals.DB.connection.execute("SELECT f.*, af.path as filepath FROM file f, archive_file af WHERE af.archive_id=:n and af.file_id=f.id",{'n':archive.id}).fetchall()
        retval=[]
        for row in rows:
            a = ArchiveFile()
            a.read(row)
            # overwrite path with the path defined for this archive
            a.path = unicode(row['filepath'])
            retval.append(a)
        return retval

    @staticmethod
    def list_all():
        # make use of the cached values in the file table (path, lastupload, in_archives)
        rows=globals.DB.connection.execute("SELECT f.* FROM file f ORDER BY f.path, f.name, f.id")
        retval=[]
        for row in rows:
            a = ArchiveFile()
            a.read(row)
            a.path = unicode(row['path'])
            retval.append(a)
        return retval

    @staticmethod
    def by_sha256(sha256, size, name):
        row=globals.DB.connection.execute("SELECT * FROM file where sha256=:h and size=:s and name=:n",{'h':sha256, 's': size, 'n': name}).fetchone()
        if row != None:
            a = ArchiveFile()
            a.read(row)
            return a
        return None

    def get_archives(self):
        rows=globals.DB.connection.execute("SELECT a.* FROM archive a, archive_file af where af.file_id=:f and af.archive_id=a.id ORDER BY a.lastupload DESC",{'f':self.id}).fetchall()
        retval=[]
        for r in rows:
            a=archive.Archive()
            a.read(r)
            retval.append(a)
        return retval

    def load(self,id=None):
        if id != None:
            self.id=id
        row=globals.DB.connection.execute("select * from file where id=:id",{'id':self.id}).fetchone()
        if row != None:
            self.read(row)
        else:
            self.id=None

    def read(self,row):
        self.id=self.to_int(row['id'])
        self.name=self.to_str(row['name'])
        self.path=self.to_str(row['path'])
        self.size=self.to_int(row['size'])
        self.sha256=self.to_str(row['sha256'])
        self.date=self.to_str(row['date'])
        self.is_dirty=self.to_int(row['is_dirty'])
        self.lastupload=self.to_str(row['lastupload'])
        self.in_archives=self.to_str(row['in_archives'])

    def save(self):
        obj = {
            "id": self.id,
            "n": self.name,
            "p": self.path,
            "s": self.size,
            "d": self.date,
            "h": self.sha256,
            "i": self.is_dirty,
            "l": self.lastupload,
            "ia": self.in_archives
        }
        if not self.id:
            globals.DB.connection.execute("INSERT INTO file (name,size,date,sha256,path,is_dirty,lastupload,in_archives) VALUES(:n,:s,:d,:h,:p,:i,:l,:ia)",obj)
        else:
            globals.DB.connection.execute("UPDATE file SET name=:n, size=:s, date=:d, sha256=:h, path=:p, is_dirty=:i, lastupload=:l, in_archives=:ia where id=:id",obj)
        globals.DB.connection.commit()

        if not self.id:
            row = globals.DB.connection.execute("SELECT max(id) as id FROM file").fetchone()
            if row != None:
                self.id = row['id']

    def set_from_path(self, name):
        if os.path.exists(name):
            path = os.path.abspath(os.path.realpath(name))
            self.name = os.path.basename(path)
            self.path = os.path.dirname(path)
            mtime = os.path.getmtime(path)
            self.date = datetime.datetime.fromtimestamp(int(mtime)).strftime("%Y-%m-%d %H:%M:%S")
            self.size = os.path.getsize(path)

            m=hashlib.sha256()
            BLOCKSIZE=65536
            with open(path,"rb") as afile:
                buf = afile.read(BLOCKSIZE)
                while len(buf)>0:
                    m.update(buf)
                    buf=afile.read(BLOCKSIZE)

            self.sha256 = m.hexdigest()
        