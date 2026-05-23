import sys

# Сначала torch, потом PyQt5
import torch  # noqa
from PyQt5.QtWidgets import QApplication


def main():
    from models import autodiscover_algorithms
    autodiscover_algorithms()

    from ui.main_window import MainWindow
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()