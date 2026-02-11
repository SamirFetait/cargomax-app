"""
Livestock pen model for Phase 2.

Pens belong to a ship and have position (VCG, LCG, TCG), area, and capacity.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LivestockPen:
    """A livestock pen on a ship deck."""

    id: int | None = None
    ship_id: int | None = None
    name: str = ""  # e.g. PEN 1-1, 1-2
    deck: str = ""  # e.g. DK1, DK2, DK3

    # Position / CoG (m from AP for LCG, from centerline for TCG, from keel for VCG)
    vcg_m: float = 0.0
    lcg_m: float = 0.0
    tcg_m: float = 0.0

    # Area and capacity
    area_m2: float = 0.0
    capacity_head: int = 0  # max head count (optional)