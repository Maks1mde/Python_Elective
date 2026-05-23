from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QSpinBox, QLabel, QGroupBox,
    QProgressBar, QTextEdit, QCheckBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from ui.widgets.test_runner import TestRunner
from models.algorithm_plugin import AlgorithmMeta


class TestTab(QWidget):
    """Вкладка тестирования алгоритмов."""

    test_finished = pyqtSignal(str)  # путь к HTML-отчёту

    def __init__(self):
        super().__init__()
        self.image_paths: list[str] = []
        self.targets: dict[str, int] = {}

        self._init_ui()

    def set_data(self, image_paths: list[str], targets: dict[str, int]):
        """Установка данных для тестирования."""
        self.image_paths = image_paths
        self.targets = targets

        # Обновляем максимальное значение спиннера
        self.spin_count.setMaximum(len(image_paths))
        self.spin_count.setValue(min(10, len(image_paths)))

        self.lbl_available.setText(f"Доступно изображений: {len(image_paths)}")

        # Активируем кнопку, если есть данные
        self.btn_run.setEnabled(len(image_paths) > 0)

    def _init_ui(self):
        """Построение интерфейса вкладки."""
        layout = QVBoxLayout(self)

        # === Настройки тестирования ===
        settings_group = QGroupBox("Параметры тестирования")
        settings_layout = QVBoxLayout(settings_group)

        # Выбор количества
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Количество изображений:"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 100)
        self.spin_count.setValue(10)
        count_layout.addWidget(self.spin_count)
        settings_layout.addLayout(count_layout)

        # Режим выбора
        self.chk_random = QCheckBox("Случайный выбор")
        self.chk_random.setChecked(True)
        settings_layout.addWidget(self.chk_random)

        self.lbl_available = QLabel("Доступно изображений: 0")
        settings_layout.addWidget(self.lbl_available)

        layout.addWidget(settings_group)

        # === Кнопка запуска ===
        btn_layout = QHBoxLayout()

        self.btn_run = QPushButton("🚀 Запустить тестирование")
        self.btn_run.clicked.connect(self._run_tests)
        self.btn_run.setEnabled(False)
        btn_layout.addWidget(self.btn_run)

        self.btn_stop = QPushButton("⏹ Остановить")
        self.btn_stop.clicked.connect(self._stop_tests)
        self.btn_stop.setEnabled(False)
        btn_layout.addWidget(self.btn_stop)

        layout.addLayout(btn_layout)

        # === Прогресс ===
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # === Лог ===
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        layout.addWidget(self.log)

        # === Поток для тестов ===
        self.test_thread: QThread | None = None
        self.test_runner: TestRunner | None = None

    def _run_tests(self):
        """Запуск тестирования."""
        if not self.image_paths:
            return

        # Определяем выбранный алгоритм
        # (используем тот же, что в главном окне)
        main_window = self.window()
        if not hasattr(main_window, 'cmb_algorithm'):
            return

        algo_name = main_window.cmb_algorithm.currentData()
        if not algo_name:
            return

        n_images = self.spin_count.value()
        random_order = self.chk_random.isChecked()

        # Создаём runner в отдельном потоке
        self.test_thread = QThread()
        self.test_runner = TestRunner(
            self.image_paths,
            self.targets,
            algo_name,
            n_images,
            random_order,
        )
        self.test_runner.moveToThread(self.test_thread)

        # Сигналы
        self.test_thread.started.connect(self.test_runner.run)
        self.test_runner.progress.connect(self.progress.setValue)
        self.test_runner.log.connect(self._append_log)
        self.test_runner.finished.connect(self._on_finished)
        self.test_runner.error.connect(self._on_error)
        self.test_runner.finished.connect(self.test_thread.quit)

        # Запуск
        self.test_thread.start()

        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setValue(0)
        self.log.clear()
        self._append_log("Тестирование запущено...\n")

    def _stop_tests(self):
        """Остановка тестирования."""
        if self.test_runner:
            self.test_runner.stop()
        self._append_log("Тестирование остановлено пользователем.\n")

    def _append_log(self, message: str):
        """Добавление сообщения в лог."""
        self.log.append(message)

    def _on_finished(self, report_path: str):
        """Обработчик завершения тестирования."""
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._append_log(f"\nТестирование завершено.\nОтчёт: {report_path}")
        self.test_finished.emit(report_path)

    def _on_error(self, error_msg: str):
        """Обработчик ошибки."""
        self._append_log(f"ОШИБКА: {error_msg}\n")
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)