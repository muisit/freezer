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

import os.path
import globals
import Crypto.Cipher
import Crypto.Random
import json
import binascii
import struct
import key

class Encrypter:
    def __init__(self, key, filename):
        self.filename = filename
        self.file=None

        self.key = key
        if self.key != None:
            self.iv = Crypto.Random.get_random_bytes(self.key.blocksize)
            #globals.Reporter.message("IV is " + binascii.hexlify(self.iv),"encrypt")
            globals.Reporter.message("Key is " + str(self.key.keystring) +"/" + str(len(self.key.keystring)),"encrypt")
            self.encoder=None

    def close_file(self):
        if self.file !=None:
            self.file.close()

    def conv_bytes_to_bytestring(self,lst):
        return ''.join(lst)

    def create_encoder(self):
        self.encoder=None
        if self.key == None:
            #globals.Reporter.error("no key information found")
            return
        self.encoder = self.key.encoder(self.iv)
        val = Crypto.Random.get_random_bytes(1)[0]
        self.randomsize = int(ord(val))
        self.start_of_file = self.randomsize+self.key.blocksize + 1

    def chunksize(self, sz):
        if self.key==None:
            return sz

        if sz < self.key.blocksize:
            sz=self.key.blocksize
        if sz % self.key.blocksize != 0:
            sz += self.key.blocksize - (sz % self.key.blocksize)
        return sz

class Encoder(Encrypter):
    def __init__(self, key,fname):
        Encrypter.__init__(self,key,fname)
        self.create_encoder()
        self.open_file()

    def open_file(self):
        if os.path.exists(self.filename):
            self.file = open(self.filename,'rb')
            self.filesize = os.path.getsize(self.filename)

    def total_size(self):
        if self.key == None:
            return self.filesize
        # we prepend the file data with a random IV vector, then a random number and that number
        # of random bytes
        totalsize = self.filesize + self.start_of_file
        # normalise to a whole number of blocks
        if totalsize % self.key.blocksize != 0:
            # change the number of random prefix bytes to end up with a correct blocksize count
            diff = self.key.blocksize - (totalsize % self.key.blocksize)
            while diff + self.randomsize > 0xff:
                self.randomsize-=self.key.blocksize
            self.randomsize+=diff
            self.start_of_file = self.randomsize+self.key.blocksize + 1
            totalsize = self.filesize + self.start_of_file
        return totalsize

    def read(self, offset, chunksize):
        globals.Reporter.message("reading chunk at "+str(offset) + " of size " + str(chunksize),"encrypt")
        position = 0
        chunk=[]

        if self.key != None:
            # insert the requested randomness
            if offset == 0:
                globals.Reporter.message("making room for IV","encrypt")
                # prepend the iv at the end, after encryption
                position = self.key.blocksize
            globals.Reporter.message("position '" + str(position) + "', offset '" + str(offset) + "', blocksize '" + str(self.key.blocksize)+"'","encrypt")
            if position < chunksize and (offset+position) == self.key.blocksize:
                globals.Reporter.message("adding randomsize","encrypt")
                chunk += struct.pack('B',self.randomsize)
                position+=1
            rnds=(offset + position - self.key.blocksize - 1)
            if position < chunksize and rnds < self.randomsize:
                globals.Reporter.message("adding random pre-padding (" + str(self.randomsize) + "/" + str(rnds) +")","encrypt")
                while position < chunksize and rnds < self.randomsize:
                    position+=1
                    rnds+=1
                    chunk += [Crypto.Random.get_random_bytes(1)]

        globals.Reporter.message("converting chunk of size '" + str(len(chunk)) + "' to byte buffer","encrypt")
        chunk = self.conv_bytes_to_bytestring(chunk)
        if position < chunksize:
            # room left to add bytes from the file
            bytes_to_read = chunksize - position
            globals.Reporter.message("reading additional " + str(bytes_to_read) + " bytes from file","encrypt")

            if self.file != None:
                chunk = chunk + self.file.read(bytes_to_read)
            else:
                chunk = chunk + Crypto.Random.get_random_bytes(bytes_to_read)

        # now encrypt the chunk using our key
        globals.Reporter.message("chunk has size "+str(len(chunk)),"encrypt")
        # test for size in case chunksize == blocksize and our first read is only the IV vector
        if self.key != None and len(chunk)>0:
            encrypted_chunk = self.encoder.encrypt(chunk)
        elif self.key != None:
            encrypted_chunk=""
        else:
            encrypted_chunk = chunk

        if self.key != None and offset == 0:
            # prepend the unencrypted IV list
            globals.Reporter.message("prepending IV","encrypt")
            encrypted_chunk = self.conv_bytes_to_bytestring(self.iv) + encrypted_chunk
        globals.Reporter.message("encrypted chunk has size "+str(len(encrypted_chunk)),"encrypt")
        return encrypted_chunk

class Decoder(Encrypter):
    def __init__(self, key,filename):
        Encrypter.__init__(self,key,filename)
        self.open_file()
        self.buffer=""

    def open_file(self):
        if not os.path.exists(self.filename):
            self.file = open(self.filename,'wb')

    def write(self, offset, chunk, chunksize):
        # to support reading in non-blocksize chunks, we append the provided chunk
        # to our internal buffer, then process that buffer in as muchs blocks as possible
        globals.Reporter.message("buffering decryption stream","encrypt")
        self.buffer +=chunk
        bufsize=len(self.buffer)
        orichunksize = chunksize
        if self.key != None:
            chunksize = int(bufsize / self.key.blocksize) * self.key.blocksize
            if chunksize == 0:
                globals.Reporter.message("postponing decryption due to too small chunk","encrypt")
                return

            chunk = "".join(self.buffer[:chunksize])
            self.buffer = "".join(self.buffer[chunksize:])
        else:
            chunk = self.buffer
            self.buffer=""

        globals.Reporter.message("calculating offset: "  +str(offset)+"," + str(orichunksize) + "," + str(bufsize),"encrypt")
        offset = offset + orichunksize - bufsize
        globals.Reporter.message("Using buffered values offset " + str(offset) + "/chunk size " + str(chunksize),"encrypt")

        position = 0
        if self.key != None and offset == 0:
            globals.Reporter.message("removing IV vector from start of decoding stream","encrypt")
            # remove the unencrypted IV list and create the decoder
            self.iv = "".join(chunk[:self.key.blocksize])
            chunk="".join(chunk[self.key.blocksize:])
            chunksize-=self.key.blocksize
            offset+=self.key.blocksize
            self.create_encoder()
            globals.Reporter.message("IV vector is " + binascii.hexlify(self.iv),"encrypt")

        # if chunksize == blocksize and we are at the first block
        if len(chunk) == 0:
            return

        # decrypt the remaining part of the chunk
        if self.key != None:
            decrypted_chunk = self.encoder.decrypt(chunk)
            if position < chunksize and (offset+position) == self.key.blocksize:
                self.randomsize = int(ord(decrypted_chunk[position]))
                globals.Reporter.message("skipping randomsize value of " + str(self.randomsize),"encrypt")
                position+=1

            if offset+position < self.key.blocksize + 1 + self.randomsize:
                # skip the random bytes
                globals.Reporter.message("skipping random values of " + str(self.randomsize),"encrypt")
                position=self.key.blocksize + self.randomsize + 1 - offset
        else:
            decrypted_chunk = chunk


        if position < chunksize:
            # room left to read bytes for the file
            globals.Reporter.message("reading " + str(chunksize - position) + " bytes for file","encrypt")
            bytes = "".join(decrypted_chunk[position:])

            if self.file != None:
                self.file.write(bytes)

