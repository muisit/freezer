import globals
import guiobj

class VaultDialog(guiobj.GUIObj):
    def __init__(self, builder, name):
        globals.GUI.vaultdialog[name]=self

        self.window = builder.get_object('vaultoverview')
        self.archiveview = builder.get_object('archiveview')
        self.statusbar = builder.get_object('statusbar_vault')
        self.dialog = builder.get_object('removearchive_dialog')
        self.dialog_label = builder.get_object('archivename_label')

        handlers = {
            "menu_newarchive": self.toolbar_uploadarchive,
            "toolbar_removearchive":self.toolbar_removearchive,
            "toolbar_savearchive": self.toolbar_savearchive,
            "toolbar_refreshvault":self.toolbar_refreshvault,
            "toolbar_closevaultdialog": self.toolbar_closevaultdialog,
            "removearchive_click": self.removearchive_click,
            "remove_local_file": self.remove_local_file,
            "row_activated": self.row_activated
        }
        builder.connect_signals(handlers)

        self.archiveview.set_model(globals.GUI.create_archive_model())
        self.statusbar.remove_all(self.statusbar.get_context_id('vault'))
        self.vault_name=name
        self.window.set_transient_for(globals.GUI.maindialog.window)
        self.window.show_all()

        globals.ActionFactory.fill_vault_dialog(name)

    def statusbar_push(self, txt):
        cid = self.statusbar.get_context_id('vault')
        self.statusbar.push(cid,txt)

    def row_activated(self, widget, index, column):
        sel = self.archiveview.get_selection()
        if sel.count_selected_rows() > 0:
            (model,iter) = sel.get_selected()
            aid = str(model.get_value(iter,0))
            globals.GUI.archive_dialog(self.vault_name, aid)

    def toolbar_uploadarchive(self,widget):
        globals.GUI.archive_dialog(self.vault_name)

    def removearchive_click(self,widget):
        id = self.get_widget_id(widget)
        self.dialog.hide()

        if id == "button_ok":
            val = self.get_entry(self.dialog, 'entry_iamsure')
            if val != None and val == "I am sure":
                self.removearchive(self.aid)

    def remove_local_file(self,widget):
        sel = self.archiveview.get_selection()
        if sel.count_selected_rows() > 0:
            (model,iter) = sel.get_selected()
            id = str(model.get_value(iter,0))
            descr = str(model.get_value(iter,3))
            state = str(model.get_value(iter,4))

            if state == "liquid":
                globals.ActionFactory.remove_archive_file(id)

    def toolbar_removearchive(self,widget):
        sel = self.archiveview.get_selection()
        if sel.count_selected_rows() > 0:
            (model,iter) = sel.get_selected()
            id = str(model.get_value(iter,0))
            descr = str(model.get_value(iter,3))
            state = str(model.get_value(iter,4))

            if state != "invalid":
                self.aid=id
                self.set_entry(self.dialog, 'entry_iamsure','')
                self.dialog_label.set_markup('<b>' + str(descr) + "</b>")
                self.dialog.show_all()
            else:
                self.removearchive(id)

    def removearchive(self,id):
        globals.ActionFactory.remove_archive(id)

    def toolbar_savearchive(self,widget):
        sel = self.archiveview.get_selection()
        if sel.count_selected_rows() > 0:
            (model,iter) = sel.get_selected()
            id = str(model.get_value(iter,0))
            globals.ActionFactory.save_archive(self.vault_name, id)

    def toolbar_refreshvault(self,widget):
        globals.ActionFactory.refresh_vault(self,self.vault_name)

    def toolbar_closevaultdialog(self,widget):
        self.window.destroy()
        del globals.GUI.vaultdialog[self.vault_name]
