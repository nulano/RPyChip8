
class Stdio:
    def __init__(self, i, o):
        self.i = i
        self.o = o

    def send(self, m):
        self.o.write(m)
        self.o.write('\n')

    def read(self):
        return self.i.readline()

    def ask(self, m):
        self.send(m)
        self.o.flush()
        return self.read()
