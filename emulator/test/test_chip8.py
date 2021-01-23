import subprocess

import pytest

from assembler.chip8 import assemble
from emulator.chip8 import Io
from emulator.test.conftest import option
from emulator.types import uint8_t

pytestmark = pytest.mark.timeout(10)


class IoTest(Io):
    def __init__(self):
        self.events = []
        self.events_expected = [("sync",)]
        self.val_is_key_down = False
        self.val_next_key = 0
        self.val_delay = 0

    def sync(self, time):
        self.events.append(("sync",))

    def is_key_down(self, key):
        self.events.append(("is_key_down", key))
        return self.val_is_key_down

    def next_key(self):
        self.events.append(("next_key",))
        return uint8_t(self.val_next_key)

    def set_sound(self, delay):
        self.events.append(("set_sound", delay))

    def set_delay(self, delay):
        self.events.append(("set_delay", delay))

    def get_delay(self):
        self.events.append(("get_delay",))
        return uint8_t(self.val_delay)


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
        chip8 = Chip8(None, IoTest())
        chip8.ram.load_bin(code)
        yield chip8
        assert chip8.io.events == chip8.io.events_expected

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
        chip8.io.events_expected = []
        assert chip8.cpu.program_counter == 0x204
        assert chip8.paused

    def test_call(self, chip8):
        """;steps=2
            CALL b
            HLT
        b:
            HLT
        """
        chip8.io.events_expected = []
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
        chip8.io.events_expected = []
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
        chip8.io.events_expected = []
        assert chip8.cpu.index_register == 0xABC

    def test_jump_offset(self, chip8):
        """;steps=2
            LD V0, 42h
            JP V0, 300h
        """
        chip8.io.events_expected = []
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

    def test_draw1(self, chip8):
        """
            CALL main
            HLT
        main:
            LD V1, 2
            LD V2, 4
            LD VF, 2
            LD I, img1
            DRW V1, V2, 3
            IFNE VF, 0
            HLT
            LD I, img2
            DRW V1, V2, 1
            IFNE VF, 1
            HLT
            RET
        img1:
            DW A55Ah
            DW FFFFh
        img2:
            DW 80FFh
        """
        assert chip8.cpu.program_counter == 0x202
        assert chip8.display.data[0] == 0
        assert chip8.display.data[1] == 0
        assert chip8.display.data[2] == 0
        assert chip8.display.data[3] == 0
        assert chip8.display.data[4] == 0b0000100101000000L << 48
        assert chip8.display.data[5] == 0b0001011010000000L << 48
        assert chip8.display.data[6] == 0b0011111111000000L << 48
        assert chip8.display.data[7] == 0
        assert chip8.display.data[8] == 0
        assert chip8.display.data[9] == 0

    def test_draw2(self, chip8):
        # make sure clear works
        """
            CALL main
            HLT
        main:
            LD V1, 2
            LD V2, 4
            LD VF, 2
            LD I, img1
            DRW V1, V2, 15
            IFNE VF, 0
            HLT
            DRW V1, V2, 15
            IFNE VF, 1
            HLT
            RET
        img1:
            DW A55Ah
            DW FFFFh
            DW BCDEh
            DW A55Ah
            DW FFFFh
            DW BCDEh
            DW A55Ah
            DW FFFFh
            DW BCDEh
        """
        assert chip8.cpu.program_counter == 0x202
        for i in xrange(chip8.display.height):
            assert chip8.display.data[i] == 0
    
    def test_if_key_up1(self, chip8):
        """;steps=0
            LD V1, 5
            IFUP V1
            HLT
            HLT
        """
        chip8.io.val_is_key_down = False
        chip8.io.events_expected = [("sync",), ("is_key_down", 5), ("sync",)]
        chip8.run()
        assert chip8.cpu.program_counter == 0x204
    
    def test_if_key_up2(self, chip8):
        """;steps=0
            LD V1, 6
            IFUP V1
            HLT
            HLT
        """
        chip8.io.val_is_key_down = True
        chip8.io.events_expected = [("sync",), ("is_key_down", 6), ("sync",)]
        chip8.run()
        assert chip8.cpu.program_counter == 0x206
    
    def test_if_key_dn1(self, chip8):
        """;steps=0
            LD V1, 5
            IFDN V1
            HLT
            HLT
        """
        chip8.io.val_is_key_down = False
        chip8.io.events_expected = [("sync",), ("is_key_down", 5), ("sync",)]
        chip8.run()
        assert chip8.cpu.program_counter == 0x206
    
    def test_if_key_dn2(self, chip8):
        """;steps=0
            LD V1, 6
            IFDN V1
            HLT
            HLT
        """
        chip8.io.val_is_key_down = True
        chip8.io.events_expected = [("sync",), ("is_key_down", 6), ("sync",)]
        chip8.run()
        assert chip8.cpu.program_counter == 0x204
        
    def test_get_delay(self, chip8):
        """;steps=0
            LD V3, DT
        """
        chip8.io.val_delay = 0xFC
        chip8.io.events_expected = [("sync",), ("get_delay",)]
        chip8.step()
        assert chip8.cpu.general_registers[3] == 0xFC

    def test_next_key(self, chip8):
        """;steps=0
            LD V7, K
        """
        chip8.io.val_next_key = 0xB
        chip8.io.events_expected = [("sync",), ("next_key",)]
        chip8.step()
        assert chip8.cpu.general_registers[7] == 0xB

    def test_set_delay(self, chip8):
        """;steps=2
            LD V4, 0xAB
            LD DT, V4
        """
        chip8.io.events_expected = [("sync",), ("set_delay", 0xAB)]

    def test_set_sound(self, chip8):
        """;steps=2
            LD V4, 0xBC
            LD ST, V4
        """
        chip8.io.events_expected = [("sync",), ("set_sound", 0xBC)]

    def test_add_index(self, chip8):
        """
            LD I, 0x123
            LD V6, 0x22
            ADD I, V6
            HLT
        """
        assert chip8.cpu.index_register == 0x145

    def test_load_digit(self, chip8):
        """
            LD V4, 0xC
            LD F, V4
            HLT
        """
        assert chip8.cpu.index_register == 0x5C  # FIXME

    # TODO LD B, Vx
    # TODO LD [I], Vx
    # TODO LD Vx, [I]


def _apptest_unique_file(LAST=[0]):
    from rpython.tool.udir import udir

    i = LAST[0]
    LAST[0] += 1
    return udir.join('%s_%d.ch8' % (__name__, i))


class AppTestChip8(TestChip8):
    def get_chip8(self, code):
        from emulator.chip8 import Chip8_Rpc, Io
        from emulator.io.stdio import StdioTest

        path = _apptest_unique_file()
        path.write_binary(code)

        proc = subprocess.Popen([option.apptest], executable=option.apptest,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        chip8 = Chip8_Rpc(StdioTest(proc.stdout, proc.stdin), IoTest())
        assert chip8.initialize(str(path))
        yield chip8
        assert chip8.io.events == chip8.io.events_expected
        chip8.quit()
        assert proc.wait() == 0
