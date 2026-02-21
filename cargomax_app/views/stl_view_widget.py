"""
3D STL view widget using PyVistaQt.

Shows STL mesh(es) in an interactive 3D view (rotate/pan/zoom).
Used instead of 2D DXF for profile and deck drawings.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

# Prefer PyQt6 for PyVistaQt; set before first pyvistaqt import if needed
try:
    import os
    if "QT_API" not in os.environ:
        os.environ["QT_API"] = "pyqt6"
except Exception:
    pass

PYVISTA_AVAILABLE = False
QtInteractor = None
pv = None

try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    PYVISTA_AVAILABLE = True
except ImportError:
    pass


def _load_stl_mesh(path: Path):
    """Load STL into PyVista mesh. Returns None if failed or pyvista unavailable."""
    if not PYVISTA_AVAILABLE or not pv or not path.exists():
        return None
    try:
        mesh = pv.read(str(path))
        return mesh
    except Exception:
        return None


class StlViewWidget(QWidget):
    """
    Widget that displays one or more STL files in an interactive 3D view.
    Replace 2D DXF profile/deck view when STL files are available.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._paths: List[Path] = []
        self._plotter = None
        self._placeholder_label: Optional[QLabel] = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if not PYVISTA_AVAILABLE:
            self._placeholder_label = QLabel(
                "3D view requires pyvista and pyvistaqt.\n"
                "Install: pip install pyvista pyvistaqt"
            )
            self._placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._placeholder_label.setStyleSheet("color: gray; padding: 20px;")
            layout.addWidget(self._placeholder_label)
            return

        self._frame = QFrame(self)
        self._frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame_layout = QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        try:
            self._plotter = QtInteractor(self._frame)
            frame_layout.addWidget(self._plotter.interactor)
            self._plotter.set_background("white")
        except Exception:
            self._placeholder_label = QLabel("Could not create 3D view.")
            layout.addWidget(self._placeholder_label)
            return
        layout.addWidget(self._frame)

    def load_stl(self, path: "Path | str | None") -> bool:
        """
        Load and display STL from the given path.
        If path is None or missing, clear the view.
        Returns True if something was drawn.
        """
        if not PYVISTA_AVAILABLE or self._plotter is None:
            return False
        self._plotter.clear()
        self._paths = []
        if path is None:
            return False
        path = Path(path)
        if not path.exists():
            return False
        mesh = _load_stl_mesh(path)
        if mesh is None:
            return False
        self._plotter.add_mesh(mesh, color="lightgray", show_edges=True)
        self._plotter.reset_camera()
        self._paths.append(path)
        return True

    def load_stl_paths(self, paths: "List[Path] | List[str]") -> bool:
        """Load and display multiple STL files. Returns True if at least one was drawn."""
        if not PYVISTA_AVAILABLE or self._plotter is None:
            return False
        self._plotter.clear()
        self._paths = []
        drawn = False
        for p in paths:
            p = Path(p)
            if not p.exists():
                continue
            mesh = _load_stl_mesh(p)
            if mesh is not None:
                self._plotter.add_mesh(mesh, color="lightgray", show_edges=True)
                self._paths.append(p)
                drawn = True
        if drawn:
            self._plotter.reset_camera()
        return drawn

    def clear(self) -> None:
        """Clear the 3D view."""
        if self._plotter is not None:
            self._plotter.clear()
        self._paths = []

    def fit_to_view(self) -> None:
        """Reset camera to fit content (for zoom/fit from toolbar)."""
        if self._plotter is not None:
            self._plotter.reset_camera()

    def zoom_in(self) -> None:
        """Zoom in (for toolbar)."""
        if self._plotter is not None and hasattr(self._plotter, "camera"):
            self._plotter.camera.zoom(1.25)

    def zoom_out(self) -> None:
        """Zoom out (for toolbar)."""
        if self._plotter is not None and hasattr(self._plotter, "camera"):
            self._plotter.camera.zoom(1.0 / 1.25)


def stl_view_available() -> bool:
    """Return True if 3D STL view can be used (pyvista + pyvistaqt)."""
    return PYVISTA_AVAILABLE
