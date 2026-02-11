"""
Results view.

Displays basic calculated results for a loading condition and a simple
text report generated from the reports module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QSplitter,
    QGroupBox,
)
from PyQt6.QtCore import Qt

from ..models import Voyage
from ..reports import build_condition_summary_text, export_condition_to_pdf, export_condition_to_excel
from ..services.stability_service import ConditionResults
from ..services.validation import ValidationResult
from ..services.criteria_rules import CriterionResult
from ..services.alarms import build_alarm_rows, AlarmStatus


class ResultsView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._ship_name = QLineEdit(self)
        self._condition_name = QLineEdit(self)
        self._disp_edit = QLineEdit(self)
        self._draft_edit = QLineEdit(self)
        self._draft_aft_edit = QLineEdit(self)
        self._draft_fwd_edit = QLineEdit(self)
        self._trim_edit = QLineEdit(self)
        self._heel_edit = QLineEdit(self)
        self._gm_edit = QLineEdit(self)
        self._kg_edit = QLineEdit(self)
        self._km_edit = QLineEdit(self)
        self._swbm_edit = QLineEdit(self)
        self._bm_pct_edit = QLineEdit(self)
        self._sf_pct_edit = QLineEdit(self)
        self._prop_imm_edit = QLineEdit(self)
        self._visibility_edit = QLineEdit(self)
        self._air_draft_edit = QLineEdit(self)
        for w in (
            self._ship_name,
            self._condition_name,
            self._disp_edit,
            self._draft_edit,
            self._draft_aft_edit,
            self._draft_fwd_edit,
            self._trim_edit,
            self._heel_edit,
            self._gm_edit,
            self._kg_edit,
            self._km_edit,
            self._swbm_edit,
            self._bm_pct_edit,
            self._sf_pct_edit,
            self._prop_imm_edit,
            self._visibility_edit,
            self._air_draft_edit,
        ):
            w.setReadOnly(True)

        self._alarms_table = QTableWidget(self)
        self._alarms_table.setColumnCount(6)
        self._alarms_table.setHorizontalHeaderLabels(
            ["No", "Status", "Description", "Attained", "Pass If", "Type"]
        )
        self._alarms_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._alarms_table.setMaximumHeight(200)

        self._report_view = QPlainTextEdit(self)
        self._report_view.setReadOnly(True)

        self._status_label = QLabel(self)
        self._status_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self._warnings_edit = QPlainTextEdit(self)
        self._warnings_edit.setReadOnly(True)
        self._warnings_edit.setMaximumHeight(80)

        self._criteria_table = QTableWidget(self)
        self._criteria_table.setColumnCount(7)
        self._criteria_table.setHorizontalHeaderLabels(
            ["Rule Set", "Code", "Name", "Result", "Value", "Limit", "Margin"]
        )
        self._criteria_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._criteria_table.setMaximumHeight(180)

        self._trace_label = QLabel(self)
        self._trace_label.setWordWrap(True)

        self._export_pdf_btn = QPushButton("Export PDF", self)
        self._export_excel_btn = QPushButton("Export Excel", self)

        self._last_results: ConditionResults | None = None
        self._last_ship: Any = None
        self._last_condition: Any = None
        self._last_voyage: Voyage | None = None

        self._build_layout()
        self._connect_signals()

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Condition Results", self))

        # Top split: Alarms (left) | Calculation Summary (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        # Alarms panel with tabs
        alarms_tabs = QTabWidget()
        alarms_tabs.addTab(self._alarms_table, "Alarms")
        alarms_weights = QLabel("Weights view – coming soon", self)
        alarms_tabs.addTab(alarms_weights, "Weights")
        alarms_trim = QLabel("Trim & Stability – coming soon", self)
        alarms_tabs.addTab(alarms_trim, "Trim & Stability")
        alarms_str = QLabel("Strength – coming soon", self)
        alarms_tabs.addTab(alarms_str, "Strength")
        alarms_cargo = QLabel("Cargo – coming soon", self)
        alarms_tabs.addTab(alarms_cargo, "Cargo")
        splitter.addWidget(alarms_tabs)

        # Calculation summary group
        summary_group = QGroupBox("Calculation Summary")
        summary_form = QFormLayout()
        summary_form.addRow("Ship:", self._ship_name)
        summary_form.addRow("Condition:", self._condition_name)
        summary_form.addRow("Displacement (t):", self._disp_edit)
        summary_form.addRow("Draft Mid (m):", self._draft_edit)
        summary_form.addRow("Draft Aft (m):", self._draft_aft_edit)
        summary_form.addRow("Draft Fwd (m):", self._draft_fwd_edit)
        summary_form.addRow("Trim (m):", self._trim_edit)
        summary_form.addRow("Heel (°):", self._heel_edit)
        summary_form.addRow("GM (m):", self._gm_edit)
        summary_form.addRow("KG (m):", self._kg_edit)
        summary_form.addRow("KM (m):", self._km_edit)
        summary_form.addRow("SWBM (tm):", self._swbm_edit)
        summary_form.addRow("BM % Allow:", self._bm_pct_edit)
        summary_form.addRow("SF % Allow:", self._sf_pct_edit)
        summary_form.addRow("Prop immersion %:", self._prop_imm_edit)
        summary_form.addRow("Visibility (m):", self._visibility_edit)
        summary_form.addRow("Air draft (m):", self._air_draft_edit)
        summary_group.setLayout(summary_form)
        splitter.addWidget(summary_group)
        splitter.setSizes([400, 280])
        root.addWidget(splitter)

        root.addWidget(self._status_label)
        root.addWidget(QLabel("Validation messages", self))
        root.addWidget(self._warnings_edit)
        root.addWidget(QLabel("IMO & Livestock Criteria Checklist", self))
        root.addWidget(self._criteria_table)
        root.addWidget(QLabel("Calculation traceability", self))
        root.addWidget(self._trace_label)
        root.addWidget(QLabel("Text Report", self))
        root.addWidget(self._report_view, 1)

        export_row = QHBoxLayout()
        export_row.addWidget(self._export_pdf_btn)
        export_row.addWidget(self._export_excel_btn)
        root.addLayout(export_row)

    def _connect_signals(self) -> None:
        self._export_pdf_btn.clicked.connect(self._on_export_pdf)
        self._export_excel_btn.clicked.connect(self._on_export_excel)

    def _populate_alarms_table(
        self,
        results: ConditionResults,
        validation: ValidationResult | None,
        criteria: object | None,
    ) -> None:
        rows = build_alarm_rows(results, validation, criteria)
        self._alarms_table.setRowCount(len(rows))
        for row, ar in enumerate(rows):
            self._alarms_table.setItem(row, 0, QTableWidgetItem(str(ar.no)))
            status_item = QTableWidgetItem(ar.status.value)
            if ar.status == AlarmStatus.PASS:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif ar.status == AlarmStatus.FAIL:
                status_item.setForeground(Qt.GlobalColor.darkRed)
            elif ar.status == AlarmStatus.WARN:
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self._alarms_table.setItem(row, 1, status_item)
            self._alarms_table.setItem(row, 2, QTableWidgetItem(ar.description))
            self._alarms_table.setItem(row, 3, QTableWidgetItem(ar.attained))
            self._alarms_table.setItem(row, 4, QTableWidgetItem(ar.pass_if))
            self._alarms_table.setItem(row, 5, QTableWidgetItem(ar.type.value))

    def _populate_criteria_table(self, criteria: object | None) -> None:
        self._criteria_table.setRowCount(0)
        if not criteria or not hasattr(criteria, "lines"):
            return
        for row, line in enumerate(criteria.lines):
            self._criteria_table.insertRow(row)
            self._criteria_table.setItem(row, 0, QTableWidgetItem(line.parent_code or ""))
            self._criteria_table.setItem(row, 1, QTableWidgetItem(line.code))
            self._criteria_table.setItem(row, 2, QTableWidgetItem(line.name))
            result_item = QTableWidgetItem(line.result.value)
            if line.result == CriterionResult.PASS:
                result_item.setForeground(Qt.GlobalColor.darkGreen)
            elif line.result == CriterionResult.FAIL:
                result_item.setForeground(Qt.GlobalColor.darkRed)
            self._criteria_table.setItem(row, 3, result_item)
            val_str = f"{line.value:.3f}" if line.value is not None else "—"
            self._criteria_table.setItem(row, 4, QTableWidgetItem(val_str))
            lim_str = f"{line.limit:.3f}" if line.limit is not None else "—"
            self._criteria_table.setItem(row, 5, QTableWidgetItem(lim_str))
            marg_str = f"{line.margin:+.3f}" if line.margin is not None else "—"
            self._criteria_table.setItem(row, 6, QTableWidgetItem(marg_str))

    def _populate_traceability(self, snapshot: object | None) -> None:
        if not snapshot:
            self._trace_label.setText("")
            return
        ts = getattr(snapshot, "timestamp", None)
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(ts, "strftime") else str(ts)
        summary = getattr(snapshot, "criteria_summary", "")
        ship = getattr(snapshot, "ship_name", "")
        cond = getattr(snapshot, "condition_name", "")
        self._trace_label.setText(
            f"Calculated: {ts_str} | Ship: {ship} | Condition: {cond} | {summary}"
        )

    def update_results(
        self,
        results: ConditionResults,
        ship: Any,
        condition: Any,
        voyage: Voyage | None = None,
    ) -> None:
        """Slot called when a condition has been computed."""
        self._last_results = results
        self._last_ship = ship
        self._last_condition = condition
        self._last_voyage = voyage or Voyage(
            id=None,
            ship_id=getattr(ship, "id", None),
            name="Ad-hoc",
            departure_port="",
            arrival_port="",
        )

        self._ship_name.setText(getattr(ship, "name", ""))
        self._condition_name.setText(getattr(condition, "name", ""))

        self._disp_edit.setText(f"{results.displacement_t:.1f}")
        self._draft_edit.setText(f"{results.draft_m:.2f}")
        draft_aft = getattr(results, "draft_aft_m", results.draft_m + results.trim_m / 2)
        draft_fwd = getattr(results, "draft_fwd_m", results.draft_m - results.trim_m / 2)
        heel = getattr(results, "heel_deg", 0.0)
        self._draft_aft_edit.setText(f"{draft_aft:.2f}")
        self._draft_fwd_edit.setText(f"{draft_fwd:.2f}")
        self._trim_edit.setText(f"{results.trim_m:.2f}")
        self._heel_edit.setText(f"{heel:.2f}")
        validation: ValidationResult | None = getattr(results, "validation", None)
        gm_display = validation.gm_effective if validation else results.gm_m
        self._gm_edit.setText(f"{gm_display:.2f}")

        if validation:
            if validation.has_errors:
                self._status_label.setText("FAILED – Condition does not meet limits")
                self._status_label.setStyleSheet(
                    "font-weight: bold; font-size: 11pt; color: #c0392b;"
                )
            elif validation.has_warnings:
                self._status_label.setText("WARNING – Review before approval")
                self._status_label.setStyleSheet(
                    "font-weight: bold; font-size: 11pt; color: #d35400;"
                )
            else:
                self._status_label.setText("OK – Within limits")
                self._status_label.setStyleSheet(
                    "font-weight: bold; font-size: 11pt; color: #27ae60;"
                )
            lines = [f"[{i.severity.value.upper()}] {i.message}" for i in validation.issues]
            self._warnings_edit.setPlainText("\n".join(lines) if lines else "No issues.")
        else:
            self._status_label.setText("OK")
            self._status_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
            self._warnings_edit.setPlainText("")
        self._kg_edit.setText(f"{results.kg_m:.2f}")
        self._km_edit.setText(f"{results.km_m:.2f}")
        strength = getattr(results, "strength", None)
        swbm = strength.still_water_bm_approx_tm if strength else 0.0
        bm_pct = getattr(strength, "bm_pct_allow", 0.0) if strength else 0.0
        sf_pct = getattr(strength, "sf_pct_allow", 0.0) if strength else 0.0
        self._swbm_edit.setText(f"{swbm:.0f}")
        self._bm_pct_edit.setText(f"{bm_pct:.1f}%")
        self._sf_pct_edit.setText(f"{sf_pct:.1f}%")

        anc = getattr(results, "ancillary", None)
        if anc:
            self._prop_imm_edit.setText(f"{getattr(anc, 'prop_immersion_pct', 0):.1f}%")
            self._visibility_edit.setText(f"{getattr(anc, 'visibility_m', 0):.1f}")
            self._air_draft_edit.setText(f"{getattr(anc, 'air_draft_m', 0):.1f}")
        else:
            self._prop_imm_edit.setText("")
            self._visibility_edit.setText("")
            self._air_draft_edit.setText("")

        voyage = self._last_voyage

        # Populate alarms table
        self._populate_alarms_table(results, validation, getattr(results, "criteria", None))

        # Populate criteria checklist
        self._populate_criteria_table(getattr(results, "criteria", None))

        # Populate traceability
        self._populate_traceability(getattr(results, "snapshot", None))

        strength = getattr(results, "strength", None)
        swbm = strength.still_water_bm_approx_tm if strength else 0.0
        snapshot = getattr(results, "snapshot", None)
        criteria = getattr(results, "criteria", None)
        crit_sum = ""
        if criteria and hasattr(criteria, "passed") and hasattr(criteria, "failed"):
            crit_sum = f"{criteria.passed} passed, {criteria.failed} failed"
        ts_str = ""
        if snapshot and hasattr(snapshot, "timestamp"):
            ts_str = snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        text = build_condition_summary_text(
            ship, voyage, condition,
            kg_m=results.kg_m,
            km_m=results.km_m,
            swbm_tm=swbm,
            criteria_summary=crit_sum,
            trace_timestamp=ts_str,
        )
        self._report_view.setPlainText(text)

    def _on_export_pdf(self) -> None:
        if not all([self._last_results, self._last_ship, self._last_condition, self._last_voyage]):
            QMessageBox.information(
                self,
                "Export",
                "Compute a condition first to export.",
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PDF",
            str(Path.home()),
            "PDF (*.pdf)",
        )
        if not path:
            return
        try:
            export_condition_to_pdf(
                Path(path),
                self._last_ship,
                self._last_voyage,
                self._last_condition,
                self._last_results,
            )
            QMessageBox.information(self, "Export", f"Saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _on_export_excel(self) -> None:
        if not all([self._last_results, self._last_ship, self._last_condition, self._last_voyage]):
            QMessageBox.information(
                self,
                "Export",
                "Compute a condition first to export.",
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Excel",
            str(Path.home()),
            "Excel (*.xlsx)",
        )
        if not path:
            return
        if not path.endswith(".xlsx"):
            path += ".xlsx"
        try:
            export_condition_to_excel(
                Path(path),
                self._last_ship,
                self._last_voyage,
                self._last_condition,
                self._last_results,
            )
            QMessageBox.information(self, "Export", f"Saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))


