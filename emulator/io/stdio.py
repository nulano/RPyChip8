from rpython.rlib.objectmodel import not_rpython

from emulator.error import error
from emulator.io.message import unserialize


class Stdio:
    def __init__(self, i, o):
        self.i = i
        self.o = o

    def tell(self, msg):
        assert msg is not None
        self.o.write(msg.serialize())
        self.o.write('\n')
        self.o.flush()

    def get(self):
        msg = self.i.readline()
        return unserialize(msg)

    def ask(self, question):
        assert question is not None
        self.tell(question)
        return self.get()


class StdioTest(Stdio):
    @not_rpython
    def __init__(self, i, o):
        Stdio.__init__(self, i, o)

    def tell(self, msg):
        assert msg is not None
        s = msg.serialize()
        error('>>> ', s)
        self.o.write(s)
        self.o.write('\n')

    def get(self):
        msg = self.i.readline()
        error('<<< ', msg.rstrip())
        return unserialize(msg)
