import sys
import contextlib

# -------------------------------- Imports ----------------------------------- #

# Support functions borrowed from CPython's test.support
@contextlib.contextmanager
def import_scripts(dir='..'):
    with DirsOnSysPath(dir) as cm:
        yield cm


class DirsOnSysPath(object):
    def __init__(self, *paths):
        self.original_value = sys.path[:]
        self.original_object = sys.path
        sys.path.extend(paths)

    def __enter__(self):
        return self

    def __exit__(self, *ignore_exc):
        sys.path = self.original_object
        sys.path[:] = self.original_value
