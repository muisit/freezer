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