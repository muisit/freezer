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

class CreateVaultDialog(guiobj.GUIObj):
    def __init__(self,builder):
        globals.GUI.createvaultdialog=self
        self.window = builder.get_object('dialog_create_vault')

        handlers ={
            "createvault_button": self.createvault_button_clicked
        }
        builder.connect_signals(handlers)

        self.set_entry(self.window, 'newvault_name','')
        self.window.set_transient_for(globals.GUI.maindialog.window)
        self.window.show_all()

    def createvault_button_clicked(self, widget):
        id = self.get_widget_id(widget)
        globals.Reporter.message("createvault button clicked " + id,"gui")
        if id == "button_createvault_ok":
            globals.Reporter.message("creating vault","gui")
            name = self.get_entry(self.window,"newvault_name")
            globals.ActionFactory.create_vault(name)
        else:
            globals.Reporter.message("closing dialog","gui")
        self.window.destroy()
        globals.GUI.createvaultdialog=None        