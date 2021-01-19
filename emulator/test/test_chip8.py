import pytest

from emulator.chip8 import Chip8


@pytest.yield_fixture(scope="function")
def chip8(request):
    text = request.function.__doc__
    try:
        mark = text.index(";")
        steps = int(text[:mark])
        code = text[mark+1:]
    except ValueError:
        steps = -1
        code = text
    chip8 = Chip8()
    chip8.ram.load_bin(code)
    if steps < 0:
        chip8.run()
    else:
        for i in range(steps):
            chip8.step()
    yield chip8
    assert chip8.paused
    assert chip8.errors == 0


class TestChip8:
    def test_halt(self, chip8):
        """1;\x12\x00"""  # JP 200h
        assert not chip8.paused
        chip8.step()
        assert chip8.paused
        assert chip8.cpu.program_counter == 0x200
        chip8.step()
        assert chip8.paused
        assert chip8.cpu.program_counter == 0x200
        # should not loop
        chip8.run()

    def test_call(self, chip8):
        """2;\x22\x04\x12\x02\x12\x04"""  # CALL 204h; JP 202h; JP 204h
        assert chip8.cpu.program_counter == 0x204

    def test_ret(self, chip8):
        """3;\x22\x04\x12\x02\x00\xEE\x12\x06"""  # CALL 204h; JP 202h; RET; JP 206h
        assert chip8.cpu.program_counter == 0x202
    
    def test_if_ne_equal(self, chip8):
        """\x61\x42\x31\x42\x12\x04\x12\x06"""  # LD V1, 42h; SE V1, 42h; JP 204h; JP 206h

