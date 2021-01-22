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


@serialized_field_list('data', s_uint64)
@serialized_field('height', s_uint16)
@serialized_field('width', s_uint16)
@_register('_display')
class M_Display(Message):
    def __init__(self, display):
        self.width = uint16_t(display.width)
        self.height = uint16_t(display.height)
        self.data = display.data

    def unpack(self, display):
        display.width = int(self.width)
        display.height = int(self.height)
        display.data = self.data


@serialized_field('errors', s_uint32)
@serialized_field('paused', s_uint8)
@serialized_field_array('cpu__general_registers', 16, s_uint8)
@serialized_field('cpu__index_register', s_uint16)
@serialized_field('cpu__stack_pointer', s_uint16)
@serialized_field('cpu__program_counter', s_uint16)
@_register('_cpu')
class M_Cpu(Message):
    def __init__(self, chip8):
        self.cpu__program_counter = chip8.cpu.program_counter
        self.cpu__stack_pointer = chip8.cpu.stack_pointer
        self.cpu__index_register = chip8.cpu.index_register
        self.cpu__general_registers = chip8.cpu.general_registers
        self.paused = uint8_t(bool(chip8.paused))
        self.errors = uint32_t(chip8.errors)
    
    def unpack(self, chip8):
        chip8.cpu.program_counter = self.cpu__program_counter
        chip8.cpu.stack_pointer = self.cpu__stack_pointer
        chip8.cpu.index_register = self.cpu__index_register
        chip8.cpu.general_registers = self.cpu__general_registers
        chip8.paused = bool(self.paused)
        chip8.errors = int(self.errors)


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
