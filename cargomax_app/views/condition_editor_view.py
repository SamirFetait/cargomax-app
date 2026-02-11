"""
Loading Condition editor view.

Allows selecting a ship (and optionally voyage/condition) for tank fillings,
computing stability, and saving conditions to a voyage.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QMessageBox,
)

from ..models import Ship, Voyage, LoadingCondition, Tank
from ..repositories import database
from ..repositories.ship_repository import ShipRepository
from ..services.condition_service import (
    ConditionService,
    ConditionValidationError,
    ConditionResults,
)
from ..services.voyage_service import VoyageService, VoyageValidationError


class ConditionEditorView(QWidget):
    # Signal emitted when a condition has been computed:
    # args: results, ship, condition, voyage (or None for ad-hoc)
    condition_computed = pyqtSignal(object, object, object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        if database.SessionLocal is None:
            raise RuntimeError("Database not initialized")

        self._ships: List[Ship] = []
        self._voyages: List[Voyage] = []
        self._conditions: List[LoadingCondition] = []
        self._current_ship: Optional[Ship] = None
        self._current_voyage: Optional[Voyage] = None
        self._current_condition: Optional[LoadingCondition] = None

        self._ship_combo = QComboBox(self)
        self._voyage_combo = QComboBox(self)
        self._condition_combo = QComboBox(self)
        self._condition_name_edit = QLineEdit(self)
        self._tank_table = QTableWidget(self)
        self._tank_table.setColumnCount(3)
        self._tank_table.setHorizontalHeaderLabels(
            ["Tank", "Capacity (m³)", "Fill %"]
        )
        self._tank_table.horizontalHeader().setStretchLastSection(True)

        self._pen_table = QTableWidget(self)
        self._pen_table.setColumnCount(4)
        self._pen_table.setHorizontalHeaderLabels(
            ["Pen", "Deck", "Area (m²)", "Head Count"]
        )
        self._pen_table.horizontalHeader().setStretchLastSection(True)
        self._pen_table.setMaximumHeight(120)

        self._compute_btn = QPushButton("Compute Results", self)
        self._save_condition_btn = QPushButton("Save Condition", self)

        self._build_layout()
        self._connect_signals()
        self._save_condition_btn.setEnabled(False)
        self._load_ships()

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Ship:", self))
        top.addWidget(self._ship_combo, 1)
        top.addWidget(QLabel("Voyage:", self))
        top.addWidget(self._voyage_combo, 1)
        top.addWidget(QLabel("Condition:", self))
        top.addWidget(self._condition_combo, 1)
        root.addLayout(top)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Condition name:", self))
        name_row.addWidget(self._condition_name_edit, 2)
        root.addLayout(name_row)

        root.addWidget(QLabel("Tank fillings", self))
        root.addWidget(self._tank_table, 1)
        root.addWidget(QLabel("Livestock pen loadings", self))
        root.addWidget(self._pen_table)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self._compute_btn)
        btn_row.addWidget(self._save_condition_btn)
        root.addLayout(btn_row)

    def _connect_signals(self) -> None:
        self._ship_combo.currentIndexChanged.connect(self._on_ship_changed)
        self._voyage_combo.currentIndexChanged.connect(self._on_voyage_changed)
        self._condition_combo.currentIndexChanged.connect(self._on_condition_changed)
        self._compute_btn.clicked.connect(self._on_compute)
        self._save_condition_btn.clicked.connect(self._on_save_condition)

    def _load_ships(self) -> None:
        self._ship_combo.clear()
        self._ships = []
        if database.SessionLocal is None:
            return
        with database.SessionLocal() as db:
            repo = ShipRepository(db)
            self._ships = repo.list()

        for ship in self._ships:
            self._ship_combo.addItem(ship.name, ship.id)

        if self._ships:
            self._ship_combo.setCurrentIndex(0)
            self._on_ship_changed(0)

    def _load_voyages(self) -> None:
        self._voyage_combo.clear()
        self._voyages = []
        if not self._current_ship or not self._current_ship.id:
            self._condition_combo.clear()
            self._conditions = []
            return
        if database.SessionLocal is None:
            return
        with database.SessionLocal() as db:
            svc = VoyageService(db)
            self._voyages = svc.list_voyages_for_ship(self._current_ship.id)

        self._voyage_combo.addItem("-- None (ad-hoc) --", None)
        for v in self._voyages:
            self._voyage_combo.addItem(f"{v.name} ({v.departure_port}→{v.arrival_port})", v.id)
        self._voyage_combo.setCurrentIndex(0)
        self._on_voyage_changed(0)

    def _load_conditions(self) -> None:
        self._condition_combo.clear()
        self._conditions = []
        if not self._current_voyage or not self._current_voyage.id:
            return
        if database.SessionLocal is None:
            return
        with database.SessionLocal() as db:
            svc = VoyageService(db)
            self._conditions = svc.list_conditions_for_voyage(self._current_voyage.id)

        self._condition_combo.addItem("-- New --", None)
        for c in self._conditions:
            self._condition_combo.addItem(c.name, c.id)
        self._condition_combo.setCurrentIndex(0)
        self._on_condition_changed(0)

    def _set_current_ship(self, ship: Ship) -> None:
        self._current_ship = ship
        if database.SessionLocal is None:
            return
        with database.SessionLocal() as db:
            cond_service = ConditionService(db)
            tanks = cond_service.get_tanks_for_ship(ship.id)

        volumes: Dict[int, float] = {}
        pen_loadings: Dict[int, int] = {}
        if self._current_condition:
            volumes = self._current_condition.tank_volumes_m3
            pen_loadings = getattr(self._current_condition, "pen_loadings", {}) or {}
        self._populate_tanks_table(tanks, volumes)
        pens = cond_service.get_pens_for_ship(ship.id)
        self._populate_pens_table(pens, pen_loadings)

    def _populate_tanks_table(
        self, tanks: List[Tank], volumes: Dict[int, float] | None = None
    ) -> None:
        volumes = volumes or {}
        self._tank_table.setRowCount(0)
        for tank in tanks:
            row = self._tank_table.rowCount()
            self._tank_table.insertRow(row)

            name_item = QTableWidgetItem(tank.name)
            name_item.setData(Qt.ItemDataRole.UserRole, tank.id)

            cap_item = QTableWidgetItem(f"{tank.capacity_m3:.2f}")
            vol = volumes.get(tank.id or -1, 0.0)
            fill_pct = (vol / tank.capacity_m3 * 100.0) if tank.capacity_m3 > 0 else 0.0
            fill_item = QTableWidgetItem(f"{fill_pct:.1f}")

            self._tank_table.setItem(row, 0, name_item)
            self._tank_table.setItem(row, 1, cap_item)
            self._tank_table.setItem(row, 2, fill_item)

    def _populate_pens_table(
        self, pens: list, pen_loadings: Dict[int, int] | None = None
    ) -> None:
        loadings = pen_loadings or {}
        self._pen_table.setRowCount(0)
        for pen in pens:
            row = self._pen_table.rowCount()
            self._pen_table.insertRow(row)
            name_item = QTableWidgetItem(pen.name)
            name_item.setData(Qt.ItemDataRole.UserRole, pen.id)
            self._pen_table.setItem(row, 0, name_item)
            self._pen_table.setItem(row, 1, QTableWidgetItem(pen.deck))
            self._pen_table.setItem(row, 2, QTableWidgetItem(f"{pen.area_m2:.2f}"))
            heads = loadings.get(pen.id or -1, 0)
            self._pen_table.setItem(row, 3, QTableWidgetItem(str(heads)))

    def load_condition(self, voyage_id: int, condition_id: int) -> None:
        """Load a stored condition for editing. Called when user clicks Edit in Voyage Planner."""
        if database.SessionLocal is None:
            return
        with database.SessionLocal() as db:
            svc = VoyageService(db)
            voyage = svc.get_voyage(voyage_id)
            condition = svc.get_condition(condition_id)
        if not voyage or not condition:
            return

        ship = next((s for s in self._ships if s.id == voyage.ship_id), None)
        if not ship:
            with database.SessionLocal() as db:
                ship = ShipRepository(db).get(voyage.ship_id)
            if ship:
                self._ships.append(ship)
                self._ship_combo.addItem(ship.name, ship.id)

        self._current_ship = ship
        self._current_voyage = voyage
        self._current_condition = condition

        self._ship_combo.blockSignals(True)
        idx = self._ship_combo.findData(voyage.ship_id)
        if idx >= 0:
            self._ship_combo.setCurrentIndex(idx)
        self._ship_combo.blockSignals(False)

        self._load_voyages()

        self._voyage_combo.blockSignals(True)
        idx = self._voyage_combo.findData(voyage_id)
        if idx >= 0:
            self._voyage_combo.setCurrentIndex(idx)
        self._voyage_combo.blockSignals(False)

        self._load_conditions()

        self._condition_combo.blockSignals(True)
        idx = self._condition_combo.findData(condition_id)
        if idx >= 0:
            self._condition_combo.setCurrentIndex(idx)
        self._condition_combo.blockSignals(False)

        self._condition_name_edit.setText(condition.name)
        self._save_condition_btn.setEnabled(True)
        if ship:
            with database.SessionLocal() as db:
                cond_svc = ConditionService(db)
                tanks = cond_svc.get_tanks_for_ship(ship.id)
                pens = cond_svc.get_pens_for_ship(ship.id)
            self._populate_tanks_table(tanks, condition.tank_volumes_m3)
            self._populate_pens_table(
                pens, getattr(condition, "pen_loadings", {}) or {}
            )

    def _on_ship_changed(self, index: int) -> None:
        if index < 0 or index >= len(self._ships):
            self._current_ship = None
            self._voyage_combo.clear()
            self._condition_combo.clear()
            self._tank_table.setRowCount(0)
            return
        self._current_ship = self._ships[index]
        self._current_voyage = None
        self._current_condition = None
        self._load_voyages()
        self._set_current_ship(self._current_ship)

    def _on_voyage_changed(self, index: int) -> None:
        if index <= 0:
            self._current_voyage = None
            self._current_condition = None
        elif index - 1 < len(self._voyages):
            self._current_voyage = self._voyages[index - 1]
            self._current_condition = None
        self._load_conditions()
        self._save_condition_btn.setEnabled(self._current_voyage is not None)
        if self._current_ship:
            self._set_current_ship(self._current_ship)

    def _on_condition_changed(self, index: int) -> None:
        if index <= 0:
            self._current_condition = None
            self._condition_name_edit.clear()
        elif index - 1 < len(self._conditions):
            self._current_condition = self._conditions[index - 1]
            self._condition_name_edit.setText(self._current_condition.name)
        self._save_condition_btn.setEnabled(self._current_voyage is not None)
        if self._current_ship:
            self._set_current_ship(self._current_ship)

    def _on_compute(self) -> None:
        if not self._current_ship or self._current_ship.id is None:
            QMessageBox.information(self, "No ship", "Please select a ship first.")
            return

        condition_name = self._condition_name_edit.text().strip() or "Condition"

        condition = LoadingCondition(
            id=self._current_condition.id if self._current_condition else None,
            voyage_id=self._current_voyage.id if self._current_voyage else None,
            name=condition_name,
        )

        tank_volumes: Dict[int, float] = {}
        pen_loadings: Dict[int, int] = {}

        if database.SessionLocal is None:
            QMessageBox.critical(self, "Error", "Database not initialized.")
            return

        with database.SessionLocal() as db:
            cond_service = ConditionService(db)
            tanks = cond_service.get_tanks_for_ship(self._current_ship.id)
            tank_by_id = {t.id: t for t in tanks}

        for row in range(self._tank_table.rowCount()):
            name_item = self._tank_table.item(row, 0)
            fill_item = self._tank_table.item(row, 2)
            if not name_item or not fill_item:
                continue

            tank_id = name_item.data(Qt.ItemDataRole.UserRole)
            if tank_id is None:
                continue

            try:
                fill_pct = float(fill_item.text())
            except (TypeError, ValueError):
                fill_pct = 0.0

            fill_pct = max(0.0, min(100.0, fill_pct))
            tank = tank_by_id.get(int(tank_id))
            if not tank:
                continue

            vol = tank.capacity_m3 * (fill_pct / 100.0)
            tank_volumes[int(tank_id)] = vol

        for row in range(self._pen_table.rowCount()):
            name_item = self._pen_table.item(row, 0)
            head_item = self._pen_table.item(row, 3)
            if not name_item or not head_item:
                continue
            pen_id = name_item.data(Qt.ItemDataRole.UserRole)
            if pen_id is None:
                continue
            try:
                heads = int(float(head_item.text()))
            except (TypeError, ValueError):
                heads = 0
            heads = max(0, heads)
            if heads > 0:
                pen_loadings[int(pen_id)] = heads

        condition.tank_volumes_m3 = tank_volumes
        condition.pen_loadings = pen_loadings

        try:
            results: ConditionResults = cond_service.compute(
                self._current_ship, condition, tank_volumes
            )
        except ConditionValidationError as exc:
            QMessageBox.warning(self, "Validation", str(exc))
            return

        self._current_condition = condition
        voyage = self._current_voyage
        self.condition_computed.emit(results, self._current_ship, condition, voyage)
        validation = getattr(results, "validation", None)
        if validation and getattr(validation, "has_errors", False):
            QMessageBox.warning(
                self,
                "Computed – FAILED",
                "Condition computed but fails validation. Check Results tab.",
            )
        else:
            QMessageBox.information(self, "Computed", "Condition results computed.")

    def _on_save_condition(self) -> None:
        if not self._current_voyage or not self._current_voyage.id:
            QMessageBox.information(
                self, "Save", "Select a voyage first to save a condition."
            )
            return
        if not self._current_ship:
            return
        if database.SessionLocal is None:
            return

        # Build condition from current form (same as compute but we need volumes)
        condition_name = self._condition_name_edit.text().strip() or "Condition"
        tank_volumes: Dict[int, float] = {}
        pen_loadings: Dict[int, int] = {}

        with database.SessionLocal() as db:
            cond_service = ConditionService(db)
            tanks = cond_service.get_tanks_for_ship(self._current_ship.id)
            tank_by_id = {t.id: t for t in tanks}

        for row in range(self._tank_table.rowCount()):
            name_item = self._tank_table.item(row, 0)
            fill_item = self._tank_table.item(row, 2)
            if not name_item or not fill_item:
                continue
            tank_id = name_item.data(Qt.ItemDataRole.UserRole)
            if tank_id is None:
                continue
            try:
                fill_pct = float(fill_item.text())
            except (TypeError, ValueError):
                fill_pct = 0.0
            fill_pct = max(0.0, min(100.0, fill_pct))
            tank = tank_by_id.get(int(tank_id))
            if not tank:
                continue
            tank_volumes[int(tank_id)] = tank.capacity_m3 * (fill_pct / 100.0)

        for row in range(self._pen_table.rowCount()):
            name_item = self._pen_table.item(row, 0)
            head_item = self._pen_table.item(row, 3)
            if not name_item or not head_item:
                continue
            pen_id = name_item.data(Qt.ItemDataRole.UserRole)
            if pen_id is None:
                continue
            try:
                heads = int(float(head_item.text()))
            except (TypeError, ValueError):
                heads = 0
            if heads > 0:
                pen_loadings[int(pen_id)] = heads

        condition = LoadingCondition(
            id=self._current_condition.id if self._current_condition else None,
            voyage_id=self._current_voyage.id,
            name=condition_name,
            tank_volumes_m3=tank_volumes,
            pen_loadings=pen_loadings,
        )

        with database.SessionLocal() as db:
            svc = VoyageService(db)
            cond_svc = ConditionService(db)
            try:
                results = cond_svc.compute(self._current_ship, condition, tank_volumes)
                condition.displacement_t = results.displacement_t
                condition.draft_m = results.draft_m
                condition.trim_m = results.trim_m
                condition.gm_m = results.gm_m
                condition = svc.save_condition(condition)
            except (ConditionValidationError, VoyageValidationError) as exc:
                QMessageBox.warning(self, "Validation", str(exc))
                return

        self._current_condition = condition
        self._load_conditions()
        QMessageBox.information(self, "Saved", "Condition saved.")


