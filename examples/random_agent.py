"""Example: run a random agent for one full headless game.

Usage
-----
    cd suika_pygame/pysuika
    pip install -e .
    python examples/random_agent.py
"""
from __future__ import annotations

import random

from pysuika import BaseAgent, GameEngine, GameState


class RandomAgent(BaseAgent):
    """Drops each fruit at a uniformly random x position within the valid range."""

    def get_action(self, state: GameState) -> int:
        from pysuika.config import config
        return random.randint(config.pad.left, config.pad.right)


def main() -> None:
    agent = RandomAgent()
    engine = GameEngine(seed=42)
    state = engine.reset()

    print("Running random agent headlessly …")
    while not state.is_game_over:
        x = agent.get_action(state)
        result = engine.step(x)
        state = result.state
        print(
            f"  step={state.step:3d}  drop_x={x:4d}  "
            f"reward={result.reward:5.0f}  score={state.score:6d}"
        )

    print(f"\nGame over!  Final score: {state.score}")


if __name__ == "__main__":
    main()
