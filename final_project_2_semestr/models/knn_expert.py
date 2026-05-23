import cv2
import numpy as np
from .algorithm_plugin import AlgorithmMeta


class KNNExpertModel(AlgorithmMeta, algorithm_name="knn_expert"):
    """
    Подсчёт тёмных пятен фиксированным порогом + фильтрация.
    """

    def __init__(
        self,
        threshold: int = 150,
        min_area: int = 30,
        max_area: int = 20000,
        close_iter: int = 2,
    ):
        self.threshold = threshold
        self.min_area = min_area
        self.max_area = max_area
        self.close_iter = close_iter

    def get_name(self) -> str:
        return "KNN + экспертная перекодировка"

    def count_cells(self, image: np.ndarray) -> int:
        if image.shape[-1] != 3:
            raise ValueError(f"Expected 3-channel image, got shape {image.shape}")

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Фиксированный порог
        _, binary = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY_INV)

        # Закрываем дырки внутри пятен
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close, iterations=self.close_iter)

        # Убираем мелкий шум
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)

        count = 0
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if self.min_area <= area <= self.max_area:
                count += 1

        return count