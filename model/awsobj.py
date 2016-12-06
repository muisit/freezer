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