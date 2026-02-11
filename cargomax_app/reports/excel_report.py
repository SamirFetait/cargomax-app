"""
Excel report generation for loading conditions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from ..models import Ship, Voyage, LoadingCondition
    from ..services.stability_service import ConditionResults


def export_condition_to_excel(
    filepath: Path,
    ship: "Ship",
    voyage: "Voyage",
    condition: "LoadingCondition",
    results: "ConditionResults",
) -> None:
    """
    Generate an Excel report for a loading condition.
    """
    data = {
        "Parameter": [
            "Ship",
            "IMO",
            "Voyage",
            "Departure",
            "Arrival",
            "Condition",
            "Displacement (t)",
            "Draft (m)",
            "Trim (m)",
            "GM (m)",
            "KG (m)",
            "KM (m)",
        ],
        "Value": [
            ship.name,
            ship.imo_number,
            voyage.name,
            voyage.departure_port,
            voyage.arrival_port,
            condition.name,
            f"{condition.displacement_t:.1f}",
            f"{condition.draft_m:.2f}",
            f"{condition.trim_m:.2f}",
            f"{condition.gm_m:.2f}",
            f"{results.kg_m:.2f}",
            f"{results.km_m:.2f}",
        ],
    }
    if hasattr(results, "strength") and results.strength:
        data["Parameter"].append("SWBM (tm)")
        data["Value"].append(f"{results.strength.still_water_bm_approx_tm:.0f}")

    df = pd.DataFrame(data)
    with pd.ExcelWriter(str(filepath), engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Condition Summary", index=False)
        writer.sheets["Condition Summary"].column_dimensions["A"].width = 22
        writer.sheets["Condition Summary"].column_dimensions["B"].width = 25
