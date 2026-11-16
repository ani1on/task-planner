"""Простые векторные иконки, нарисованные через QPainter.

Отдельный набор нужен, чтобы не тянуть внешние ресурсы: иконки
рисуются в рантайме монохромным цветом и масштабируются под нужный размер.
"""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

DEFAULT_COLOR = "#8a919b"


def _grid(painter: QPainter, size: float):
    margin = size * 0.2
    gap = size * 0.14
    box = (size - 2 * margin - gap) / 2

    for row in range(2):
        for col in range(2):
            x = margin + col * (box + gap)
            y = margin + row * (box + gap)
            painter.drawRoundedRect(QRectF(x, y, box, box), 2, 2)


def _list(painter: QPainter, size: float):
    margin = size * 0.22
    for index in range(3):
        y = margin + index * (size - 2 * margin) / 2
        painter.drawEllipse(QPointF(margin, y), 1.0, 1.0)
        painter.drawLine(QPointF(margin + 4.5, y), QPointF(size - margin, y))


def _columns(painter: QPainter, size: float):
    margin = size * 0.2
    gap = size * 0.1
    width = (size - 2 * margin - 2 * gap) / 3
    height = size - 2 * margin

    for index in range(3):
        x = margin + index * (width + gap)
        painter.drawRoundedRect(QRectF(x, margin, width, height), 1.5, 1.5)


def _folder(painter: QPainter, size: float):
    margin = size * 0.18
    width = size - 2 * margin
    top = size * 0.3
    height = size * 0.5

    path = QPainterPath()
    path.moveTo(margin, top + height)
    path.lineTo(margin, top)
    path.lineTo(margin + width * 0.42, top)
    path.lineTo(margin + width * 0.52, top + height * 0.16)
    path.lineTo(margin + width, top + height * 0.16)
    path.lineTo(margin + width, top + height)
    path.closeSubpath()

    painter.drawPath(path)


def _calendar(painter: QPainter, size: float):
    margin = size * 0.18
    width = size - 2 * margin
    top = size * 0.28
    height = size * 0.62

    painter.drawRoundedRect(QRectF(margin, top, width, height), 2, 2)
    painter.drawLine(
        QPointF(margin, top + height * 0.28),
        QPointF(margin + width, top + height * 0.28),
    )
    painter.drawLine(
        QPointF(margin + width * 0.3, top - height * 0.16),
        QPointF(margin + width * 0.3, top + height * 0.08),
    )
    painter.drawLine(
        QPointF(margin + width * 0.7, top - height * 0.16),
        QPointF(margin + width * 0.7, top + height * 0.08),
    )


def _note(painter: QPainter, size: float):
    margin = size * 0.2
    width = size - 2 * margin
    height = size - 2 * margin
    fold = width * 0.35

    path = QPainterPath()
    path.moveTo(margin, margin)
    path.lineTo(margin + width - fold, margin)
    path.lineTo(margin + width, margin + fold)
    path.lineTo(margin + width, margin + height)
    path.lineTo(margin, margin + height)
    path.closeSubpath()

    painter.drawPath(path)
    painter.drawLine(
        QPointF(margin + width - fold, margin),
        QPointF(margin + width - fold, margin + fold),
    )
    painter.drawLine(
        QPointF(margin + width - fold, margin + fold),
        QPointF(margin + width, margin + fold),
    )
    painter.drawLine(
        QPointF(margin + width * 0.2, margin + height * 0.58),
        QPointF(margin + width * 0.8, margin + height * 0.58),
    )
    painter.drawLine(
        QPointF(margin + width * 0.2, margin + height * 0.76),
        QPointF(margin + width * 0.6, margin + height * 0.76),
    )


def _sliders(painter: QPainter, size: float):
    margin = size * 0.2
    positions = (0.36, 0.68, 0.46)

    for index, ratio in enumerate(positions):
        y = margin + index * (size - 2 * margin) / 2
        painter.drawLine(QPointF(margin, y), QPointF(size - margin, y))
        painter.drawEllipse(
            QPointF(margin + (size - 2 * margin) * ratio, y),
            1.7,
            1.7,
        )


def _search(painter: QPainter, size: float):
    margin = size * 0.22
    radius = size * 0.25
    center = QPointF(margin + radius, margin + radius)

    painter.drawEllipse(center, radius, radius)
    painter.drawLine(
        QPointF(center.x() + radius * 0.72, center.y() + radius * 0.72),
        QPointF(size - margin, size - margin),
    )


def _bell(painter: QPainter, size: float):
    margin = size * 0.2
    width = size - 2 * margin

    path = QPainterPath()
    path.moveTo(margin, size * 0.68)
    path.lineTo(margin + width * 0.12, size * 0.6)
    path.lineTo(margin + width * 0.12, size * 0.44)
    path.cubicTo(
        margin + width * 0.12,
        size * 0.16,
        margin + width * 0.88,
        size * 0.16,
        margin + width * 0.88,
        size * 0.44,
    )
    path.lineTo(margin + width * 0.88, size * 0.6)
    path.lineTo(margin + width, size * 0.68)
    path.closeSubpath()

    painter.drawPath(path)
    painter.drawLine(
        QPointF(margin + width * 0.38, size * 0.8),
        QPointF(margin + width * 0.62, size * 0.8),
    )


def _sun(painter: QPainter, size: float):
    center = QPointF(size / 2, size / 2)
    radius = size * 0.19

    painter.drawEllipse(center, radius, radius)

    for index in range(8):
        angle = math.pi * index / 4
        inner = radius * 1.5
        outer = radius * 2.0
        painter.drawLine(
            QPointF(
                center.x() + math.cos(angle) * inner,
                center.y() + math.sin(angle) * inner,
            ),
            QPointF(
                center.x() + math.cos(angle) * outer,
                center.y() + math.sin(angle) * outer,
            ),
        )


def _moon(painter: QPainter, size: float):
    radius = size * 0.3

    full = QPainterPath()
    full.addEllipse(QPointF(size * 0.5, size * 0.5), radius, radius)

    cut = QPainterPath()
    cut.addEllipse(QPointF(size * 0.66, size * 0.38), radius * 0.92, radius * 0.92)

    painter.drawPath(full.subtracted(cut))


def _logout(painter: QPainter, size: float):
    margin = size * 0.2

    painter.drawLine(QPointF(margin, margin), QPointF(margin, size - margin))
    painter.drawLine(QPointF(margin, margin), QPointF(size * 0.52, margin))
    painter.drawLine(
        QPointF(margin, size - margin),
        QPointF(size * 0.52, size - margin),
    )
    painter.drawLine(
        QPointF(size * 0.46, size / 2),
        QPointF(size - margin, size / 2),
    )
    painter.drawLine(
        QPointF(size - margin - size * 0.14, size / 2 - size * 0.13),
        QPointF(size - margin, size / 2),
    )
    painter.drawLine(
        QPointF(size - margin - size * 0.14, size / 2 + size * 0.13),
        QPointF(size - margin, size / 2),
    )


def _plus(painter: QPainter, size: float):
    margin = size * 0.25

    painter.drawLine(QPointF(size / 2, margin), QPointF(size / 2, size - margin))
    painter.drawLine(QPointF(margin, size / 2), QPointF(size - margin, size / 2))


def _clock(painter: QPainter, size: float):
    center = QPointF(size / 2, size / 2)
    radius = size * 0.3

    painter.drawEllipse(center, radius, radius)
    painter.drawLine(center, QPointF(center.x(), center.y() - radius * 0.6))
    painter.drawLine(
        center, QPointF(center.x() + radius * 0.5, center.y() + radius * 0.32)
    )


def _eye(painter: QPainter, size: float):
    margin = size * 0.16
    width = size - 2 * margin
    height = width * 0.6
    top = (size - height) / 2

    path = QPainterPath()
    path.moveTo(margin, size / 2)
    path.cubicTo(
        margin + width * 0.28,
        top,
        margin + width * 0.72,
        top,
        margin + width,
        size / 2,
    )
    path.cubicTo(
        margin + width * 0.72,
        top + height,
        margin + width * 0.28,
        top + height,
        margin,
        size / 2,
    )

    painter.drawPath(path)
    painter.drawEllipse(QPointF(size / 2, size / 2), width * 0.14, width * 0.14)


def _eye_off(painter: QPainter, size: float):
    _eye(painter, size)
    painter.drawLine(
        QPointF(size * 0.2, size * 0.8),
        QPointF(size * 0.8, size * 0.2),
    )


_DRAWERS = {
    "grid": _grid,
    "list": _list,
    "columns": _columns,
    "folder": _folder,
    "calendar": _calendar,
    "note": _note,
    "sliders": _sliders,
    "search": _search,
    "bell": _bell,
    "sun": _sun,
    "moon": _moon,
    "logout": _logout,
    "plus": _plus,
    "clock": _clock,
    "eye": _eye,
    "eye_off": _eye_off,
}


def make_icon(
    name: str,
    color: str = DEFAULT_COLOR,
    size: int = 18,
) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pen = QPen(QColor(color))
    pen.setWidthF(1.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    drawer = _DRAWERS.get(name)
    if drawer is not None:
        drawer(painter, float(size))

    painter.end()

    return QIcon(pixmap)
