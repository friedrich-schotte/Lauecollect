from inspect import getfile
from os.path import dirname
def f(): pass
dir=dirname(getfile(f))
