from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices


class ReportTab(QWidget):
    """Вкладка отображения HTML-отчётов (открытие в браузере)."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.lbl_status = QLabel(
            "Отчёт не загружен.\n"
            "Запустите тестирование для генерации отчёта."
        )
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(self.lbl_status)

    def load_report(self, path: str):
        """Открытие HTML-отчёта в системном браузере."""
        from pathlib import Path
        file_path = Path(path).resolve()
        if file_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
            self.lbl_status.setText(f"Отчёт открыт в браузере:\n{file_path}")
        else:
            self.lbl_status.setText(f"Файл не найден:\n{file_path}")