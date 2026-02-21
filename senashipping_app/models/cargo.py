from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Cargo:
    id: int | None = None
    name: str = ""
    cargo_type: str = ""  # e.g. "crude oil", "products", "bulk"
    density_t_per_m3: float = 1.0

