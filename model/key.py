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
import Crypto.Cipher
import Crypto.Cipher.Blowfish
import Crypto.Cipher.CAST
import Crypto.Cipher.DES
import Crypto.Cipher.DES3
import binascii

class Key(awsobj.Object):
    def __init__(self):
        self.algorithm="AES"
        self.keysize=128
        self.blocksize=8
        self.keystring=""
        self.id=None

    def encoder(self,iv):
        encoder=None
        ks = binascii.unhexlify(self.keystring)
        if self.algorithm == "AES":
            encoder = Crypto.Cipher.AES.new     (ks,Crypto.Cipher.AES.MODE_CBC,iv)
        elif self.algorithm == "Blowfish":
            encoder = Crypto.Cipher.Blowfish.new(ks,Crypto.Cipher.Blowfish.MODE_CBC,iv)
        elif self.algorithm == "CAST":
            encoder = Crypto.Cipher.CAST.new    (ks,Crypto.Cipher.CAST.MODE_CBC,iv)
        elif self.algorithm == "DES":
            encoder = Crypto.Cipher.DES.new     (ks,Crypto.Cipher.DES.MODE_CBC,iv)
        elif self.algorithm == "DES3":
            encoder = Crypto.Cipher.DES3.new    (ks,Crypto.Cipher.DES3.MODE_CBC,iv)
        #elif self.key['algorithm'] == "IDEA":
        #    self.encoder = Crypto.Cipher.IDEA.new    (ks,Crypto.Cipher.IDEA.MODE_CBC,iv)
        #elif self.key['algorithm'] == "RC5":
        #    self.encoder = Crypto.Cipher.RC5.new     (ks,Crypto.Cipher.RC5.MODE_CBC,iv)
        return encoder

    @staticmethod
    def list_all():
        rows=globals.DB.connection.execute("SELECT * FROM key ORDER BY id").fetchall()
        retval=[]
        for row in rows:
            d = Key()
            d.read(row)
            retval.append(d)
        return retval

    def keyid(self):
        if len(self.keystring) > 8:
            return self.keystring[:8]
        return None

    def check_existance(self,keyvals):
        dct={
            'k': keyvals.keystring,
            'a': keyvals.algorithm,
            'b': keyvals.blocksize,
            's': keyvals.keysize
        }
        row = globals.DB.connection.execute("SELECT * FROM key WHERE keystring=:k AND keysize=:s AND blocksize=:b AND algorithm=:a",dct).fetchone()
        if row != None:
            self.read(row)
        else:
            globals.Reporter.message("no such keyid found","db")
            self.id=None

    def load(self, id=None):
        if id != None:
            self.id=id
        row = globals.DB.connection.execute("SELECT * FROM key WHERE id=:id",{'id':self.id}).fetchone()
        if row != None:
            self.read(row)
        else:
            self.id=None

    def read(self, row):
        self.id=self.to_int(row['id'])
        self.algorithm = self.to_str(row['algorithm'])
        self.keysize = self.to_int(row['keysize'])
        self.blocksize = self.to_int(row['blocksize'])
        self.keystring = self.to_str(row['keystring'])

    def save(self):
        obj={
            'id': self.id,
            'a': self.algorithm,
            's': self.keysize,
            'b': self.blocksize,
            'k': self.keystring
        }
        if not self.id:
            globals.DB.connection.execute("INSERT INTO key (algorithm,keysize,blocksize,keystring) VALUES (:a,:s,:b,:k)", obj)
        else:
            globals.DB.connection.execute("UPDATE key SET algorithm=:a, keysize=:s, blocksize=:b, keystring=:k WHERE id=:id",obj)
        globals.DB.connection.commit()
        if not self.id:
            row = globals.DB.connection.execute("SELECT max(id) as id FROM key").fetchone()
            if row != None:
                self.id = row['id']
