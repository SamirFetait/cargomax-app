"""
Qt main window for the CargoMax desktop app.
"""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QWidget,
    QToolBar,
    QLabel,
    QStatusBar,
    QFrame,
)

from ..config.settings import Settings
from .ship_manager_view import ShipManagerView
from .voyage_planner_view import VoyagePlannerView
from .condition_editor_view import ConditionEditorView
from .results_view import ResultsView
from .test_view import TestView  # For development/testing purposes


@dataclass
class _PageIndexes:
    ship_manager: int
    voyage_planner: int
    condition_editor: int
    results: int
    test: int  # For development/testing purposes


class MainWindow(QMainWindow):
    """Main application window with navigation and central stacked views."""

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Osama bay app")
        self.resize(1200, 800)

        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)

        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)

        self._page_indexes = self._create_pages()
        self._create_menu()
        self._create_toolbar()

        self._status_bar.showMessage("Ready")

    def _create_pages(self) -> _PageIndexes:
        """Create core application pages and add them to the stacked widget."""
        # Keep references to views to allow signal wiring between them
        self._ship_manager = ShipManagerView(self)
        self._voyage_planner = VoyagePlannerView(self)
        self._condition_editor = ConditionEditorView(self)
        self._results_view = ResultsView(self)
        self._test_view = TestView(self)  # For development/testing purposes

        ship_idx = self._stack.addWidget(self._ship_manager)
        voy_idx = self._stack.addWidget(self._voyage_planner)
        cond_idx = self._stack.addWidget(self._condition_editor)
        res_idx = self._stack.addWidget(self._results_view)
        test_idx = self._stack.addWidget(self._test_view)

        # Default page
        self._stack.setCurrentIndex(ship_idx)

        pages = _PageIndexes(
            ship_manager=ship_idx,
            voyage_planner=voy_idx,
            condition_editor=cond_idx,
            results=res_idx,
            test=test_idx,  # For development/testing purposes
        )

        # Wire condition editor to results view
        self._condition_editor.condition_computed.connect(
            self._results_view.update_results
        )

        # Wire voyage planner: when user clicks Edit Condition, switch to editor and load it
        self._voyage_planner.condition_selected.connect(
            self._on_condition_selected_from_voyage
        )

        return pages

    def _on_condition_selected_from_voyage(self, voyage_id: int, condition_id: int) -> None:
        self._condition_editor.load_condition(voyage_id, condition_id)
        self._stack.setCurrentIndex(self._page_indexes.condition_editor)
        self._status_bar.showMessage("Loading Condition")

    def _create_menu(self) -> None:
        """Create the menu bar and actions."""
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        edit_menu = menu_bar.addMenu("&Edit")
        view_menu = menu_bar.addMenu("&View")
        tools_menu = menu_bar.addMenu("&Tools")
        Damage_menu = menu_bar.addMenu("&Damage")
        Grounding_menu = menu_bar.addMenu("&Grounding")
        History_menu = menu_bar.addMenu("&History")
        help_menu = menu_bar.addMenu("&Help")

        # File actions
        new_action = QAction("&New Loading condition ...                       CTRL+N", self)
        new_action.triggered.connect(lambda: self._status_bar.showMessage("New Loading Condition"))
        file_menu.addAction(new_action)

        open_action = QAction("&Open Loading condition ...                     CTRL+O", self)
        open_action.triggered.connect(lambda: self._status_bar.showMessage("Open Loading Condition"))
        file_menu.addAction(open_action)

        open_recent_action = QAction("&Open Recent Loading conditions ...", self)
        open_recent_action.triggered.connect(lambda: self._status_bar.showMessage("Open Recent Loading Conditions"))
        file_menu.addAction(open_recent_action)

        open_standard_action = QAction("&Open Standard Loading conditions ...", self)
        open_standard_action.triggered.connect(lambda: self._status_bar.showMessage("Open Standard Loading Conditions"))
        file_menu.addAction(open_standard_action)

        save_action = QAction("&Save Loading condition ...                     CTRL+S", self)
        save_action.triggered.connect(lambda: self._status_bar.showMessage("Save Loading Condition"))
        file_menu.addAction(save_action)

        save_as_action = QAction("&Save Loading condition As ...", self)
        save_as_action.triggered.connect(lambda: self._status_bar.showMessage("Save Loading Condition As"))
        file_menu.addAction(save_as_action)

        import_action = QAction("&Import from Excel ...", self)
        import_action.triggered.connect(lambda: self._status_bar.showMessage("Import from Excel"))
        file_menu.addAction(import_action)

        export_action = QAction("&Export to Excel ...", self)
        export_action.triggered.connect(lambda: self._status_bar.showMessage("Export to Excel"))
        file_menu.addAction(export_action)

        summary_action = QAction("&Summary Info ...", self)
        summary_action.triggered.connect(lambda: self._status_bar.showMessage("Summary Info"))
        file_menu.addAction(summary_action)

        program_notes_action = QAction("&Program Notes ...", self)
        program_notes_action.triggered.connect(lambda: self._status_bar.showMessage("Program Notes"))
        file_menu.addAction(program_notes_action)

        send_loading_condition_by_email_action = QAction("&Send Loading condition by email ...", self)
        send_loading_condition_by_email_action.triggered.connect(lambda: self._status_bar.showMessage("Send Loading Condition by Email"))
        file_menu.addAction(send_loading_condition_by_email_action)

        print_action = QAction("&Print ...", self)
        print_action.triggered.connect(lambda: self._status_bar.showMessage("Print"))
        file_menu.addAction(print_action)

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        #edit actions
        edit_item_action = QAction("&Edit item ...", self)
        edit_item_action.triggered.connect(lambda: self._status_bar.showMessage("Edit Item"))
        edit_menu.addAction(edit_item_action)

        delete_item_action = QAction("&Delete item(s) ...", self)
        delete_item_action.triggered.connect(lambda: self._status_bar.showMessage("Delete Item(s)"))
        edit_menu.addAction(delete_item_action)

        search_new_misc_weight_action = QAction("&Search item ...", self)
        search_new_misc_weight_action.triggered.connect(lambda: self._status_bar.showMessage("Search Item"))
        edit_menu.addAction(search_new_misc_weight_action)

        add_new_item_action = QAction("&Add new item ...", self)
        add_new_item_action.triggered.connect(lambda: self._status_bar.showMessage("Add New Item"))
        edit_menu.addAction(add_new_item_action)

        empty_space_action = QAction("&Empty space(s)...", self)
        empty_space_action.triggered.connect(lambda: self._status_bar.showMessage("Empty Space(s)"))
        edit_menu.addAction(empty_space_action)

        fill_space_action = QAction("&Fill space(s)...", self)
        fill_space_action.triggered.connect(lambda: self._status_bar.showMessage("Fill Space(s)"))
        edit_menu.addAction(fill_space_action)

        fill_spaces_action = QAction("&Fill spaces To..", self)
        fill_spaces_action.triggered.connect(lambda: self._status_bar.showMessage("Fill Spaces To.."))
        edit_menu.addAction(fill_spaces_action)

        select_all_action = QAction("&Select all", self)
        select_all_action.triggered.connect(lambda: self._status_bar.showMessage("Select All"))
        edit_menu.addAction(select_all_action)

        clear_selection_action = QAction("&Clear selection", self)
        clear_selection_action.triggered.connect(lambda: self._status_bar.showMessage("Clear Selection"))
        edit_menu.addAction(clear_selection_action)

        # View actions
        ship_action = QAction("&Ship Manager", self)
        ship_action.triggered.connect(
            lambda: self._switch_page(self._page_indexes.ship_manager, "Ship Manager")
        )

        voyage_action = QAction("&Voyage Planner", self)
        voyage_action.triggered.connect(
            lambda: self._switch_page(
                self._page_indexes.voyage_planner, "Voyage Planner"
            )
        )

        condition_action = QAction("&Loading Condition", self)
        condition_action.triggered.connect(
            lambda: self._switch_page(
                self._page_indexes.condition_editor, "Loading Condition"
            )
        )

        results_action = QAction("&Results", self)
        results_action.triggered.connect(
            lambda: self._switch_page(self._page_indexes.results, "Results")
        )

        for action in (
            ship_action,
            voyage_action,
            condition_action,
            results_action,
        ):
            view_menu.addAction(action)

        # Help menu
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self) -> None:
        """Create a simple navigation toolbar."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)

        def add_nav_button(text: str, page_index: int, status: str) -> None:
            action = toolbar.addAction(text)
            action.triggered.connect(lambda: self._switch_page(page_index, status))

        add_nav_button("Ship Manager", self._page_indexes.ship_manager, "Ship Manager")
        add_nav_button(
            "Voyage Planner", self._page_indexes.voyage_planner, "Voyage Planner"
        )
        add_nav_button(
            "Loading Condition",
            self._page_indexes.condition_editor,
            "Loading Condition",
        )
        add_nav_button("Results", self._page_indexes.results, "Results")
        add_nav_button("test", self._page_indexes.test, "test")  # For development/testing purposes

    def _switch_page(self, index: int, status_message: str) -> None:
        self._stack.setCurrentIndex(index)
        self._status_bar.showMessage(status_message)

    def _show_about(self) -> None:
        # Keep it lightweight for now – can replace with a dialog later
        self._status_bar.showMessage("CargoMax Desktop – Prototype", 5000)

