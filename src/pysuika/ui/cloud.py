"""Cloud UI element — the "dispenser" that shows the current and next fruit."""
from __future__ import annotations

import importlib.resources

import numpy as np
import pygame

from pysuika.config import config
from pysuika.physics.preparticle import PreParticle


def _load_asset(name: str) -> pygame.Surface:
    """Load a PNG from the bundled assets directory."""
    pkg = importlib.resources.files("pysuika.assets")
    data = (pkg / name).read_bytes()
    import io
    return pygame.image.load(io.BytesIO(data))


class Cloud:
    """Manages the current and next :class:`PreParticle` for on-screen display.

    Parameters
    ----------
    rng: numpy random Generator shared with the game engine for consistent
         fruit generation.
    """

    def __init__(self, rng: np.random.Generator | None = None) -> None:
        self._rng = rng or np.random.default_rng()
        self.curr = PreParticle(rng=self._rng)
        self.next = PreParticle(rng=self._rng)
        self._cloud_img: pygame.Surface | None = None
        self._fruit_imgs: dict[int, pygame.Surface] = {}

    # ------------------------------------------------------------------
    # Lazy asset loading (called on first draw, after pygame.init())
    # ------------------------------------------------------------------

    def _ensure_assets(self) -> None:
        if self._cloud_img is None:
            self._cloud_img = _load_asset("cloud.png")
        for n, name in enumerate(config.fruit_names):
            if n not in self._fruit_imgs:
                raw = _load_asset(f"{name}.png")
                size = config[n, "size"]
                self._fruit_imgs[n] = pygame.transform.scale(raw, size)

    def _fruit_surface(self, pre: PreParticle) -> pygame.Surface:
        return self._fruit_imgs[pre.n]

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, wait: int) -> None:
        """Draw cloud image and current/next fruit sprites."""
        self._ensure_assets()
        assert self._cloud_img is not None

        # Current fruit (below cloud)
        screen.blit(self._cloud_img, (self.curr.x, 8))
        if not wait:
            pygame.draw.line(
                screen,
                color=config.screen.white,
                start_pos=(self.curr.x, config.pad.line_top),
                end_pos=(self.curr.x, config.pad.line_bot),
                width=2,
            )
            spr = self._fruit_surface(self.curr)
            screen.blit(spr, self._sprite_pos(self.curr, (self.curr.x, config.pad.top)))

        # Next fruit (preview position)
        spr = self._fruit_surface(self.next)
        screen.blit(spr, self._sprite_pos(self.next, (1084, 185)))

    def release(self) -> None:
        """Advance to the next fruit (called after the engine drops the current one)."""
        self.curr = self.next
        self.next = PreParticle(rng=self._rng)

    def sync(self, pre: PreParticle) -> None:
        """Sync the cloud's current fruit position with the engine's PreParticle."""
        self.curr.n = pre.n
        self.curr.x = pre.x

    # ------------------------------------------------------------------

    def _sprite_pos(
        self, pre: PreParticle, pos: tuple[float, float]
    ) -> tuple[float, float]:
        x, y = pos
        spr = self._fruit_surface(pre)
        w, h = spr.get_size()
        a, b = config[pre.n, "offset"]
        return x - w / 2 + a, y - h / 2 + b
