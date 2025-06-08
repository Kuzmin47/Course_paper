from PySide6.QtWidgets import QApplication
from Windows import ChessAppWindow

if __name__ == "__main__":
    chess_app = QApplication([])
    main_window = ChessAppWindow()
    main_window.show()
    chess_app.exec()