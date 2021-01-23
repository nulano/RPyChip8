import sys

from rpython import conftest

from assembler.chip8 import assemble
from emulator.chip8 import Chip8, Io
from emulator.error import errorstream

class err:
    def write(self, data):
        raise Exception()


errorstream.stream = err()


class o:
    view = False
    viewloops = True
conftest.option = o

from rpython.rlib.nonconst import NonConstant
from rpython.rlib import jit
from rpython.jit.metainterp.test.test_ajit import LLJitMixin


class TestLLtype(LLJitMixin):
    def run_code(self, source):
        code = assemble(source.splitlines())
        chip8 = Chip8(None, Io())
        chip8.ram.load_bin(code)

        def interp_w():
            jit.set_param(None, "disable_unrolling", 5000)
            chip8.run()

        self.meta_interp(interp_w, [], listcomp=True, listops=True, backendopt=True, inline=True)

    # def test_loop_infinite(self):
    #     self.run_code("""
    #         LD V1, V1
    #         JP $-2
    #     """)

    def test_loop_counting(self):
        self.run_code("""
            LD V1, 123
        loop:
            IFEQ V1, 0
            HLT
            ADD V1, 255
            JP loop
        """)

    def test_rewrite(self):
        self.run_code("""
            LD I, ins
            LD V0, 7Ah
            LD V1, 1h
            LD VA, 123
        loop:
            IFEQ VA, 0
            HLT
        ins:
            ADD VA, 255
            LD [I], V1
            JP loop
        """)

    def test_mult(self):
        self.run_code("""
                LD VA, 200
                LD VB, 143
                CALL mult
                HLT
            
            mult:
                LD V1, VA
                LD V2, VB
                LD VA, 0
                LD VB, 0
            loop:
                IFEQ V1, 0
                RET
                ADD V1, 255
                ADD VB, V2
                IFEQ VF, 1
                ADD VA, 1
                JP loop
            """)
