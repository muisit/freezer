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
import guiobj
import gnupg
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject
import os
import logging
import debug
import Crypto
import Crypto.Random
import json
import binascii

class SettingsDialog(guiobj.GUIObj):
    def __init__(self, builder):
        gpglogger = logging.getLogger('gnupg')
        gpglogger.setLevel(logging.DEBUG)
        gpglogger.addHandler(debug.LogHandler(logging.DEBUG))

        globals.GUI.settingsdialog=self
        self.window = builder.get_object('configdialog')
        self.keyview = builder.get_object('keyview')
        self.algo_box = builder.get_object('algo_box')
        self.import_box=builder.get_object('keyview_box')
        self.path_view = builder.get_object("path_view")

        handlers = {
            "settings_button_clicked": self.setting_button_clicked,
            "create_key": self.create_key,
            "import_clicked": self.import_key,
            "select_key_row": self.select_key_row,
            "open_upload_folder": self.open_upload_folder,
            "path_add": self.path_add,
            "path_remove": self.path_remove
        }
        builder.connect_signals(handlers)

        accountid = globals.Config.getValue("accountid")
        accesskey = globals.Config.getValue("accesskey")
        secretkey = globals.Config.getValue("secretkey")
        reg = globals.Config.getValue("awsregion")
        snstopic = globals.Config.getValue("snstopic")
        sqsqueue = globals.Config.getValue("sqsqueue")
        upfolder = globals.Config.getValue("uploadfolder")
        paths=globals.Config.getValue("exclude_paths")
        if not paths:
            paths=[]
        else:
            paths = json.loads(paths)
        self.set_paths(paths)

        self.set_entry(self.window, 'settings_accountid',accountid)
        self.set_entry(self.window, 'settings_accesskey',accesskey)
        self.set_entry(self.window, 'settings_secretkey',secretkey)
        self.set_entry(self.window, 'settings_region',reg)
        self.set_entry(self.window, 'snstopic',snstopic)
        self.set_entry(self.window, "sqsqueue",sqsqueue)
        if upfolder != None:
            self.set_entry(self.window, 'uploadfolder',upfolder)

        globals.ActionFactory.list_keys(self)
        self.fill_keyselection_boxes()

        self.window.set_transient_for(globals.GUI.maindialog.window)
        self.window.show_all()

    def set_paths(self,paths):
        model = Gtk.ListStore(str)
        for p in paths:
            model.append([p])
        self.path_view.set_model(model)

    def path_add(self, widget):
        val = str(self.get_entry(self.window, 'path_entry'))
        globals.Reporter.message("new value to add is '" + val + "'","gui")
        if val:
            model = self.path_view.get_model()
            model.append([val])
            self.set_entry(self.window, 'path_entry','')

    def path_remove(self, widget, index,column):
        sel = widget.get_selection()
        if sel.count_selected_rows() > 0:
            (model,iter) = sel.get_selected()
            model.remove(iter)

    def open_upload_folder(self,widget):
        dialog = Gtk.FileChooserDialog("Please select a folder or folders", self.window.get_transient_for(),
            Gtk.FileChooserAction.SELECT_FOLDER, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK))
        dialog.set_show_hidden(True)
        dialog.set_select_multiple(False)
        pwd=globals.Config.getValue('pwd')
        if pwd != None:
            dialog.set_current_folder(pwd)
        response=dialog.run()
        if response == Gtk.ResponseType.OK:
            fnames = dialog.get_filenames()
            if len(fnames)>0:
                self.set_entry(self.window, 'uploadfolder',fnames[0])
                globals.Config.setValue('pwd',os.path.dirname(fnames[0]))
        dialog.destroy()

    def select_key_row(self,widget, index, column):
        sel = self.keyview.get_selection()
        model = self.keyview.get_model()
        iter=model.get_iter_first()
        while iter !=None:
            if sel.iter_is_selected(iter):
                dct={}
                dct['algorithm'] = model.get_value(iter,1)
                dct['keysize'] = model.get_value(iter,2)
                dct['blocksize'] = model.get_value(iter,3)
                dct['keystring'] = model.get_value(iter,4)
                self.import_box.get_buffer().set_text(json.dumps(dct,indent=4))
            iter=model.iter_next(iter)

    def import_key(self,widget):
        buf = self.import_box.get_buffer()
        txt = self.get_buffer(buf)
        keyvals = json.loads(txt)
        if keyvals != None:
            globals.ActionFactory.create_key(keyvals,self)
            buf.set_text('')

    def setting_button_clicked(self,obj):
        id = self.get_widget_id(obj)
        globals.Reporter.message("settings button clicked " + id,"gui")
        if id == "settings_button_ok":
            globals.Reporter.message("saving settings","gui")
            accountid = self.get_entry(self.window,"settings_accountid")
            accesskey = self.get_entry(self.window,"settings_accesskey")
            secretkey = self.get_entry(self.window,"settings_secretkey")
            upfolder = self.get_entry(self.window, "uploadfolder")
            reg = self.get_entry(self.window,"settings_region")
            snstopic = self.get_entry(self.window,"snstopic")
            sqsqueue = self.get_entry(self.window, "sqsqueue")

            pathlist=[]
            model=self.path_view.get_model()
            iter=model.get_iter_first()
            while iter:
                val = model.get_value(iter,0)
                iter=model.iter_next(iter)
                pathlist.append(val)


            selkey=-1
            sel = self.keyview.get_selection()
            model = self.keyview.get_model()
            iter=model.get_iter_first()
            while iter !=None:
                if sel.iter_is_selected(iter):
                    selkey = model.get_value(iter,0)
                iter=model.iter_next(iter)

            vals = {
                "accountid" : accountid,
                "accesskey": accesskey,
                "secretkey": secretkey,
                "awsregion": reg,
                "snstopic": snstopic,
                "sqsqueue": sqsqueue,
                "encryptionkey": selkey,
                "uploadfolder": upfolder,
                "exclude_paths": json.dumps(pathlist)
            }
            globals.ActionFactory.store_settings(vals)

        globals.Reporter.message("closing dialog","gui")
        self.window.destroy()

        # if we have no vaults present, load the vault list now
        globals.ActionFactory.conditionally_load_vaults()
        globals.GUI.settingsdialog=None

    def create_key(self,widget):
        model = self.algo_box.get_model()
        iter =self.algo_box.get_active_iter()
        if iter != None:
            algosize = model.get_value(iter,0)
            algo = model.get_value(iter,1)
            keysize = model.get_value(iter,2)
            blocksize = model.get_value(iter,3)

            key = Crypto.Random.get_random_bytes(keysize)

            dct = {
                'selection': algosize,
                "algorithm": algo,
                "keysize": int(keysize*8),
                "blocksize": int(blocksize),
                "keystring": binascii.hexlify(key)
            }

            globals.ActionFactory.create_key(dct,self)

    def fill_keyselection_boxes(self):
        model =Gtk.ListStore(str,str, int,int)
        model.append(["AES-128", "AES",16,16])
        model.append(["AES-196", "AES", 24,16])
        model.append(["AES-256", "AES",32,16])
        model.append(["Blowfish-128","Blowfish",16,8])
        model.append(["Blowfish-196","Blowfish",24,8])
        model.append(["Blowfish-256","Blowfish",32,8])
        model.append(["CAST-40","CAST",5,8])
        model.append(["CAST-80","CAST",10,8])
        model.append(["CAST-128","CAST",16,8])
        model.append(["DES-64","DES",8,8])
        model.append(["DES3-128","DES3",16,8])
        #model.append(["IDEA-128","IDEA",16,8])
        #model.append(["RC5-128","RC5",16,8])
        #model.append(["RC5-256","RC5",32,8])
        #model.append(["RC5-512","RC5",64,8])
        self.algo_box.set_model(model)
        self.algo_box.set_active_iter(model.get_iter_first())

