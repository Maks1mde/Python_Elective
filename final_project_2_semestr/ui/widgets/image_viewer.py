from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import numpy as np


class ImageViewer(QScrollArea):
    """Виджет для отображения изображения с возможностью наложения маски."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)

        self.lbl_image = QLabel("Изображение не загружено")
        self.lbl_image.setAlignment(Qt.AlignCenter)
        self.lbl_image.setStyleSheet("color: gray; font-size: 14px;")
        self.setWidget(self.lbl_image)

        self._original_image: np.ndarray | None = None
        self._mask: np.ndarray | None = None
        self._show_mask = False

    def set_image(self, image: np.ndarray):
        """Установка изображения (RGB, HxWx3, uint8)."""
        self._original_image = image
        self._mask = None
        self._show_mask = False
        self._update_display()

    def set_mask(self, mask: np.ndarray):
        """Наложение маски (HxW, uint8 {0,255})."""
        self._mask = mask
        self._update_display()

    def toggle_mask(self, show: bool):
        """Показать/скрыть маску."""
        self._show_mask = show
        self._update_display()

    def _update_display(self):
        """Обновление отображаемого изображения."""
        if self._original_image is None:
            self.lbl_image.setText("Изображение не загружено")
            return

        display = self._original_image.copy()

        if self._show_mask and self._mask is not None:
            # Накладываем маску красным цветом с прозрачностью
            mask_bool = self._mask > 128
            overlay = display.copy()
            overlay[mask_bool] = [255, 0, 0]
            alpha = 0.4
            display = (display * (1 - alpha) + overlay * alpha).astype(np.uint8)

        h, w = display.shape[:2]
        bytes_per_line = 3 * w
        qimage = QImage(
            display.data, w, h, bytes_per_line, QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qimage)

        # Масштабируем под размер виджета
        scaled = pixmap.scaled(
            self.viewport().size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.lbl_image.setPixmap(scaled)