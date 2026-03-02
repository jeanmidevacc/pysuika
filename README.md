# pysuika

A Python package for the Suika (watermelon-drop) physics game with a clean agent API.

## Installation

```bash
pip install -e .
```

## Quick start

### Interactive play

```bash
python -m pysuika
# or, after pip install:
suika
```

### Headless agent loop

```python
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
```

## Package structure

```
src/pysuika/
├── game/       # GameEngine, GameState, ActionResult
├── physics/    # Particle, PreParticle, Wall, collision handlers
├── agents/     # BaseAgent ABC
├── ui/         # GameRenderer (pygame), Cloud
└── config/     # Config (loaded from default.yaml)
```
