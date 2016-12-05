import awsobj
import globals

class Archive(awsobj.Object):
    def __init__(self):
        self.name=''
        self.id=None
        self.vault_id=-1
        self.lastupload=''
        self.size=0
        self.created=''
        self.description=''
        self.local_file=''
        self.key_id=-1

    def add_files(self, lst):
        for f in lst:
            f.save()
            if f.id != None:
                obj={'a': self.id, 'f': f.id, 'p': f.path}
                globals.DB.connection.execute("delete from archive_file where archive_id=:a and file_id=:f",obj)
                globals.DB.connection.execute("INSERT INTO archive_file (archive_id, file_id,path) VALUES(:a,:f,:p)",obj)
                globals.DB.connection.execute("UPDATE file SET is_dirty=1 WHERE id=:f",obj)

    def by_name(self, name):
        row=globals.DB.connection.execute("select * from archive where name=:n",{'n': name}).fetchone()
        if row != None:
            self.read(row)
        else:
            self.id=None

    @staticmethod
    def by_vault(vault):
        rows=globals.DB.connection.execute("SELECT * FROM archive WHERE vault_id=:n",{'n': vault.id}).fetchall()
        retval=[]
        for row in rows:
            archive = Archive()
            archive.read(row)
            retval.append(archive)
        return retval

    def load(self,id=None):
        if id != None:
            self.id=id
        row=globals.DB.connection.execute("select * from archive where id=:id",{'id':self.id}).fetchone()
        if row != None:
            self.read(row)
        else:
            self.id=None

    def read(self,row):
        self.id=self.to_int(row['id'])
        self.name=self.to_str(row['name'])
        self.vault_id=self.to_int(row['vault_id'])
        self.size=self.to_int(row['size'])
        self.lastupload=self.to_str(row['lastupload'])
        self.created=self.to_str(row['created'])
        self.description=self.to_str(row['description'])
        self.local_file=self.to_str(row['local_file'])
        self.key_id=self.to_int(row['key_id'])

    def save(self):
        obj = {
            "id": self.id,
            "n": self.name,
            "v": self.vault_id,
            "s": self.size,
            "d": self.description,
            "l": self.lastupload,
            "c": self.created,
            "lf": self.local_file,
            'k': self.key_id
        }
        if not self.id:
            globals.DB.connection.execute("INSERT INTO archive (name,vault_id,size,lastupload,created,description,local_file,key_id) VALUES(:n,:v,:s,:l,:c,:d,:lf,:k)",obj)
        else:
            globals.DB.connection.execute("UPDATE archive SET name=:n, vault_id=:v, size=:s, lastupload=:l, created=:c, description=:d, local_file=:lf, key_id=:k where id=:id",obj)
        globals.DB.connection.commit()

        if not self.id:
            row = globals.DB.connection.execute("SELECT max(id) as id FROM archive").fetchone()
            if row != None:
                self.id = row['id']

    def import_aws(self, v):
        globals.Reporter.message("importing AWS Archive " + str(v),"db")
        self.name = self.to_str(v['ArchiveId'])
        self.description = self.to_str(v['ArchiveDescription'])
        self.lastupload = self.to_str(v['CreationDate'])
        self.size = self.to_int(v['Size'])

    def copy(self, v):
        self.name=v.name
        self.description=v.description
        self.lastupload=v.lastupload
        self.size=v.size

    def delete(self):
        if self.id != None:
            obj = {'id': self.id}
            globals.DB.connection.execute("UPDATE file SET is_dirty=1 WHERE id in (SELECT file_id FROM archive_file WHERE archive_id=:id)",obj)
            globals.DB.connection.execute("DELETE FROM archive_file WHERE archive_id=:id",obj)
            globals.DB.connection.execute("DELETE FROM archive WHERE id=:id",obj)
            globals.DB.connection.commit()
