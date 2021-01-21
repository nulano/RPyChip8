"""
This file defines all messages that can be passed using the io functions.

Each message must inherit from the abstract base class Message, and have
the `@_register(...)` annotation listing all supported spellings for the
given message. The `@_register(...)` function makes sure these are unique;
the complete list is dumped to stderr when this file is imported.

Message classes should follow the following naming convention:
* `M_...` -> Message from emulator to user, may be in response to a Command
* `Q_...` -> Question from emulator to user, expecting response
* `A_Xyz` -> Answer to `Q_Xyz` from user to emulator
* `C_...` -> Command from user to emulator, answer to `Q_NextCommand`

Unexpected messages may be ignored or terminate the connection.
"""

from rpython.rlib.objectmodel import not_rpython, always_inline, instantiate
from rpython.rlib.rStringIO import RStringIO

from assembler.tokenizer import tokenize
from emulator.error import error
from emulator.io.serialize import *
from emulator.types import *

_codes = {}


@not_rpython
def _register(*codes):
    @not_rpython
    def impl(cls):
        cls._CODE = codes[0]
        for code in codes:
            assert code not in _codes
            _codes[code] = cls
        return cls
    return impl


class Message(object):
    _CODE = None

    def __init__(self):
        pass

    def serialize(self):
        out = RStringIO()
        self.serialize_impl(out)
        return out.getvalue()

    @always_inline
    def serialize_impl(self, out):
        assert self._CODE is not None
        out.write(self._CODE)

    def unserialize(self, m, t):
        assert type(self) is not Message
        return self.unserialize_impl(t) == len(t)

    @always_inline
    def unserialize_impl(self, t):
        return 1


@serialized_field('version', s_str)
@_register('version')
class M_Version(Message):
    def __init__(self, version=''):
        self.version = version


@_register('_display')
class M_Display(Message):
    def __init__(self, line=0, val=''):
        self.line = line
        self.val = val

    # def serialize(self):
    #     return self._CODE + ' ' + str(self.line).zfill(2) + ' ' + self.val

    def unserialize(self, m, t):
        assert False


@_register('_cpu')
class M_Cpu(Message):
    def __init__(self, reg_name, reg_val):
        self.reg_name = reg_name
        self.reg_val = reg_val

    def serialize(self):
        return self._CODE + ' ' + self.reg_name + ' ' + hex(self.reg_val)

    def unserialize(self, m, t):
        self.reg_name = t[1]
        self.reg_val = unsigned(int(t[2], 16))
        return True


@_register('?')
class Q_NextCommand(Message):
    pass


@_register('!', 'die')
class C_Die(Message):
    pass


@_register('s', 'step')
class C_Step(Message):
    pass


@_register('r', 'run')
class C_Run(Message):
    def __init__(self, watchdog=2**30):
        self.watchdog = watchdog

    def serialize(self):
        return self._CODE + ' ' + hex(self.watchdog)[2:]#.zfill(16)

    def unserialize(self, m, t):
        self.watchdog = int(t[1], 16)
        return True


@serialized_field('path', s_str)
@_register('l', 'load')
class C_Load(Message):
    def __init__(self, path=''):
        self.path = path


@_register('display')
class C_Display(Message):
    pass


@_register('cpu')
class C_Cpu(Message):
    pass


def unserialize(m):
    tokens = tokenize(m, whitespace=' \t\n\r', op='', comment='')
    try:
        cls = _codes[tokens[0]]
    except KeyError:
        error('bad message: ', tokens[0])
        return None
    except IndexError:
        # EOF?
        return None
    msg = instantiate(cls)
    if not msg.unserialize(m, tokens):
        error('malformed message: ', tokens[0])
        return None
    return msg


if 1:  # finalize _codes
    del _register
    import sys
    print >>sys.stderr, 'registered message codes:'
    for _code, _cmd in sorted(_codes.iteritems()):
        print >>sys.stderr, '*', _code, '-->', _cmd
    del sys, _code, _cmd
