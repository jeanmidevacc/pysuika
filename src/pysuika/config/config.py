"""Game configuration loaded from the bundled YAML.

This module is intentionally free of pygame so it can be imported in headless
mode.  Image loading is deferred to the UI layer (GameRenderer).
"""
from __future__ import annotations

import importlib.resources
from typing import Any

import yaml


class ConfigNode:
    """Simple namespace built from a dict."""

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


class Config:
    """Parsed game configuration.

    Attributes
    ----------
    screen:  width, height, fps, delay, white, score
    pad:     left, top, right, bot, line_top, line_bot, killy
    physics: density, elasticity, impulse, gravity, damping, bias,
             fruit_friction, wall_friction
    fruit_names: ordered list of the 11 fruit names (index == fruit type)
    """

    fruit_names: list[str] = [
        "cherry", "strawberry", "grapes", "orange", "persimmon",
        "apple", "pear", "peach", "pineapple", "melon", "watermelon",
    ]

    def __init__(self) -> None:
        pkg = importlib.resources.files("pysuika.config")
        yaml_bytes = (pkg / "default.yaml").read_bytes()
        self._data: dict[str, Any] = yaml.safe_load(yaml_bytes)

        self.screen = ConfigNode(**self._data["screen"])
        self.pad = ConfigNode(**self._data["pad"])
        self.physics = ConfigNode(**self._data["physics"])

    # Fruit-level access: config[index, field]  e.g. config[0, "radius"]
    def __getitem__(self, key: tuple[int, str]) -> Any:
        index, field = key
        fruit = self.fruit_names[index]
        return self._data[fruit][field]

    # Convenience corner properties (used by Wall and PreParticle)
    @property
    def top_left(self) -> tuple[int, int]:
        return self.pad.left, self.pad.top

    @property
    def bot_left(self) -> tuple[int, int]:
        return self.pad.left, self.pad.bot

    @property
    def top_right(self) -> tuple[int, int]:
        return self.pad.right, self.pad.top

    @property
    def bot_right(self) -> tuple[int, int]:
        return self.pad.right, self.pad.bot


# Module-level singleton — created once on first import.
config = Config()
