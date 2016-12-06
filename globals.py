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
#
# Although frowned upon, we need some globals that we can use to
# communicate with between threads
#

# The global configuration object, holding settings and variables
Config=None

# The global controller object, allowing communication between View and Model
Controller=None

# the global reporter object, allowing messaging, tracing and reporting
Reporter=None

# the global database object, allowing threaded database access
DB=None

# the global ActionFactory object, storing all available actions
ActionFactory=None

AWS=None
Firebase=None