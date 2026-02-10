"""
A script to show you various builtins and internals.
"""

# An anonymous object of class 'object'
# It is hashable and equal only to itelf.
obj = object()

# The dir() builtin (should) show all defined attributes:
print(f"{dir(object) = }")
# dir(object) = [
#   "__class__",        # the class object for this object
#   "__delattr__",      # implements attribute deletion logic
#   "__dir__",          # implements the dir() builtin function
#   "__doc__",          # docstring of the object (triple-quoted)
#   "__eq__",           # implements the == operator
#   "__format__",       # implements string formatting
#   "__ge__",           # implements the >= operator (raises error by default)
#   "__getattribute__", # implements attribute getting logic
#   "__getstate__",     # used by pickle (serialisation protocol)
#   "__gt__",           # implements the > operator (raises error by default)
#   "__hash__",         # implements the hash() builtin function
#   "__init__",         # default initialiser, does nothing
#   "__init_subclass__",# (a class method, we'll see later on)
#   "__le__",           # implements the <= operator (raises error by default)
#   "__lt__",           # implements the < operator (raises error by default)
#   "__ne__",           # implements the != operator (x != y same as not x == y)
#   "__new__",          # (a static method, we'll see later on)
#   "__reduce__",       # used by pickle (serialisation protocol)
#   "__reduce_ex__",    # used by pickle (serialisation protocol)
#   "__repr__",         # implements the repr() builtin function (debug print)
#   "__setattr__",      # implements attribute setting logic
#   "__sizeof__",       # a guess of how many bytes the object uses on heap
#   "__str__",          # implements the str() builtin function (pretty print)
#   "__subclasshook__"  # (a class method, we'll see later on)
# ]

# Defaults for some operations:
# - objects are hashable by default
# - equality (the == operator) is the same as pointer identity (the is operator)
# - inequality comparisons (the >=, >, <=, <) are undefined

# If you implement == you get != for free
# If you implement any of >=, >, <=, <, you get the other for free.
