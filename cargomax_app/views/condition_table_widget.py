"""
Tabbed table widget for displaying livestock pens and tanks by category.

Matches the reference UI with tabs for each deck, tank type, etc.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from ..models import Tank, LivestockPen


MASS_PER_HEAD_T = 0.5  # Average mass per head in tonnes


class ConditionTableWidget(QWidget):
    """
    Tabbed table widget showing livestock pens and tanks organized by category.
    
    Tabs include:
    - Livestock-DK1 through Livestock-DK8 (one per deck)
    - Water Ballast, Fresh Water, Heavy Fuel Oil, Diesel Oil, Lube Oil, Gray Water
    - Misc. Tanks, Dung, Fodder Hold
    - Misc. Weights, Spaces
    - All, Selected
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self._tabs = QTabWidget(self)
        self._table_widgets: Dict[str, QTableWidget] = {}
        
        # Create all tabs
        self._create_tabs()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)
        
    def _create_tabs(self) -> None:
        """Create all category tabs."""
        # Livestock deck tabs
        for deck_num in range(1, 9):
            tab_name = f"Livestock-DK{deck_num}"
            table = self._create_table()
            self._table_widgets[tab_name] = table
            self._tabs.addTab(table, tab_name)
            
        # Tank category tabs
        tank_categories = [
            "Water Ballast",
            "Fresh Water",
            "Heavy Fuel Oil",
            "Diesel Oil",
            "Lube Oil",
            "Gray Water",
            "Misc. Tanks",
            "Dung",
            "Fodder Hold",
        ]
        
        for cat in tank_categories:
            table = self._create_table()
            self._table_widgets[cat] = table
            self._tabs.addTab(table, cat)
            
        # Special tabs
        for tab_name in ["Misc. Weights", "Spaces", "All", "Selected"]:
            table = self._create_table()
            self._table_widgets[tab_name] = table
            self._tabs.addTab(table, tab_name)
            
    def _create_table(self) -> QTableWidget:
        """Create a table with the standard column structure."""
        table = QTableWidget(self)
        table.setColumnCount(14)
        table.setHorizontalHeaderLabels([
            "Name",
            "Cargo",
            "# Head",
            "Head %Full",
            "Head Capacity",
            "Used Area m2",
            "Total Area m2",
            "Area/Head",
            "AvW/Head MT",
            "Weight MT",
            "VCG m-BL",
            "LCG m-[FR]",
            "TCG m-CL",
            "LS Moment m-MT",
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        return table
        
    def update_data(
        self,
        pens: List[LivestockPen],
        tanks: List[Tank],
        pen_loadings: Dict[int, int],
        tank_volumes: Dict[int, float],
    ) -> None:
        """
        Update all tables with current pens and tanks data.
        
        Args:
            pens: List of all livestock pens
            tanks: List of all tanks
            pen_loadings: Dict mapping pen ID to head count
            tank_volumes: Dict mapping tank ID to volume in m³
        """
        # Clear all tables first
        for table in self._table_widgets.values():
            table.setRowCount(0)
            
        # Update livestock deck tabs
        for deck_num in range(1, 9):
            tab_name = f"Livestock-DK{deck_num}"
            deck_letter = chr(ord('A') + deck_num - 1)  # A-H
            self._populate_livestock_tab(tab_name, pens, pen_loadings, deck_letter)
            
        # Update tank category tabs (simplified - would need tank type mapping)
        self._populate_tank_tabs(tanks, tank_volumes)
        
        # Update "All" tab
        self._populate_all_tab(pens, tanks, pen_loadings, tank_volumes)
        
    def _populate_livestock_tab(
        self,
        tab_name: str,
        pens: List[LivestockPen],
        pen_loadings: Dict[int, int],
        deck_letter: str,
    ) -> None:
        """Populate a livestock deck tab with pens for that deck."""
        table = self._table_widgets.get(tab_name)
        if not table:
            return
            
        deck_pens = [p for p in pens if (p.deck or "").strip().upper() == deck_letter.upper()]
        
        total_weight = 0.0
        total_area_used = 0.0
        total_area = 0.0
        
        for pen in deck_pens:
            row = table.rowCount()
            table.insertRow(row)
            
            heads = pen_loadings.get(pen.id or -1, 0)
            weight_mt = heads * MASS_PER_HEAD_T
            total_weight += weight_mt
            
            area_used = pen.area_m2 if heads > 0 else 0.0
            total_area_used += area_used
            total_area += pen.area_m2
            
            head_pct = (heads / pen.capacity_head * 100.0) if pen.capacity_head > 0 else 0.0
            area_per_head = pen.area_m2 / heads if heads > 0 else 0.0
            
            # LCG moment (simplified - would need ship length for normalization)
            lcg_moment = weight_mt * pen.lcg_m
            
            table.setItem(row, 0, QTableWidgetItem(pen.name))
            table.setItem(row, 1, QTableWidgetItem("Livestock"))
            table.setItem(row, 2, QTableWidgetItem(str(heads)))
            table.setItem(row, 3, QTableWidgetItem(f"{head_pct:.1f}"))
            table.setItem(row, 4, QTableWidgetItem(str(pen.capacity_head)))
            table.setItem(row, 5, QTableWidgetItem(f"{area_used:.2f}"))
            table.setItem(row, 6, QTableWidgetItem(f"{pen.area_m2:.2f}"))
            table.setItem(row, 7, QTableWidgetItem(f"{area_per_head:.2f}"))
            table.setItem(row, 8, QTableWidgetItem(f"{MASS_PER_HEAD_T:.2f}"))
            table.setItem(row, 9, QTableWidgetItem(f"{weight_mt:.2f}"))
            table.setItem(row, 10, QTableWidgetItem(f"{pen.vcg_m:.3f}"))
            table.setItem(row, 11, QTableWidgetItem(f"{pen.lcg_m:.3f}"))
            table.setItem(row, 12, QTableWidgetItem(f"{pen.tcg_m:.3f}"))
            table.setItem(row, 13, QTableWidgetItem(f"{lcg_moment:.2f}"))
            
        # Add totals row
        if deck_pens:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(f"Livestock-DK{deck_letter} Totals"))
            table.setItem(row, 1, QTableWidgetItem(""))
            table.setItem(row, 2, QTableWidgetItem(""))
            table.setItem(row, 3, QTableWidgetItem(""))
            table.setItem(row, 4, QTableWidgetItem(""))
            table.setItem(row, 5, QTableWidgetItem(f"{total_area_used:.2f}"))
            table.setItem(row, 6, QTableWidgetItem(f"{total_area:.2f}"))
            table.setItem(row, 7, QTableWidgetItem(""))
            table.setItem(row, 8, QTableWidgetItem(""))
            table.setItem(row, 9, QTableWidgetItem(f"{total_weight:.2f}"))
            table.setItem(row, 10, QTableWidgetItem(""))
            table.setItem(row, 11, QTableWidgetItem(""))
            table.setItem(row, 12, QTableWidgetItem(""))
            table.setItem(row, 13, QTableWidgetItem(""))
            
    def _populate_tank_tabs(
        self,
        tanks: List[Tank],
        tank_volumes: Dict[int, float],
    ) -> None:
        """Populate tank category tabs (simplified - all tanks in Misc. Tanks for now)."""
        misc_table = self._table_widgets.get("Misc. Tanks")
        if not misc_table:
            return
            
        for tank in tanks:
            row = misc_table.rowCount()
            misc_table.insertRow(row)
            
            vol = tank_volumes.get(tank.id or -1, 0.0)
            fill_pct = (vol / tank.capacity_m3 * 100.0) if tank.capacity_m3 > 0 else 0.0
            
            # Simplified: assume water density
            weight_mt = vol * 1.025  # Sea water density
            
            misc_table.setItem(row, 0, QTableWidgetItem(tank.name))
            misc_table.setItem(row, 1, QTableWidgetItem("Tank"))
            misc_table.setItem(row, 2, QTableWidgetItem(""))
            misc_table.setItem(row, 3, QTableWidgetItem(f"{fill_pct:.1f}"))
            misc_table.setItem(row, 4, QTableWidgetItem(f"{tank.capacity_m3:.2f}"))
            misc_table.setItem(row, 5, QTableWidgetItem(""))
            misc_table.setItem(row, 6, QTableWidgetItem(""))
            misc_table.setItem(row, 7, QTableWidgetItem(""))
            misc_table.setItem(row, 8, QTableWidgetItem(""))
            misc_table.setItem(row, 9, QTableWidgetItem(f"{weight_mt:.2f}"))
            misc_table.setItem(row, 10, QTableWidgetItem(""))
            misc_table.setItem(row, 11, QTableWidgetItem(f"{tank.longitudinal_pos:.3f}"))
            misc_table.setItem(row, 12, QTableWidgetItem(""))
            misc_table.setItem(row, 13, QTableWidgetItem(""))
            
    def _populate_all_tab(
        self,
        pens: List[LivestockPen],
        tanks: List[Tank],
        pen_loadings: Dict[int, int],
        tank_volumes: Dict[int, float],
    ) -> None:
        """Populate the 'All' tab with everything."""
        all_table = self._table_widgets.get("All")
        if not all_table:
            return
            
        # Add all pens
        for pen in pens:
            heads = pen_loadings.get(pen.id or -1, 0)
            if heads == 0:
                continue
                
            row = all_table.rowCount()
            all_table.insertRow(row)
            
            weight_mt = heads * MASS_PER_HEAD_T
            head_pct = (heads / pen.capacity_head * 100.0) if pen.capacity_head > 0 else 0.0
            area_per_head = pen.area_m2 / heads if heads > 0 else 0.0
            lcg_moment = weight_mt * pen.lcg_m
            
            all_table.setItem(row, 0, QTableWidgetItem(pen.name))
            all_table.setItem(row, 1, QTableWidgetItem("Livestock"))
            all_table.setItem(row, 2, QTableWidgetItem(str(heads)))
            all_table.setItem(row, 3, QTableWidgetItem(f"{head_pct:.1f}"))
            all_table.setItem(row, 4, QTableWidgetItem(str(pen.capacity_head)))
            all_table.setItem(row, 5, QTableWidgetItem(f"{pen.area_m2:.2f}"))
            all_table.setItem(row, 6, QTableWidgetItem(f"{pen.area_m2:.2f}"))
            all_table.setItem(row, 7, QTableWidgetItem(f"{area_per_head:.2f}"))
            all_table.setItem(row, 8, QTableWidgetItem(f"{MASS_PER_HEAD_T:.2f}"))
            all_table.setItem(row, 9, QTableWidgetItem(f"{weight_mt:.2f}"))
            all_table.setItem(row, 10, QTableWidgetItem(f"{pen.vcg_m:.3f}"))
            all_table.setItem(row, 11, QTableWidgetItem(f"{pen.lcg_m:.3f}"))
            all_table.setItem(row, 12, QTableWidgetItem(f"{pen.tcg_m:.3f}"))
            all_table.setItem(row, 13, QTableWidgetItem(f"{lcg_moment:.2f}"))
            
        # Add all tanks
        for tank in tanks:
            vol = tank_volumes.get(tank.id or -1, 0.0)
            if vol == 0.0:
                continue
                
            row = all_table.rowCount()
            all_table.insertRow(row)
            
            fill_pct = (vol / tank.capacity_m3 * 100.0) if tank.capacity_m3 > 0 else 0.0
            weight_mt = vol * 1.025
            
            all_table.setItem(row, 0, QTableWidgetItem(tank.name))
            all_table.setItem(row, 1, QTableWidgetItem("Tank"))
            all_table.setItem(row, 2, QTableWidgetItem(""))
            all_table.setItem(row, 3, QTableWidgetItem(f"{fill_pct:.1f}"))
            all_table.setItem(row, 4, QTableWidgetItem(f"{tank.capacity_m3:.2f}"))
            all_table.setItem(row, 5, QTableWidgetItem(""))
            all_table.setItem(row, 6, QTableWidgetItem(""))
            all_table.setItem(row, 7, QTableWidgetItem(""))
            all_table.setItem(row, 8, QTableWidgetItem(""))
            all_table.setItem(row, 9, QTableWidgetItem(f"{weight_mt:.2f}"))
            all_table.setItem(row, 10, QTableWidgetItem(""))
            all_table.setItem(row, 11, QTableWidgetItem(f"{tank.longitudinal_pos:.3f}"))
            all_table.setItem(row, 12, QTableWidgetItem(""))
            all_table.setItem(row, 13, QTableWidgetItem(""))
