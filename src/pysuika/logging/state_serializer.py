"""Serialise a GameState into a plain dict suitable for JSON logging."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pysuika.game.state import GameState

from pysuika.config import config


def serialize_state(state: "GameState") -> dict:
    """Convert a :class:`~pysuika.game.state.GameState` to a JSON-safe dict.

    The returned structure mirrors what an agent sees, making log files
    directly usable for offline analysis or replay.

    Fields
    ------
    step, score, is_game_over:
        Top-level scalars from the state.
    next_fruit:
        Index and name of the fruit about to be dropped.
    particles:
        List of dicts with keys ``x``, ``y``, ``n``, ``name``, ``radius``.
    """
    return {
        "step": state.step,
        "score": state.score,
        "is_game_over": state.is_game_over,
        "next_fruit": {
            "n": state.next_fruit_type,
            "name": config.fruit_names[state.next_fruit_type],
        },
        "particles": [
            {
                "x": round(p["x"], 2),
                "y": round(p["y"], 2),
                "n": p["n"],
                "name": config.fruit_names[p["n"]],
                "radius": p["radius"],
            }
            for p in state.particles
        ],
    }
