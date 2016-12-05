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