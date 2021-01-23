import subprocess
from array import array
from math import pi, sin

import pygame
from PIL import Image, ImageEnhance

from emulator.chip8 import Chip8_Rpc, Io
from emulator.error import errorstream
from emulator.io.stdio import Stdio, StdioTest
from emulator.types import uint64_t, uint8_t

speed_factor = 1
crt_factor = 0.7
sound_fq = 440
sound_amp = 0.1

keymap = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
          pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r,
          pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f,
          pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v]

frames_per_s = 60
ms_per_frame = 1000 / 60
cycles_per_ms = 1000 * speed_factor
cycles_per_frame = cycles_per_ms * ms_per_frame

keypad = [keymap[13], keymap[0], keymap[1], keymap[2],
          keymap[4], keymap[5], keymap[6], keymap[8],
          keymap[9], keymap[10], keymap[12], keymap[14],
          keymap[3], keymap[7], keymap[11], keymap[15]]


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
        self.sound = create_sound()
        self.delay = 0L
        self.last = 0L
        self.offset = 0L

    def sync(self, time):
        global cycles_per_ms
        self.last = long(time)
        time = self.last / cycles_per_ms
        ticks = long(pygame.time.get_ticks()) + self.offset
        ahead = int(time - ticks)
        if ahead >= 0:
            if ahead >= 5 * ms_per_frame:
                print "cpu is %d ms ahead" % ahead
                self.offset += ahead - 5 * ms_per_frame
                ahead = 5 * ms_per_frame
            pygame.time.delay(ahead)
        elif ahead <= -ms_per_frame:
            print "cpu is %d ms behind" % (-ahead)
            self.offset += ahead

    def is_key_down(self, key):
        return pygame.key.get_pressed()[keypad[key]]

    def next_key(self):
        print "waiting for key..."
        for event in pygame.event.get(pygame.KEYDOWN):
            pass
        while True:
            for event in pygame.event.get(pygame.KEYDOWN):
                # print event
                try:
                    i = keypad.index(event.key)
                except ValueError:
                    pass
                else:
                    return uint8_t(i)

    def set_sound(self, delay):
        self.sound.stop()
        self.sound.play(loops=-1, maxtime=long(delay) * ms_per_frame)

    def set_delay(self, delay):
        self.delay = self.last + long(delay) * cycles_per_frame

    def get_delay(self):
        diff = self.delay - self.last
        if diff <= 0:
            return uint8_t(0)
        diff = diff / cycles_per_frame
        return uint8_t(min(diff, 255))


def create_sound():
    pygame.mixer.pre_init(channels=1)
    fq, fmt, ch = pygame.mixer.get_init()

    period = fq / sound_fq
    amplitude = int((2 ** (abs(fmt) - 1) - 1) * sound_amp)

    samples = [int(sin(pi * x / period) * amplitude) for x in xrange(period)]

    return pygame.mixer.Sound(array("h", samples))


def main(argv):
    pygame.init()
    window = pygame.display.set_mode((640, 320))

    screen = Screen()

    proc = subprocess.Popen(['./chip8-c'], executable='./chip8-c.exe',
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    pipe = Stdio(proc.stdout, proc.stdin)
    chip8 = Chip8_Rpc(pipe, Io_Impl())
    chip8.initialize(argv[1])

    # ticks = pygame.time.get_ticks()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                chip8.quit()
                pygame.quit()
                return 0

        if not chip8.paused:
            # print "game loop took %d ms" % (pygame.time.get_ticks() - ticks)
            chip8.run(cycles_per_frame)
            # ticks = pygame.time.get_ticks()
            screen.update(chip8.display)

            im = pygame.image.frombuffer(screen.im.tobytes(), screen.im.size, "RGBA")
            pygame.transform.scale(im, window.get_size(), window)
            pygame.display.flip()


if __name__ == '__main__':
    import sys

    errorstream.stream = sys.stdout
    main(sys.argv)
