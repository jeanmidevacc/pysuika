"""PreParticle — a fruit waiting at the top of the board before being dropped."""
from __future__ import annotations

import numpy as np
import pymunk

from pysuika.config import config
from pysuika.physics.particle import Particle


class PreParticle:
    """A fruit held at the drop line, not yet in the physics simulation.

    Parameters
    ----------
    n:  fruit type index (0–10); if None a random type 0–4 is chosen
    rng: numpy random Generator for reproducibility
    """

    def __init__(
        self,
        n: int | None = None,
        rng: np.random.Generator | None = None,
    ) -> None:
        _rng = rng if rng is not None else np.random.default_rng()
        self.n: int = int(_rng.integers(0, 5)) if n is None else n % 11
        self.x: float = float(config.screen.width // 2)

    @property
    def radius(self) -> float:
        return config[self.n, "radius"]

    def set_x(self, x: float) -> None:
        left_lim = config.pad.left + self.radius
        right_lim = config.pad.right - self.radius
        self.x = float(np.clip(x, left_lim, right_lim))

    def release(self, space: pymunk.Space) -> Particle:
        return Particle((self.x, config.pad.top), self.n, space)
