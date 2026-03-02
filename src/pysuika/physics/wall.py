"""Static wall segment in the pymunk space."""
from __future__ import annotations

import pymunk

from pysuika.config import config
from pysuika.physics.particle import CollisionTypes


class Wall(pymunk.Segment):
    """An immovable boundary wall.

    Parameters
    ----------
    a, b:  endpoints in pixel coordinates
    space: the pymunk Space to add this wall to
    """

    def __init__(
        self,
        a: tuple[int, int],
        b: tuple[int, int],
        space: pymunk.Space,
    ) -> None:
        super().__init__(
            body=pymunk.Body(body_type=pymunk.Body.STATIC),
            a=a,
            b=b,
            radius=2,
        )
        self.collision_type = CollisionTypes.WALL
        self.friction = config.physics.wall_friction
        space.add(self.body, self)
