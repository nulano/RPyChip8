
from rpython.rlib import rrandom

from emulator.types import *


INS_SYSCALL =           0x0000
INS_JUMP =              0x1000
INS_CALL =              0x2000
INS_IF_NE =             0x3000
INS_IF_EQ =             0x4000
INS_IF_NOT =            0x5000
INS_LOAD_IMM =          0x6000
INS_ADD_IMM =           0x7000
INS_ARITH =             0x8000
INS_IF =                0x9000
INS_LOAD_INDEX_IMM =    0xA000
INS_JUMP_OFFSET =       0xB000
INS_RANDOM =            0xC000
INS_DRAW =              0xD000
INS_EXTRA =             0xE000
INS_EXTRA2 =            0xF000

SYSCALL_CLEAR =          0x0E0
SYSCALL_RETURN =         0x0EE

IF_EQ =                    0x0

AR_LD =                    0x0
AR_OR =                    0x1
AR_AND =                   0x2
AR_XOR =                   0x3
AR_ADD =                   0x4
AR_SUB =                   0x5
AR_SHR =                   0x6
AR_SUBN =                  0x7
AR_SHL =                   0xE


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
        pass  # FIXME

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


class Chip8:
    def __init__(self):
        self.cpu = Cpu()
        self.ram = Memory()
        self.display = Display()
        self.random = rrandom.Random()
        self.time = 0
        self.errors = 0
        self.paused = False

    def stack_push(self, val):
        self.ram.store16(self.cpu.stack_pointer, val)
        self.cpu.stack_pointer += 2

    def stack_pop(self):
        self.cpu.stack_pointer -= 2
        return self.ram.read16(self.cpu.stack_pointer)

    def run(self):
        while not self.paused:
            self.step()

    # def _steps(self, count):
    #     """NOT_RPYTHON: Used by tests"""
    #     for i in range(count):
    #         self.step()

    def step(self):
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
                self.errors += 1
                print "unknown syscall: ", imm12
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
                print "unknown compare: ", imm4
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
                print "unknown arithmetic instruction: ", imm4
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
            self.time += 22734  # +- 4634...
            collision = False
            x = reg1 & 63  # TODO use display size
            y = reg2 & 31
            s = self.cpu.index_register
            for i in range(imm4):
                if y >= self.display.height:
                    break
                collision = collision or self.display.draw(x, y, self.ram.read8(s))
                s += 1
                y += 1
            if not collision:
                self.cpu.general_registers[15] = uint8_t(0)
            else:
                self.cpu.general_registers[15] = uint8_t(1)
        # elif ins_type == INS_EXTRA:  # 0xExkk
        #     self.time += 64
        #     xxx
        # elif ins_type == INS_EXTRA2:  # 0xFxkk
        #     xxx

        if skip_next:
            self.time += 18
            self.cpu.program_counter += 2


def entrypoint(argv):
    data = open(argv[1], "rb").read()

    chip8 = Chip8()
    chip8.ram.load_bin(data)
    chip8.run()

    print "Finished after: ", chip8.time
    for x in chip8.display.data:
        print bin(x)[2:].zfill(64)


if __name__ == '__main__':
    import sys

    entrypoint(sys.argv)
