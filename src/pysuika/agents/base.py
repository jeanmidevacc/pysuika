"""Base agent contract for pysuika."""
from __future__ import annotations

from abc import ABC, abstractmethod

from pysuika.game.state import GameState


class BaseAgent(ABC):
    """Abstract base class for Suika-playing agents.

    Subclass this and implement :meth:`get_action` to create your own agent.

    Example
    -------
    .. code-block:: python

        from pysuika.agents import BaseAgent
        from pysuika.game import GameState

        class MyAgent(BaseAgent):
            def get_action(self, state: GameState) -> int:
                # Drop in the centre every time
                return 640
    """

    @abstractmethod
    def get_action(self, state: GameState) -> int | float:
        """Choose a horizontal drop position given the current game state.

        Parameters
        ----------
        state: current :class:`~pysuika.game.state.GameState` observation.

        Returns
        -------
        x coordinate (pixels) where the next fruit should be dropped.
        Must be within the valid pad range defined in the configuration.
        """
        ...
