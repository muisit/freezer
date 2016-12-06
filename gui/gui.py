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
import config
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject
import threading
import os, os.path
import datetime

import maindialog, settingsdialog, createvaultdialog, vaultdialog, archivedialog, jobdialog, filedialog

class GUI(threading.Thread):
    def mainLoop(self, basedir):
        self.basedir=basedir
        self.run()

    def activate(self, act):
        GLib.idle_add(self.applyAction, act)

    def applyAction(self, act):
        if act != None:
            act.run("gui",None)

    def run(self):
        self.vaultdialog={}
        self.main_dialog()
        Gtk.main()

    def create_vault_model(self):
        # name, arn, created, size,num objects, size-in-mbs
        return Gtk.ListStore(str,str,str,str,int,float)

    def create_archive_model(self):
        # id, size, created, descr, status, filecount, size-in-mb
        return Gtk.ListStore(int,str,str,str,str,int,float)

    def create_file_model(self):
        # path, name, size, changed, archive list, last upload, selected, excluded, size-in-mb, fullpath
        return Gtk.ListStore(str,str,str,str,str,str,int,int,float, str)

    def create_file2_model(self):
        # id, path, name, size, changed, archive list, size-in-mb, fullpath
        return Gtk.ListStore(int, str,str,str,str,str, float, str)

    def create_key_model(self):
        # id, algo, size, blocksize, keystring
        return Gtk.ListStore(int, str,int,int,str)

    def create_job_model(self):
        # jobid, vault, archive, action, status, size, requested, completed, executed
        return Gtk.ListStore(str,str,str,str,str,str,str,str,str)

    def get_object(self,name):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(str(gladefile))

    def main_dialog(self):
        builder = Gtk.Builder.new_from_file(os.path.join(self.basedir,'resources/freezer.ui'))
        maindialog.MainDialog(builder)

    def createvault_dialog(self):
        builder = Gtk.Builder.new_from_file(os.path.join(self.basedir,'resources/createvaultdialog.ui'))
        createvaultdialog.CreateVaultDialog(builder)

    def settings_dialog(self):
        builder = Gtk.Builder.new_from_file(os.path.join(self.basedir,'resources/settingsdialog.ui'))
        settingsdialog.SettingsDialog(builder)

    def vault_dialog(self, name):
        builder = Gtk.Builder.new_from_file(os.path.join(self.basedir,'resources/vaultdialog.ui'))
        vaultdialog.VaultDialog(builder,name)

    def message_dialog(self, txt, txt2=""):
        dialog = Gtk.MessageDialog(self.maindialog.window, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, txt)
        if txt2 != "":
            dialog.format_secondary_text(txt2)
        dialog.run()
        dialog.destroy()

    def archive_dialog(self,name, aid=None):
        builder = Gtk.Builder.new_from_file(os.path.join(self.basedir,'resources/archivedialog.ui'))
        return archivedialog.ArchiveDialog(builder,name,aid)

    def job_dialog(self):
        builder = Gtk.Builder.new_from_file(os.path.join(self.basedir,'resources/jobdialog.ui'))
        return jobdialog.JobDialog(builder)

    def file_dialog(self):
        builder = Gtk.Builder.new_from_file(os.path.join(self.basedir,'resources/filedialog.ui'))
        return filedialog.FileDialog(builder)

    def long_to_size(self, longsize):
        if longsize < 1024:
            return str(longsize)
        elif longsize < 1024*1024:
            return "%.1fkb" % (float(longsize) / 1024)
        elif longsize < 1024*1024*1024:
            return "%.1fMb" % (float(longsize) / (1024*1024))
        elif longsize < 1024*1024*1024*1024:
            return "%.1fGb" % (float(longsize) / (1024*1024*1024))

globals.GUI = GUI()
