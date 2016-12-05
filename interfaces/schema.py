import globals
import db

def update_schema(connection):
    tables=[]
    for v in connection.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        tables.append(str(v['name']))
    globals.Reporter.message("table list in database is " + str(tables), "db")

    if not "vault" in tables:
        connection.execute("CREATE TABLE vault (id INTEGER PRIMARY KEY ASC, name text, arn text, created text, size integer, objects integer)")
    if not "file" in tables:
        connection.execute("CREATE TABLE file (id INTEGER PRIMARY KEY ASC, name text, path text, sha256 text, size integer, date text)")
    if not "archive" in tables:
        connection.execute("CREATE TABLE archive (id INTEGER PRIMARY KEY ASC, name text, vault_id integer, size integer)")
    if not "archive_file" in tables:
        connection.execute("CREATE TABLE archive_file (archive_id INTEGER, file_id INTEGER)")
    if not "settings" in tables:
        connection.execute("CREATE TABLE settings (id INTEGER PRIMARY KEY ASC, name text, value text, mutated text)")
        connection.execute("PRAGMA schema_version=1")

    row = connection.execute("PRAGMA schema_version").fetchone()
    version="1"
    try:
        version = row[0]
    except:
        globals.Reporter.error("caught exception determining schema version",True)
        version="1"
    version=int(version)
    globals.Reporter.message("Database schema version is " + str(version),"db")

    if version < 2:
        globals.Reporter.message("applying schema update 2 to database","db")
        try:
            connection.execute("ALTER TABLE vault ADD COLUMN lastinventory text")
            connection.execute("ALTER TABLE vault ADD COLUMN lastupload text")
            connection.execute("ALTER TABLE vault ADD COLUMN my_objects integer")
            connection.execute("ALTER TABLE archive ADD COLUMN lastupload text")
            globals.Reporter.message("setting schema version to 2")
            connection.execute("PRAGMA schema_version=2")
            connection.commit()
            version = 2
        except:
            globals.Reporter.error("caught exception on applying schema update 2",True)
            raise

    if version < 3:
        globals.Reporter.message("applying schema update 3 to database","db")
        try:
            connection.execute("CREATE TABLE job (id INTEGER PRIMARY KEY ASC, vault_id, jobid text, description text, action text, archiveid text, vault_arn text, creation_date text, completed text, status_code text, status_message text, archive_size integer, inventory_size integer, snstopic text, completion_date text, sha256 text, archive_hash text, range text)")
            connection.execute("ALTER TABLE archive ADD COLUMN description text")
            connection.execute("ALTER TABLE archive ADD COLUMN created text")
            connection.execute("PRAGMA schema_version=3")
            connection.commit()
            version = 3
        except:
            globals.Reporter.error("caught exception on applying schema update 3",True)
            raise
        globals.Reporter.message("setting schema version to 3")

    if version < 4:
        globals.Reporter.message("applying schema update 4 to database","db")
        try:
            connection.execute("ALTER TABLE archive ADD COLUMN local_file text")
            connection.execute("PRAGMA schema_version=4")
            connection.commit()
            version=4
        except:
            globals.Reporter.error("caught exception on applying schema update 4",True)
            raise


    if version < 5:
        globals.Reporter.message("applying schema update 5 to database","db")
        try:
            connection.execute("CREATE TABLE key (id INTEGER PRIMARY KEY ASC, algorithm text, keysize integer, blocksize integer, keystring text)")
            connection.execute("ALTER TABLE archive ADD COLUMN key_id integer")
            connection.execute("PRAGMA schema_version=5")
            connection.commit()
            version=5
        except:
            globals.Reporter.error("caught exception on applying schema update 5",True)
            raise

    if version < 6:
        globals.Reporter.message("applying schema update 6 to database","db")
        try:
            connection.execute("ALTER TABLE job ADD COLUMN executed text")
            connection.execute("PRAGMA schema_version=6")
            connection.commit()
            version=6
        except:
            globals.Reporter.error("caught exception on applying schema update 6",True)
            raise


    if version < 7:
        globals.Reporter.message("applying schema update 7 to database","db")
        try:
            connection.execute("ALTER TABLE archive ADD COLUMN validate text")
            connection.execute("ALTER TABLE archive_file ADD COLUMN path text")
            connection.execute("UPDATE archive_file SET path=(SELECT path FROM file f WHERE f.id=archive_file.file_id)")
            connection.execute("CREATE INDEX file_hash ON file (sha256,size,name)")
            connection.execute("PRAGMA schema_version=7")
            connection.commit()
            version=7
        except:
            globals.Reporter.error("caught exception on applying schema update 7",True)
            raise

    if version < 8:
        globals.Reporter.message("applying schema update 8 to database","db")
        try:
            connection.execute("ALTER TABLE file ADD COLUMN is_dirty integer")
            connection.execute("ALTER TABLE file ADD COLUMN in_archives text")
            connection.execute("ALTER TABLE file ADD COLUMN lastupload text")
            connection.execute("PRAGMA schema_version=8")
            connection.commit()
            version=8
        except:
            globals.Reporter.error("caught exception on applying schema update 8",True)
            raise

    if version < 9:
        globals.Reporter.message("applying schema update 9 to database","db")
        try:
            connection.execute("CREATE INDEX ix_archive_file ON archive_file (archive_id, file_id)")
            connection.execute("CREATE INDEX ix_archive_file2 ON archive_file (file_id)")
            connection.execute("PRAGMA schema_version=9")
            connection.commit()
            version=9
        except:
            globals.Reporter.error("caught exception on applying schema update 9",True)
            raise

    if version < 10:
        globals.Reporter.message("applying schema update 10 to database","db")
        try:
            connection.execute("ALTER TABLE file ADD COLUMN is_excluded integer")
            connection.execute("UPDATE file SET is_excluded=0")
            connection.execute("PRAGMA schema_version=10")
            connection.commit()
            version=10
        except:
            globals.Reporter.error("caught exception on applying schema update 10",True)
            raise

            