
option = None


def pytest_configure(config):
    global option
    option = config.option

    import rpython.conftest
    rpython.conftest.option = option


def pytest_addoption(parser):
    parser.addoption('--view', action="store_true", dest="view", default=False,
           help="view translation tests' flow graphs with Pygame")
    parser.addoption('--viewloops', action="store_true",
           default=False, dest="viewloops",
           help="show only the compiled loops")
    parser.addoption('--viewdeps', action="store_true",
           default=False, dest="viewdeps",
           help="show the dependencies that have been constructed from a trace")
