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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject

import os, datetime, re, json

import globals
import guiobj

class ArchiveDialog(guiobj.GUIObj):
    def __init__(self, builder, name, aid):
        globals.Reporter.message("creating archive dialog","gui")
        globals.GUI.archivedialog=self
        self.window = builder.get_object('filedialog')
        self.fileview = builder.get_object('fileview')
        self.statusbar = builder.get_object("statusbar_file")
        self.archive_status = builder.get_object('archive_status')
        self.vault_name = name
        self.aid=aid
        self.files={}
        self.toolbutton = builder.get_object('toolbutton_archive')
        self.outputtype = builder.get_object('output_selection')

        handlers = {
            "fileview_add": self.fileview_add,
            "fileview_create": self.fileview_create,
            "fileview_select": self.fileview_select,
            "fileview_add_folder": self.fileview_add_folder,
            "output_filter_apply": self.fileview_apply_filter,
            "filterfrozen_click": self.fileview_apply_frozen,
            "filterbackup_click": self.fileview_apply_bak,
            "filterexclude_clicked": self.fileview_apply_exclude,
            "toolbar_remove": self.fileview_remove_unselected,
            "filter_excludefiles": self.fileview_apply_excludefiles
        }
        globals.Reporter.message("connecting handlers","gui")
        builder.connect_signals(handlers)
        if name in globals.GUI.vaultdialog:
            self.window.set_transient_for(globals.GUI.vaultdialog[name].window)
        else:
            self.window.set_transient_for(globals.GUI.maindialog.window)

        globals.Reporter.message("updating label status","gui")
        # setting the model causes a apply_filter call, which requires the filecount member to be present
        self.update_status(0,0,0)
        globals.Reporter.message("setting basic model","gui")
        self.fileview.set_model(globals.GUI.create_file_model())
        self.toolbutton.set_active(True)
        globals.Reporter.message("showing all","gui")
        self.window.show_all()

        if self.aid != None:
            globals.ActionFactory.fill_archive_list(self, self.aid)
            self.disable_entry(self.window,'output_name')
            self.disable_entry(self.window, 'output_filter')

    def statusbar_push(self, txt):
        cid = self.statusbar.get_context_id('archive')
        self.statusbar.push(cid,txt)

    def update_status(self, filecount, sizecount, selfilecount):
        self.filecount=filecount
        self.sizecount=sizecount
        self.selfilecount=selfilecount

        txt = "List contains %d files, selected %d files with %s size" % (filecount, selfilecount, globals.GUI.long_to_size(sizecount))
        self.archive_status.set_text(txt)

    def fileview_select(self, widget, index, column):
        if self.aid!=None:
            return

        globals.Reporter.message("selecting fileview " + str(widget) ,"gui")
        sel = widget.get_selection()
        if sel.count_selected_rows() > 0:
            (model,iter) = sel.get_selected()
            state = int(model[iter][6])
            path=model.get_value(iter,0)
            name=model.get_value(iter,1)
            val = os.path.join(path,name)
            if state == 0:
                model[iter][6]=1
                model[iter][7]=0
                self.selfilecount+=1
                self.sizecount+=self.files[val]
            else:
                model[iter][6]=0
                model[iter][7]=1
                self.selfilecount-=1
                self.sizecount-=self.files[val]

            self.update_status(self.filecount, self.sizecount, self.selfilecount)

    def fileview_add(self,widget):
        if self.aid!= None:
            return

        dialog = Gtk.FileChooserDialog("Please select a file or files", self.window.get_transient_for(),
            Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK))
        dialog.set_show_hidden(True)
        dialog.set_select_multiple(True)
        pwd=globals.Config.getValue('pwd')
        if pwd != None:
            dialog.set_current_folder(pwd)
        response=dialog.run()
        if response == Gtk.ResponseType.OK:
            fnames = dialog.get_filenames()
            if len(fnames)>0:
                globals.ActionFactory.add_files_to_archiveview(self,fnames)
                globals.Config.setValue('pwd',os.path.dirname(fnames[0]))
        dialog.destroy()

    def insert_file_path(self, d,b,s,m,a,u,i):
        # insert the values and depend on the tree-sorting capabilities
        foldernames = d.split('/')
        while len(foldernames)>0 and foldernames[0] == '':
            foldernames=foldernames[1:]
        model = self.fileview.get_model()
        iter = self.find_iter_for_path(foldernames, model, model.get_iter_first())
        if iter==None:
            globals.Reporter.message("appending file at end of list","gui")
            model.append([d,b,s,m,a,u,i])
        else:
            globals.Reporter.message("inserting file in list","gui")
            model.insert_after(iter,[d,b,s,m,a,u,i])

    def fileview_add_folder(self,widget):
        dialog = Gtk.FileChooserDialog("Please select a folder or folders", self.window.get_transient_for(),
            Gtk.FileChooserAction.SELECT_FOLDER, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK))
        dialog.set_show_hidden(True)
        dialog.set_select_multiple(True)
        pwd=globals.Config.getValue('pwd')
        if pwd != None:
            dialog.set_current_folder(pwd)
        response=dialog.run()
        if response == Gtk.ResponseType.OK:
            fnames = dialog.get_filenames()
            if len(fnames)>0:
                globals.ActionFactory.add_files_to_archiveview(self,fnames)
                globals.Config.setValue('pwd',os.path.dirname(fnames[0]))
        dialog.destroy()

    def fileview_create(self,widget):
        if self.aid!= None:
            return

        name = self.get_entry(self.window, 'output_name')
        if not name:
            name="archive"
        ext=".tar.bz2"
        if self.outputtype.get_has_entry():
            ext = self.outputtype.get_child().get_buffer().get_text()
        else:
            iter = self.outputtype.get_active_iter()
            if iter != None:
                model= self.outputtype.get_model()
                ext = model.get_value(iter, self.outputtype.get_id_column())

        path = globals.Config.getValue("uploadfolder")
        fname = os.path.join(path,name+ext)
        idx=0
        while os.path.exists(fname):
             idx+=1
             fname = os.path.join(path, name + str(idx) + ext)

        globals.Reporter.message("archive name is "+str(fname),"gui")
        filelist = []
        excludelist=[]
        model = self.fileview.get_model()
        iter = model.get_iter_first()
        while iter != None:
            if model.get_value(iter,6) == 1:
                fname2 = os.path.join(model.get_value(iter,0), model.get_value(iter,1))
                globals.Reporter.message("appending " + fname2 + "/"+ str(type(fname2)) + " to list of archived files","gui")
                filelist.append(fname2)
            elif model.get_value(iter,7) == 1:
                fname2 = os.path.join(model.get_value(iter,0), model.get_value(iter,1))
                globals.Reporter.message("appending " + fname2 + "/"+ str(type(fname2)) + " to list of excluded files","gui")
                excludelist.append(fname2)
            iter=model.iter_next(iter)

        if len(filelist) > 0 or len(excludelist)>0:
            globals.ActionFactory.create_archive(self.vault_name, fname, ext, filelist,excludelist)
            self.window.destroy()
        else:
            globals.GUI.message_dialog("No archive created","No files were selected, so no archive was created. Please select some files first")

    def fileview_apply_filter(self,widget):
        if self.aid!= None:
            return
        content = self.get_entry(self.window,'output_filter')
        self.apply_regex_filter(content,0)

    def apply_regex_filter(self,content, valtoset):
        model = self.fileview.get_model()
        iter = model.get_iter_first()
        expr = re.compile(content)
        while iter != None:
            name = model.get_value(iter,1)
            path = model.get_value(iter,0)
            selected = model.get_value(iter,6)
            val = os.path.join(path,name)
            globals.Reporter.message("value is "+str(val)+", applying filter " + str(content) + " and value "+ str(valtoset) +"/" + str(selected),"gui")
            if expr.search(val) != None:
                if valtoset > 0 and selected == 0:
                    self.selfilecount+=1
                    self.sizecount += self.files[val]
                elif valtoset == 0 and selected>0:
                    self.selfilecount-=1
                    self.sizecount-=self.files[val]
                model.set_value(iter,6,valtoset)
            iter = model.iter_next(iter)
        self.update_status(self.filecount, self.sizecount, self.selfilecount)

    def fileview_apply_frozen(self,widget):
        if self.aid!= None:
            return
        isactive = widget.get_active()
        valtoset = 0
        if not isactive:
            valtoset=1

        model = self.fileview.get_model()
        iter = model.get_iter_first()
        while iter != None:
            val = model.get_value(iter,4)
            selected = model.get_value(iter,6)
            if val != "":
                if valtoset > 0 and selected == 0:
                    self.selfilecount+=1
                    self.sizecount += self.files[val]
                elif valtoset == 0 and selected>1:
                    self.selfilecount-=1
                    self.sizecount-=self.files[val]

                model.set_value(iter, 6, valtoset)
            iter = model.iter_next(iter)
        self.update_status(self.filecount, self.sizecount, self.selfilecount)

    def fileview_apply_exclude(self,widget):
        isactive = widget.get_active()
        valtoset = 0
        if not isactive:
            valtoset=1

        excludepaths=globals.Config.getValue("exclude_paths")
        if excludepaths:
            excludepaths = json.loads(excludepaths)
            if excludepaths:
                for p in excludepaths:
                    self.apply_regex_filter(p, valtoset)

    def fileview_apply_excludefiles(self,widget):
        isactive = widget.get_active()
        valtoset = 0
        if not isactive:
            valtoset=1

        model = self.fileview.get_model()
        iter = model.get_iter_first()
        while iter != None:
            val = model.get_value(iter,7)
            selected = model.get_value(iter,6)
            if val != 0:
                if valtoset > 0 and selected == 0:
                    self.selfilecount+=1
                    self.sizecount += self.files[val]
                elif valtoset == 0 and selected>1:
                    self.selfilecount-=1
                    self.sizecount-=self.files[val]

                model.set_value(iter, 6, valtoset)
            iter = model.iter_next(iter)
        self.update_status(self.filecount, self.sizecount, self.selfilecount)

    def fileview_apply_bak(self, widget):
        if self.aid!= None:
            return

        isactive = widget.get_active()
        valtoset = 0
        if not isactive:
            valtoset=1
        self.apply_backup_filter(valtoset)

    def apply_backup_filter(self, valtoset):
        self.apply_regex_filter("~$", valtoset)
        self.apply_regex_filter("\.o$", valtoset)
        self.apply_regex_filter("\.pyc$",valtoset)
        self.apply_regex_filter("\.bak$",valtoset)
        self.apply_regex_filter("\.Po?$",valtoset)
        self.apply_regex_filter("^#.*#$",valtoset)
        self.apply_regex_filter("^~",valtoset)

    def fileview_remove_unselected(self,widget):
        if self.aid!= None:
            return
        model = self.fileview.get_model()
        iter = model.get_iter_first()
        while iter != None:
            val = model.get_value(iter,6)
            if val == 0:
                self.filecount-=1
                if not model.remove(iter):
                    iter=None
            else:
                iter = model.iter_next(iter)
        self.update_status(self.filecount, self.sizecount, self.selfilecount)
        