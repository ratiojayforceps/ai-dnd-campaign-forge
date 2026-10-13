"""Hexcrawl region generator.

Produces a hex grid with biome assignments and 3-6 points of interest. The
grid is a simple axial coordinate list; render plugins turn it into an actual
image. Biome weights shift with latitude so northern rows lean tundra, southern
rows lean desert.
"""

from __future__ import annotations