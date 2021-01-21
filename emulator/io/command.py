from assembler.tokenizer import tokenize
from emulator.error import error

commands = {}


def _register(cmd, *codes):
    cmd._CODE = codes[0]
    for code in codes:
        commands[code] = cmd


class Command(object):
    _CODE = None

    def __init__(self, m, t):
        pass

    def serialize(self):
        return self._CODE


class C_Die(Command):
    pass


class C_Step(Command):
    pass


class C_Run(Command):
    def __init__(self, m, t):
        self.watchdog = int(t[1], 16)

    def serialize(self):
        return self._CODE + hex(self.watchdog)[2:].zfill(16)


class C_Load(Command):
    def __init__(self, m, t):
        self.path = m[1:].strip()

    def serialize(self):
        return self._CODE + self.path


class C_Display(Command):
    pass


class C_Cpu(Command):
    pass


_register(C_Die, '!', 'die')
_register(C_Step, 's', 'step')
_register(C_Run, 'r', 'run')
_register(C_Load, 'l', 'load')
_register(C_Display, 'display')
_register(C_Cpu, 'cpu')


def unserialize(m):
    tokens = tokenize(m, whitespace=" \t\n\r", op="", comment="")
    try:
        cls = commands[tokens[0]]
    except KeyError:
        error("bad command: ", tokens[0])
        return None
    except IndexError:
        # EOF?
        return None
    return cls(m, tokens)
