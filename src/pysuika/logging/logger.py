"""GameLogger — writes game events to a JSONL file and/or the console."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TYPE_CHECKING

from pysuika.logging.events import GameEvent, create_event

if TYPE_CHECKING:
    from pysuika.game.state import GameState


class GameLogger:
    """Records :class:`~pysuika.logging.events.GameEvent` objects to a
    JSON-Lines file (one JSON object per line) and optionally to stdout.

    Designed to be used as a context manager::

        with GameLogger("logs/run.jsonl", verbose=True) as logger:
            logger.log("game_start", data={"seed": 42})
            # … game loop …
            logger.log("drop", data={"x": 640, "step": 1}, state=state)
            logger.log("game_over", data={"score": 567})

    Parameters
    ----------
    path:    Path to the ``.jsonl`` output file.  Pass ``None`` to disable
             file output (useful for console-only logging).
    verbose: If ``True``, each event is also printed to stdout.
    """

    def __init__(
        self,
        path: str | Path | None = None,
        verbose: bool = False,
    ) -> None:
        self._path = Path(path) if path is not None else None
        self._verbose = verbose
        self._fh = None

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "GameLogger":
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(self._path, "w", encoding="utf-8")
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ── Public API ────────────────────────────────────────────────────────────

    def log_event(self, event: GameEvent) -> None:
        """Write a pre-built :class:`GameEvent` to the configured outputs."""
        payload = event.to_dict()
        if self._fh is not None:
            self._fh.write(json.dumps(payload) + "\n")
            self._fh.flush()
        if self._verbose:
            self._print_event(event)

    def log(
        self,
        event: str,
        data: dict[str, Any] | None = None,
        state: "GameState | None" = None,
    ) -> None:
        """Create and log an event in one call.

        Parameters
        ----------
        event: event type label (e.g. ``"drop"``, ``"game_over"``).
        data:  arbitrary event-specific dict (drop position, reward, …).
        state: optional :class:`~pysuika.game.state.GameState` to embed.
        """
        self.log_event(create_event(event, data=data, state=state))

    def close(self) -> None:
        """Flush and close the log file (called automatically by the context manager)."""
        if self._fh is not None:
            self._fh.flush()
            self._fh.close()
            self._fh = None

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _print_event(event: GameEvent) -> None:
        parts = [f"[{event.timestamp}] {event.event.upper()}"]
        for k, v in event.data.items():
            parts.append(f"  {k}={v}")
        print("\n".join(parts))
