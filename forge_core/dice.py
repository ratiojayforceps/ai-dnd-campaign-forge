"""Deterministic dice roller.

Seeded from the session. Every plugin that needs randomness goes through this
so a given seed reproduces byte-identical campaigns across runs and machines.
Uses `random.Random` (Mersenne Twister) — stable across CPython versions.
"""

from __future__ import annotations

import random
from typing import Final

DICE_FACES: Final[dict[str, int]] = {
    "d4": 4,
    "d6": 6,
    "d8": 8,
    "d10": 10,
    "d12": 12,
    "d20": 20,
    "d100": 100,
}


class Dice:
    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def roll(self, notation: str) -> int:
        """Roll standard notation like '2d6+3' or '1d20'."""
        bonus = 0
        if "+" in notation:
            notation, bonus_s = notation.split("+", 1)
            bonus = int(bonus_s)
        count_s, die = notation.split("d", 1)
        count = int(count_s) if count_s else 1
        faces = DICE_FACES[die]
        return sum(self._rng.randint(1, faces) for _ in range(count)) + bonus

    def pick(self, options: list[str]) -> str:
        return self._rng.choice(options)

    def weighted(self, options: dict[str, float]) -> str:
        keys = list(options)
        weights = [options[k] for k in keys]
        return self._rng.choices(keys, weights=weights, k=1)[0]