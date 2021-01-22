import subprocess
from time import sleep

import pygame
from PIL import Image, ImageEnhance

from emulator.chip8 import Chip8_Rpc, __version__
from emulator.error import errorstream
from emulator.io.message import C_Load, C_Die, M_Version
from emulator.io.stdio import Stdio
from emulator.types import uint64_t


class Screen:
    def __init__(self):
        self.im = Image.new("RGBA", (1, 1))

    def update(self, display):
        size = display.width, display.height
        if self.im.size != size:
            self.im = Image.new("RGBA", size)
        self.im = ImageEnhance.Brightness(self.im).enhance(0.95)
        for y in xrange(display.height):
            x = 0
            j = uint64_t(1) << (display.width - 1)
            while j:
                if j & display.data[y]:
                    self.im.putpixel((x, y), (255, 255, 255))
                j >>= 1
                x += 1


def main(argv):
    speed = 100

    proc = subprocess.Popen(['./chip8-c'], executable='./chip8-c.exe',
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    io = Stdio(proc.stdout, proc.stdin)

    vers = io.get()
    assert isinstance(vers, M_Version)
    assert vers.version == __version__

    chip8 = Chip8_Rpc(io)
    chip8._cmd(C_Load(argv[1]))

    screen = Screen()
    frame = 0
    frametimes = [0] * 60

    pygame.init()
    window = pygame.display.set_mode((640, 320))
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                chip8._cmd(C_Die())

        chip8.run(speed / 60)
        screen.update(chip8.display)

        im = pygame.image.frombuffer(screen.im.tobytes(), screen.im.size, "RGBA")
        pygame.transform.scale(im, window.get_size(), window)
        pygame.display.flip()

        frametimes[frame % 60] = clock.tick(60)
        frame += 1
        if (frame % 60) == 0:
            print "frametime (min, max, avg):", min(frametimes), max(frametimes), sum(frametimes) / 60.0
    pygame.quit()


if __name__ == '__main__':
    import sys

    errorstream.stream = sys.stdout
    main(sys.argv)
