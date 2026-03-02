"""Game event structures for pysuika logging."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pysuika.game.state import GameState


@dataclass
class GameEvent:
    """A single recorded game event.

    Attributes
    ----------
    event:     Short string identifier, e.g. ``"drop"``, ``"game_over"``.
    timestamp: ISO-8601 string captured at event creation time.
    data:      Arbitrary event-specific payload (drop position, score delta…).
    state:     Optional serialised snapshot of the GameState at this moment.
    """

    event: str
    timestamp: str
    data: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "event": self.event,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        if self.state is not None:
            d["state"] = self.state
        return d


def create_event(
    event: str,
    data: dict[str, Any] | None = None,
    state: GameState | None = None,
) -> GameEvent:
    """Factory that builds a :class:`GameEvent` with the current timestamp.

    Parameters
    ----------
    event: event type label.
    data:  optional dict with event-specific fields.
    state: optional :class:`~pysuika.game.state.GameState` to serialise
           and embed in the event.
    """
    from pysuika.logging.state_serializer import serialize_state

    return GameEvent(
        event=event,
        timestamp=datetime.now().isoformat(),
        data=data or {},
        state=serialize_state(state) if state is not None else None,
    )
