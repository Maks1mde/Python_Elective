import cv2
import numpy as np
from pathlib import Path
import time
import random
from PyQt5.QtCore import QObject, pyqtSignal
from models.algorithm_plugin import AlgorithmMeta
from ui.reports.html_generator import HtmlReportGenerator


class TestRunner(QObject):
    """
    Запускает тестирование в отдельном потоке.
    Критерий: относительная погрешность ≤ 10%.
    """

    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(str)  # путь к HTML-отчёту
    error = pyqtSignal(str)

    def __init__(
        self,
        image_paths: list[str],
        targets: dict[str, int],
        algo_name: str,
        n_images: int,
        random_order: bool = True,
    ):
        super().__init__()
        self.image_paths = image_paths
        self.targets = targets
        self.algo_name = algo_name
        self.n_images = min(n_images, len(image_paths))
        self.random_order = random_order
        self._stopped = False

    def stop(self):
        """Остановка тестирования."""
        self._stopped = True

    def run(self):
        """Основной метод, выполняемый в потоке."""
        try:
            # Выбираем изображения
            if self.random_order:
                indices = random.sample(
                    range(len(self.image_paths)), self.n_images
                )
            else:
                indices = list(range(self.n_images))

            # Получаем плагин алгоритма
            plugin = AlgorithmMeta.get_plugin(self.algo_name)
            algo_display_name = plugin.get_name()

            # Результаты
            results = []
            passed = 0
            failed = 0
            total_error = 0.0

            for i, idx in enumerate(indices):
                if self._stopped:
                    break

                path = self.image_paths[idx]
                filename = Path(path).name
                target = self.targets.get(filename)

                self.log.emit(f"[{i+1}/{self.n_images}] {filename}...")

                try:
                    # Загрузка
                    image = cv2.imread(path)
                    if image is None:
                        raise ValueError("Не удалось загрузить изображение")
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                    # Подсчёт
                    start_time = time.time()
                    predicted = plugin.count_cells(image_rgb)
                    elapsed = time.time() - start_time

                    # Расчёт погрешности
                    if target is not None and target > 0:
                        error_pct = abs(predicted - target) / target * 100
                    elif target == 0 and predicted == 0:
                        error_pct = 0.0
                    elif target == 0:
                        error_pct = 100.0
                    else:
                        error_pct = None  # нет таргета

                    is_passed = (
                        error_pct is not None and error_pct <= 10.0
                    )

                    if is_passed:
                        passed += 1
                        status = "✓ ПРОЙДЕН"
                    elif error_pct is not None:
                        failed += 1
                        status = "✗ ПРОВАЛЕН"
                    else:
                        status = "? Нет эталона"

                    if error_pct is not None:
                        total_error += error_pct

                    results.append({
                        "filename": filename,
                        "target": target,
                        "predicted": predicted,
                        "error_pct": error_pct,
                        "passed": is_passed,
                        "time": elapsed,
                        "status": status,
                    })

                    self.log.emit(
                        f"  Эталон: {target}, Найдено: {predicted}, "
                        f"Погрешность: {error_pct:.1f}% — {status}\n"
                    )

                except Exception as e:
                    self.log.emit(f"  ОШИБКА: {str(e)}\n")
                    results.append({
                        "filename": filename,
                        "target": target,
                        "predicted": None,
                        "error_pct": None,
                        "passed": False,
                        "time": 0,
                        "status": f"Ошибка: {str(e)}",
                    })
                    failed += 1

                # Обновляем прогресс
                self.progress.emit(int((i + 1) / self.n_images * 100))

            # Генерируем HTML-отчёт
            total_tested = passed + failed
            avg_error = total_error / max(total_tested, 1)

            generator = HtmlReportGenerator()
            report_path = generator.generate(
                algo_name=algo_display_name,
                results=results,
                total_tested=total_tested,
                passed=passed,
                failed=failed,
                avg_error=avg_error,
            )

            self.log.emit(
                f"\nИтого: {passed}/{total_tested} пройдено "
                f"({passed/max(total_tested,1)*100:.1f}%)"
            )
            self.log.emit(f"Средняя погрешность: {avg_error:.2f}%")

            self.finished.emit(report_path)

        except Exception as e:
            self.error.emit(str(e))