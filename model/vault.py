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

import awsobj
import globals
import job
import archive

class Vault(awsobj.Object):
    def __init__(self):
        self.name='NN'
        self.id=None
        self.arn=''
        self.size=0
        self.objects=0
        self.my_objects=0
        self.created=''
        self.lastinventory=''
        self.lastupload=''

    def by_name(self, name):
        row=globals.DB.connection.execute("select * from vault where name=:n",{'n': name}).fetchone()
        if row != None:
            self.read(row)
        else:
            self.id=None

    def by_arn(self, name):
        row=globals.DB.connection.execute("select * from vault where arn=:n",{'n': name}).fetchone()
        if row != None:
            self.read(row)
        else:
            self.id=None

    @staticmethod
    def list_all():
        rows=globals.DB.connection.execute("SELECT * FROM vault ORDER BY name,id").fetchall()
        retval=[]
        for row in rows:
            vault = Vault()
            vault.read(row)
            retval.append(vault)
        return retval

    def get_jobs(self):
        return job.Job.by_vault(self)

    def get_inventory_jobs(self):
        return job.Job.inventory_by_vault(self)

    def get_archives(self):
        return archive.Archive.by_vault(self)

    def load(self,id=None):
        if id != None:
            self.id=id
        row=globals.DB.connection.execute("select * from vault where id=:id",{'id':self.id}).fetchone()
        if row != None:
            self.read(row)
        else:
            self.id=None

    def read(self,row):
        self.id=self.to_int(row['id'])
        self.name=self.to_str(row['name'])
        self.arn=self.to_str(row['arn'])
        self.size=self.to_int(row['size'])
        self.objects=self.to_int(row['objects'])
        self.my_objects=self.to_int(row['my_objects'])
        self.created=self.to_str(row['created'])
        self.lastinventory=self.to_str(row['lastinventory'])
        self.lastupload=self.to_str(row['lastupload'])

    def count_objects(self):
        globals.Reporter.message("counting objects in vault "+ str(self.name),"db")
        row = globals.DB.connection.execute("SELECT COUNT(*) as cnt FROM archive WHERE vault_id=:i",{'i':self.id}).fetchone()
        if row != None:
            self.my_objects = self.to_int(row['cnt'])
            globals.Reporter.message("setting objects to " + str(self.my_objects),"db")
            self.save()

    def save(self):
        obj = {
            "id": self.id,
            "n": self.name,
            "a": self.arn,
            "s": self.size,
            "o": self.objects,
            "mo": self.my_objects,
            "c": self.created,
            "li": self.lastinventory,
            "lu": self.lastupload
        }
        if not self.id:
            globals.DB.connection.execute("INSERT INTO vault (name,arn,size,objects,my_objects,created,lastinventory,lastupload) VALUES(:n,:a,:s,:o,:mo,:c,:li,:lu)",obj)
        else:
            globals.DB.connection.execute("UPDATE vault SET name=:n, arn=:a, size=:s, objects=:o, my_objects=:mo, created=:c, lastinventory=:li, lastupload=:lu where id=:id",obj)
        globals.DB.connection.commit()

        if not self.id:
            self.by_name(self.name)

    def delete_jobs(self):
        if self.id != None:
            obj = {'id': self.id}
            globals.DB.connection.execute("DELETE FROM job WHERE vault_id=:id",obj)

    def delete(self):
        if self.id != None:
            obj = {'id': self.id}
            globals.DB.connection.execute("DELETE FROM archive_file WHERE archive_id in (SELECT id FROM archive WHERE vault_id=:id)",obj)
            globals.DB.connection.execute("DELETE FROM archive WHERE vault_id=:id",obj)
            self.delete_jobs()
            globals.DB.connection.execute("DELETE FROM vault WHERE id=:id",obj)
            globals.DB.connection.commit()

    def import_aws(self, res):
        self.name=res['VaultName'] if 'VaultName' in res else 'NN'
        self.arn=res['VaultARN'] if 'VaultARN' in res else ""
        self.size=res['SizeInBytes'] if 'SizeInBytes' in res else "0"
        self.objects=res['NumberOfArchives'] if 'NumberOfArchives' in res else '0'
        self.created=res['CreationDate'] if 'CreationDate' in res else '<unknown>'
        self.lastinventory=res['LastInventoryDate'] if 'LastInventoryDate' in res else "<unknown>"

    def copy(self,v):
        self.name=v.name
        self.arn=v.arn
        self.size=v.size
        self.objects=v.objects
        self.created=v.created
        self.lastinventory=v.lastinventory

    def __repr__(self):
        return "Vault " + str(self.name) + " (" + str(self.arn) + ") has size " + str(self.size) + " bytes"
