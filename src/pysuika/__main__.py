"""Entry point: ``python -m pysuika`` or ``suika``.

Usage
-----
Interactive (human) play::

    python -m pysuika

Watch an agent play (rendered window)::

    python -m pysuika --agent my_agent.py

Fast headless run (no window)::

    python -m pysuika --agent my_agent.py --headless

With logging and seed::

    python -m pysuika --agent my_agent.py --headless --seed 42 --log logs/run.jsonl
"""
from __future__ import annotations

import argparse
import importlib.util
import inspect
import sys
from pathlib import Path

from pysuika.agents.base import BaseAgent
from pysuika.config import config
from pysuika.game.engine import GameEngine
from pysuika.game.state import GameState
from pysuika.logging import GameLogger

ARROW_STEP = 8   # pixels to move per arrow key press


# ── Agent loading ─────────────────────────────────────────────────────────────

def load_agent_from_file(path: Path) -> BaseAgent:
    """Dynamically load a BaseAgent subclass from a .py file.

    The file is searched for (in order):
    1. A class literally named ``Agent``
    2. Any class that is a subclass of :class:`BaseAgent` (excluding the base)
    3. A top-level variable or callable named ``agent``

    Raises
    ------
    SystemExit if no valid agent is found.
    """
    spec = importlib.util.spec_from_file_location("_user_agent", path)
    if spec is None or spec.loader is None:
        sys.exit(f"Cannot load agent file: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    # 1. Class named Agent
    cls = getattr(module, "Agent", None)
    if cls is not None and inspect.isclass(cls) and issubclass(cls, BaseAgent):
        return cls()

    # 2. Any BaseAgent subclass in the module
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseAgent) and obj is not BaseAgent:
            return obj()

    # 3. Variable/callable named agent
    agent_obj = getattr(module, "agent", None)
    if agent_obj is not None:
        instance = agent_obj() if callable(agent_obj) else agent_obj
        if isinstance(instance, BaseAgent):
            return instance

    sys.exit(
        f"No BaseAgent subclass found in {path}.\n"
        "Expected a class named 'Agent' or any class inheriting from BaseAgent."
    )


# ── Game loops ────────────────────────────────────────────────────────────────

def _run_headless(
    engine: GameEngine,
    agent: BaseAgent,
    logger: GameLogger | None = None,
) -> None:
    """Run a full game headlessly and print the result."""
    print("Running agent headlessly …")
    state = engine.reset()
    if logger is not None:
        logger.log("game_start", data={"seed": engine._rng.bit_generator.state["state"]["state"]})
    while not state.is_game_over:
        x = agent.get_action(state)
        result = engine.step(x)
        state = result.state
        print(f"  step={state.step:3d}  x={int(x):4d}  reward={result.reward:5.0f}  score={state.score:6d}")
        if logger is not None:
            logger.log(
                "drop",
                data={"step": state.step, "x": int(x), "reward": result.reward, "score": state.score},
                state=state,
            )
    if logger is not None:
        logger.log("game_over", data={"score": state.score, "steps": state.step}, state=state)
    print(f"\nGame over — final score: {state.score}")


def _run_rendered_agent(
    engine: GameEngine,
    agent: BaseAgent,
    logger: GameLogger | None = None,
) -> None:
    """Run an agent with a pygame window so you can watch it play."""
    import pygame
    from pysuika.ui.renderer import GameRenderer

    state = engine.reset()
    if logger is not None:
        logger.log("game_start", data={"seed": engine._rng.bit_generator.state["state"]["state"]})
    renderer = GameRenderer(engine)
    wait_frames = 0

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_q, pygame.K_ESCAPE
                ):
                    return

            # Agent acts when the wait is over
            if wait_frames == 0 and not engine.is_game_over:
                x = agent.get_action(state)
                engine.drop_fruit(x)
                wait_frames = config.screen.delay
                if logger is not None:
                    logger.log(
                        "drop",
                        data={"step": state.step + 1, "x": int(x), "score": state.score},
                        state=state,
                    )

            engine.step_frame()
            state = engine.state
            if wait_frames > 0:
                wait_frames -= 1

            renderer.render()

            if engine.is_game_over:
                if logger is not None:
                    logger.log("game_over", data={"score": state.score, "steps": state.step}, state=state)
                pygame.time.wait(2000)
                return
    finally:
        renderer.quit()


def _run_interactive(engine: GameEngine) -> None:
    """Human play: mouse + keyboard controls."""
    import pygame
    from pysuika.ui.renderer import GameRenderer

    engine.reset()
    renderer = GameRenderer(engine)
    wait_frames = 0
    drop_x: float = config.screen.width / 2
    using_keyboard = False

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        return
                    if event.key == pygame.K_LEFT:
                        drop_x -= ARROW_STEP
                        using_keyboard = True
                    elif event.key == pygame.K_RIGHT:
                        drop_x += ARROW_STEP
                        using_keyboard = True
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if wait_frames == 0 and not engine.is_game_over:
                            engine.drop_fruit(drop_x)
                            wait_frames = config.screen.delay
                if event.type == pygame.MOUSEMOTION:
                    using_keyboard = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if wait_frames == 0 and not engine.is_game_over:
                        engine.drop_fruit(drop_x)
                        wait_frames = config.screen.delay

            if not using_keyboard:
                drop_x = float(pygame.mouse.get_pos()[0])

            if engine.next_particle is not None:
                engine.next_particle.set_x(drop_x)

            engine.step_frame()
            if wait_frames > 0:
                wait_frames -= 1

            renderer.render()

            if engine.is_game_over:
                pygame.time.wait(2000)
                return
    finally:
        renderer.quit()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pysuika",
        description="Suika game — play interactively or run an agent.",
    )
    parser.add_argument(
        "--agent", type=Path, default=None,
        metavar="AGENT.PY",
        help="Path to a Python file containing a BaseAgent subclass.",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run without a pygame window (requires --agent).",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducible fruit sequences.",
    )
    parser.add_argument(
        "--log", type=Path, default=None,
        metavar="FILE.jsonl",
        help="Path to write a JSONL game log (requires --agent).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print each logged event to stdout (used with --log).",
    )
    args = parser.parse_args()

    if args.headless and args.agent is None:
        parser.error("--headless requires --agent.")
    if args.log is not None and args.agent is None:
        parser.error("--log requires --agent.")

    engine = GameEngine(seed=args.seed)

    if args.agent is not None:
        agent = load_agent_from_file(args.agent)
        with GameLogger(path=args.log, verbose=args.verbose) as logger:
            log = logger if args.log is not None else None
            if args.headless:
                _run_headless(engine, agent, logger=log)
            else:
                engine.reset()
                _run_rendered_agent(engine, agent, logger=log)
    else:
        _run_interactive(engine)


if __name__ == "__main__":
    main()
