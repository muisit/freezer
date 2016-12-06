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

import globals
import action
import datetime, time
import json
import os,re
import tarfile
import binascii

import vault, job, archive, archivefile, key

class ActionFactory:
    def __init__(self):
        pass

    def initialise_db(self):
        act = action.Action(cmd_initialise_db)
        globals.Controller.activate(act)

    def sqs_long_poll(self):
        act = action.Action(cmd_sqs_long_poll)
        globals.Controller.activate(act)

    def store_settings(self, vals):
        act = action.Action(cmd_store_settings)
        act.values=vals
        globals.DB.activate(act)

    def conditionally_load_vaults(self):
        act = action.Action(cmd_conditionally_retrieve_vaults)
        globals.DB.activate(act)

    def load_jobs(self,vault, dorefresh=False):
        act = action.Action(cmd_retrieve_jobs)
        act.vault=vault
        if dorefresh:
            act.refresh=True
        globals.Controller.activate(act)

    def display_vault(self, widget, name):
        act = action.Action(cmd_load_and_display_vault)
        act.vaultname=name
        act.widget=widget
        globals.DB.activate(act)

    def create_vault(self, name):
        act = action.Action(cmd_create_vault)
        act.vaultname=name
        act.status="init"
        globals.DB.activate(act)

    def remove_vault(self, name):
        act = action.Action(cmd_remove_vault)
        act.vault_name=name
        act.status="init"
        globals.DB.activate(act)

    def fill_vault_dialog(self,name, withrefresh=False):
        act = action.Action(cmd_select_vault_content)
        act.vaultname=name
        act.status="init"
        if not withrefresh:
            act.no_refresh=True
        globals.DB.activate(act)

    def refresh_vault(self,widget,name):
        act = action.Action(cmd_request_inventory_conditionally)
        act.widget=widget
        act.vaultname=name
        act.status="init"
        globals.DB.activate(act)

    def add_files_to_archiveview(self,widget,pathlist):
        act = action.Action(cmd_add_files_to_archiveview)
        act.files=pathlist
        act.widget=widget
        globals.Controller.activate(act)

    def create_archive(self, vault, name, ext, lst, excludelist):
        act = action.Action(cmd_create_archive)
        act.vault_name=vault
        act.archive_name = name
        act.extension=ext
        act.files =lst
        act.excludelist = excludelist
        act.status="init"
        globals.DB.activate(act)

    def show_message(self, txt, secondtxt=""):
        act = action.Action(cmd_message)
        act.txt=txt
        act.txt2=secondtxt
        globals.GUI.activate(act)

    def remove_archive(self, id):
        act = action.Action(cmd_remove_archive)
        act.archive_id = id
        act.status='init'
        globals.DB.activate(act)

    def remove_archive_file(self, id):
        act = action.Action(cmd_remove_archive_file)
        act.archive_id = id
        globals.DB.activate(act)

    def vault_status(self,vault, msg):
        act = action.Action(cmd_vault_status_message)
        act.message=msg
        act.vault=vault
        globals.GUI.activate(act)

    def window_status(self,widget,msg):
        act = action.Action(cmd_window_status_message)
        act.widget=widget
        act.message=msg
        globals.GUI.activate(act)

    def list_keys(self, widget):
        act = action.Action(cmd_list_keys)
        act.widget=widget
        globals.DB.activate(act)

    def create_key(self,keyvals,widget):
        act = action.Action(cmd_save_key)
        act.widget=widget
        act.keyvals=keyvals
        globals.DB.activate(act)

    def fill_archive_list(self, widget, archiveid):
        act = action.Action(cmd_fill_archive_list)
        act.widget=widget
        act.archive_id = archiveid
        globals.DB.activate(act)

    def fill_job_list(self,widget):
        act = action.Action(cmd_fill_job_list)
        act.widget=widget
        globals.DB.activate(act)

    def fill_file_list(self,widget):
        act = action.Action(cmd_fill_file_list)
        act.widget=widget
        globals.DB.activate(act)

    def save_archive(self, vault_name, archive_id):
        act = action.Action(cmd_save_archive)
        act.vault_name = vault_name
        act.archive_id = archive_id
        globals.DB.activate(act)

def util_decode_fname(fname):
    try:
        if not isinstance(fname, unicode):
            #globals.Reporter.message("decoding file '"+ binascii.hexlify(fname) + " using utf-8","action")
            fname = fname.decode('utf-8')
            #globals.Reporter.message("result is "+binascii.hexlify(fname.encode('utf-8')),"action")
    except:
        try:
            #globals.Reporter.message("decoding file '"+ binascii.hexlify(fname) + " using windows-1252","action")
            fname = fname.decode('windows-1252')
            #globals.Reporter.message("result is "+binascii.hexlify(fname.encode('utf-8')),"action")
        except:
            globals.Reporter.error("unable to decode filename",True)
            fname=""
    return fname

def util_file_exists(path,name=None):
    path1=path
    path2=path
    path3=path
    if name != None:
        #globals.Reporter.message("testing file "+binascii.hexlify(name.encode('utf-8')) + " parameter of type " +str(type(name)),"action")
        # this never fails, as we are adding 2 unicode strings. However, the os.path.exists test later on might fail
        # which is the reason we need the 2 decoding steps
        path1=os.path.join(path1,name)
        try:
            path2=os.path.join(path.encode('utf-8'),name.encode('utf-8'))
            #globals.Reporter.message("path 2 is valid: " + path2)
        except:
            #globals.Reporter.error("path 2 is invalid",True)
            path2=None
        try:
            path3=os.path.join(path.encode('windows-1252'),name.encode('windows-1252'))
            #globals.Reporter.message("path 3 is valid: " + path3.decode('windows-1252'))
        except:
            #globals.Reporter.error("path 3 is invalid",True)
            path3=None
    else:
        try:
            path2 = path1.encode('utf-8')
            #globals.Reporter.message("path 2 is valid: " + path2)
        except:
            #globals.Reporter.error("path 2 is invalid",True)
            path2=None
        try:
            path3=path1.encode('windows-1252')
            #globals.Reporter.message("path 3 is valid: " + path3.decode('windows-1252'))
        except:
            #globals.Reporter.error("path 3 is invalid",True)
            path3=None

    if os.path.exists(path1):
        return path1
    if path2 and os.path.exists(path2):
        return path2
    if path3 and os.path.exists(path3):
        return path3
    if name:
        globals.Reporter.message("file resembling "+name.encode('ascii','ignore') + " does not exist")
    else:
        globals.Reporter.message("file resembling "+path.encode('ascii','ignore') + " does not exist")
    return None

def cmd_save_archive(cmd, caller, data=None):
    if caller == "db":
        globals.Reporter.message("save archive test","action")
        globals.DB.open()
        cmd.vault =vault.Vault()
        cmd.vault.by_name(cmd.vault_name)
        cmd.archive=archive.Archive()
        cmd.archive.load(cmd.archive_id)

        if cmd.archive.id != None and cmd.vault.id != None and cmd.archive.vault_id == cmd.vault.id:
            globals.Reporter.message("archive and vault exists, local file is '" + str(cmd.archive.local_file) + "'")
            if not cmd.archive.local_file:
                lst = cmd.archive.description.rsplit(':',1)
                if len(lst)>0:
                    cmd.archive.local_file = lst[0]
                    globals.Reporter.message("set local file to '" + cmd.archive.local_file + "' based on description '" + str(cmd.archive.description) + "'","action")
                if not cmd.archive.local_file:
                    cmd.archive.local_file="archive.dat"
                cmd.archive.save()
            filename = util_file_exists(globals.Config.getValue('uploadfolder'),os.path.basename(cmd.archive.local_file))
            if  filename != None:
                globals.Reporter.message("filename '" + str(filename) + "' already present, refreshing listing","action")
                globals.DB.close()
                globals.ActionFactory.fill_vault_dialog(cmd.vault.name)
            else:
                globals.Reporter.message("searching for job","action")
                cmd.job=None
                jobs = job.Job.by_vault(cmd.vault)
                for j in jobs:
                    if j.action == 'ArchiveRetrieval' and j.archiveid == cmd.archive.name:
                        globals.Reporter.message("found job id " + str(j.id),"action")
                        cmd.job = j

                globals.DB.close()
                if cmd.job != None:
                    globals.Reporter.message("job found with completion date " + str(cmd.job.completion_date),"action")
                    if cmd.job.completion_date:
                        globals.Reporter.message("downloading file","action")
                        act = action.Action(cmd_download_archive)
                        act.job=cmd.job
                        act.vault=cmd.vault
                        act.state="init"
                        globals.DB.activate(act)
                        globals.ActionFactory.vault_status(cmd.vault,"Downloading archive " + cmd.archive.description)
                    else:
                        globals.Reporter.message("job is pending, so we skip any action","action")
                    # else the job is already pending, so we cannot do anything
                else:
                    # create a download job
                    globals.Reporter.message("creating download job","action")
                    globals.Controller.activate(cmd)
        else:
            globals.Reporter.message("archive " + str(cmd.archive_id) + " or vault " + str(cmd.vault_name) + " does not exist","action")
    elif caller == "backend":
        globals.Reporter.message("creating download job","action")
        jobid = globals.AWS.archive(cmd.vault, cmd.archive)
        if jobid == None:
            globals.Reporter.message("failed","action")
            globals.ActionFactory.show_message("Unable to initiate archive download","AWS Glacier refused to create a retrieval job")
        else:
            globals.Reporter.message("succeeded","action")
            globals.ActionFactory.vault_status(cmd.vault, "Initiated retrieval job " + str(jobid))
            globals.ActionFactory.load_jobs(cmd.vault,True)

def cmd_fill_file_list(cmd, caller, data=None):
    if caller=="db":
        globals.DB.open()
        files = archivefile.ArchiveFile.list_all()
        cmd.files=[]
        for fl in files:
            fl.fullpath = os.path.join(fl.path,fl.name)
            cmd.files.append(fl)
        globals.DB.close()
        globals.GUI.activate(cmd)
    elif caller == "gui":
        cmd.widget.original_files=cmd.files
        cmd.widget.fill_file_model(cmd.files)

def cmd_fill_job_list(cmd, caller, data=None):
    if caller == "db":
        globals.DB.open()
        jobs = job.Job.list_all()
        vlist={}
        alist={}
        cmd.jobs=[]
        for j in jobs:
            k = "vault_" + str(j.vault_id)
            if not k in vlist:
                v = vault.Vault()
                v.load(j.vault_id)
                if not v.id == None:
                    vlist[k] = v
            if k in vlist:
                j.vault = vlist[k].name
            else:
                j.vault="Unknown"

            if j.archiveid and not j.archiveid in alist:
                a = archive.Archive()
                a.by_name(j.archiveid)
                if a.id != None:
                    alist[j.archiveid] = a
            if j.archiveid and j.archiveid in alist:
                j.archive=alist[j.archiveid].description
            else:
                j.archive=""
            cmd.jobs.append(j)
        globals.DB.close()
        globals.GUI.activate(cmd)
    elif caller=="gui":
        model = globals.GUI.create_job_model()
        for j in cmd.jobs:
            # jobid, vault, archive, action, status, size, requested, completed, executed
            sz=""
            if j.archive_size>0:
                sz = str(j.archive_size)
            elif j.inventory_size>0:
                sz = str(j.inventory_size)
            lst=[j.jobid[:10]+"...", j.vault, j.archive, j.action, j.status_code, sz, j.creation_date, j.completion_date, j.executed]
            globals.Reporter.message("pushing " + str(lst),"action")
            model.append(lst)
        cmd.widget.jobview.set_model(model)

def cmd_fill_archive_list(cmd, caller, data=None):
    if caller =="db":
        globals.DB.open()
        globals.Reporter.message("selecting archive " + str(cmd.archive_id),"action")
        cmd.archive=archive.Archive()
        cmd.archive.load(cmd.archive_id)
        if cmd.archive.id != None:
            cmd.files = archivefile.ArchiveFile.by_archive(cmd.archive)
            globals.Reporter.message("found " + str(len(cmd.files)) + " files in archive","action")
        globals.DB.close()
        if cmd.archive.id != None:
            globals.GUI.activate(cmd)
    elif caller=="gui":
        globals.Reporter.message("filling GUI file list")
        # path, name, size, changed, archive list, last upload, selected
        model = globals.GUI.create_file_model()
        for f in cmd.files:
            model.append([f.path, f.name, globals.GUI.long_to_size(f.size), f.date, f.in_archives, f.lastupload,int(not f.is_excluded),f.is_excluded, float(f.size)/(1024*1024), os.path.join(f.path,f.name)])
        cmd.widget.fileview.set_model(model)
        cmd.widget.set_entry(cmd.widget.window, 'output_name', os.path.basename(cmd.archive.local_file))

def cmd_save_key(cmd, caller,data=None):
    if caller=="db":
        globals.DB.open()
        k = key.Key()
        k.algorithm = cmd.keyvals['algorithm']
        k.keysize = int(cmd.keyvals['keysize'])
        k.blocksize = int(cmd.keyvals['blocksize'])
        k.keystring = cmd.keyvals['keystring']

        k2 = key.Key()
        k2.check_existance(k)
        if k2.id==None:
            k.save()

        globals.DB.close()
        globals.ActionFactory.list_keys(cmd.widget)

def cmd_list_keys(cmd,caller,data=None):
    if caller == "db":
        globals.DB.open()
        cmd.keys=key.Key.list_all()
        globals.DB.close()
        globals.GUI.activate(cmd)
    elif caller=="gui":
        selkey=-1
        try:
            selkey = int(globals.Config.getValue("encryptionkey"))
        except:
            pass
        model=globals.GUI.create_key_model()
        for k in cmd.keys:
            model.append([k.id, k.algorithm,k.keysize, k.blocksize,k.keystring])

        cmd.widget.keyview.set_model(model)
        sel = cmd.widget.keyview.get_selection()
        iter=model.get_iter_first()
        while iter != None:
            val = model.get_value(iter,0)
            if selkey == int(val):
                globals.Reporter.message("selecting key with id " + str(selkey),"action")
                sel.select_iter(iter)
            iter=model.iter_next(iter)

def cmd_remove_archive(cmd, caller, data=None):
    if caller == "backend":
        if cmd.archive.name != '':
            globals.AWS.remove_archive(cmd.archive, cmd.vault)

        filename = util_file_exists(os.path.join(globals.Config.getValue('uploadfolder'),os.path.basename(cmd.archive.local_file)))
        if filename != None:
            os.unlink(filename)

        globals.ActionFactory.vault_status(cmd.vault,"Removed archive "+cmd.archive.description)
        globals.ActionFactory.fill_vault_dialog(cmd.vault.name)
        cmd.status='postdelete'
        globals.DB.activate(cmd)
    elif caller == "db":
        if cmd.status == 'init':
            globals.DB.open()
            arch = archive.Archive()
            arch.load(cmd.archive_id)
            if arch.id != None:
                cmd.vault = vault.Vault()
                cmd.vault.load(arch.vault_id)
                cmd.archive = arch
            globals.DB.close()
            if arch.id != None:
                globals.Controller.activate(cmd)
        elif cmd.status == 'postdelete':
            cmd.archive.delete()
            cmd.vault.my_objects-=1
            cmd.vault.save()

            # update database cache values
            act=action.Action(cmd_db_maintenance)
            globals.DB.activate(act)

def cmd_remove_archive_file(cmd, caller, data=None):
    if caller == "db":
        globals.DB.open()
        arch = archive.Archive()
        arch.load(cmd.archive_id)
        if arch.id != None:
            filename = util_file_exists(arch.local_file)
            if filename != None:
                os.unlink(filename)

            cmd.vault = vault.Vault()
            cmd.vault.load(arch.vault_id)
        globals.DB.close()

        if arch.id != None:
            globals.ActionFactory.vault_status(cmd.vault,"Unlinked archive "+arch.description)
            globals.ActionFactory.fill_vault_dialog(cmd.vault.name)


def cmd_message(cmd, caller, data=None):
    if caller == "gui":
        globals.GUI.message_dialog(cmd.txt, cmd.txt2)

def cmd_test_download(cmd, caller, data=None):
    if caller == "backend":
        if tarfile.is_tarfile(cmd.filename):
            try:
                tar = tarfile.open(cmd.filename, "r:*")
                members = tar.getnames()
                cmd.archive.validate=globals.DB.timestamp()
                globals.DB.activate(cmd)
                return
            except:
                pass
        globals.ActionFactory.show_message("Archive Invalid","Unable to validate archive '" + cmd.archive.description + "'. It does not seem to be a valid TAR archive")
    elif caller == "db":
        cmd.archive.save()

def cmd_create_archive(cmd,caller, data=None):
    if caller == "backend":
        if len(cmd.excludelist):
            newlst=[]
            cnt=0
            for f in cmd.files:
                # f is a filename with path, all in utf-8 (because Gtk does not work well with unicode...)
                # we use the util_file_exists check to get an encoded filepath that exists
                # and use that to add to the tar file and set the ArchiveFile basics
                # However, we must use the unicode versions of name and path for the database
                unicode_name = f.decode('utf-8')
                encoded_name = util_file_exists(unicode_name)
                if encoded_name!=None:
                    #globals.Reporter.message("encoded name for " + unicode_name + " exists","action")
                    af=archivefile.ArchiveFile()
                    af.set_from_path(encoded_name)
                    # now use the unicode versions of the name for the database
                    af.name=os.path.basename(unicode_name)
                    af.path=os.path.dirname(unicode_name)
                    newlst.append(af)
            cmd.excludelist = newlst

        if len(cmd.files):
            if cmd.extension == ".tar.bz2" or cmd.extension == ".tar" or cmd.extension == ".tar.gz":
                tar=None
                if cmd.extension == ".tar.bz2":
                    tar = tarfile.open(cmd.archive_name, 'w:bz2')
                elif cmd.extension == ".tar.gz":
                    tar = tarfile.open(cmd.archive_name, 'w:gz')
                else:
                    tar = tarfile.open(cmd.archive_name, 'w')

                newlst=[]
                cnt=0
                for f in cmd.files:
                    if globals.Controller.exitting:
                        return
                    # f is a filename with path, all in utf-8 (because Gtk does not work well with unicode...)
                    # we use the util_file_exists check to get an encoded filepath that exists
                    # and use that to add to the tar file and set the ArchiveFile basics
                    # However, we must use the unicode versions of name and path for the database
                    unicode_name = f.decode('utf-8')
                    encoded_name = util_file_exists(unicode_name)
                    if encoded_name!=None:
                        #globals.Reporter.message("encoded name for " + unicode_name + " exists","action")
                        af=archivefile.ArchiveFile()
                        globals.ActionFactory.vault_status(cmd.vault,"Adding file " + os.path.basename(f))
                        cnt+=1
                        tar.add(encoded_name,None,False)
                        af.set_from_path(encoded_name)
                        # now use the unicode versions of the name for the database
                        af.name=os.path.basename(unicode_name)
                        af.path=os.path.dirname(unicode_name)
                        newlst.append(af)
                    #else:
                    #    globals.Reporter.message("encoded name for " + f + " does NOT exist","action")
                tar.close()
                globals.Reporter.message("added " + str(cnt) + " files to tar","action")

                if len(newlst):
                    cmd.tar = tar
                    cmd.files=newlst
        globals.DB.activate(cmd)

    elif caller == "db":
        if cmd.status=="init":
            globals.DB.open()
            cmd.vault=vault.Vault()
            cmd.vault.by_name(cmd.vault_name)
            cmd.status="store"
            globals.DB.close()
            globals.Controller.activate(cmd)
        else:
            globals.DB.open()
            for f in cmd.excludelist:
                if globals.Controller.exitting:
                    return
                fl = archivefile.ArchiveFile.by_sha256(f.sha256, f.size, f.name)
                if fl != None:
                    if fl.is_excluded==0:
                        fl.is_excluded=1
                        fl.save()
                    else:
                        fl.is_excluded=1
                        fl.save()

            newlst=[]
            for f in cmd.files:
                if globals.Controller.exitting:
                    return
                fl = archivefile.ArchiveFile.by_sha256(f.sha256, f.size, f.name)
                if fl != None:
                    fl.path = f.path
                    newlst.append(fl)
                else:
                    newlst.append(f)
            cmd.files=newlst

            if len(cmd.files) and hasattr(cmd, 'tar'):
                enckey = globals.Config.getValue("encryptionkey")
                k = key.Key()
                k.load(enckey)

                descr = os.path.basename(cmd.archive_name)
                if k.id != None:
                    descr+=":" + k.algorithm +"-" + str(k.keysize) + "-" + str(k.id)

                cmd.archive = archive.Archive()
                cmd.archive.description = descr
                cmd.archive.size = os.path.getsize(cmd.archive_name)
                cmd.archive.created = globals.DB.timestamp()
                cmd.archive.local_file=cmd.archive_name
                cmd.archive.vault_id=cmd.vault.id
                cmd.archive.save()
                cmd.archive.add_files(cmd.files)
                globals.DB.close()

                globals.Reporter.message("local file of archive is '" + str(cmd.archive.local_file) + "'","action")
                # refresh the vault listing in the main screen
                act = action.Action(cmd_display_vaults)
                globals.DB.activate(act)

                # refresh the vault content listing (if displayed)
                globals.ActionFactory.fill_vault_dialog(cmd.vault.name,True)

                # then start uploading the new archive
                act = action.Action(cmd_upload_archive)
                act.archive = cmd.archive
                act.vault=cmd.vault
                act.key=k
                globals.Controller.activate(act)

                # and update the file status
                act = action.Action(cmd_db_maintenance)
                globals.DB.activate(act)

def cmd_upload_archive(cmd, caller, data=None):
    def upload_callback(current, total):
        if current < 0:
            if current == -1:
                globals.ActionFactory.show_message("Unable to upload archive " + str(cmd.archive.description) + " at " + str(cmd.archive.local_file))
            elif current == -2:
                globals.ActionFactory.show_message("Upload initiation returned an error")
            elif current == -3:
                globals.ActionFactory.show_message("Error uploading chunk")
            elif current == -4:
                if total == 0:
                    message = "Finished computing tree hash"
                    globals.ActionFactory.vault_status(cmd.vault, message)
                else:
                    message = "Computing tree hash for " + str(total) + " hashes"
                    globals.ActionFactory.vault_status(cmd.vault, message)
            elif current == -5:
                if total == 0:
                    message = "Finalizing upload to Glacier"
                    globals.ActionFactory.vault_status(cmd.vault, message)

        else:
            percentage = str(int(100 * float(current) / total)) + "%"
            message = "Uploading archive "+cmd.archive.description + " at " + str(percentage)
            globals.ActionFactory.vault_status(cmd.vault, message)

    if caller == "backend":
        aid = globals.AWS.upload_file(cmd.vault, cmd.archive, cmd.key,upload_callback)
        cmd.archive.name=aid
        cmd.archive.key_id=cmd.key.id
        globals.DB.activate(cmd)
    elif caller == "db":
        globals.DB.open()
        cmd.archive.save()
        cmd.vault.count_objects()
        globals.DB.close()
        globals.ActionFactory.vault_status(cmd.vault,"Succesfully uploaded archive "+cmd.archive.description + " as " + cmd.archive.name)
        globals.ActionFactory.fill_vault_dialog(cmd.vault.name)

def cmd_vault_status_message(cmd, caller, data=None):
    if caller == "gui":
        if cmd.vault.name in globals.GUI.vaultdialog:
            widget = globals.GUI.vaultdialog[cmd.vault.name]
            widget.statusbar_push(cmd.message)

def cmd_window_status_message(cmd, caller, data=None):
    if caller == "gui":
        if cmd.widget and hasattr(cmd.widget,'statusbar'):
            cmd.widget.statusbar_push(cmd.message)

def cmd_add_files_to_archiveview(cmd, caller, data=None):
    def recursively_add_files(path, fname):
        if globals.Controller.exitting:
            return None

        #if fname != None:
        #    globals.Reporter.message("recursively adding path '" + path + "' and '" + fname + "'","action")
        fpath = util_file_exists(path,fname)
        if fpath != None:
            if os.path.isdir(fpath):
                # http://stackoverflow.com/questions/10180765/open-file-with-a-unicode-filename
                # os.listdir needs to be called with an explicit unicode string
                fnames = os.listdir(unicode(fpath))
                retval=[]
                for f in fnames:
                    # this decode step takes care of non-utf8 encodings in the OS (read: Windows)
                    f = util_decode_fname(f)
                    if f:
                        lst = recursively_add_files(fpath,f)
                        if lst != None:
                            retval += lst
                return retval
            elif os.path.isfile(fpath):
                return [fpath]
        else:
            globals.Reporter.message("unable to add file of which name resembles " + os.path.join(path.encode('utf-8','ignore'), fname.encode('utf-8','ignore')),"action")
            globals.ActionFactory.window_status(cmd.widget,"Error adding filename " + fname.encode('utf-8','ignore'))
        return None

    if caller == "backend":
        filelist=[]
        cmd.files_by_name = {}
        globals.ActionFactory.window_status(cmd.widget,"Searching for files in selected paths")
        for f in cmd.files:
            f = util_decode_fname(f)
            filelist += recursively_add_files(f,None)
        # no we end up with a list of filenames in various encodings (ascii, utf8, windows-1252)
        globals.ActionFactory.window_status(cmd.widget,"Found " + str(len(filelist)) + " files, creating models (0%)")
        sz=len(filelist)
        step=sz / 100
        if step < 2:
            step = 2
        cmd.files=[]
        file_by_path={}
        cnt=0
        nextstep=step
        for name in filelist:
            if globals.Controller.exitting:
                return

            cnt+=1
            if cnt > nextstep:
                globals.ActionFactory.window_status(cmd.widget,"Found " + str(len(filelist)) + " files, creating models (%2.0f%%)" % (float(cnt*100) / sz))
                nextstep+=step
            af=archivefile.ArchiveFile()
            af.set_from_path(name)
            # now re-decode the filename and path to unicode
            af.name = util_decode_fname(af.name)
            af.path = util_decode_fname(af.path)
            fullpath=os.path.join(af.path,af.name)
            if fullpath not in file_by_path:
                file_by_path[fullpath]=True
                cmd.files.append(af)
        globals.DB.activate(cmd)
    elif caller == "db":
        globals.DB.open()
        newlst=[]
        globals.ActionFactory.window_status(cmd.widget,"Matching files with existing files in database (0%)")
        sz = len(cmd.files)
        step = sz/100
        if step < 2:
            step = 2
        cnt=0
        nextstep=step
        for f in cmd.files:
            if globals.Controller.exitting:
                return

            cnt+=1
            if cnt > nextstep:
                nextstep+=step
                globals.ActionFactory.window_status(cmd.widget,"Matching files with existing files in database (%2.0f%%)" % (float(100*cnt) / sz))

            #globals.Reporter.message("searching for "+ f.name,"action")
            fl = archivefile.ArchiveFile.by_sha256(f.sha256, f.size, f.name)
            if fl != None:
                fl.path=f.path
                newlst.append(fl)
            else:
                f.lastupload=''
                f.in_archives=""
                newlst.append(f)
        cmd.files=newlst
        globals.DB.close()
        globals.ActionFactory.window_status(cmd.widget,"Creating GUI model")
        globals.GUI.activate(cmd)
    elif caller=="gui":
        model = cmd.widget.fileview.get_model()
        cmd.widget.fileview.set_model(globals.GUI.create_file_model())
        iter= model.get_iter_first()
        selfiles={}
        sizecount=long(0)
        filecount=0
        selfilecount=0
        # the model contains a string instead of a unicode-string, so we must encode everything to utf-8
        while iter != None:
            fname = os.path.join(model.get_value(iter,0),model.get_value(iter,1))
            filecount+=1
            if model.get_value(iter,6) == 1:
                selfilecount+=1
                sizecount+= cmd.widget.files[fname]
            selfiles[fname]=True
            iter = model.iter_next(iter)
        for f in cmd.files:
            fname = os.path.join(f.path.encode('utf-8'),f.name.encode('utf-8'))
            if fname not in selfiles:
                cmd.widget.files[fname] = f.size
                if not f.is_excluded:
                    selfilecount+=1
                    sizecount+=f.size
                filecount+=1
                model.append([f.path, f.name, globals.GUI.long_to_size(f.size), f.date, f.in_archives,f.lastupload,int(not f.is_excluded),f.is_excluded, float(f.size)/(1024*1024), os.path.join(f.path,f.name)])
        cmd.widget.fileview.set_model(model)
        cmd.widget.update_status(filecount,sizecount,selfilecount)
        if cmd.widget.toolbutton.get_active():
            cmd.widget.apply_backup_filter(0)

def cmd_select_vault_content(cmd, caller, data=None):
    if caller == "db":
        globals.DB.open()
        globals.Reporter.message("select-vault-content DB thread","action")
        cmd.vault=vault.Vault()
        cmd.vault.by_name(cmd.vaultname)
        cmd.jobs={}
        jobs = cmd.vault.get_jobs()
        cmd.inventory_in_progress=False
        cmd.inventory_available=False
        for r in jobs:
            if r.action == 'InventoryRetrieval':
                if r.completed == 0:
                    cmd.inventory_in_progress=True
                else:
                    cmd.inventory_available=True
                    cmd.job = r
            else:
                aid = r.archiveid
                # overwrite preceding jobs for the same archive
                globals.Reporter.message("archive job state is "  + str(r.completed),"action")
                if r.completed == 1:
                    cmd.jobs[aid]="melted"
                else:
                    cmd.jobs[aid]='melting'

        cmd.archives=cmd.vault.get_archives()
        for r in cmd.archives:
            r.status='frozen'
            fname = util_file_exists(globals.Config.getValue('uploadfolder'),os.path.basename(r.local_file))
            if fname != None and os.path.isfile(fname):
                if r.name == '':
                    r.status='local'
                else:
                    r.status = "liquid"
            elif r.name == '':
                r.status = "invalid"
            elif r.name in cmd.jobs:
                r.status=cmd.jobs[r.name]

            r.files = archivefile.ArchiveFile.by_archive(r)
        globals.DB.close()
        globals.GUI.activate(cmd)
    elif caller == "gui":
        if cmd.vault.name in globals.GUI.vaultdialog:
            widget = globals.GUI.vaultdialog[cmd.vault.name]

            globals.Reporter.message("select-vault-content GUI thread for " + str(len(cmd.archives)) + " archives","action")
            # populate the treemodel with the archive values
            model=globals.GUI.create_archive_model()
            # count only the archives that actually uploaded succesfully
            countstoredarchives=0
            for v in cmd.archives:
                globals.Reporter.message("pushing archive '" + v.description + "' on model","action")
                model.append([v.id, globals.GUI.long_to_size(v.size), v.lastupload, v.description, v.status, len(v.files), float(v.size)/(1024*1024)])
                if v.name != '':
                    countstoredarchives+=1
            widget.archiveview.set_model(model)
            globals.Reporter.message("model is "+str(model),"action")

            # Adjust the inventory if required
            globals.Reporter.message("archives in list: " + str(len(cmd.archives)) + " and according to listing: " + str(cmd.vault.objects),"action")
            if countstoredarchives != cmd.vault.objects and not hasattr(cmd,'no_refresh'):
                if hasattr(cmd,'job') and cmd.inventory_available:
                    globals.Reporter.message("inventory available, downloading", "action")
                    act=action.Action(cmd_download_inventory)
                    act.vault=cmd.vault
                    act.job=cmd.job
                    globals.Controller.activate(act)
                elif not cmd.inventory_in_progress:
                    globals.Reporter.message("inventory not available and not in progress, requesting","action")
                    act=action.Action(cmd_request_inventory)
                    act.vault=cmd.vault
                    globals.Controller.activate(act)
            globals.Reporter.message("end of select-vault-content","action")

def cmd_create_vault(cmd, caller, data=None):
    if caller == "db":
        globals.DB.open()
        cmd.error=""
        name = globals.DB.sanitise(cmd.vaultname)
        if name != cmd.vaultname:
            cmd.error="Name contains invalid characters. Please correct the name and try again"
        if not cmd.error:
            v = vault.Vault()
            v.by_name(cmd.vaultname)
            if v.id != None:
                cmd.error="This vault name is already in use. Please change the name of the vault"
        if not cmd.error:
            cmd.vault = vault.Vault()
            cmd.vault.name=cmd.vaultname
            cmd.vault.created = globals.DB.timestamp()
            cmd.vault.objects=0
            cmd.vault.my_objects=0
            cmd.vault.size=0
            cmd.vault.save()
        cmd.status="precall"
        globals.DB.close()
        globals.GUI.activate(cmd)
    elif caller == "gui":
        if cmd.status == "precall":
            if cmd.error != "":
                globals.GUI.message_dialog(cmd.error)
            else:
                globals.Controller.activate(cmd)
        elif cmd.status == "postcall":
            if cmd.message != "":
                globals.UI.message_dialog(cmd.message)
    elif caller=="backend":
        cmd.status="postcall"
        if globals.AWS.create_vault(cmd.vault):
            cmd.message = "Vault created succesfully"
            act = action.Action(cmd_retrieve_vaults)
            globals.Controller.activate(act)
        else:
            cmd.vault.delete()
            cmd.message = "Error creating vault. Please try again"
        globals.GUI.activate(cmd)

def cmd_remove_vault(cmd, caller, data=None):
    if caller == "db":
        globals.DB.open()
        if cmd.status=="init":
            cmd.vault = vault.Vault()
            cmd.vault.by_name(cmd.vault_name)
            globals.DB.close()
            if cmd.vault.id != None:
                cmd.status="precall"
                if cmd.vault.my_objects>0:
                    globals.ActionFactory.show_message("Vault '" + str(cmd.vault.name)+"' seems to contain files","Please remove all archives first before attempting to remove a vault")
                else:
                    globals.Controller.activate(cmd)
        else:
            cmd.vault.delete()
            globals.DB.close()
            globals.GUI.activate(cmd)
            act = action.Action(cmd_display_vaults)
            globals.DB.activate(act)
    elif caller == "gui":
        globals.GUI.maindialog.statusbar_push("Removed vault '" + str(cmd.vault.name) + "' successfully")

    elif caller == "backend":
        try:
            resp=globals.AWS.remove_vault(cmd.vault)
            globals.Reporter.message("removing vault returned " + str(resp),"action")
            globals.DB.activate(cmd)
        except:
            globals.ActionFactory.show_message("Unable to remove vault '" + str(cmd.vault.name) + "'","Glacier backend refused removal, possibly due to archives present in the vault")
            globals.Reporter.error("caught exception on vault removal",True)


def cmd_load_and_display_vault(cmd, caller,data=None):
    if caller=="db":
        globals.DB.open()
        globals.Reporter.message('getting vault '+ str(cmd.vaultname),"action")
        cmd.vault=vault.Vault()
        cmd.vault.by_name(cmd.vaultname)
        globals.DB.close()
        if cmd.vault.id != None:
            globals.GUI.activate(cmd)
    elif caller=="gui":
        label = cmd.widget.vaultinfo
        txt="<b>Name</b>: " + cmd.widget.sanitise_label(str(cmd.vault.name)) + "\r\n"
        txt+="<b>ARN</b>: " + cmd.widget.sanitise_label(str(cmd.vault.arn)) + "\r\n"
        txt+="<b>Created</b>: " + cmd.widget.sanitise_label(str(cmd.vault.created)) + "\r\n"
        txt+="<b>Last Upload</b>: " + cmd.widget.sanitise_label(str(cmd.vault.lastupload)) + "\r\n"
        txt+="<b>Last Inventory</b>: " + cmd.widget.sanitise_label(str(cmd.vault.lastinventory)) + "\r\n"
        txt+="<b>Size</b>: " + cmd.widget.sanitise_label(globals.GUI.long_to_size(cmd.vault.size)) + "\r\n"
        txt+="<b>Objects</b>: " + cmd.widget.sanitise_label(str(cmd.vault.objects)) + "/" + cmd.widget.sanitise_label(str(cmd.vault.my_objects)) + "\r\n"
        label.set_markup(txt)

def cmd_display_vaults(cmd, caller, data=None):
    if caller == "db":
        globals.DB.open()
        # list all vaults as defined in our database
        cmd.vaults=vault.Vault.list_all()
        globals.DB.close()
        globals.GUI.activate(cmd)
    elif caller == "gui":
        # populate the treemodel with the vault values
        model=globals.GUI.create_vault_model()
        for v in cmd.vaults:
            model.append([v.name,v.arn,v.created,globals.GUI.long_to_size(v.size), v.objects, float(v.size)/(1024*1024)])
        globals.GUI.maindialog.vaultview.set_model(model)

def cmd_store_settings(cmd, caller,data=None):
    if caller == "db":
        globals.DB.open()
        globals.Reporter.message("saving settings to database")
        dt=globals.DB.timestamp()
        c = data.connection.cursor()
        inserts=[]
        dels=[]
        for k in cmd.values.keys():
            v = cmd.values[k]
            k=data.sanitise(k)
            dels.append([k])
            inserts.append((k,v,dt))
            globals.Config.setValue(k,v)
        c.executemany("DELETE FROM settings WHERE name=?",dels)
        c.executemany("INSERT INTO settings (name, value, mutated) VALUES (?,?,?)",inserts)
        data.connection.commit()
        globals.DB.close()

def cmd_initialise_db(cmd, caller,data=None):
    globals.Reporter.message("cmd_initialise_db called with caller " + str(caller),"action")
    if caller == "backend":
        # add ourselves to the db thread
        globals.Reporter.message("pushing database initialisation to the DB thread","action")
        globals.DB.activate(cmd)
    elif caller == "db":
        bkfile=globals.DB.backup_database()
        globals.DB.open()
        if bkfile != None and globals.DB.update_schema():
            os.unlink(bkfile)
        else:
            globals.DB.restore_backup(bkfile)
            globals.Controller.exitting=True
            globals.Reporter.error("Failed to apply database schema update, please check manually")

        # select the settings table and add all values to the Configuration
        values = data.query("SELECT name,value FROM settings")
        for v in values:
            key = v['name']
            value=v['value']
            if key != None:
                globals.Reporter.message("setting "+str(key) + "=" + str(value),"action")
                globals.Config.setValue(key,value)

        globals.DB.close()

        accountid = globals.Config.getValue("accountid")
        accesskey = globals.Config.getValue("accesskey")
        secretkey = globals.Config.getValue("secretkey")
        if not accountid or not accesskey or not secretkey:
            act = action.Action(cmd_open_settings_dialog)
            globals.GUI.activate(act)
        else:
            act = action.Action(cmd_display_vaults)
            globals.DB.activate(act)

            # AWS is uninitialised. To prevent errors from multithreaded initialisation, create a few clients now
            globals.AWS.create_glacier_client()
            globals.AWS.create_sqs_client()

            act = action.Action(cmd_retrieve_vaults)
            act.include_jobs=True
            globals.Controller.activate(act)

        globals.ActionFactory.sqs_long_poll()

        act = action.Action(cmd_db_maintenance)
        globals.DB.activate(act)

def cmd_db_maintenance(cmd, caller, data=None):
    if caller == "db":
        globals.Reporter.message("database maintenance, testing action to take","action")
        globals.DB.open()
        action = globals.DB.test_maintenance()
        if action:
            globals.GUI.maindialog.statusbar_push('Database maintenance: ' + action)
            globals.Reporter.message("taking " + action,"action")
        retval = globals.DB.run_maintenance()
        if action != None:
            globals.Reporter.message("action " + action + " done","action")
        globals.DB.close()
        if retval:
            globals.Reporter.message("new maintenance activity","action")
            globals.DB.activate(cmd)
        else:
            globals.GUI.maindialog.statusbar_push("Database updated")

def cmd_open_settings_dialog(cmd, caller, data=None):
    if caller == "gui":
        globals.GUI.open_settings_dialog()

#
#
# AWS Interfacing
#
#
def cmd_download_inventory(cmd,caller,data=None):
    if caller == "backend":
        globals.Reporter.message("downloading inventory based on job id " + str(cmd.job.jobid),"action")
        cmd.inventory = globals.AWS.download_inventory(cmd.vault,cmd.job)
        globals.DB.activate(cmd)
        globals.Reporter.message("inventory is "+str(cmd.inventory),"action")
        obj = json.loads(cmd.inventory)
        cmd.archives=[]
        if 'VaultARN' in obj and obj['VaultARN'] == cmd.vault.arn:
            cmd.vault.lastinventory = obj['InventoryDate']
            for a in obj['ArchiveList']:
                arch = archive.Archive()
                arch.import_aws(a)
                cmd.archives.append(arch)
            globals.DB.activate(cmd)
        else:
            globals.Reporter.error("Vault ARN unavailable or does not match stored ARN")
    elif caller == "db":
        globals.DB.open()
        # save a change in the inventory date
        cmd.vault.save()
        cmd.job.executed = globals.DB.timestamp()
        cmd.job.save()
        archives = cmd.vault.get_archives()
        sortlist = {}
        availablelist={}
        for a in archives:
            if a.name != '':
                globals.Reporter.message('DB archive: '+ a.name + "/" + a.description,"action")
                sortlist[a.name] = a
        for a in cmd.archives:
            availablelist[a.name]=True
            if a.name != '' and a.name in sortlist:
                globals.Reporter.message('archive from AWS found in DB',"action")
                sortlist[a.name].copy(a)
                sortlist[a.name].save()
            elif a.name !='':
                globals.Reporter.message('archive ' + a.name +'/' + a.description +  ' not found in DB',"action")
                a.vault_id=cmd.vault.id
                sortlist[a.name] = a
                a.save()
        invdate = globals.AWS.parse_time(cmd.vault.lastinventory)
        for a in archives:
            if a.name not in availablelist:
                uploaddate = globals.AWS.parse_time(a.created)
                if uploaddate < invdate:
                    a.lastupload = 'missing'
                    a.save()
                    globals.Reporter.message("archive " + a.name + " missing in Glacier","action")
        globals.DB.close()

        # refresh the vault content listing (if displayed)
        globals.ActionFactory.fill_vault_dialog(cmd.vault.name,True)

def cmd_download_archive(cmd,caller,data=None):
    if caller == "backend":
        globals.Reporter.message("downloading archive with local file '" + str(cmd.archive.local_file) + "'","action")
        cmd.filename = util_file_exists(globals.Config.getValue("uploadfolder"), os.path.basename(cmd.archive.local_file))
        globals.Reporter.message("testing filename " + str(cmd.filename),"action")
        if cmd.filename == None or os.path.getsize(cmd.filename) != cmd.archive.size:
            globals.Reporter.message("file does not exist or is not large enough, downloading","action")
            sz = globals.AWS.download_file(cmd.vault,cmd.job, cmd.filename, cmd.key)
            if sz!=None:
                globals.DB.activate(cmd)

    elif caller == "db":
        globals.DB.open()
        if cmd.state == "init":
            cmd.state="download"
            cmd.archive = archive.Archive()
            globals.Reporter.message("searching for archive based on job id " + str(cmd.job.id),"action")
            cmd.archive.by_name(cmd.job.archiveid)
            cmd.key=None
            if cmd.archive.id != None:
                globals.Reporter.message("archive found, local file is " + str(cmd.archive.local_file),"action")
                cmd.key = key.Key()
                cmd.key.load(cmd.archive.key_id)
                if cmd.key.id == None:
                    cmd.key=None
            globals.DB.close()

            if cmd.archive.id != None:
                globals.Controller.activate(cmd)
        else:
            cmd.job.executed = globals.DB.timestamp()
            cmd.job.save()
            globals.DB.close()

            # refresh the vault content listing (if displayed)
            globals.ActionFactory.fill_vault_dialog(cmd.vault.name,True)

            if cmd.archive.validated==0:
                act=action.Action(cmd_test_download)
                act.archive=cmd.archive
                act.filename=cmd.filename
                globals.Controller.activate(act)

def cmd_request_inventory(cmd,caller,data=None):
    if caller == "backend":
        cmd.jobid = globals.AWS.inventory(cmd.vault)
        globals.DB.activate(cmd)
    elif caller == "db":
        globals.DB.open()
        j = job.Job()
        j.by_jobid(cmd.jobid)
        if j.id == None:
            j.jobid=cmd.jobid
            j.creation_date=globals.DB.timestamp()
            j.action="InventoryRetrieval"
            j.vault_id = cmd.vault.id
            j.save()
        globals.DB.close()

        act = action.Action(cmd_retrieve_jobs)
        act.vault=cmd.vault
        globals.Controller.activate(act)

def cmd_request_inventory_conditionally(cmd,caller,data=None):
    if caller == "db":
        globals.DB.open()
        cmd.vault=vault.Vault()
        cmd.vault.by_name(cmd.vaultname)
        cmd.jobs = cmd.vault.get_inventory_jobs()
        cmd.inventory_in_progress=False
        cmd.inventory_available=False
        for r in cmd.jobs:
            globals.Reporter.message("job is "+str(r.completed),"action")
            if r.action == 'InventoryRetrieval':
                if r.completed == 0:
                    cmd.inventory_in_progress=True
                else:
                    cmd.inventory_available=True
                    cmd.job = r
        globals.DB.close()

        if not cmd.inventory_in_progress:
            act = action.Action(cmd_request_inventory)
            act.vault = cmd.vault
            globals.Controller.activate(act)
            globals.GUI.activate(cmd)
    elif caller=="GUI":
        globals.ActionFactory.vault_status(cmd.vault,"Inventory download requested")


def cmd_conditionally_retrieve_vaults(cmd, caller, data=None):
    if caller=="db":
        globals.DB.open()
        vaults=vault.Vault.list_all()
        globals.DB.close()
        if len(vaults) == 0:
            act = action.Action(cmd_retrieve_vaults)
            globals.Controller.activate(act)

def cmd_retrieve_vaults(cmd, caller, data=None):
    if caller=="backend":
        cmd.vaults = globals.AWS.list_vaults()
        globals.Reporter.message("vault listing: " + str(cmd.vaults),"action")
        globals.DB.activate(cmd)
    elif caller == "db":
        globals.Reporter.message("retrieve vaults, DB section","action")
        globals.DB.open()
        newlst=[]
        actlst=[]
        for v in cmd.vaults:
            v2=vault.Vault()
            v2.by_name(v.name)
            v2.copy(v)
            v2.save()
            newlst.append(v2)

            if hasattr(cmd, 'include_jobs') and cmd.include_jobs:
                act=action.Action(cmd_retrieve_jobs)
                act.vault=v2
                actlst.append(act)

        globals.DB.close()
        # push all retrieve-jobs-for-vault calls after we closed the DB
        for a in actlst:
            globals.Controller.activate(a)

        act = action.Action(cmd_display_vaults)
        act.vaults=newlst
        globals.DB.activate(act)

def cmd_retrieve_jobs(cmd, caller, data=None):
    if caller == "backend":
        cmd.jobs = globals.AWS.list_jobs(cmd.vault)
        globals.DB.activate(cmd)
    elif caller == "db":
        globals.DB.open()
        alljobs = job.Job.by_vault(cmd.vault)
        newjobs={}
        for v in cmd.jobs:
            j = job.Job()
            j.by_jobid(v.jobid)
            if j.id !=None:
                j.copy(v)
                j.save()
                newjobs[j.jobid]=True
            else:
                v.vault_id=cmd.vault.id
                v.save()

        # clean all jobs that expired
        for j in alljobs:
            if not j.jobid in newjobs:
                j.delete()

        globals.DB.close()

        if hasattr(cmd,'refresh'):
            globals.ActionFactory.fill_vault_dialog(cmd.vault.name)

def cmd_action_on_job(cmd, caller, data=None):
    if caller == "db":
        globals.DB.open()
        j = job.Job()
        j.by_jobid(cmd.job['JobId'])
        v = None
        if j.id == None:
            v = vault.Vault()
            v.by_arn(cmd.job["VaultARN"])
            if v.id != None:
                j.vault_id = v.id
                j.save()
        else:
            v = vault.Vault()
            v.load(j.vault_id)
        globals.DB.close()

        if j.id != None and not j.executed:
            if j.action == 'InventoryRetrieval':
                act = action.Action(cmd_download_inventory)
                act.vault=v
                act.job=j
                globals.Controller.activate(act)
            elif j.action == "ArchiveRetrieval":
                act = action.Action(cmd_download_archive)
                act.vault=v
                act.job=j
                act.state="init"
                globals.DB.activate(act)

def cmd_sqs_long_poll(cmd, caller, data=None):
    if caller == "backend":
        while not globals.Controller.exitting:
            queue = globals.Config.getValue("sqsqueue")
            msg = globals.AWS.poll_sqs_queue(queue)

            if msg != None:
                if 'Body' in msg:
                    body = json.loads(msg['Body'])
                    globals.Reporter.message("received SQS message: " + str(body),"action")

                    act = action.Action(cmd_action_on_job)
                    act.job=body
                    globals.DB.activate(act)

                if 'ReceiptHandle' in msg:
                    msgid=msg['ReceiptHandle']
                    globals.AWS.delete_msg(queue,msgid)

globals.ActionFactory=ActionFactory()
