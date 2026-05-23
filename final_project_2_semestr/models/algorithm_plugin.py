from abc import ABC, abstractmethod
import numpy as np


class AlgorithmMeta(ABC):
    """
    Базовый метакласс для алгоритмов подсчёта клеток.
    Аналог DataLoaderMeta — автоматическая регистрация плагинов по имени.
    """
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, algorithm_name: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if algorithm_name:
            AlgorithmMeta._registry[algorithm_name] = cls
            cls.algorithm_name = algorithm_name

    @abstractmethod
    def count_cells(self, image: np.ndarray) -> int:
        """
        Подсчёт клеток на изображении.

        Args:
            image: RGB-изображение (H, W, 3) в формате numpy array (uint8)

        Returns:
            int: количество найденных клеток
        """

    @abstractmethod
    def get_name(self) -> str:
        """Человекочитаемое название метода"""

    @classmethod
    def get_plugin(cls, algorithm_name: str) -> "AlgorithmMeta":
        """Получить экземпляр плагина по имени"""
        plugin_cls = cls._registry.get(algorithm_name)
        if not plugin_cls:
            available = list(cls._registry.keys())
            raise ValueError(
                f"Unknown algorithm: '{algorithm_name}'. "
                f"Available: {available}"
            )
        return plugin_cls()

    @classmethod
    def list_algorithms(cls) -> list[str]:
        """Список всех зарегистрированных алгоритмов"""
        return list(cls._registry.keys())