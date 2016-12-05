import awsobj
import globals

class Job(awsobj.Object):
    def __init__(self):
        self.vault_id=-1
        self.id=None

        self.vault_id = -1
        self.jobid = ''
        self.description = ''
        self.action = ''
        self.archiveid = ''
        self.vault_arn = ''
        self.creation_date = ''
        self.completed = ''
        self.status_code = ''
        self.status_message = ''
        self.archive_size = -1
        self.inventory_size = -1
        self.snstopic = ''
        self.completion_date = ''
        self.sha256=''
        self.archive_hash = ''
        self.range = ''
        self.executed=''

    def by_jobid(self,jobid):
        row = globals.DB.connection.execute("SELECT * FROM job WHERE jobid=:jid",{'jid': jobid}).fetchone()
        if row != None:
            self.read(row)
        else:
            self.id=None

    @staticmethod
    def inventory_by_vault(vault):
        rows = globals.DB.connection.execute("SELECT * FROM job WHERE vault_id=:vid and action='InventoryRetrieval' ORDER BY completion_date asc",{'vid': vault.id}).fetchall()
        retval=[]
        for row in rows:
            job = Job()
            job.read(row)
            retval.append(job)
        return retval

    @staticmethod
    def by_vault(vault):
        rows = globals.DB.connection.execute("SELECT * FROM job WHERE vault_id=:vid  ORDER BY completion_date asc",{'vid': vault.id}).fetchall()
        retval=[]
        for row in rows:
            job = Job()
            job.read(row)
            retval.append(job)
        return retval

    @staticmethod
    def list_all():
        rows = globals.DB.connection.execute("SELECT * FROM job ORDER BY completion_date asc").fetchall()
        retval=[]
        for row in rows:
            job = Job()
            job.read(row)
            retval.append(job)
        return retval

    def load(self, id=None):
        if id != None:
            self.id=id
        row = globals.DB.connection.execute("SELECT * FROM job WHERE id=:id",{'id':self.id})
        if row != None:
            self.read(row)
        else:
            self.id=None

    def read(self, row):
        self.id=self.to_int(row['id'])
        self.vault_id = self.to_int(row['vault_id'])
        self.jobid = self.to_str(row['jobid'])
        self.description = self.to_str(row['description'])
        self.action = self.to_str(row['action'])
        self.archiveid = self.to_str(row['archiveid'])
        self.vault_arn = self.to_str(row['vault_arn'])
        self.creation_date = self.to_str(row['creation_date'])
        self.completed = self.to_int(row['completed'])
        self.status_code = self.to_str(row['status_code'])
        self.status_message = self.to_str(row['status_message'])
        self.archive_size = self.to_int(row['archive_size'])
        self.inventory_size = self.to_str(row['inventory_size'])
        self.snstopic = self.to_str(row['snstopic'])
        self.completion_date = self.to_str(row['completion_date'])
        self.sha256=self.to_str(row['sha256'])
        self.archive_hash = self.to_str(row['archive_hash'])
        self.range = self.to_str(row['range'])
        self.executed = self.to_str(row['executed'])

    def save(self):
        obj={
            'id': self.id,
            'v': self.vault_id,
            'j': self.jobid,
            'd': self.description,
            'a': self.action,
            'aid': self.archiveid,
            'va': self.vault_arn,
            'cd': self.creation_date,
            'c': self.completed,
            'sc': self.status_code,
            'sm': self.status_message,
            'as': self.archive_size,
            'is': self.inventory_size,
            's': self.snstopic,
            'cm': self.completion_date,
            'h': self.sha256,
            'ah': self.archive_hash,
            'r': self.range,
            'e': self.executed
        }
        if not self.id:
            globals.DB.connection.execute("INSERT INTO job (vault_id,jobid, description,action, archiveid,vault_arn, creation_date, completed, status_code, status_message, archive_size, inventory_size," +
                "snstopic, completion_date, sha256, archive_hash, range,executed) VALUES (:v,:j,:d,:a, :aid, :va, :cd, :c, :sc, :sm, :as, :is, :s, :cm, :h, :ah, :r,:e)", obj)
        else:
            globals.DB.connection.execute("UPDATE job SET vault_id=:v, jobid=:j, description=:d, action=:a, archiveid=:aid, vault_arn=:va," +
                "creation_date=:cd, completed=:c, status_code=:sc, status_message=:sm, archive_size=:as, inventory_size=:is, snstopic=:s, "+
                "completion_date=:cm, sha256=:h, archive_hash=:ah, range=:r, executed=:e WHERE id=:id",obj)
        globals.DB.connection.commit()
        if not self.id:
            self.by_jobid(self.jobid)

    def import_aws(self, res):
        self.jobid=self.import_setting('JobId',res,'')
        self.description=self.import_setting('JobDescription',res,'')
        self.action=self.import_setting('Action',res,'')
        self.archiveid=self.import_setting('ArchiveId',res,'')
        self.vault_arn=self.import_setting('VaultARN',res,'')
        self.creation_date=self.import_setting('CreationDate',res,'')
        self.completed=self.import_setting('Completed',res,False)
        self.status_code=self.import_setting('StatusCode',res,'')
        self.status_message=self.import_setting('StatusMessage',res,'')
        self.archive_size=self.import_setting('ArchiveSizeInBytes',res,0)
        self.inventory_size=self.import_setting('InventorySizeInBytes',res,0)
        self.snstopic=self.import_setting('SNSTopic',res,'')
        self.completion_date=self.import_setting('CompletionDate',res,'')
        self.sha256=self.import_setting('SHA256TreeHash',res,'')
        self.archive_hash=self.import_setting('ArchiveSHA256TreeHash',res,'')
        self.range=self.import_setting('RetrievalByteRange',res,'')

    def copy(self, v):
        self.jobid=v.jobid
        self.description=v.description
        self.action=v.action
        self.archiveid=v.archiveid
        self.vault_arn=v.vault_arn
        self.creation_date=v.creation_date
        self.completed=v.completed
        self.status_code=v.status_code
        self.status_message=v.status_message
        self.archive_size=v.archive_size
        self.inventory_size=v.inventory_size
        self.snstopic=v.snstopic
        self.completion_date=v.completion_date
        self.sha256=v.sha256
        self.archive_hash=v.archive_hash
        self.range=v.range

    def delete(self):
        globals.DB.connection.execute("DELETE FROM job WHERE id=:i",{'i': self.id})

