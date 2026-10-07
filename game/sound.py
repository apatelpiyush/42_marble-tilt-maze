import array
import math
import pygame


class SoundManager:
    BOUNCE_COOLDOWN_MS = 120

    def __init__(self):
        self.enabled = False
        self.last_bounce_ms = 0
        self.bounce = None
        self.win = None
        self.timeout = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            settings = pygame.mixer.get_init()
            if settings is None or settings[1] != -16:
                return
            self.rate, _, self.channels = settings

            self.bounce = self._build([(220, 70)], 0.6)
            self.win = self._build([(523, 120), (659, 120), (784, 240)], 0.5)
            self.timeout = self._build([(392, 180), (330, 180), (262, 360)], 0.5)
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def _build(self, notes, volume):
        samples = array.array("h")
        for frequency, duration_ms in notes:
            count = int(self.rate * duration_ms / 1000)
            for i in range(count):
                fade = 1 - i / count
                wave = math.sin(2 * math.pi * frequency * i / self.rate)
                value = int(32767 * volume * fade * wave)
                for _ in range(self.channels):
                    samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play_bounce(self, strength):
        if not self.enabled:
            return
        now = pygame.time.get_ticks()
        if now - self.last_bounce_ms < self.BOUNCE_COOLDOWN_MS:
            return
        self.last_bounce_ms = now
        self.bounce.set_volume(max(0.2, min(1.0, strength / 8)))
        self.bounce.play()

    def play_win(self):
        if self.enabled:
            self.win.play()

    def play_timeout(self):
        if self.enabled:
            self.timeout.play()
