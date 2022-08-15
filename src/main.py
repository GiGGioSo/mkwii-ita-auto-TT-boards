import sys
import traceback
import gspread
from PySide6.QtWidgets import QApplication

from gui import window as win

def main():
    try:
        app = QApplication(sys.argv)
        window = win.MainWindow()
        window.show()
        app.exec()
        input("\n\n[SUCCESSFUL] The program terminated without errors. \n\nPress ENTER to exit...")
    except gspread.exceptions.APIError:
        print("\n\n----------------------------------------\nGOOGLE SHEET ERROR CODE 429: Quota of requests exceeded.")
        print("\nFirst try to rerun the program a couple of times. If it still happens execute the program with the Debug mode ON and send me the full output of the program on discord (Wol_loW#5995)")
        input("\n\nPress ENTER to exit...")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()
