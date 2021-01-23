from rpython.rlib import rrandom

from emulator.error import error, errorstream
from emulator.io.dispatcher import Dispatcher
from emulator.io.message import *
from emulator.io.stdio import Stdio
from emulator.types import *

__version__ = '0.1.0'

from rpython.rlib.rarithmetic import intmask

INS_SYSCALL =               0x0000
INS_JUMP =                  0x1000
INS_CALL =                  0x2000
INS_IF_NE =                 0x3000
INS_IF_EQ =                 0x4000
INS_IF_NOT =                0x5000
INS_LOAD_IMM =              0x6000
INS_ADD_IMM =               0x7000
INS_ARITH =                 0x8000
INS_IF =                    0x9000
INS_LOAD_INDEX_IMM =        0xA000
INS_JUMP_OFFSET =           0xB000
INS_RANDOM =                0xC000
INS_DRAW =                  0xD000
INS_IFSYS =                 0xE000
INS_SYSCALL1 =              0xF000

SYSCALL_CLEAR =              0x0E0
SYSCALL_RETURN =             0x0EE

IF_EQ =                        0x0

AR_LD =                        0x0
AR_OR =                        0x1
AR_AND =                       0x2
AR_XOR =                       0x3
AR_ADD =                       0x4
AR_SUB =                       0x5
AR_SHR =                       0x6
AR_SUBN =                      0x7
AR_SHL =                       0xE

IFSYS_KEY_UP =                0x9E
IFSYS_KEY_DN =                0xA1

SYSCALL1_LOAD_DELAY =         0x07
SYSCALL1_LOAD_KEY =           0x0A
SYSCALL1_SET_DELAY =          0x15
SYSCALL1_SET_SOUND =          0x18
SYSCALL1_ADD_INDEX =          0x1E
SYSCALL1_LOAD_INDEX_DIGIT =   0x29
SYSCALL1_LOAD_BCD =           0x33
SYSCALL1_REG_SAVE =           0x55
SYSCALL1_REG_LOAD =           0x65


class Cpu:
    def __init__(self):
        self.program_counter = uint16_t(0x200)
        self.stack_pointer = uint16_t(0)
        self.index_register = uint16_t(0)
        self.general_registers = [uint8_t(0)] * 16


class Memory:
    def __init__(self):
        self.contents = [uint8_t(0)] * 0x1000
        self.load_font()

    def load_font(self):
        # 0
        self.contents[0x50] = uint8_t(0b01100000)
        self.contents[0x51] = uint8_t(0b10010000)
        self.contents[0x52] = uint8_t(0b10010000)
        self.contents[0x53] = uint8_t(0b10010000)
        self.contents[0x54] = uint8_t(0b01100000)
        # 1
        self.contents[0x55] = uint8_t(0b00100000)
        self.contents[0x56] = uint8_t(0b01100000)
        self.contents[0x57] = uint8_t(0b00100000)
        self.contents[0x58] = uint8_t(0b00100000)
        self.contents[0x59] = uint8_t(0b01110000)
        # 2
        self.contents[0x5A] = uint8_t(0b11110000)
        self.contents[0x5B] = uint8_t(0b00010000)
        self.contents[0x5C] = uint8_t(0b11110000)
        self.contents[0x5D] = uint8_t(0b10000000)
        self.contents[0x5E] = uint8_t(0b11110000)
        # 3
        self.contents[0x5F] = uint8_t(0b11110000)
        self.contents[0x60] = uint8_t(0b00010000)
        self.contents[0x61] = uint8_t(0b11110000)
        self.contents[0x62] = uint8_t(0b00010000)
        self.contents[0x63] = uint8_t(0b11110000)
        # 4
        self.contents[0x64] = uint8_t(0b10010000)
        self.contents[0x65] = uint8_t(0b10010000)
        self.contents[0x66] = uint8_t(0b11110000)
        self.contents[0x67] = uint8_t(0b00010000)
        self.contents[0x68] = uint8_t(0b00010000)
        # 5
        self.contents[0x69] = uint8_t(0b11110000)
        self.contents[0x6A] = uint8_t(0b10000000)
        self.contents[0x6B] = uint8_t(0b11110000)
        self.contents[0x6C] = uint8_t(0b00010000)
        self.contents[0x6D] = uint8_t(0b11110000)
        # 6
        self.contents[0x6E] = uint8_t(0b11110000)
        self.contents[0x6F] = uint8_t(0b10000000)
        self.contents[0x70] = uint8_t(0b11110000)
        self.contents[0x71] = uint8_t(0b10010000)
        self.contents[0x72] = uint8_t(0b11110000)
        # 7
        self.contents[0x73] = uint8_t(0b11110000)
        self.contents[0x74] = uint8_t(0b00010000)
        self.contents[0x75] = uint8_t(0b00100000)
        self.contents[0x76] = uint8_t(0b01000000)
        self.contents[0x77] = uint8_t(0b01000000)
        # 8
        self.contents[0x78] = uint8_t(0b11110000)
        self.contents[0x79] = uint8_t(0b10010000)
        self.contents[0x7A] = uint8_t(0b11110000)
        self.contents[0x7B] = uint8_t(0b10010000)
        self.contents[0x7C] = uint8_t(0b11110000)
        # 9
        self.contents[0x7D] = uint8_t(0b11110000)
        self.contents[0x7E] = uint8_t(0b10010000)
        self.contents[0x7F] = uint8_t(0b11110000)
        self.contents[0x80] = uint8_t(0b00010000)
        self.contents[0x81] = uint8_t(0b11110000)
        # A
        self.contents[0x82] = uint8_t(0b11110000)
        self.contents[0x83] = uint8_t(0b10010000)
        self.contents[0x84] = uint8_t(0b11110000)
        self.contents[0x85] = uint8_t(0b10010000)
        self.contents[0x86] = uint8_t(0b10010000)
        # B
        self.contents[0x87] = uint8_t(0b11100000)
        self.contents[0x88] = uint8_t(0b10010000)
        self.contents[0x89] = uint8_t(0b11100000)
        self.contents[0x8A] = uint8_t(0b10010000)
        self.contents[0x8B] = uint8_t(0b11100000)
        # C
        self.contents[0x8C] = uint8_t(0b11110000)
        self.contents[0x8D] = uint8_t(0b10000000)
        self.contents[0x8E] = uint8_t(0b10000000)
        self.contents[0x8F] = uint8_t(0b10000000)
        self.contents[0x90] = uint8_t(0b11110000)
        # D
        self.contents[0x91] = uint8_t(0b11100000)
        self.contents[0x92] = uint8_t(0b10010000)
        self.contents[0x93] = uint8_t(0b10010000)
        self.contents[0x94] = uint8_t(0b10010000)
        self.contents[0x95] = uint8_t(0b11100000)
        # E
        self.contents[0x96] = uint8_t(0b11110000)
        self.contents[0x97] = uint8_t(0b10000000)
        self.contents[0x98] = uint8_t(0b11110000)
        self.contents[0x99] = uint8_t(0b10000000)
        self.contents[0x9A] = uint8_t(0b11110000)
        # F
        self.contents[0x9B] = uint8_t(0b11110000)
        self.contents[0x9C] = uint8_t(0b10000000)
        self.contents[0x9D] = uint8_t(0b11110000)
        self.contents[0x9E] = uint8_t(0b10000000)
        self.contents[0x9F] = uint8_t(0b10000000)

    def load_bin(self, data):
        for i, v in enumerate(data):
            self.contents[0x200 + i] = uint8_t(ord(v))

    def read8(self, addr):
        return self.contents[addr]

    def read16(self, addr):
        a = uint16_t(self.contents[addr])
        b = uint16_t(self.contents[addr + 1])
        return (a << 8) | b

    def store8(self, addr, val):
        self.contents[addr] = val

    def store16(self, addr, val):
        self.contents[addr] = uint8_t((val & 0xFF00) >> 8)
        self.contents[addr + 1] = uint8_t(val & 0xFF)

    def digit(self, d):
        return uint16_t(0x50 + d * 5)


class Display:
    def __init__(self):
        self.width = 64
        self.height = 32
        self.data = [uint64_t(0)] * self.height

    def clear(self):
        for i in range(self.height):
            self.data[i] = uint64_t(0)

    def draw(self, x, y, m):
        m = uint64_t(m)
        if x <= 56:
            m = m << (56 - x)
        else:
            m = m >> (x - 56)
        self.data[y] ^= m
        return self.data[y] & m != m


class Io:
    def sync(self, time):
        raise NotImplementedError, 'abstract base class'

    def is_key_down(self, key):
        raise NotImplementedError, 'abstract base class'

    def next_key(self):
        raise NotImplementedError, 'abstract base class'

    def set_sound(self, delay):
        raise NotImplementedError, 'abstract base class'

    def set_delay(self, delay):
        raise NotImplementedError, 'abstract base class'

    def get_delay(self):
        raise NotImplementedError, 'abstract base class'


class Io_Rpc(Io):
    def __init__(self, pipe):
        self.pipe = pipe

    def sync(self, time):
        self.pipe.tell(M_Sync(time))

    def is_key_down(self, key):
        ans = self.pipe.ask(Q_KeyDown(key))
        assert isinstance(ans, A_KeyDown)
        return ans.down

    def next_key(self):
        ans = self.pipe.ask(Q_NextKey())
        assert isinstance(ans, A_NextKey)
        return ans.key

    def set_sound(self, delay):
        self.pipe.tell(M_SetSoundTimer(delay))

    def set_delay(self, delay):
        self.pipe.tell(M_SetDelayTimer(delay))

    def get_delay(self):
        ans = self.pipe.ask(Q_DelayTimer())
        assert isinstance(ans, A_DelayTimer)
        return ans.delay


class Chip8:
    DISPATCH = Dispatcher()

    def __init__(self, pipe, io):
        assert isinstance(io, Io)

        self.pipe = pipe
        self.random = rrandom.Random()

        self.cpu = Cpu()
        self.ram = Memory()
        self.display = Display()
        self.io = io

        self.time = 0
        self.watchdog = 2**30
        self.errors = 0
        self.paused = False

    def stack_push(self, val):
        self.ram.store16(self.cpu.stack_pointer, val)
        self.cpu.stack_pointer += 2

    def stack_pop(self):
        self.cpu.stack_pointer -= 2
        return self.ram.read16(self.cpu.stack_pointer)

    @DISPATCH.handler(C_Run)
    def cmd_run(self, msg):
        self.run(msg.watchdog)

    def run(self, time=2**30):
        self.watchdog = self.time + time
        while not self.paused and (self.watchdog - self.time) > 0:
            self.step()
        self.io.sync(self.time)

    @DISPATCH.handler(C_Step)
    def step(self, msg=None):
        ins = self.ram.read16(self.cpu.program_counter)
        self.cpu.program_counter += 2

        ins_type = ins & 0xF000
        imm12 = ins & 0x0FFF
        imm8 = ins & 0x00FF
        imm4 = ins & 0x000F
        imm_r1 = (ins & 0x0F00) >> 8
        imm_r2 = (ins & 0x00F0) >> 4
        reg1 = self.cpu.general_registers[imm_r1]
        reg2 = self.cpu.general_registers[imm_r2]

        skip_next = False

        if ins_type == INS_SYSCALL:  # 0x0nnn
            if imm12 == SYSCALL_CLEAR:  # 0x0E0
                self.time += 109
                self.display.clear()
            elif imm12 == SYSCALL_RETURN:  # 0x0EE
                self.cpu.program_counter = self.stack_pop()
            else:
                self.time += 100
                self.errors += 1
                error('unknown syscall: ', hex(imm12))
        elif ins_type == INS_JUMP:  # 0x1nnn
            self.time += 105
            if imm12 == self.cpu.program_counter - 2:
                self.paused = True  # infinite loop, stop emulation
            self.cpu.program_counter = uint16_t(imm12)
        elif ins_type == INS_CALL:  # 0x2nnn
            self.time += 105
            self.stack_push(self.cpu.program_counter)
            self.cpu.program_counter = uint16_t(imm12)
        elif ins_type == INS_IF_NE:  # 0x3xkk
            self.time += 46
            skip_next = reg1 == imm8
        elif ins_type == INS_IF_EQ:  # 0x4xkk
            self.time += 46
            skip_next = reg1 != imm8
        elif ins_type == INS_IF_NOT or ins_type == INS_IF:  # 0x5xyn, 0x9xyn
            if imm4 == IF_EQ:
                self.time += 73
                skip_next = reg1 == reg2
            else:
                self.errors += 1
                error('unknown compare: ', hex(imm4))
            if ins_type == INS_IF:
                skip_next = not skip_next
        elif ins_type == INS_LOAD_IMM:  # 0x6xkk
            self.time += 27
            self.cpu.general_registers[imm_r1] = uint8_t(imm8)
        elif ins_type == INS_ADD_IMM:  # 0x7xkk
            self.time += 45
            self.cpu.general_registers[imm_r1] += uint8_t(imm8)
        elif ins_type == INS_ARITH:  # 0x8xyn
            self.time += 200
            out = reg1
            carry = -1
            if imm4 == AR_LD:
                out = reg2
            elif imm4 == AR_OR:
                out = reg1 | reg2
            elif imm4 == AR_AND:
                out = reg1 & reg2
            elif imm4 == AR_XOR:
                out = reg1 ^ reg2
            elif imm4 == AR_ADD:
                out = reg1 + reg2
                if out < reg1:
                    carry = 1
                else:
                    carry = 0
            elif imm4 == AR_SUB:
                out = reg1 - reg2
                if reg1 > reg2:
                    carry = 1
                else:
                    carry = 0
            elif imm4 == AR_SHR:
                out = reg1 >> 1
                if (reg1 & 1) != 0:
                    carry = 1
                else:
                    carry = 0
            elif imm4 == AR_SUBN:
                out = reg2 - reg1
                if reg2 > reg1:
                    carry = 1
                else:
                    carry = 0
            elif imm4 == AR_SHL:
                out = reg1 << 1
                if (reg1 & 0x80) != 0:
                    carry = 1
                else:
                    carry = 0
            else:
                self.errors += 1
                error('unknown arithmetic instruction: ', hex(imm4))
            if carry != -1:
                self.cpu.general_registers[15] = uint8_t(carry)
            self.cpu.general_registers[imm_r1] = out
        elif ins_type == INS_LOAD_INDEX_IMM:  # 0xAnnn
            self.time += 55
            self.cpu.index_register = imm12
        elif ins_type == INS_JUMP_OFFSET:  # 0xBnnn
            self.time += 105
            self.cpu.program_counter = self.cpu.general_registers[0] + uint16_t(imm12)
        elif ins_type == INS_RANDOM:  # 0xCxkk
            self.time += 164
            self.cpu.general_registers[imm_r1] = uint8_t(self.random.genrand32() & imm8)
        elif ins_type == INS_DRAW:  # 0xDxyn
            collision = False
            x = reg1 & 63  # TODO use display size
            y = reg2 & 31
            s = self.cpu.index_register
            for i in range(imm4):
                if y >= self.display.height:
                    break
                collision = self.display.draw(x, y, self.ram.read8(s)) or collision
                s += 1
                y += 1
                self.time += 1000  # approximate
            if not collision:
                self.cpu.general_registers[15] = uint8_t(0)
            else:
                self.cpu.general_registers[15] = uint8_t(1)
        elif ins_type == INS_IFSYS:  # 0xExkk
            if imm8 == IFSYS_KEY_DN:
                self.io.sync(self.time)
                skip_next = not self.io.is_key_down(reg1)
                self.time += 64
            elif imm8 == IFSYS_KEY_UP:
                self.io.sync(self.time)
                skip_next = self.io.is_key_down(reg1)
                self.time += 64
            else:
                self.time += 100
                self.errors += 1
                error('unknown syscall: ', hex(imm8))
        elif ins_type == INS_SYSCALL1:  # 0xFxkk
            if imm8 == SYSCALL1_LOAD_DELAY:
                self.io.sync(self.time)
                self.cpu.general_registers[imm_r1] = self.io.get_delay()
                self.time += 45
            elif imm8 == SYSCALL1_LOAD_KEY:
                self.io.sync(self.time)
                self.cpu.general_registers[imm_r1] = self.io.next_key()
                # XXX waited for user input, however long it takes
                self.time += 100
            elif imm8 == SYSCALL1_SET_DELAY:
                self.io.sync(self.time)
                self.io.set_delay(reg1)
                self.time += 45
            elif imm8 == SYSCALL1_SET_SOUND:
                self.io.sync(self.time)
                self.io.set_sound(reg1)
                self.time += 45
            elif imm8 == SYSCALL1_ADD_INDEX:
                self.time += 72
                self.cpu.index_register += reg1
            elif imm8 == SYSCALL1_LOAD_INDEX_DIGIT:
                self.time += 91
                self.cpu.index_register = self.ram.digit(reg1)
            elif imm8 == SYSCALL1_LOAD_BCD:
                # TODO this shouldn't need intmask
                a = uint8_t(intmask(reg1) / 100)
                b = uint8_t((intmask(reg1) / 10) % 10)
                c = uint8_t(intmask(reg1) % 10)
                self.ram.store8(self.cpu.index_register, a)
                self.ram.store8(self.cpu.index_register + 1, b)
                self.ram.store8(self.cpu.index_register + 2, c)
                self.time += 364 + 73 * intmask(a + b + c)
            elif imm8 == SYSCALL1_REG_SAVE:
                self.time += 64 * intmask(imm_r1 + 1)
                j = self.cpu.index_register
                for i in xrange(imm_r1 + 1):
                    self.ram.store8(j, self.cpu.general_registers[i])
                    j += 1
            elif imm8 == SYSCALL1_REG_LOAD:
                self.time += 64 * intmask(imm_r1 + 1)
                j = self.cpu.index_register
                for i in xrange(imm_r1 + 1):
                    self.cpu.general_registers[i] = self.ram.read8(j)
                    j += 1
            else:
                self.time += 100
                self.errors += 1
                error('unknown syscall: ', hex(imm8))

        if skip_next:
            self.time += 18
            self.cpu.program_counter += 2

    @DISPATCH.handler(C_Load)
    def cmd_load(self, msg):
        self.load(msg.path)

    def load(self, path):
        data = open(path, "rb").read()
        self.ram.load_bin(data)

    @DISPATCH.handler(C_Display)
    def cmd_display(self, msg):
        self.pipe.tell(M_Display(self.display))

    @DISPATCH.handler(C_Cpu)
    def cmd_cpu(self, msg):
        self.pipe.tell(M_Cpu(self))

    @DISPATCH.unhandler
    def unknown_command(self, c):
        error('unimplemented command: ', c._CODE)
        return False


class Chip8_Rpc:
    DISPATCH = Dispatcher()

    def __init__(self, pipe, io):
        assert isinstance(io, Io)

        self.pipe = pipe
        self.io = io

        self.cpu = Cpu()
        self.display = Display()

        self.errors = 0
        self.paused = False

    def _cmd(self, cmd):
        self.pipe.tell(cmd)
        while True:
            msg = self.pipe.get()
            if msg is None:
                pass
            elif isinstance(msg, Q_NextCommand):
                return
            elif not self.DISPATCH.dispatch(self, msg):
                error('unhandled message: ', msg.serialize())

    def initialize(self, path):
        vers = self.pipe.get()
        if not isinstance(vers, M_Version):
            return False
        if vers.version != __version__:
            return False
        if not isinstance(self.pipe.get(), Q_NextCommand):
            return False
        self._cmd(C_Load(path))
        return True

    def quit(self):
        self.pipe.tell(C_Die())

    def _sync(self):
        self._cmd(C_Cpu())
        self._cmd(C_Display())

    def step(self):
        self._cmd(C_Step())
        self._sync()

    def run(self, watchdog=2**30):
        self._cmd(C_Run(watchdog))
        self._sync()

    @DISPATCH.handler(M_Cpu)
    def msg_cpu(self, msg):
        msg.unpack(self)

    @DISPATCH.handler(M_Display)
    def msg_display(self, msg):
        msg.unpack(self.display)

    @DISPATCH.handler(M_Sync)
    def msg_sync(self, msg):
        self.io.sync(msg.time)

    @DISPATCH.handler(Q_KeyDown)
    def msg_key_down(self, msg):
        self.pipe.tell(A_KeyDown(self.io.is_key_down(msg.key)))

    @DISPATCH.handler(Q_NextKey)
    def msg_next_key(self, msg):
        self.pipe.tell(A_NextKey(self.io.next_key()))

    @DISPATCH.handler(M_SetDelayTimer)
    def msg_set_delay(self, msg):
        self.io.set_delay(msg.delay)

    @DISPATCH.handler(M_SetSoundTimer)
    def msg_set_sound(self, msg):
        self.io.set_sound(msg.delay)

    @DISPATCH.handler(Q_DelayTimer)
    def msg_get_delay(self, msg):
        self.pipe.tell(A_DelayTimer(self.io.get_delay()))


class _stdio:
    def __init__(self):
        self.stdin = None
        self.stdout = None
        self.stderr = None


_stdio = _stdio()


def entrypoint(argv):
    pipe = Stdio(_stdio.stdin, _stdio.stdout)
    pipe.tell(M_Version(__version__))

    chip8 = Chip8(pipe, Io_Rpc(pipe))

    while True:
        c = pipe.ask(Q_NextCommand())
        if c is None:
            pass
        elif isinstance(c, C_Die):
            return 0
        else:
            chip8.DISPATCH.dispatch(chip8, c)


if __name__ == '__main__':
    import sys

    _stdio.stdin, _stdio.stdout, _stdio.stderr = sys.stdin, sys.stdout, sys.stderr
    errorstream.stream = _stdio.stderr
    entrypoint(sys.argv)
else:
    from rpython.rlib import rfile

    def target(*args):
        def entrypoint_wrap(argv):
            _stdio.stdin, _stdio.stdout, _stdio.stderr = rfile.create_stdio()
            errorstream.stream = _stdio.stderr
            # XXX obscure RPython bug: on linux, rffi.scoped_alloc_buffer
            #     is annotated with size=const(100) which causes
            #     late-stage annotation error
            with rffi.scoped_alloc_buffer(123) as buf:
                return entrypoint(argv)

        return entrypoint_wrap
