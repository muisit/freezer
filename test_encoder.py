#!/usr/bin/python
#
import sys
sys.path.append("interfaces")
sys.path.append("debug")
sys.path.append("model")

import globals
import debug
import config

import encoder

import Crypto.Cipher
import Crypto.Random
import Crypto.Random.random
import binascii
import json
import tempfile
import os
import os.path
import key

def header():
    print "Freezer Encoder Test"

def usage():
    print "Usage: test_encoder"
    globals.Config.printOptions()

globals.Config.setOption("iterations",globals.Config.Option("-i","--iterations","Number of iterations","1",True))
globals.Config.setOption("size",globals.Config.Option("-s","--file-size","Maximum file size to test with","1024",True))
globals.Config.setOption("enckey",globals.Config.Option("-e","--encryption-key","Encryption algorithm","AES",True))

def create_file(fsize):
    (fhandle, fname) = tempfile.mkstemp(".txt","test_encoder")
    txt="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    txtsz=len(txt) - 1
    obj = Crypto.Random.random.StrongRandom()
    for i in range(fsize):
        c = txt[obj.randint(0,txtsz)]
        os.write(fhandle,c)
    os.close(fhandle)
    return fname

def create_key(algo):
    dct = key.Key()
    obj = Crypto.Random.random.StrongRandom()
    choice = obj.randint(1,3)
    if algo == "AES":
        dct.algorithm="AES"
        dct.blocksize=16
        if choice == 1:
            dct.keysize=128
        elif choice == 2:
            dct.keysize=196
        else:
            dct.keysize=256
    if algo == "Blowfish":
        dct.algorithm="Blowfish"
        dct.blocksize=8
        if choice == 1:
            dct.keysize=128
        elif choice == 2:
            dct.keysize=196
        else:
            dct.keysize=256
    if algo == "CAST":
        dct.algorithm="CAST"
        dct.blocksize=8
        if choice == 1:
            dct.keysize=40
        elif choice == 2:
            dct.keysize=80
        else:
            dct.keysize=128
    if algo == "RC5":
        dct.algorithm="RC5"
        dct.blocksize=8
        if choice == 1:
            dct.keysize=128
        elif choice == 2:
            dct.keysize=196
        else:
            dct.keysize=512
    if algo == "DES":
        dct.algorithm="DES"
        dct.blocksize=8
        dct.keysize=64
    if algo == "DES3":
        dct.algorithm="DES3"
        dct.blocksize=8
        dct.keysize=128
    if algo == "IDEA":
        dct.algorithm="IDEA"
        dct.blocksize=8
        dct.keysize=128
    if algo == "none":
        dct.algorithm="none"
        dct.keysize=8

    dct.keystring= binascii.hexlify(Crypto.Random.get_random_bytes(int(dct.keysize / 8)))
    if dct.algorithm == "none":
        dct=None
    return dct

if __name__ == "__main__":
    files=globals.Config.readArguments(sys.argv[1:],header,usage)
    globals.Reporter.message("Started Test")

    algo = globals.Config.getValue("enckey")

    num = int(globals.Config.getValue('iterations'))
    globals.Reporter.message("running " + str(num) + " iterations","main")

    rnd = Crypto.Random.random.StrongRandom()
    maxfsize = int(globals.Config.getValue("size"))
    for i in range(num):
        keyvals = create_key(algo)

        filesize = rnd.randint(maxfsize / 10,maxfsize)
        globals.Reporter.message("creating random file of " + str(filesize) + " size","main")
        fname = create_file(filesize)
        globals.Reporter.message("file is called '"  +str(fname)+"'","main")
        enc = encoder.Encoder(keyvals,fname)
        if hasattr(enc,'iv'):
            globals.Reporter.message("IV is " + binascii.hexlify(enc.iv),"main")
        tsize = enc.total_size()
        globals.Reporter.message("total encoded size is " + str(tsize),"main")
        chunksize=enc.chunksize(Crypto.Random.random.randint(2,35))
        globals.Reporter.message("reading chunks of size "+ str(chunksize),"main")

        offset = 0
        allchunks=[]
        while offset < tsize:
            csize = offset+chunksize
            if csize > tsize:
                csize=tsize
            csize = csize - offset
            chunk = enc.read(offset, csize)
            offset += chunksize
            allchunks+=chunk
        enc.close_file()

        globals.Reporter.message("displaying encoded file of size "+ str(len(allchunks)),"main")
        tsize = len(allchunks)
        pos=0
        while pos < tsize:
            endpos = pos+16
            if endpos > tsize:
                endpos = tsize
            display_chunk="".join(allchunks[pos:endpos])
            #print "%04d" % (pos) + ": " + binascii.hexlify(display_chunk)
            pos = endpos

        globals.Reporter.message("writing chunks to decoder and file " + fname+ ".out","main")
        decoder= encoder.Decoder(keyvals,fname + ".out")

        offset = 0
        echunks=chunksize
        chunksize = rnd.randint(2,1024)
        while offset < tsize:
            globals.Reporter.message("decoding at "+str(offset)  + "/" + str(tsize),"main")
            endpos = offset+chunksize
            if endpos > tsize:
                endpos=tsize
            prtchunk = "".join(allchunks[offset:endpos])
            decoder.write(offset, prtchunk, endpos - offset)
            offset=endpos
        decoder.close_file()
        globals.Reporter.message("end of decoding","main")

        # now check both files
        if not os.path.exists(fname):
            print "%8d"%i + ": ERROR: initial file does not exist"
        elif not os.path.exists(fname + ".out"):
            print "%8d"%i + ": ERROR: output file does not exist"
        else:
            sz1 = os.path.getsize(fname)
            sz2 = os.path.getsize(fname+".out")
            if sz1 != sz2:
               print "%8d"%i + ": ERROR: file size differences: " + str(sz1) + " vs " + str(sz2)
            else:
                fl = open(fname,"rb")
                buf1 = fl.read(sz1)
                fl.close()
                fl = open(fname+".out","rb")
                buf2 = fl.read(sz1)
                fl.close()
                if buf1 != buf2:
                    print "%8d"%i + ": ERROR: file content differences"
                else:
                    if keyvals == None:
                        print "%8d"%i+": OKAY " + "none/" + str(echunks) + "/" + str(chunksize) + "/" + str(sz1) + "/" + str(algo)
                    else:
                        print "%8d"%i+": OKAY " + str(keyvals.keysize) + "/" + str(echunks) + "/" + str(chunksize) + "/" + str(sz1) + "/" + str(algo)

                