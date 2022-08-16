import sys
from PySide6.QtWidgets import QApplication

from gui import window as win

def main():
    app = QApplication(sys.argv)
    window = win.MainWindow()
    window.show()
    app.exec()
    input("\n\n[SUCCESSFUL] The program terminated without errors. \n\nPress ENTER to exit...")

if __name__ == "__main__":
    main()
