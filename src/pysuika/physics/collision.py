"""Collision detection and resolution for same-type fruit merging."""
from __future__ import annotations

import numpy as np
import pymunk

from pysuika.config import config
from pysuika.physics.particle import Particle


def resolve_collision(
    p1: Particle,
    p2: Particle,
    space: pymunk.Space,
) -> Particle:
    """Merge two same-type particles into one of the next type.

    The merged particle appears at the midpoint of p1 and p2, and an impulse
    is applied outward to nearby particles (the classic Suika "explosion").
    """
    p1.kill(space)
    p2.kill(space)
    mid = np.mean([p1.pos, p2.pos], axis=0)
    merged = Particle(mid, p1.n + 1, space)

    for shape in space.shapes:
        if isinstance(shape, Particle) and shape.alive:
            vec = shape.pos - merged.pos
            dist = float(np.linalg.norm(vec))
            if dist < merged.radius + shape.radius and dist > 0:
                impulse = config.physics.impulse * vec / (dist ** 2)
                shape.body.apply_impulse_at_local_point(tuple(impulse))

    return merged


def collide(arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> None:
    """Pymunk collision begin handler for PARTICLE–PARTICLE contacts.

    Registered via ``space.on_collision(..., begin=collide, data=...)``.
    ``data`` must contain a ``"score"`` key (int).

    Uses ``arbiter.process_collision`` to suppress contacts when particles
    merge (pymunk 7+ API).
    """
    p1, p2 = arbiter.shapes
    if not (isinstance(p1, Particle) and isinstance(p2, Particle)):
        return
    if not (p1.alive and p2.alive):
        arbiter.process_collision = False
        return

    same_type = p1.n == p2.n
    p1.has_collided = not same_type
    p2.has_collided = not same_type

    if same_type:
        resolve_collision(p1, p2, space)
        data["score"] += config[p1.n, "points"]
        arbiter.process_collision = False  # shapes were removed; suppress contact
