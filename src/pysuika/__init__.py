"""pysuika — a Python package for the Suika (watermelon-drop) game.

Quick start
-----------
Headless agent loop::

    from pysuika import GameEngine, GameState, BaseAgent

    class MyAgent(BaseAgent):
        def get_action(self, state: GameState) -> int:
            return 640  # always drop in the centre

    engine = GameEngine(seed=42)
    state = engine.reset()
    while not state.is_game_over:
        result = engine.step(MyAgent().get_action(state))
        state = result.state
    print(f"Final score: {state.score}")

Interactive play::

    python -m pysuika
"""
from pysuika.agents.base import BaseAgent
from pysuika.game.actions import ActionResult
from pysuika.game.engine import GameEngine
from pysuika.game.state import GameState
from pysuika.logging import GameEvent, GameLogger, create_event, serialize_state

__version__ = "0.1.0"
__all__ = [
    "ActionResult",
    "BaseAgent",
    "GameEngine",
    "GameState",
    "GameEvent",
    "GameLogger",
    "create_event",
    "serialize_state",
]
