from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QComboBox, QLabel,
    QFileDialog, QSpinBox, QCheckBox, QGroupBox,
    QMessageBox, QSplitter,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
import cv2
import numpy as np
from pathlib import Path
from ui.widgets.image_viewer import ImageViewer
from ui.test_tab import TestTab
from models.algorithm_plugin import AlgorithmMeta
from ui.report_tab import ReportTab


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Подсчёт клеток на гистологических изображениях")
        self.resize(1200, 800)

        # Данные
        self.image_paths: list[str] = []
        self.targets: dict[str, int] = {}  # filename -> ground truth count
        self.current_image: np.ndarray | None = None
        self.current_image_path: str | None = None

        # Инициализация UI
        self._init_ui()

        # Загрузка доступных алгоритмов
        self._load_algorithms()

    def _init_ui(self):
        """Построение интерфейса."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # === Верхняя панель: загрузка данных и выбор алгоритма ===
        top_panel = QHBoxLayout()

        # Группа загрузки данных
        data_group = QGroupBox("Данные")
        data_layout = QHBoxLayout(data_group)

        self.btn_load_dir = QPushButton("📁 Загрузить датасет")
        self.btn_load_dir.clicked.connect(self._load_dataset)
        data_layout.addWidget(self.btn_load_dir)

        self.btn_generate = QPushButton("🔄 Генератор")
        self.btn_generate.clicked.connect(self._generate_images)
        data_layout.addWidget(self.btn_generate)

        top_panel.addWidget(data_group)

        # Группа выбора алгоритма
        algo_group = QGroupBox("Алгоритм")
        algo_layout = QHBoxLayout(algo_group)

        algo_layout.addWidget(QLabel("Метод:"))
        self.cmb_algorithm = QComboBox()
        self.cmb_algorithm.currentTextChanged.connect(self._on_algorithm_changed)
        algo_layout.addWidget(self.cmb_algorithm)

        self.btn_count = QPushButton("🔍 Подсчитать")
        self.btn_count.clicked.connect(self._count_cells)
        self.btn_count.setEnabled(False)
        algo_layout.addWidget(self.btn_count)

        top_panel.addWidget(algo_group)

        # Группа навигации
        nav_group = QGroupBox("Изображение")
        nav_layout = QHBoxLayout(nav_group)

        self.btn_random = QPushButton("🎲 Случайное")
        self.btn_random.clicked.connect(self._show_random_image)
        self.btn_random.setEnabled(False)
        nav_layout.addWidget(self.btn_random)

        self.lbl_filename = QLabel("Изображение не выбрано")
        self.lbl_filename.setWordWrap(True)
        nav_layout.addWidget(self.lbl_filename, stretch=1)

        top_panel.addWidget(nav_group)

        main_layout.addLayout(top_panel)

        # === Центральная область: изображение и результат ===
        self.image_viewer = ImageViewer()
        self.lbl_result = QLabel("Количество клеток: —")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.lbl_result.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")

        main_layout.addWidget(self.image_viewer, stretch=1)
        main_layout.addWidget(self.lbl_result)

        # === Вкладки: тестирование и отчёты ===
        self.tabs = QTabWidget()

        self.test_tab = TestTab()
        self.test_tab.test_finished.connect(self._on_test_finished)
        self.tabs.addTab(self.test_tab, "🧪 Тестирование")

        self.report_tab = ReportTab()
        self.tabs.addTab(self.report_tab, "📊 Отчёты")

        main_layout.addWidget(self.tabs)

    def _load_algorithms(self):
        """Загрузка списка алгоритмов в выпадающий список."""
        self.cmb_algorithm.clear()
        algorithms = AlgorithmMeta.list_algorithms()
        for algo_name in algorithms:
            plugin = AlgorithmMeta.get_plugin(algo_name)
            self.cmb_algorithm.addItem(plugin.get_name(), algo_name)

    def _load_dataset(self):
        """Загрузка изображений и таргетов из каталога."""
        directory = QFileDialog.getExistingDirectory(
            self, "Выберите каталог с датасетом"
        )
        if not directory:
            return

        dir_path = Path(directory)

        # Ищем изображения
        extensions = ("*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff")
        self.image_paths = []
        for ext in extensions:
            self.image_paths.extend(
                str(p) for p in dir_path.glob(ext)
            )
        self.image_paths.sort()

        if not self.image_paths:
            QMessageBox.warning(self, "Ошибка", "В каталоге нет изображений")
            return

        # Ищем файл с таргетами (targets.csv или targets.txt)
        targets_file = dir_path / "targets.csv"
        if not targets_file.exists():
            targets_file = dir_path / "targets.txt"

        self.targets = {}
        if targets_file.exists():
            with open(targets_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.replace(",", " ").split()
                    if len(parts) >= 2:
                        filename = parts[0]
                        try:
                            count = int(parts[1])
                            self.targets[filename] = count
                        except ValueError:
                            continue

        # Передаём данные в тестовую вкладку
        self.test_tab.set_data(self.image_paths, self.targets)

        self.btn_random.setEnabled(True)
        QMessageBox.information(
            self, "Загружено",
            f"Изображений: {len(self.image_paths)}\n"
            f"С таргетами: {len(self.targets)}"
        )

    def _generate_images(self):
        """Генерация изображений (заглушка)."""
        QMessageBox.information(
            self, "Генератор",
            "Генерация изображений ещё не реализована.\n"
            "Здесь будет создание синтетических гистологических изображений."
        )

    def _on_algorithm_changed(self, name: str):
        """Обработчик смены алгоритма."""
        self.btn_count.setEnabled(
            bool(name) and self.current_image is not None
        )

    def _show_random_image(self):
        """Отображение случайного изображения из датасета."""
        import random
        if not self.image_paths:
            return

        path = random.choice(self.image_paths)
        self._load_and_display(path)

    def _load_and_display(self, path: str):
        """Загрузка и отображение изображения."""
        image = cv2.imread(path)
        if image is None:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить: {path}")
            return

        self.current_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.current_image_path = path

        # Отображаем
        self.image_viewer.set_image(self.current_image)
        self.lbl_filename.setText(f"Файл: {Path(path).name}")
        self.lbl_result.setText("Количество клеток: —")
        self.btn_count.setEnabled(bool(self.cmb_algorithm.currentText()))

        # Если есть таргет — показываем
        filename = Path(path).name
        if filename in self.targets:
            self.lbl_result.setText(
                f"Эталон: {self.targets[filename]} | Количество клеток: —"
            )

    def _count_cells(self):
        """Подсчёт клеток на текущем изображении."""
        if self.current_image is None:
            return

        algo_name = self.cmb_algorithm.currentData()
        if not algo_name:
            return

        try:
            plugin = AlgorithmMeta.get_plugin(algo_name)
            count = plugin.count_cells(self.current_image)

            filename = Path(self.current_image_path).name if self.current_image_path else "?"
            if filename in self.targets:
                target = self.targets[filename]
                error = abs(count - target) / max(target, 1) * 100
                self.lbl_result.setText(
                    f"Эталон: {target} | Найдено: {count} | Погрешность: {error:.1f}%"
                )
            else:
                self.lbl_result.setText(f"Количество клеток: {count}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка алгоритма:\n{str(e)}")

    def _on_test_finished(self, report_path: str):
        """Обработчик завершения тестирования."""
        self.report_tab.load_report(report_path)
        self.tabs.setCurrentWidget(self.report_tab)