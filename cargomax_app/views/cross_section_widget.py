"""
Cross-section/stability diagram widget.

Shows a simplified cross-section view of the ship hull with waterline
and stability indicators.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGraphicsScene,
)

from .graphics_views import ShipGraphicsView


class CrossSectionView(ShipGraphicsView):
    """
    Cross-section view showing hull shape, waterline, and stability indicators.
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        self._waterline_item = None
        self._hull_item = None
        
        self._draw_placeholder()
        
    def _draw_placeholder(self) -> None:
        """Draw a placeholder cross-section."""
        self._scene.clear()
        
        # Draw water area (blue rectangle)
        water_rect = QRectF(-300, -100, 600, 200)
        water_brush = QBrush(QColor(173, 216, 230, 150))  # Light blue, semi-transparent
        water_pen = QPen(QColor(100, 150, 200), 1)
        self._scene.addRect(water_rect, water_pen, water_brush)
        
        # Draw hull cross-section (inverted triangle/trapezoid shape)
        from PyQt6.QtGui import QPainterPath
        hull_path = QPainterPath()
        hull_path.moveTo(-250, -50)  # Port side at waterline
        hull_path.lineTo(-300, -100)  # Port bottom
        hull_path.lineTo(300, -100)   # Starboard bottom
        hull_path.lineTo(250, -50)    # Starboard side at waterline
        hull_path.closeSubpath()
        
        hull_brush = QBrush(QColor(200, 200, 200))
        hull_pen = QPen(QColor(100, 100, 100), 2)
        self._hull_item = self._scene.addPath(hull_path, hull_pen, hull_brush)
        
        # Draw deckhouses/cargo units above waterline
        deckhouse1 = QRectF(-100, -150, 80, 50)
        self._scene.addRect(deckhouse1, QPen(QColor(150, 150, 150)), QBrush(QColor(180, 180, 180)))
        
        deckhouse2 = QRectF(20, -150, 80, 50)
        self._scene.addRect(deckhouse2, QPen(QColor(150, 150, 150)), QBrush(QColor(180, 180, 180)))
        
        # Add text label
        font = QFont("Arial", 9)
        label = self._scene.addText("[164] 115.000F-Looking Fwd", font)
        label.setDefaultTextColor(QColor(80, 80, 80))
        label.setPos(-280, -180)
        
        # Fit view
        if self._scene.items():
            self.fitInView(self._scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
    def update_waterline(self, draft: float, breadth: float = 20.0) -> None:
        """
        Update waterline position based on draft.
        
        Args:
            draft: Draft in meters
            breadth: Ship breadth in meters (for scaling)
        """
        # Scale draft to scene coordinates
        scale = 200.0 / max(breadth, 1.0)  # Scene height ~200 units
        y_waterline = -50 - (draft * scale)
        
        # Remove old waterline
        if self._waterline_item:
            self._scene.removeItem(self._waterline_item)
            
        # Draw new waterline
        waterline_pen = QPen(QColor(0, 100, 200), 2)
        self._waterline_item = self._scene.addLine(-300, y_waterline, 300, y_waterline, waterline_pen)
        if self._waterline_item:
            self._waterline_item.setZValue(100)


class CrossSectionWidget(QWidget):
    """
    Widget container for cross-section view.
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._view = CrossSectionView(self)
        layout.addWidget(self._view)
        
    def update_waterline(self, draft: float, breadth: float = 20.0) -> None:
        """Update waterline in cross-section view."""
        self._view.update_waterline(draft, breadth)
