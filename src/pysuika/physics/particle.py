"""Physics particle — a fruit in the pymunk simulation."""
from __future__ import annotations

import numpy as np
import pymunk

from pysuika.config import config


class Particle(pymunk.Circle):
    """A fruit body in the pymunk space.

    Parameters
    ----------
    pos:   (x, y) starting position in pixels
    n:     fruit type index (0–10); wraps modulo 11
    space: the pymunk Space to add this particle to
    """

    def __init__(self, pos: tuple[float, float], n: int, space: pymunk.Space) -> None:
        self.n = n % 11
        super().__init__(
            body=pymunk.Body(body_type=pymunk.Body.DYNAMIC),
            radius=config[self.n, "radius"],
        )
        self.body.position = tuple(pos)
        self.density = config.physics.density
        self.elasticity = config.physics.elasticity
        self.collision_type = CollisionTypes.PARTICLE
        self.friction = config.physics.fruit_friction
        self.has_collided: bool = False
        self.alive: bool = True
        space.add(self.body, self)

    def kill(self, space: pymunk.Space) -> None:
        space.remove(self.body, self)
        self.alive = False

    @property
    def pos(self) -> np.ndarray:
        return np.array(self.body.position)

    @property
    def radius(self) -> float:  # type: ignore[override]
        return config[self.n, "radius"]


class CollisionTypes:
    PARTICLE = 1
    WALL = 2
