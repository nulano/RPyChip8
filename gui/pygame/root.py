import struct
import subprocess

import pygame
from PIL import Image, ImageDraw, ImageEnhance

from emulator.chip8 import Chip8_Rpc, Io
from emulator.error import errorstream
from emulator.io.stdio import Stdio, StdioTest
from emulator.types import uint64_t, uint8_t

# chip 8 time is in us, pygame time in ms
speed = 1000
offset = 0L


class Screen:
    def __init__(self):
        self.im = Image.new("RGBA", (1, 1))

    def update(self, display):
        size = display.width, display.height
        if self.im.size != size:
            self.im = Image.new("RGBA", size)
        self.im = ImageEnhance.Brightness(self.im).enhance(0.6)
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

    def sync(self, time):
        global speed, offset
        time = long(time) / speed
        self.last = time
        ticks = long(pygame.time.get_ticks()) + offset
        ahead = int(time - ticks)
        if ahead >= 0:
            print "cpu is %d ms ahead" % ahead
            pygame.time.delay(min(ahead, 1000))
        elif ahead <= -10:
            print "cpu is %d ms behind" % (-ahead)
            offset += ahead

    def is_key_down(self, key):
        raise NotImplementedError

    def next_key(self):
        raise NotImplementedError

    def set_sound(self, delay):
        print "set sound", delay
        self.sound = self.last + long(delay) * (1000 / 60)

    def set_delay(self, delay):
        print "set delay", delay
        self.delay = self.last + long(delay) * (1000 / 60)

    def get_delay(self):
        print "get delay"
        diff = self.delay - self.last
        if diff <= 0:
            return uint8_t(0)
        diff = diff / (1000 / 60)
        return uint8_t(min(diff, 255))


def time_dbg(name, last=[0]):
    now = pygame.time.get_ticks()
    delta = now - last[0]
    if name:
        print "%s took %d ms" % (name, delta)
    last[0] = now


def main(argv):
    screen = Screen()

    proc = subprocess.Popen(['./chip8-c'], executable='./chip8-c.exe',
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    pipe = Stdio(proc.stdout, proc.stdin)
    chip8 = Chip8_Rpc(pipe, Io_Impl())
    chip8.initialize(argv[1])

    pygame.init()
    window = pygame.display.set_mode((640, 320))
    # clock = pygame.time.Clock()

    # time_dbg(None)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                chip8.quit()
        # time_dbg("event loop")

        time_dbg(None)
        chip8.run(1000 * speed / 60)
        time_dbg("cpu loop")
        screen.update(chip8.display)
        # time_dbg("screen update")

        im = pygame.image.frombuffer(screen.im.tobytes(), screen.im.size, "RGBA")
        pygame.transform.scale(im, window.get_size(), window)
        # time_dbg("screen draw")
        pygame.display.flip()
        # time_dbg("screen flip")
    pygame.quit()


if __name__ == '__main__':
    import sys

    errorstream.stream = sys.stdout
    main(sys.argv)
