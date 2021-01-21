import sys

import pytest

from emulator.error import errorstream

errorstream.stream = sys.stderr

option = None


def pytest_configure(config):
    global option
    option = config.option

    import rpython.conftest
    rpython.conftest.option = option


def pytest_addoption(parser):
    parser.addoption('-A', '--apptest', action="store",
           default=None, dest="apptest", help="test translated executable")

    parser.addoption('--view', action="store_true", dest="view", default=False,
           help="view translation tests' flow graphs with Pygame")
    parser.addoption('--viewloops', action="store_true",
           default=False, dest="viewloops",
           help="show only the compiled loops")
    parser.addoption('--viewdeps', action="store_true",
           default=False, dest="viewdeps",
           help="show the dependencies that have been constructed from a trace")


def pytest_pycollect_makemodule(path, parent):
    class EmulatorModule(pytest.Module):
        def classnamefilter(self, name):
            if name.startswith('Test'):
                return self.config.option.apptest is None
            if name.startswith('AppTest'):
                return self.config.option.apptest is not None
            return False

    return EmulatorModule(path, parent)
