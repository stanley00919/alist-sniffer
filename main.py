import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from ui.styles.theme import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('WebMedia Sniffer')
    app.setStyleSheet(STYLESHEET)

    icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
