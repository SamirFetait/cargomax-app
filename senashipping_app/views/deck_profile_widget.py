from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
)

from .stl_view_widget import StlViewWidget
from ..utils.sorting import get_pen_sort_key


BASE_DIR = Path(__file__).resolve().parent.parent  # -> senashipping_app
CAD_DIR = BASE_DIR / "cads"


def _profile_stl_path() -> Path | None:
    """Return path to ship/profile STL if it exists (ship.stl, hull.stl, profile.stl)."""
    for name in ("ship.stl", "hull.stl", "profile.stl"):
        p = CAD_DIR / name
        if p.exists():
            return p
    return None


def _deck_stl_path(deck_name: str) -> Path | None:
    """Return path to deck STL if it exists (e.g. deck_A.stl)."""
    p = CAD_DIR / f"deck_{deck_name}.stl"
    return p if p.exists() else None


def _fmt_val(v: float | None, decimals: int = 2) -> str:
    """Format number or '---' when None."""
    if v is None:
        return "---"
    return f"{v:.{decimals}f}"


class DeckTabWidget(QWidget):
    """
    Widget for a single deck tab: deck table (title + table) only.
    The 3D deck STL is shown in a single shared view in DeckProfileWidget to avoid
    multiple VTK render windows on Windows (wglMakeCurrent code 2004).
    """

    def __init__(self, deck_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._deck_name = deck_name

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._title_label = QLabel(self)
        self._title_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(self._title_label)

        self._table = QTableWidget(self)
        layout.addWidget(self._table, 1)
        # self._table.setColumnCount(12)
        # self._table.setHorizontalHeaderLabels([
        #     "Pens no.",
        #     "A", "B", "C", "D",  # Area
        #     "LCG (m) from Fr. -6",
        #     "VCG (m) from B.L.",
        #     "A", "B", "C", "D",  # TCG (m) from C.L.
        # ])
        # self._table.horizontalHeader().setStretchLastSection(False)
        # for i in range(12):
        #     self._table.setColumnWidth(i, 72 if i > 0 else 56)
        # right.addWidget(self._table, 1)
        # layout.addLayout(right, 1)

    def update_table(self, pens: list, tanks: list) -> None:
        """Update deck tab data (no 2D view to update)."""
        deck_pens = [
            p for p in pens
            if (getattr(p, "deck", None) or "").strip().upper() == self._deck_name.upper()
        ]
        # Sort pens by the 3-level key: number -> letter pattern (A,B,D,C) -> deck
        deck_pens = sorted(deck_pens, key=get_pen_sort_key)

        # Net area: sum of area_a+area_b+area_c+area_d when set, else area_m2
        net_area = 0.0
        sums = [0.0, 0.0, 0.0, 0.0]  # Area A, B, C, D

        # self._table.setRowCount(0)
        # for pen in deck_pens:
        #     row = self._table.rowCount()
        #     self._table.insertRow(row)
        #     pen_no = getattr(pen, "pen_no", None)
        #     self._table.setItem(
        #         row, 0,
        #         QTableWidgetItem(str(pen_no) if pen_no is not None else pen.name or "—")
        #     )
        #     area_a = getattr(pen, "area_a_m2", None)
        #     area_b = getattr(pen, "area_b_m2", None)
        #     area_c = getattr(pen, "area_c_m2", None)
        #     area_d = getattr(pen, "area_d_m2", None)
        #     if area_a is None and area_b is None and area_c is None and area_d is None:
        #         area_a = getattr(pen, "area_m2", 0.0) or 0.0
        #         if area_a:
        #             sums[0] += area_a
        #         net_area += area_a
        #     else:
        #         for i, v in enumerate([area_a, area_b, area_c, area_d]):
        #             if v is not None:
        #                 sums[i] += v
        #                 net_area += v
        #     self._table.setItem(row, 1, QTableWidgetItem(_fmt_val(area_a)))
        #     self._table.setItem(row, 2, QTableWidgetItem(_fmt_val(area_b)))
        #     self._table.setItem(row, 3, QTableWidgetItem(_fmt_val(area_c)))
        #     self._table.setItem(row, 4, QTableWidgetItem(_fmt_val(area_d)))
        #     self._table.setItem(
        #         row, 5,
        #         QTableWidgetItem(_fmt_val(getattr(pen, "lcg_m", None)))
        #     )
        #     self._table.setItem(
        #         row, 6,
        #         QTableWidgetItem(_fmt_val(getattr(pen, "vcg_m", None)))
        #     )
        #     tcg_a = getattr(pen, "tcg_a_m", None)
        #     tcg_b = getattr(pen, "tcg_b_m", None)
        #     tcg_c = getattr(pen, "tcg_c_m", None)
        #     tcg_d = getattr(pen, "tcg_d_m", None)
        #     if tcg_a is None and tcg_b is None and tcg_c is None and tcg_d is None:
        #         tcg = getattr(pen, "tcg_m", 0.0)
        #         tcg_a = tcg_b = tcg_c = tcg_d = tcg if tcg else None
        #     self._table.setItem(row, 7, QTableWidgetItem(_fmt_val(tcg_a)))
        #     self._table.setItem(row, 8, QTableWidgetItem(_fmt_val(tcg_b)))
        #     self._table.setItem(row, 9, QTableWidgetItem(_fmt_val(tcg_c)))
        #     self._table.setItem(row, 10, QTableWidgetItem(_fmt_val(tcg_d)))

        # # TOTAL row
        # self._table.insertRow(self._table.rowCount())
        # total_row = self._table.rowCount() - 1
        # self._table.setItem(total_row, 0, QTableWidgetItem("TOTAL:"))
        # for c in range(1, 5):
        #     self._table.setItem(
        #         total_row, c,
        #         QTableWidgetItem(f"{sums[c - 1]:.2f}" if sums[c - 1] else "")
        #     )
        # for c in range(5, 12):
        #     self._table.setItem(total_row, c, QTableWidgetItem(""))

        # if net_area == 0.0 and deck_pens:
        #     net_area = sum(getattr(p, "area_m2", 0.0) or 0.0 for p in deck_pens)
        # self._title_label.setText(
        #     f"{self._deck_name} DECK (net area {net_area:.2f} sq.m.)"
        # )


class DeckProfileWidget(QWidget):
    """
    Composite widget:
      - top half: ship profile view
      - bottom half: tabs for each deck (A-H), each showing deck plan + pens/tanks table.
    """

    # Emitted whenever the active deck changes, e.g. "A", "B", "C"
    deck_changed = pyqtSignal(str)
    # Emitted when user selects a tank polygon in a deck view (connects to calculation UI)
    tank_selected = pyqtSignal(int)
    # Emitted when selection changes anywhere in profile/deck views.
    # pens_selected/tanks_selected are `set[int]` or `None` (None = no change to that type).
    selection_changed = pyqtSignal(object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top: 3D STL only (no 2D drawings)
        self._profile_stl_view = StlViewWidget(self)
        _stl_path = _profile_stl_path()
        if _stl_path is not None:
            self._profile_stl_view.load_stl(_stl_path)
        main_layout.addWidget(self._profile_stl_view, 55)

        # Single shared 3D view for deck STL (avoids multiple VTK render windows → wglMakeCurrent 2004 on Windows)
        self._deck_stl_view = StlViewWidget(self)
        _deck_a_stl = _deck_stl_path("A")
        if _deck_a_stl is not None:
            self._deck_stl_view.load_stl(_deck_a_stl)
        main_layout.addWidget(self._deck_stl_view, 25)

        # Deck tabs: table-only content per deck; STL for current deck is shown in _deck_stl_view above
        self._deck_tabs = QTabWidget(self)
        self._deck_tab_widgets: dict[str, DeckTabWidget] = {}

        for deck_letter in ["A", "B", "C", "D", "E", "F", "G", "H"]:
            tab_widget = DeckTabWidget(deck_letter, self)
            self._deck_tab_widgets[deck_letter] = tab_widget
            self._deck_tabs.addTab(tab_widget, f"Deck {deck_letter}")

        self._syncing_selection = False

        main_layout.addWidget(self._deck_tabs, 20)

        # Wire tab changes: update shared deck 3D view and emit deck_changed
        self._deck_tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index: int) -> None:
        """Called when user switches to a different deck tab. Updates shared deck STL view."""
        if 0 <= index < self._deck_tabs.count():
            tab_widget = self._deck_tabs.widget(index)
            if isinstance(tab_widget, DeckTabWidget):
                deck_name = tab_widget._deck_name
                deck_stl = _deck_stl_path(deck_name)
                if deck_stl is not None:
                    self._deck_stl_view.load_stl(deck_stl)
                else:
                    self._deck_stl_view.clear()
                self.deck_changed.emit(deck_name)

    def update_tables(self, pens: list, tanks: list) -> None:
        """Update deck tab data (selection is from table only now; no 2D drawings)."""
        for tab_widget in self._deck_tab_widgets.values():
            tab_widget.update_table(pens, tanks)

    def set_selected(self, pen_ids: set[int], tank_ids: set[int]) -> None:
        """No-op: selection is from condition table only (no 2D profile/deck view)."""
        pass

    def highlight_pen(self, pen_id: int) -> None:
        """No-op: no 2D profile/deck view to highlight."""
        pass

    def get_current_deck(self) -> str:
        """Return the currently selected deck letter."""
        current_tab = self._deck_tabs.currentWidget()
        if isinstance(current_tab, DeckTabWidget):
            return current_tab._deck_name
        return "A"
    
        
    def update_waterline(
        self,
        draft_mid: float,
        draft_aft: float | None = None,
        draft_fwd: float | None = None,
        ship_length: float | None = None,
        ship_depth: float | None = None,
        trim_m: float | None = None,
    ) -> None:
        """Waterline visualization removed - method kept for compatibility but does nothing."""
        pass

