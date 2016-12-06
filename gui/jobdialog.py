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


        