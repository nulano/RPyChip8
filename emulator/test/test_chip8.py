import subprocess

import pytest

from assembler.chip8 import assemble
from emulator.test.conftest import option

pytestmark = pytest.mark.timeout(10)


@pytest.yield_fixture(scope="function")
def chip8(request):
    lines = request.function.__doc__.splitlines()
    code = assemble(lines)
    ctx = request.instance.get_chip8(code)
    chip8 = next(ctx)
    if lines[0][:7] == ";steps=":
        for i in range(int(lines[0][7:])):
            chip8.step()
    else:
        chip8.run()
    yield chip8
    if lines[0][:7] != ";steps=":
        assert chip8.paused
    assert chip8.errors == 0
    try:
        next(ctx)
    except StopIteration:
        pass
    else:
        assert False


class TestChip8:
    def get_chip8(self, code):
        from emulator.chip8 import Chip8
        # TODO use I/O test harness
        chip8 = Chip8(None)
        chip8.ram.load_bin(code)
        yield chip8

    def test_halt(self, chip8):
        """;steps=0
            HLT
        """
        assert not chip8.paused
        chip8.step()
        assert chip8.paused
        assert chip8.cpu.program_counter == 0x200
        chip8.step()
        assert chip8.paused
        assert chip8.cpu.program_counter == 0x200
        # should not loop
        chip8.run()

    def test_jump(self, chip8):
        """;steps=2
            JP b
            JP $
        b:
            JP $
        """
        assert chip8.cpu.program_counter == 0x204
        assert chip8.paused

    def test_call(self, chip8):
        """;steps=2
            CALL b
            HLT
        b:
            HLT
        """
        assert chip8.cpu.program_counter == 0x204
        assert chip8.paused

    def test_ret(self, chip8):
        """
            CALL b
            HLT
        b:
            RET
            HLT
        """
        assert chip8.cpu.program_counter == 0x202

    def test_ld_byte(self, chip8):
        """;steps=1
            LD VA, FEh
        """
        assert chip8.cpu.general_registers[10] == 0xFE
    
    def test_if_ne(self, chip8):
        """
            CALL main
            HLT
        main:
            LD V1, 42h
            IFNE V1, 42h
            JP fail
            IFNE V1, 24h
            RET
        fail:
            HLT
        """
        assert chip8.cpu.program_counter == 0x202

    def test_if_eq(self, chip8):
        """
            CALL main
            HLT
        main:
            LD V1, 42h
            IFEQ V1, 24h
            JP fail
            IFEQ V1, 42h
            RET
        fail:
            HLT
        """
        assert chip8.cpu.program_counter == 0x202

    def test_if_not_reg_eq(self, chip8):
        """
            CALL main
            HLT
        main:
            LD V1, 42h
            LD V2, 42h
            IFNE V1, V2
            JP fail
            LD V2, 24h
            IFNE V1, V2
            RET
        fail:
            HLT
        """
        assert chip8.cpu.program_counter == 0x202

    def test_if_reg_eq(self, chip8):
        """
            CALL main
            HLT
        main:
            LD V1, 42h
            LD V2, 24h
            IFEQ V1, V2
            JP fail
            LD V2, 42h
            IFEQ V1, V2
            RET
        fail:
            HLT
        """
        assert chip8.cpu.program_counter == 0x202

    def test_add_no_overflow(self, chip8):
        """
            LD VF, 2
            LD V1, 7Fh
            ADD V1, 80h
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0xFF
        assert chip8.cpu.general_registers[15] == 2

    def test_add_with_overflow(self, chip8):
        """
            LD VF, 2
            LD V1, FFh
            ADD V1, FFh
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0xFE
        assert chip8.cpu.general_registers[15] == 2

    def test_arith_ld(self, chip8):
        """
            LD VF, 2
            LD V1, ABh
            LD V2, V1
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0xAB
        assert chip8.cpu.general_registers[2] == 0xAB
        assert chip8.cpu.general_registers[15] == 2

    def test_arith_or(self, chip8):
        """
            LD VF, 2
            LD V1, AAh
            LD V2, 5Ah
            OR V1, V2
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0xFA
        assert chip8.cpu.general_registers[2] == 0x5A
        assert chip8.cpu.general_registers[15] == 2

    def test_arith_and(self, chip8):
        """
            LD VF, 2
            LD V1, AAh
            LD V2, 5Ah
            AND V1, V2
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0x0A
        assert chip8.cpu.general_registers[2] == 0x5A
        assert chip8.cpu.general_registers[15] == 2

    def test_arith_xor(self, chip8):
        """
            LD VF, 2
            LD V1, AAh
            LD V2, 5Ah
            XOR V1, V2
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0xF0
        assert chip8.cpu.general_registers[2] == 0x5A
        assert chip8.cpu.general_registers[15] == 2

    def test_arith_add_no_overflow(self, chip8):
        """
            LD VF, 2
            LD V1, 7Fh
            LD V2, 80h
            ADD V1, V2
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0xFF
        assert chip8.cpu.general_registers[2] == 0x80
        assert chip8.cpu.general_registers[15] == 0

    def test_arith_add_with_overflow(self, chip8):
        """
            LD VF, 2
            LD V1, 7Fh
            LD V2, FFh
            ADD V1, V2
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0x7E
        assert chip8.cpu.general_registers[2] == 0xFF
        assert chip8.cpu.general_registers[15] == 1

    def test_arith_sub_no_borrow(self, chip8):
        """
            LD VF, 2
            LD V1, AAh
            LD V2, 5Ah
            SUB V1, V2
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0x50
        assert chip8.cpu.general_registers[2] == 0x5A
        assert chip8.cpu.general_registers[15] == 1

    def test_arith_sub_with_borrow(self, chip8):
        """
            LD VF, 2
            LD V1, 5Ah
            LD V2, AAh
            SUB V1, V2
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0xB0
        assert chip8.cpu.general_registers[2] == 0xAA
        assert chip8.cpu.general_registers[15] == 0

    def test_arith_shr0(self, chip8):
        """
            LD VF, 3
            LD V1, AAh
            SHR V1
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0x55
        assert chip8.cpu.general_registers[15] == 0

    def test_arith_shr1(self, chip8):
        """
            LD VF, 3
            LD V1, 55h
            SHR V1
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0x2A
        assert chip8.cpu.general_registers[15] == 1

    def test_arith_subn_no_borrow(self, chip8):
        """
            LD VF, 2
            LD V1, 5Ah
            LD V2, AAh
            SUBN V1, V2
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0x50
        assert chip8.cpu.general_registers[2] == 0xAA
        assert chip8.cpu.general_registers[15] == 1

    def test_arith_subn_with_borrow(self, chip8):
        """
            LD VF, 2
            LD V1, AAh
            LD V2, 5Ah
            SUBN V1, V2
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0xB0
        assert chip8.cpu.general_registers[2] == 0x5A
        assert chip8.cpu.general_registers[15] == 0

    def test_arith_shl0(self, chip8):
        """
            LD VF, 3
            LD V1, 55h
            SHL V1
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0xAA
        assert chip8.cpu.general_registers[15] == 0

    def test_arith_shl1(self, chip8):
        """
            LD VF, 3
            LD V1, AAh
            SHL V1
            HLT
        """
        assert chip8.cpu.general_registers[1] == 0x54
        assert chip8.cpu.general_registers[15] == 1

    def test_ld_index(self, chip8):
        """;steps=1
            LD I, ABCh
        """
        assert chip8.cpu.index_register == 0xABC

    def test_jump_offset(self, chip8):
        """;steps=2
            LD V0, 42h
            JP V0, 300h
        """
        assert chip8.cpu.program_counter == 0x342

    def test_random(self, chip8):
        """
            LD V1, 0    ; iteration
            LD V2, 0    ; output
        loop:
            RND V3, AAh
            OR V2, V3
            ADD V1, 1
            IFNE V1, FFh
            JP loop
            HLT
        """
        assert chip8.cpu.general_registers[2] == 0xAA


def _apptest_unique_file(LAST=[0]):
    from rpython.tool.udir import udir

    i = LAST[0]
    LAST[0] += 1
    return udir.join('%s_%d.ch8' % (__name__, i))


class AppTestChip8(TestChip8):
    def get_chip8(self, code):
        from emulator.chip8 import Chip8_Rpc, __version__
        from emulator.io import message
        from emulator.io.stdio import StdioTest

        path = _apptest_unique_file()
        path.write_binary(code)

        proc = subprocess.Popen([option.apptest], executable=option.apptest,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        io = StdioTest(proc.stdout, proc.stdin)

        vers = io.get()
        assert isinstance(vers, message.M_Version)
        assert vers.version == __version__

        chip8 = Chip8_Rpc(io)
        chip8._cmd(message.C_Load(str(path)))
        yield chip8
        chip8._cmd(message.C_Die())
        assert proc.wait() == 0
