import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject

import os, datetime, re

import globals
import guiobj

class JobDialog(guiobj.GUIObj):
    def __init__(self, builder):
        globals.GUI.jobdialog=self
        self.window = builder.get_object('jobdialog')
        self.jobview = builder.get_object('jobview')

        handlers = {
            "closebutton_clicked": self.close_clicked
        }
        builder.connect_signals(handlers)
        self.window.set_transient_for(globals.GUI.maindialog.window)

        self.jobview.set_model(globals.GUI.create_job_model())
        self.window.show_all()
        globals.ActionFactory.fill_job_list(self)

    def close_clicked(self, widget):
        self.window.destroy()
        globals.GUI.jobdialog=None


        