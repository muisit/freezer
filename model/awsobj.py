
class Object:
    def import_setting(self,name,vals, defval):
        if name in vals:
            return vals[name]
        return defval

    def to_int(self,val):
        if isinstance(val,long) or isinstance(val,int):
            return long(val)
        else:
            v = self.to_str(val)
            if v=="":
                return 0
            return long(v)

    def to_str(self,val):
        if val == None:
            return ""
        elif not val:
            return ""
        elif isinstance(val,basestring):
            return unicode(val)
        else:
            return str(val)