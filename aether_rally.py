#!/usr/bin/env python3
"""Aether Rally — neon volley arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/AETHER_RALLY_ElbowOS.mp4")
TITLE = "AETHER RALLY"
HANDLE = "x.com/ElbowOS"

BG = (4, 12, 18)
COURT = (8, 28, 34)
LIME = (180, 255, 70)
CYAN = (40, 240, 220)
ORANGE = (255, 140, 40)
MAG = (255, 70, 140)
WHITE = (240, 255, 250)
NET = (30, 90, 80)


def clamp(v, a, b):
    return a if v < a else b if v > b else v


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 72, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 42, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 28)
        self.clock = pygame.time.Clock()
        self.left, self.right = 90, W - 90
        self.top, self.bot = 280, H - 220
        self.net_y = (self.top + self.bot) // 2
        self.pw, self.ph = 220, 28
        self.reset(full=True)
        self.sparks = []
        self.orbs = [
            [random.randint(self.left, self.right), random.randint(self.top, self.bot),
             random.uniform(0.4, 1.4), random.choice((CYAN, LIME, ORANGE, MAG))]
            for _ in range(18)
        ]
        self.flash = 0
        self.t = 0

    def reset(self, full=False):
        mid = (self.left + self.right) // 2
        self.px = mid
        self.ax = mid
        self.p_target = mid
        self.ball = [mid + random.randint(-80, 80), self.net_y - 40,
                     random.choice((-11, 11)), random.uniform(-16, -10)]
        if full:
            self.score_p = 0
            self.score_a = 0
            self.rally = 0
            self.best = 0

    def autoplay(self):
        bx, by, vx, vy = self.ball
        if vy > 0:
            frames = max(1.0, (self.bot - 40 - by) / max(vy, 0.1))
            pred = bx + vx * frames
            while pred < self.left + 20 or pred > self.right - 20:
                if pred < self.left + 20:
                    pred = 2 * (self.left + 20) - pred
                else:
                    pred = 2 * (self.right - 20) - pred
            self.p_target = pred + math.sin(self.t * 0.2) * 18
        else:
            self.p_target = (self.left + self.right) / 2

    def handle_human(self, keys):
        spd = 18
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.p_target = self.px - spd * 4
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.p_target = self.px + spd * 4
        if keys[pygame.K_r]:
            self.reset(full=True)

    def bounce_wall(self):
        bx, by, vx, vy = self.ball
        if bx < self.left + 18:
            self.ball[0] = self.left + 18
            self.ball[2] = abs(vx) * 1.02
            self.burst(bx, by, CYAN)
        elif bx > self.right - 18:
            self.ball[0] = self.right - 18
            self.ball[2] = -abs(vx) * 1.02
            self.burst(bx, by, CYAN)

    def hit_paddle(self, x, y, incoming_sign, color):
        bx, by, vx, vy = self.ball
        if abs(by - y) < 26 and abs(bx - x) < self.pw * 0.55:
            off = (bx - x) / (self.pw * 0.5)
            self.ball[1] = y - incoming_sign * 26
            self.ball[3] = -incoming_sign * (15 + random.uniform(0, 3) + min(self.rally, 8) * 0.35)
            self.ball[2] = clamp(vx * 0.35 + off * 12, -16, 16)
            self.rally += 1
            self.best = max(self.best, self.rally)
            if incoming_sign > 0:
                self.score_p += 10 + self.rally * 2
            else:
                self.score_a += 6
            self.burst(bx, by, color)
            self.flash = 8
            return True
        return False

    def burst(self, x, y, col):
        for _ in range(14):
            ang = random.uniform(0, 6.28)
            sp = random.uniform(2, 9)
            self.sparks.append([x, y, math.cos(ang) * sp, math.sin(ang) * sp, 22, col])

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        self.px += (self.p_target - self.px) * 0.28
        self.px = clamp(self.px, self.left + self.pw / 2, self.right - self.pw / 2)
        bx, by, vx, vy = self.ball
        aim = bx + vx * 6 + math.sin(self.t * 0.13) * 30
        self.ax += (aim - self.ax) * 0.16
        self.ax = clamp(self.ax, self.left + self.pw / 2, self.right - self.pw / 2)
        vy += 0.42
        vx *= 0.999
        self.ball[0] += vx
        self.ball[1] += vy
        self.ball[2], self.ball[3] = vx, vy
        self.bounce_wall()
        self.hit_paddle(self.px, self.bot - 8, 1, LIME)
        self.hit_paddle(self.ax, self.top + 8, -1, ORANGE)
        if self.ball[1] > self.bot + 70:
            self.score_a += 1
            self.rally = 0
            self.burst(self.ball[0], self.bot, MAG)
            self.reset()
        elif self.ball[1] < self.top - 70:
            self.score_p += 25
            self.rally = 0
            self.burst(self.ball[0], self.top, LIME)
            self.reset()
        for s in self.sparks:
            s[0] += s[2]
            s[1] += s[3]
            s[3] += 0.15
            s[4] -= 1
        self.sparks = [s for s in self.sparks if s[4] > 0]
        for o in self.orbs:
            o[1] -= o[2]
            if o[1] < self.top:
                o[1] = self.bot
                o[0] = random.randint(self.left, self.right)

    def draw(self, surf):
        surf.fill(BG)
        for o in self.orbs:
            pygame.draw.circle(surf, o[3], (int(o[0]), int(o[1])), 3)
        court = pygame.Rect(self.left - 24, self.top - 40, self.right - self.left + 48, self.bot - self.top + 80)
        pygame.draw.rect(surf, COURT, court, border_radius=28)
        pygame.draw.rect(surf, CYAN, court, 3, border_radius=28)
        for i in range(1, 6):
            y = self.top + i * (self.bot - self.top) // 6
            pygame.draw.line(surf, (20, 60, 58), (self.left, y), (self.right, y), 2)
        pygame.draw.line(surf, NET, (self.left, self.net_y), (self.right, self.net_y), 8)
        pygame.draw.line(surf, LIME, (self.left, self.net_y - 4), (self.right, self.net_y - 4), 2)

        def paddle(x, y, col):
            r = pygame.Rect(int(x - self.pw / 2), int(y - self.ph / 2), self.pw, self.ph)
            glow = r.inflate(18, 16)
            pygame.draw.rect(surf, tuple(c // 4 for c in col), glow, border_radius=16)
            pygame.draw.rect(surf, col, r, border_radius=12)
            pygame.draw.rect(surf, WHITE, r, 2, border_radius=12)
        paddle(self.px, self.bot - 8, LIME)
        paddle(self.ax, self.top + 8, ORANGE)
        bx, by = int(self.ball[0]), int(self.ball[1])
        for k in range(6, 0, -1):
            pygame.draw.circle(surf, (20, 80, 70), (bx - int(self.ball[2] * k * 0.35),
                                                    by - int(self.ball[3] * k * 0.35)), 10 - k)
        pygame.draw.circle(surf, CYAN, (bx, by), 16)
        pygame.draw.circle(surf, WHITE, (bx - 4, by - 5), 6)
        if self.flash:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((180, 255, 200, 18))
            surf.blit(overlay, (0, 0))
        for s in self.sparks:
            pygame.draw.circle(surf, s[5], (int(s[0]), int(s[1])), max(1, s[4] // 5))
        title = self.font_lg.render(TITLE, True, LIME)
        surf.blit(title, title.get_rect(center=(W // 2, 88)))
        sub = self.font_sm.render(HANDLE, True, CYAN)
        surf.blit(sub, sub.get_rect(center=(W // 2, 148)))
        you = self.font.render(f"YOU  {self.score_p}", True, LIME)
        cpu = self.font.render(f"CPU  {self.score_a}", True, ORANGE)
        surf.blit(you, (self.left, H - 150))
        surf.blit(cpu, cpu.get_rect(topright=(self.right, H - 150)))
        rally = self.font_sm.render(f"RALLY {self.rally}   BEST {self.best}", True, WHITE)
        surf.blit(rally, rally.get_rect(center=(W // 2, H - 90)))
        bar = pygame.Rect(80, H - 48, W - 160, 10)
        pygame.draw.rect(surf, (20, 40, 38), bar, border_radius=6)
        fill = bar.copy()
        fill.width = int(bar.width * min(1.0, self.rally / 12))
        pygame.draw.rect(surf, MAG if self.rally > 7 else LIME, fill, border_radius=6)

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    running = False
            keys = pygame.key.get_pressed()
            self.handle_human(keys)
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
