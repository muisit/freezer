import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject

import os, datetime, re

import globals
import guiobj

class FileDialog(guiobj.GUIObj):
    def __init__(self, builder):
        globals.GUI.filedialog=self
        self.window = builder.get_object('filedialog')
        self.fileview = builder.get_object('fileview')

        handlers = {
            "close_clicked": self.close_clicked,
            "filter_clicked": self.filter_clicked
        }
        builder.connect_signals(handlers)
        self.window.set_transient_for(globals.GUI.maindialog.window)

        self.fileview.set_model(globals.GUI.create_file2_model())
        self.window.show_all()
        globals.ActionFactory.fill_file_list(self)

    def filter_clicked(self, widget):
        value = self.get_entry(self.window, 'filter_value')
        expr = re.compile(value)
        lst=[]
        for f in self.original_files:
            if expr.search(f.fullpath) != None:
                lst.append(f)
        self.fill_file_model(lst)

    def close_clicked(self, widget):
        self.window.destroy()
        globals.GUI.filedialog=None

    def fill_file_model(self, lst):
        model = globals.GUI.create_file2_model()
        for f in lst:
            model.append([f.id, f.path, f.name, globals.GUI.long_to_size(f.size), f.date, f.in_archives, float(f.size) / (1024*1024), os.path.join(f.path,f.name)])
        self.fileview.set_model(model)
        