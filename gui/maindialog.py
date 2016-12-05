import globals
import guiobj
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject

class MainDialog(guiobj.GUIObj):
    def __init__(self, builder):
        globals.GUI.maindialog=self
        self.vaultview = builder.get_object('vaultlistview')
        self.vaultinfo = builder.get_object('vaultinfo')
        self.window = builder.get_object('mainwindow')
        self.statusbar = builder.get_object('statusbar1')

        handlers = {
            "gtk_main_quit": Gtk.main_quit,
            "delete-event": Gtk.main_quit,
            "gtk_quit_activate": Gtk.main_quit,
            "open_settings_dialog": self.open_settings_dialog,
            "vaultview_select":self.vaultview_select,
            "vaultview_select2":self.vaultview_select2,
            "view_jobs": self.view_jobs,
            "view_files": self.view_files,
            "remove_vault": self.remove_vault,
            "open_vault": self.vaultview_select2,
            "vault_new": self.create_new_vault
        }

        builder.connect_signals(handlers)
        self.window.show_all()

    def statusbar_push(self, txt):
        cid = self.statusbar.get_context_id('main')
        self.statusbar.push(cid,txt)

    def remove_vault(self,widget):
        sel = self.vaultview.get_selection()
        if sel.count_selected_rows() > 0:
            (model,iter) = sel.get_selected()
            name = str(model[iter][0])
            globals.ActionFactory.remove_vault(name)

    def create_new_vault(self, widget):
        globals.GUI.createvault_dialog()

    def view_jobs(self, widget):
        globals.GUI.job_dialog()

    def view_files(self, widget):
        globals.GUI.file_dialog()

    def vaultview_select(self,widget):
        globals.Reporter.message("selecting vaultview " + str(widget),"gui")
        sel = widget.get_selection()
        if sel.count_selected_rows() > 0:
            (model,iter) = sel.get_selected()
            name = str(model[iter][0])
            globals.Reporter.message("selected vault is '" + name + "'","gui")
            globals.ActionFactory.display_vault(self, name)

    def vaultview_select2(self,widget, index=0, column=None):
        globals.Reporter.message("selecting vaultview2 " + str(widget) + "/" + str(index) + "/" + str(column),"gui")
        sel = self.vaultview.get_selection()
        if sel.count_selected_rows() > 0:
            (model,iter) = sel.get_selected()
            name = str(model[iter][0])
        globals.GUI.vault_dialog(name)

    def open_settings_dialog(self, widget=None):
        globals.GUI.settings_dialog()


        