"""GameEngine — headless Suika game loop backed by pymunk physics."""
from __future__ import annotations

import numpy as np
import pymunk

from pysuika.config import config
from pysuika.game.actions import ActionResult
from pysuika.game.state import GameState
from pysuika.physics.collision import collide
from pysuika.physics.particle import CollisionTypes, Particle
from pysuika.physics.preparticle import PreParticle
from pysuika.physics.wall import Wall


class GameEngine:
    """Headless Suika game engine.

    Runs the pymunk physics simulation without any pygame dependency.
    Suitable for agent training loops and scripted scenarios.

    Parameters
    ----------
    seed:             RNG seed for reproducible fruit sequences.
    steps_per_action: number of physics steps to advance after each drop
                      (default 240 ≈ 2 seconds at 120 fps).
    fruit_sequence:   optional list of fruit type indices (0–10) to use
                      in order instead of the random generator.
    """

    def __init__(
        self,
        seed: int | None = None,
        steps_per_action: int = 240,
        fruit_sequence: list[int] | None = None,
    ) -> None:
        self._rng = np.random.default_rng(seed)
        self._steps_per_action = steps_per_action
        self._fruit_sequence = fruit_sequence
        self._sequence_idx: int = 0

        self._space: pymunk.Space | None = None
        self._walls: list[Wall] = []
        self._next_particle: PreParticle | None = None
        self._score: int = 0
        self._step: int = 0
        self._game_over: bool = False
        self._handler_data: dict = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self) -> GameState:
        """Initialise (or re-initialise) the physics world and return the
        first observation."""
        self._sequence_idx = 0
        self._score = 0
        self._step = 0
        self._game_over = False

        # Build pymunk space
        self._space = pymunk.Space()
        self._space.gravity = (0, config.physics.gravity)
        self._space.damping = config.physics.damping
        self._space.collision_bias = config.physics.bias

        # Walls
        self._walls = [
            Wall(config.top_left, config.bot_left, self._space),
            Wall(config.bot_left, config.bot_right, self._space),
            Wall(config.bot_right, config.top_right, self._space),
        ]

        # Collision handler (pymunk 7+ API)
        self._handler_data = {"score": 0}
        self._space.on_collision(
            CollisionTypes.PARTICLE,
            CollisionTypes.PARTICLE,
            begin=collide,
            data=self._handler_data,
        )

        # First fruit
        self._next_particle = self._new_pre_particle()

        return self._build_state()

    def step(self, x: int | float) -> ActionResult:
        """Drop the current fruit at position ``x`` and advance physics.

        Parameters
        ----------
        x: horizontal drop position in pixels (will be clamped to valid range).

        Returns
        -------
        ActionResult with the new GameState, reward (score delta), and done flag.
        """
        if self._space is None:
            raise RuntimeError("Call reset() before step().")
        if self._game_over:
            state = self._build_state()
            return ActionResult(state=state, reward=0.0, done=True)

        score_before = self._handler_data["score"]

        # Drop the fruit
        self._next_particle.set_x(float(x))
        self._next_particle.release(self._space)
        self._step += 1

        # Prepare next fruit
        self._next_particle = self._new_pre_particle()

        # Advance physics
        dt = 1.0 / config.screen.fps
        for _ in range(self._steps_per_action):
            self._space.step(dt)
            if self._check_game_over():
                self._game_over = True
                break

        self._score = self._handler_data["score"]
        reward = float(self._score - score_before)
        state = self._build_state()
        return ActionResult(state=state, reward=reward, done=self._game_over)

    @property
    def state(self) -> GameState:
        """Current game state (read-only peek, does not advance the game)."""
        if self._space is None:
            raise RuntimeError("Call reset() first.")
        return self._build_state()

    @property
    def is_game_over(self) -> bool:
        return self._game_over

    @property
    def score(self) -> int:
        return self._score

    @property
    def space(self) -> pymunk.Space | None:
        """Expose the pymunk Space for renderer access."""
        return self._space

    @property
    def next_particle(self) -> PreParticle | None:
        """The fruit currently held at the drop position."""
        return self._next_particle

    # ------------------------------------------------------------------
    # Interactive / frame-by-frame API
    # ------------------------------------------------------------------

    def drop_fruit(self, x: int | float) -> None:
        """Drop the current fruit at position ``x`` without advancing physics.

        Use this together with :meth:`step_frame` for interactive / real-time
        rendering loops where you want to control the render tick rate yourself.
        """
        if self._space is None:
            raise RuntimeError("Call reset() before drop_fruit().")
        if self._game_over:
            return
        self._next_particle.set_x(float(x))
        self._next_particle.release(self._space)
        self._step += 1
        self._next_particle = self._new_pre_particle()

    def step_frame(self) -> bool:
        """Advance physics by exactly one frame (1 / fps seconds).

        Returns True if the game ended during this frame, False otherwise.
        Use in interactive render loops together with :meth:`drop_fruit`.
        """
        if self._space is None:
            raise RuntimeError("Call reset() first.")
        if self._game_over:
            return True
        self._space.step(1.0 / config.screen.fps)
        self._score = self._handler_data["score"]
        if self._check_game_over():
            self._game_over = True
        return self._game_over

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _new_pre_particle(self) -> PreParticle:
        if self._fruit_sequence is not None:
            if self._sequence_idx < len(self._fruit_sequence):
                n = self._fruit_sequence[self._sequence_idx]
                self._sequence_idx += 1
            else:
                # Sequence exhausted — fall back to random
                n = int(self._rng.integers(0, 5))
        else:
            n = None  # PreParticle will pick randomly
        return PreParticle(n=n, rng=self._rng)

    def _check_game_over(self) -> bool:
        """Return True if any alive particle has crossed above the kill line
        after having collided with a different type (standard Suika rules)."""
        killy = config.pad.killy
        for shape in self._space.shapes:
            if isinstance(shape, Particle) and shape.alive:
                if shape.body.position.y < killy and shape.has_collided:
                    return True
        return False

    def _build_state(self) -> GameState:
        particles = []
        if self._space is not None:
            for shape in self._space.shapes:
                if isinstance(shape, Particle) and shape.alive:
                    particles.append({
                        "x": float(shape.body.position.x),
                        "y": float(shape.body.position.y),
                        "n": shape.n,
                        "radius": shape.radius,
                    })
        return GameState(
            particles=particles,
            next_fruit_type=self._next_particle.n if self._next_particle else 0,
            score=self._score,
            step=self._step,
            is_game_over=self._game_over,
        )
