"""GameState — a pure-data snapshot of the Suika game at a given moment."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GameState:
    """Immutable snapshot of the game that agents receive as observations.

    Attributes
    ----------
    particles:       list of dicts with keys ``x``, ``y``, ``n``, ``radius``
                     for every living particle in the simulation.
    next_fruit_type: type index (0–10) of the fruit that will be dropped next.
    score:           cumulative score so far.
    step:            number of fruits dropped so far.
    is_game_over:    True when a fruit has breached the kill line.
    """

    particles: list[dict] = field(default_factory=list)
    next_fruit_type: int = 0
    score: int = 0
    step: int = 0
    is_game_over: bool = False

    def to_dict(self) -> dict:
        return {
            "particles": self.particles,
            "next_fruit_type": self.next_fruit_type,
            "score": self.score,
            "step": self.step,
            "is_game_over": self.is_game_over,
        }
