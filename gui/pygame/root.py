import subprocess

import pygame
from PIL import Image, ImageEnhance

from emulator.chip8 import Chip8_Rpc, Io
from emulator.error import errorstream
from emulator.io.stdio import Stdio, StdioTest
from emulator.types import uint64_t, uint8_t

speed_factor = 1
crt_factor = 0.7

frames_per_s = 60
cycles_per_ms = 1000 * speed_factor
cycles_per_frame = 1000 * cycles_per_ms / frames_per_s


class Screen:
    def __init__(self):
        self.im = Image.new("RGBA", (1, 1))

    def update(self, display):
        size = display.width, display.height
        if self.im.size != size:
            self.im = Image.new("RGBA", size)
        self.im = ImageEnhance.Brightness(self.im).enhance(crt_factor)
        # This loop is fine on PyPy, avoid CPython if possible
        for y in xrange(display.height):
            x = 0
            j = uint64_t(1) << (display.width - 1)
            while j:
                if j & display.data[y]:
                    self.im.putpixel((x, y), (255, 255, 255, 255))
                j >>= 1
                x += 1


class Io_Impl(Io):
    def __init__(self):
        self.delay = uint8_t(0)
        self.sound = uint8_t(0)
        self.last = 0L
        self.offset = 0L

    def sync(self, time):
        global cycles_per_ms
        self.last = long(time)
        time = self.last / cycles_per_ms
        ticks = long(pygame.time.get_ticks()) + self.offset
        ahead = int(time - ticks)
        if ahead >= 0:
            print "cpu is %d ms ahead" % ahead
            pygame.time.delay(min(ahead, 1000))
        elif ahead <= -10:
            print "cpu is %d ms behind" % (-ahead)
            self.offset += ahead

    def is_key_down(self, key):
        raise NotImplementedError

    def next_key(self):
        raise NotImplementedError

    def set_sound(self, delay):
        # print "set sound", delay
        self.sound = self.last + long(delay) * cycles_per_frame

    def set_delay(self, delay):
        # print "set delay", delay
        self.delay = self.last + long(delay) * cycles_per_frame

    def get_delay(self):
        # print "get delay"
        diff = self.delay - self.last
        if diff <= 0:
            return uint8_t(0)
        diff = diff / cycles_per_frame
        return uint8_t(min(diff, 255))


def main(argv):
    screen = Screen()

    proc = subprocess.Popen(['./chip8-c'], executable='./chip8-c.exe',
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    pipe = Stdio(proc.stdout, proc.stdin)
    chip8 = Chip8_Rpc(pipe, Io_Impl())
    chip8.initialize(argv[1])

    pygame.init()
    window = pygame.display.set_mode((640, 320))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                chip8.quit()
                pygame.quit()
                return 0

        chip8.run(cycles_per_frame)
        screen.update(chip8.display)

        im = pygame.image.frombuffer(screen.im.tobytes(), screen.im.size, "RGBA")
        pygame.transform.scale(im, window.get_size(), window)
        pygame.display.flip()


if __name__ == '__main__':
    import sys

    errorstream.stream = sys.stdout
    main(sys.argv)
