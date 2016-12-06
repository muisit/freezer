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

import boto3
import globals
import config
import os
import hashlib, binascii
import time

import vault
import job
import encoder

class AWSInterface:
    def __init__(self):
        self.region=None
        self.akey=None
        self.skey=None
        self.accountid="-"

        self.glacier_client = None
        self.glacier_resource = None
        self.sqs_client = None

        self.cache={
            'jobs': {},
            'vaults': {}
        }

    def parse_time(self, tm):
        if tm == None:
            return 0
        return time.strptime(tm[:19],"%Y-%m-%dT%H:%M:%S")

    def get_config(self):
        if self.region == None:
            self.region = globals.Config.getValue('awsregion')
            self.akey= globals.Config.getValue('accesskey')
            self.skey = globals.Config.getValue('secretkey')
            self.accountid = globals.Config.getValue("accountid")

    def create_sqs_client(self):
        if self.sqs_client == None:
            self.get_config()
            self.sqs_client = boto3.client('sqs',
                aws_access_key_id = self.akey,
                aws_secret_access_key = self.skey,
                region_name = self.region
                )

    def create_glacier_client(self):
        if self.glacier_client == None:
            self.get_config()
            globals.Reporter.message("creating client with keys " + str(self.akey) + "/" + str(self.skey))
            self.glacier_client = boto3.client('glacier',
                aws_access_key_id = self.akey,
                aws_secret_access_key = self.skey,
                region_name = self.region
                )

    def create_glacier_resource(self):
        if self.glacier_resource == None:
            self.get_config()
            self.glacier_resource = boto3.resource('glacier',
                aws_access_key_id = self.akey,
                aws_secret_access_key = self.skey,
                region_name = self.region)

    def poll_sqs_queue(self, queuename):
        if not hasattr(self, 'sqs_messages'):
            self.sqs_messages=[]

        if len(self.sqs_messages) == 0:
            waittime= int(globals.Config.getValue("polltime"))
            self.create_sqs_client()
            response = self.sqs_client.receive_message(
                QueueUrl = queuename,
                AttributeNames = ['All'],
                MessageAttributeNames=['All'],
                WaitTimeSeconds = waittime)

            if response != None:
                if 'Messages' in response:
                    for m in response['Messages']:
                        self.sqs_messages.append(m)

        if len(self.sqs_messages) > 0:
            msg = self.sqs_messages[0]
            self.sqs_messages = self.sqs_messages[1:]
            return msg
        return None

    def delete_msg(self, queuename, msgid):
        self.create_sqs_client()
        response=self.sqs_client.delete_message(
            QueueUrl = queuename,
            ReceiptHandle = msgid
        )


    def download_file(self, vault, job, filename,key):
        try:
            self.create_glacier_resource()
            enc=None
            fl=None
            if key != None:
                enc=encoder.Decoder(key,filename)
            else:
                fl = open(filename,"wb")

            globals.Reporter.message("retrieving job from Glacier","aws")
            awsjob = self.glacier_resource.Job(self.accountid, vault.name, job.jobid)
            if awsjob.completed and awsjob.action == "ArchiveRetrieval":
                bytes=awsjob.retrieval_byte_range.split('-')
                if len(bytes) != 2:
                    globals.Reporter.error("byte range " + awsjob.retrieval_byte_range + " not valid")
                    return None
                sz = int(bytes[1]) - int(bytes[0])
                globals.Reporter.message("size to retrieve is "+str(sz),"aws")
                if bytes[0] != '0':
                    globals.Reporter.error("byte range does not start at 0: " + awsjob.retrieval_byte_range)
                    return None

                chunk = 1024*1024
                if enc!=None:
                    chunk = enc.chunksize(1024*1024)
                index=0
                while index < sz:
                    if globals.Controller.exitting:
                        return -1
                    if index+chunk > sz:
                        chunk = sz - index + 1
                    globals.Reporter.message("requesting range " + str(index) + "-" + str(index+chunk-1),"aws")
                    inv = awsjob.get_output('Range: bytes=' + str(index) + '-' + str(index+chunk -1))
                    if 'body' in inv:
                        data  = inv['body'].read()
                        globals.Reporter.message("size of retrieved buffer is " + str(len(data)),"aws")
                        if enc!=None:
                            enc.write(index,data, len(data))
                        else:
                            fl.write(data)
                        index+=len(data)
                if enc!=None:
                    enc.close_file()
                elif fl!=None:
                    fl.close()
                return sz
            else:
                return -1
        except:
            globals.Reporter.error("error downloading archive",True)
        return None

    def download_inventory(self, vault, job):
        if job!= None and hasattr(job,'jobid') and job.jobid in self.cache['jobs']:
            return self.cache['jobs'][job.jobid]
        try:
            self.create_glacier_resource()
            awsjob = self.glacier_resource.Job(self.accountid, vault.name, job.jobid)
            if awsjob.completed and awsjob.action=="InventoryRetrieval":
                sz = int(awsjob.inventory_size_in_bytes)
                inv=awsjob.get_output()
                globals.Reporter.message('result of AWS call is ' + str(inv),"aws")
                output=""
                if 'body' in inv:
                    output = str(inv['body'].read())
                self.cache['jobs'][job.jobid]=output
                return output
        except:
            globals.Reporter.error("caught error downloading inventory",True)
        return None

    def inventory(self, vault):
        self.create_glacier_resource()
        awsvault = self.glacier_resource.Vault(self.accountid, vault.name)
        response = awsvault.initiate_inventory_retrieval()
        id = response.id if not response is None else "N.A."
        return id

    def archive(self, vault, archive):
        self.create_glacier_resource()
        #awsvault = self.glacier_resource.Vault(self.accountid, vault.name)
        awsarchive = self.glacier_resource.Archive(self.accountid,vault.name,archive.name)
        if awsarchive:
            try:
                j = awsarchive.initiate_archive_retrieval()
                j.load()
                return j.job_id
            except:
                return None

    def upload_file(self, vault,archive, key, cb):
        fl = archive.local_file
        if os.path.exists(fl):
            self.create_glacier_client()
            enc = encoder.Encoder(key, fl)
            chunksize = enc.chunksize(int(globals.Config.getValue("chunksize")))
            filesize = enc.total_size()

            chunks = int(filesize / chunksize)
            if (chunks * chunksize) < filesize:
                chunks+=1

            globals.Reporter.message("initiating request for " + archive.description + " of size " + str(filesize) + " in " + str(chunks) + " chunks of "+ str(chunksize) + " bytes","aws")
            response = self.glacier_client.initiate_multipart_upload(
                vaultName = vault.name,
                archiveDescription = archive.description,
                partSize = str(chunksize),
                accountId = self.accountid)
            if response != None:
                uploadid = response["uploadId"]
                hashes=[]
                for i in range(chunks):
                    if globals.Controller.exitting:
                        return None

                    offset = i * chunksize
                    size = chunksize
                    if offset + size > filesize:
                        size = filesize - offset
                    cb(offset,filesize)
                    chunk = enc.read(offset,size)
                    chunkhash = hashlib.sha256(chunk).digest()
                    hashes.append(chunkhash)

                    globals.Reporter.message("initiating upload of chunk " + str(i),"aws")
                    response = self.glacier_client.upload_multipart_part(vaultName = vault.name,
                        uploadId = uploadid,
                        range = "bytes " + str(offset) + "-" + str(offset + size - 1) + "/*",
                        checksum = binascii.hexlify(chunkhash),
                        body = chunk,
                        accountId = self.accountid)
                    if "checksum" in response:
                        cb(offset+(size/2),filesize)
                    else:
                        globals.Reporter.message("upload returned "+str(response),"aws")
                        cb(-3,-3)
                        return None

                enc.close_file()

                shahash=binascii.hexlify(self.compute_tree_hash(hashes,cb))
                globals.Reporter.message("finishing upload with treehash " + str(shahash),"aws")
                cb(-5,0)
                response = self.glacier_client.complete_multipart_upload(vaultName = vault.name,
                        uploadId = uploadid,
                        archiveSize = str(filesize),
                        checksum = str(shahash),
                        accountId = self.accountid)
                globals.Reporter.message("returned value is " + str(response),"aws")
                if 'archiveId' in response:
                    return response['archiveId']
            else:
                cb(-2,-2)
        else:
            cb(-1,-1)
        return None

    def compute_tree_hash(self, hashes,cb):
        myhashes=hashes
        while len(myhashes) > 1:
            oldhashes=myhashes
            globals.Reporter.message("computing tree hash of list of " + str(len(oldhashes)) + " hashes","aws")
            cb(-4,len(oldhashes))
            myhashes=[]
            sz = len(oldhashes)
            i = 0
            while i < sz:
                hash1 = oldhashes[i]
                i += 1
                if i < sz:
                    globals.Reporter.message("combining two hashes into one at position " + str(i-1),"aws")
                    hash2 = oldhashes[i]
                    i += 1
                    m = hashlib.sha256()
                    m.update(hash1)
                    m.update(hash2)
                    hash1 = m.digest()
                else:
                    globals.Reporter.message("last hash at "+str(i-1) + " is alone","aws")
                myhashes.append(hash1)

        cb(-4,0)
        return myhashes[0]

    def remove_archive(self, archive, vault):
        if archive.name != '':
            self.create_glacier_client()
            response = self.glacier_client.delete_archive(
                vaultName = vault.name,
                archiveId = archive.name,
                accountId= self.accountid)
        if "archiveId" in response:
            return response['archiveId']
        else:
            return None


    def import_file(self, vault, filename, descr):
        if not os.path.isfile(filename):
            globals.Reporter.error("non existant file provided for upload")
            return None

        fl = open(filename,'rb')

        self.create_glacier_client()
        response = self.glacier_client.upload_archive(
            vaultName = vault.name,
            archiveDescription = descr,
            body = fl,
            accountId= self.accountid)
        if "archiveId" in response:
            return response['archiveId']
        else:
            return None

    def list_vaults(self):
        globals.Reporter.message("list-vaults")
        vaults=[]
        self.create_glacier_client()
        lst = self.glacier_client.list_vaults(accountId=self.accountid, limit='100')
        while lst != None and "VaultList" in lst:
            for i in lst["VaultList"]:
                globals.Reporter.message("iterator is " + str(i))
                v = vault.Vault()
                v.import_aws(i)
                vaults.append(v)
            if "Marker" in lst and lst["Marker"] != "":
                lst = self.glacier_client.list_vaults(accountId=self.accountid, marker=lst["Marker"], limit='100')
            else:
                lst=None
        return vaults

    def list_jobs(self,vault):
        #if vault!= None and hasattr(vault,'arn') and vault.arn in self.cache['vaults']:
        #    return self.cache['vaults'][vault.arn]

        globals.Reporter.message("list-jobs",'glacier')
        jobs=[]
        self.create_glacier_client()
        lst = self.glacier_client.list_jobs(vaultName=vault.name, accountId=self.accountid, limit='100')
        while lst != None and "JobList" in lst:
            for i in lst["JobList"]:
                globals.Reporter.message("iterator is " + str(i))
                j = job.Job()
                j.import_aws(i)
                jobs.append(j)
            if "Marker" in lst and lst["Marker"] != "":
                lst=self.glacier_client.list_jobs(vaultName=vault.name, accountId=self.accountid, marker=lst["Marker"], limit='100')
            else:
                lst=None
        self.cache['vaults'][vault.arn]=jobs
        return jobs

    def create_vault(self, vault):
        globals.Reporter.message("creating new vault","glacier")
        self.create_glacier_client()
        loc = self.glacier_client.create_vault(accountId=self.accountid, vaultName = vault.name)
        if not loc:
            return False
        return True

    def remove_vault(self,vault):
        self.create_glacier_client()
        resp = self.glacier_client.delete_vault(accountId=self.accountid, vaultName=vault.name)
        return resp


globals.Config.setOption("accountid",globals.Config.Option("-i","--accountid","AWS account id","-",True))
globals.Config.setOption("region",globals.Config.Option("-r","--region","AWS region","eu-west-1",True))
globals.Config.setOption("accesskey",globals.Config.Option("-a","--access-key","AWS access key","",True))
globals.Config.setOption("secretkey",globals.Config.Option("-s","--secret-key","AWS secret key","",True))
globals.Config.setOption("chunksize",globals.Config.Option(None,"--chunk-size","Upload chunk size","1048576",True))
globals.Config.setOption("polltime",globals.Config.Option(None,"--poll-time","Long poll wait time for SQS","20",True))
globals.Config.setOption("sqsqueue",globals.Config.Option("-q","--queue","SQS queue name to poll","https://sqs.eu-west-1.amazonaws.com/523976068759/awsfreezer",True))

globals.AWS = AWSInterface()
