import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject


class GUIObj:
    def get_widget_id(self,widget):
        return str(Gtk.Buildable.get_name(widget))

    def get_parent(self, obj, widgetname):
        if self.get_widget_id(obj) == widgetname:
            return obj
        parent = obj.get_parent()
        if parent != None:
            return self.get_parent(parent,widgetname)
        return None

    def get_child(self, obj, widgetname):
        if self.get_widget_id(obj) == widgetname:
            return obj
        if isinstance(obj,Gtk.Container):
            for v in obj.get_children():
                retval = self.get_child(v,widgetname)
                if retval != None:
                    return retval
        return None

    def get_entry(self, parent, widgetname):
        child = self.get_child(parent,widgetname)
        if child != None:
            return child.get_buffer().get_text()
        return None

    def get_buffer(self,buffer):
        return buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter(),True)

    def set_entry(self, parent, widgetname, value):
        child = self.get_child(parent, widgetname)
        if child != None:
            child.get_buffer().delete_text(0,-1)
            if value != None:
                child.get_buffer().insert_text(0,str(value),-1)

    def sanitise_label(self, txt):
        return txt.replace("<","&lt;").replace(">","&gt;")

    def disable_entry(self, widget, name):
        child = self.get_child(widget,name)
        if child != None:
            child.set_property('editable',False)
            child.set_can_focus(False)
            