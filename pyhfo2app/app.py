"""Entry point for the PyHFO application."""

import sys
import multiprocessing as mp
import warnings

warnings.filterwarnings("ignore")


def main():
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    from pyhfo2app.ui.main_window import MainWindow

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    mp.freeze_support()
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.aboutToQuit.connect(app.closeAllWindows)
    sys.exit(app.exec_())
