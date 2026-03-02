"""GameRenderer — clean minimal pygame UI for pysuika."""
from __future__ import annotations

import importlib.resources
import io

import numpy as np
import pygame
import pymunk

from pysuika.config import config
from pysuika.game.engine import GameEngine
from pysuika.physics.particle import Particle

# ── Palette ───────────────────────────────────────────────────────────────────
_BG         = (245, 240, 230)   # warm cream
_PANEL_BG   = (230, 222, 208)   # slightly darker panel
_WALL       = (90,  70,  50)    # dark brown container
_DROP_LINE  = (180, 160, 140)   # muted guide line
_TEXT_DARK  = (40,  30,  20)
_TEXT_MID   = (120, 100,  80)
_GAMEOVER_OVERLAY = (0, 0, 0, 160)   # semi-transparent


def _load_fruit(name: str) -> pygame.Surface:
    pkg = importlib.resources.files("pysuika.assets")
    data = (pkg / name).read_bytes()
    return pygame.image.load(io.BytesIO(data))


class GameRenderer:
    """Minimal pygame renderer attached to a GameEngine.

    No external background or cloud images — everything is drawn with
    pygame primitives except for the fruit sprites themselves.
    """

    # Left info panel width (score + next-fruit preview)
    _PANEL_W = config.pad.left - 10

    def __init__(self, engine: GameEngine, title: str = "PySuika") -> None:
        self.engine = engine
        pygame.init()
        self._screen = pygame.display.set_mode(
            (config.screen.width, config.screen.height)
        )
        pygame.display.set_caption(title)
        self._clock = pygame.time.Clock()

        pygame.font.init()
        self._font_lg  = pygame.font.SysFont("sans-serif", 36, bold=True)
        self._font_md  = pygame.font.SysFont("sans-serif", 22)
        self._font_sm  = pygame.font.SysFont("sans-serif", 16)
        self._font_xl  = pygame.font.SysFont("sans-serif", 72, bold=True)

        # Fruit sprites loaded lazily
        self._fruit_imgs: dict[int, pygame.Surface] = {}

    # ── Public ────────────────────────────────────────────────────────────────

    def render(self) -> None:
        self._ensure_assets()
        self._screen.fill(_BG)
        self._draw_container()
        self._draw_drop_indicator()
        self._draw_particles()
        self._draw_panel()
        if self.engine.is_game_over:
            self._draw_game_over()
        pygame.display.update()
        self._clock.tick(config.screen.fps)

    def quit(self) -> None:
        pygame.quit()

    # ── Drawing helpers ───────────────────────────────────────────────────────

    def _draw_container(self) -> None:
        """Draw the three walls of the play area as thick rounded lines."""
        w = 6
        c = _WALL
        tl = config.top_left
        bl = config.bot_left
        br = config.bot_right
        tr = config.top_right
        pygame.draw.line(self._screen, c, tl, bl, w)   # left wall
        pygame.draw.line(self._screen, c, bl, br, w)   # floor
        pygame.draw.line(self._screen, c, br, tr, w)   # right wall

        # Kill-line: faint dashed horizontal
        killy = config.pad.killy
        for x in range(config.pad.left, config.pad.right, 12):
            pygame.draw.line(
                self._screen, (210, 190, 170), (x, killy), (x + 6, killy), 1
            )

    def _draw_drop_indicator(self) -> None:
        """Vertical guide line + downward arrow + current fruit sprite."""
        pre = self.engine.next_particle
        if pre is None:
            return
        x = int(pre.x)

        # Dashed vertical line from top of screen to kill line
        for y in range(8, config.pad.killy, 14):
            pygame.draw.line(
                self._screen, _DROP_LINE, (x, y), (x, min(y + 7, config.pad.killy)), 1
            )

        # Small downward-pointing triangle at the top
        tip = (x, config.pad.top - pre.radius - 6)
        tri = [
            (x - 8, tip[1] - 14),
            (x + 8, tip[1] - 14),
            tip,
        ]
        pygame.draw.polygon(self._screen, _WALL, tri)

        # Current fruit sprite centered at drop position
        spr = self._fruit_imgs[pre.n]
        w, h = spr.get_size()
        a, b = config[pre.n, "offset"]
        self._screen.blit(spr, (x - w / 2 + a, config.pad.top - h / 2 + b))

    def _draw_particles(self) -> None:
        if self.engine.space is None:
            return
        for shape in self.engine.space.shapes:
            if isinstance(shape, Particle) and shape.alive:
                spr = self._fruit_imgs[shape.n]
                ang = shape.body.angle
                rotated = pygame.transform.rotate(spr.copy(), -ang * 180 / np.pi)
                x, y = shape.body.position
                rw, rh = rotated.get_size()
                mat = np.array([
                    [np.cos(ang), -np.sin(ang)],
                    [np.sin(ang),  np.cos(ang)],
                ])
                a, b = mat @ np.array(config[shape.n, "offset"])
                self._screen.blit(rotated, (x - rw / 2 + a, y - rh / 2 + b))

    def _draw_panel(self) -> None:
        """Left info panel: score + next-fruit preview."""
        panel_rect = pygame.Rect(0, 0, self._PANEL_W, config.screen.height)
        pygame.draw.rect(self._screen, _PANEL_BG, panel_rect)
        pygame.draw.line(
            self._screen, _WALL,
            (self._PANEL_W, 0), (self._PANEL_W, config.screen.height), 3
        )

        pad = 18
        y = 24

        # Score
        lbl = self._font_sm.render("SCORE", True, _TEXT_MID)
        self._screen.blit(lbl, (pad, y))
        y += lbl.get_height() + 4
        score_lbl = self._font_lg.render(str(self.engine.score), True, _TEXT_DARK)
        self._screen.blit(score_lbl, (pad, y))
        y += score_lbl.get_height() + 28

        # Divider
        pygame.draw.line(
            self._screen, _DROP_LINE,
            (pad, y), (self._PANEL_W - pad, y), 1
        )
        y += 16

        # Next fruit
        lbl = self._font_sm.render("NEXT", True, _TEXT_MID)
        self._screen.blit(lbl, (pad, y))
        y += lbl.get_height() + 10

        pre = self.engine.next_particle
        if pre is not None:
            spr = self._fruit_imgs[pre.n]
            # Scale down if the sprite is too wide for the panel
            max_w = self._PANEL_W - 2 * pad
            scale = min(1.0, max_w / spr.get_width())
            if scale < 1.0:
                nw = int(spr.get_width() * scale)
                nh = int(spr.get_height() * scale)
                spr = pygame.transform.scale(spr, (nw, nh))
            cx = self._PANEL_W // 2
            self._screen.blit(spr, (cx - spr.get_width() // 2, y))
            y += spr.get_height() + 10

            name = config.fruit_names[pre.n].capitalize()
            name_lbl = self._font_sm.render(name, True, _TEXT_MID)
            self._screen.blit(name_lbl, (cx - name_lbl.get_width() // 2, y))

    def _draw_game_over(self) -> None:
        # Semi-transparent dark overlay over the play area
        overlay = pygame.Surface(
            (config.pad.right - config.pad.left, config.screen.height),
            pygame.SRCALPHA,
        )
        overlay.fill(_GAMEOVER_OVERLAY)
        self._screen.blit(overlay, (config.pad.left, 0))

        lbl = self._font_xl.render("GAME OVER", True, (255, 255, 255))
        rect = lbl.get_rect(
            center=(
                (config.pad.left + config.pad.right) // 2,
                config.screen.height // 2 - 20,
            )
        )
        self._screen.blit(lbl, rect)

        score_lbl = self._font_md.render(
            f"Score: {self.engine.score}", True, (220, 210, 200)
        )
        srect = score_lbl.get_rect(center=(rect.centerx, rect.bottom + 20))
        self._screen.blit(score_lbl, srect)

    # ── Assets ────────────────────────────────────────────────────────────────

    def _ensure_assets(self) -> None:
        for n, name in enumerate(config.fruit_names):
            if n not in self._fruit_imgs:
                raw = _load_fruit(f"{name}.png")
                size = config[n, "size"]
                self._fruit_imgs[n] = pygame.transform.scale(raw, size)
