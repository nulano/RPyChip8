from rpython.rlib.objectmodel import specialize


class errorstream:
    def __init__(self):
        self.stream = None

    @specialize.call_location()
    def write(self, *m):
        for s in list(m):
            assert isinstance(s, str)
            self.stream.write(s)
        self.stream.write('\n')


errorstream = errorstream()
error = errorstream.write
