"""ActionResult — the outcome returned by GameEngine.step()."""
from __future__ import annotations

from dataclasses import dataclass

from pysuika.game.state import GameState


@dataclass
class ActionResult:
    """Result of a single game step (one fruit drop + physics advancement).

    Attributes
    ----------
    state:       the new GameState after the action.
    reward:      score gained during this step (useful for RL).
    done:        True if the game ended during this step.
    """

    state: GameState
    reward: float
    done: bool
