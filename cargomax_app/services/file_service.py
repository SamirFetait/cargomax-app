"""
File service for saving and loading condition files.

Supports JSON format for condition files and Excel import/export.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from ..models import LoadingCondition


def save_condition_to_file(filepath: Path, condition: LoadingCondition) -> None:
    """
    Save a loading condition to a JSON file.
    
    Args:
        filepath: Path where to save the file
        condition: The condition to save
    """
    data = {
        "name": condition.name,
        "voyage_id": condition.voyage_id,
        "tank_volumes_m3": condition.tank_volumes_m3,
        "pen_loadings": getattr(condition, "pen_loadings", {}) or {},
        "displacement_t": condition.displacement_t,
        "draft_m": condition.draft_m,
        "trim_m": condition.trim_m,
        "gm_m": condition.gm_m,
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_condition_from_file(filepath: Path) -> LoadingCondition:
    """
    Load a loading condition from a JSON file.
    
    Args:
        filepath: Path to the file to load
        
    Returns:
        Loaded LoadingCondition object
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    condition = LoadingCondition(
        id=None,  # New condition when loaded from file
        voyage_id=data.get("voyage_id"),
        name=data.get("name", "Loaded Condition"),
        tank_volumes_m3=data.get("tank_volumes_m3", {}),
        pen_loadings=data.get("pen_loadings", {}),
        displacement_t=data.get("displacement_t", 0.0),
        draft_m=data.get("draft_m", 0.0),
        trim_m=data.get("trim_m", 0.0),
        gm_m=data.get("gm_m", 0.0),
    )
    
    return condition
