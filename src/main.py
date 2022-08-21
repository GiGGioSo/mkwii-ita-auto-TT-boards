import sys
from PySide6.QtWidgets import QApplication, QStyleFactory

from gui import window as win

def main():
    try:
        app = QApplication(sys.argv)
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        window = win.MainWindow()
        window.show()
        app.exec()
        input("\n\n[SUCCESSFUL] The program terminated without errors. \n\nPress ENTER to exit...")
    except KeyError as ke:
        print(ke)
        if ke == "last-modified":
            print("------ ERROR ------\nI server di ChadSoft sono down (in tutti i sensi), riprova più tardi.\n------ ----- ------\n")

if __name__ == "__main__":
    main()
