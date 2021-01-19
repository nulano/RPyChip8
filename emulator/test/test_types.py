
from emulator.types import *


class TestTypes:
    def test_uint8(self):
        x = uint8_t(0)
        assert x == 0
        x += 127
        assert x == 127
        x += 128
        assert x == 255
        x += 1
        assert x == 0
        x -= 1
        assert x == 255
        x <<= 1
        assert x == 254
        x >>= 1
        assert x == 127
