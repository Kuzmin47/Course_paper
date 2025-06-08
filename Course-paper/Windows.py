from typing import List, Tuple, Optional, Set
from PySide6.QtCore import QThread, Signal, QRectF
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QDialog,
    QPushButton,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QWidget,
    QGridLayout,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QApplication,
    QFileDialog
)
from ChessLogic import ChessFigure, ChessBoard, ChessSolver
import uuid

def create_unique_id(input_data: str) -> str:
    """Создает уникальный идентификатор на основе входных данных."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, input_data))

def create_board_cell(x: int, y: int, cell_state: int) -> QGraphicsRectItem:
    """
    Создает и возвращает представление клетки шахматной доски.

    Args:
        x: Координата X клетки.
        y: Координата Y клетки.
        value: Значение клетки (0, 1: пустая, 2: фигура, 3: под угрозой).

    Returns:
        Объект QGraphicsRectItem, представляющий клетку.
    """
    CELL_COLORS = {
        0: QColor("white"),
        1: QColor("brown"),
        2: QColor("blue"),
        3: QColor("yellow")
    }

    cell_item = QGraphicsRectItem(0, 0, 40, 40)
    cell_item.setPen(QPen(QColor("black")))
    cell_item.setPos(x * 40, y * 40)
    cell_item.setBrush(CELL_COLORS.get(cell_state, QColor("white")))
    return cell_item

class ChessAppWindow(QMainWindow):
    """
    Главное окно приложения.
    """

    def __init__(self):
        """
        Инициализация главного окна.
        """
        super().__init__()
        self.setWindowTitle("Расстановка Фигур на Доске")
        self.size_label = QLabel("Размер доски (N):")
        self.board_size_input = QLineEdit()
        self.pieces_to_place_label = QLabel("Количество фигур для расстановки (L):")
        self.pieces_to_place_input = QLineEdit()
        self.placed_pieces_label = QLabel("Количество расставленных фигур (K):")
        self.placed_pieces_input = QLineEdit()

        self.create_board_button = QPushButton("Ввести координаты K фигур")
        self.draw_board_button = QPushButton("Отрисовать доску")
        self.exit_button = QPushButton("Выход")

        self.create_board_button.clicked.connect(self._initialize_board)
        self.draw_board_button.clicked.connect(self._render_board)
        self.exit_button.clicked.connect(self.close)

        layout = QGridLayout()
        layout.addWidget(self.size_label, 0, 0)
        layout.addWidget(self.board_size_input, 0, 1)
        layout.addWidget(self.pieces_to_place_label, 1, 0)
        layout.addWidget(self.pieces_to_place_input, 1, 1)
        layout.addWidget(self.placed_pieces_label, 2, 0)
        layout.addWidget(self.placed_pieces_input, 2, 1)
        layout.addWidget(self.create_board_button, 3, 0, 1, 2)
        layout.addWidget(self.draw_board_button, 4, 0, 1, 2)
        layout.addWidget(self.exit_button, 5, 0, 1, 2)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.draw_board_button.setEnabled(False)

        self.solver = ChessSolver()
        self.board_size_input.textChanged.connect(self._update_buttons_state)
        self.pieces_to_place_input.textChanged.connect(self._update_buttons_state)
        self.placed_pieces_input.textChanged.connect(self._update_buttons_state)
        self.board_initialized = False

    def _update_buttons_state(self):
        """
        Включает/выключает кнопки в зависимости от заполненности полей.
        """
        has_size = self.board_size_input.text() != ""
        has_to_place = self.pieces_to_place_input.text() != ""
        has_placed = self.placed_pieces_input.text() != ""

        self.create_board_button.setEnabled(has_placed and self.placed_pieces_input.text() != "0" and has_size)

        try:
            placed_count = int(self.placed_pieces_input.text()) if self.placed_pieces_input.text().isdigit() else 0
            self.draw_board_button.setEnabled(has_size and has_to_place and has_placed and 
                                           (placed_count == 0 or (self.board_initialized and hasattr(self, 'pieces_positions') and 
                                            len(self.pieces_positions) == placed_count)))
        except ValueError:
            self.draw_board_button.setEnabled(False)

    def get_pieces_info(self) -> Tuple[int, int, List[Tuple[int, int]]]:
        """
        Возвращает размер доски, требуемое количество фигур и координаты размещенных фигур.

        Returns:
            Кортеж (размер доски, кол-во фигур, координаты).
        """
        return int(self.board_size_input.text()), int(self.pieces_to_place_input.text()), self.pieces_positions

    def _initialize_board(self):
        """
        Создание доски и активация кнопки рисования.
        """
        try:
            size_text = self.board_size_input.text()
            to_place_text = self.pieces_to_place_input.text()
            placed_text = self.placed_pieces_input.text()

            try:
                board_size = int(size_text)
                pieces_to_place = int(to_place_text)
                placed_count = int(placed_text)
            except ValueError:
                QMessageBox.critical(self, "Ошибка", "Введены некорректные числовые значения.")
                self.draw_board_button.setEnabled(False)
                return

            if placed_count > 0:
                input_dialog = CoordinatesInputDialog(placed_count, self)
                if input_dialog.exec() == QDialog.Accepted:
                    self.pieces_positions = input_dialog.result_positions
            else:
                self.pieces_positions = []
            self.board_initialized = True
            self.draw_board_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Доска не создалась: {str(e)}")
            self.draw_board_button.setEnabled(False)

    def _render_board(self):
        """
        Отрисовка доски.
        """
        if self.board_initialized:
            try:
                size_text = self.board_size_input.text()
                to_place_text = self.pieces_to_place_input.text()
                placed_text = self.placed_pieces_input.text()

                try:
                    board_size = int(size_text)
                    pieces_to_place = int(to_place_text)
                    placed_count = int(placed_text)
                except ValueError:
                    QMessageBox.critical(self, "Ошибка", "Введены некорректные числовые значения.")
                    return

                board, placement_options = self.solver.create_board(board_size, pieces_to_place, placed_count, self.pieces_positions)
                self.solver.start_solving(board, placement_options)
                self.solver.solving_complete.connect(self._handle_solution)

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при отрисовке доски: {str(e)}")

        else:
            QMessageBox.warning(self, "Ошибка", "Создайте доску")

    def _handle_solution(self, board: "ChessBoard", solutions: Set[frozenset]):
        """
        Обработчик сигнала `finished` потока решателя.

        Args:
            board: Шахматная доска.
            solutions: Множество решений.
        """
        if solutions:
            solution_coordinates = list(next(iter(solutions)))
            solution_dialog = DeskWindow(board, solution_coordinates, self)
            solution_dialog.exec()

    def closeEvent(self, event):
        """
        Обработчик события закрытия окна.
        Остановка всех потоков при закрытии.
        """
        active_threads = [
            getattr(self, attr) for attr in dir(self)
            if attr.endswith('_thread') and isinstance(getattr(self, attr), QThread)
        ]

        for thread in active_threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(500)

        event.accept()

class CoordinatesInputDialog(QDialog):
    """
    Диалоговое окно для ввода координат фигур.
    """
    def __init__(self, pieces_count: int, parent: "ChessAppWindow"):
        """
        Инициализация диалогового окна.

        Args:
            num_figures: Количество фигур, для которых нужно ввести координаты.
            parent: Родительское окно (ChessAppWindow).
        """
        super().__init__(parent)
        self.parent_window = parent
        self.pieces_count = pieces_count
        self.setWindowTitle("Ввод координат поставленных фигур")
        self.coordinate_fields: List[QLineEdit] = []
        self.confirm_button = QPushButton("OK")
        self.cancel_button = QPushButton("Отмена")

        main_layout = QVBoxLayout()
        self.coordinates_layout = QVBoxLayout()
        main_layout.addLayout(self.coordinates_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.confirm_button)
        buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        self._setup_input_fields()

        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def _setup_input_fields(self):
        """
        Создание полей ввода для координат фигур.
        """
        for i in range(self.pieces_count):
            label = QLabel(f"Фигура №{i + 1}:")
            input_field = QLineEdit()
            input_field.setPlaceholderText("Пример: 1 1")
            self.coordinate_fields.append(input_field)
            self.coordinates_layout.addWidget(label)
            self.coordinates_layout.addWidget(input_field)
            self.coordinate_fields[-1].textChanged.connect(self._validate_inputs)

    def _check_safety(self, pieces_positions: List[Tuple[int, int]], board_size: int) -> bool:
        """
        Проверка, находятся ли фигуры в безопасных позициях на доске.

        Args:
            pieces: Список координат фигур.
            n: Размер доски.

        Returns:
            True, если все фигуры в безопасных позициях, иначе False.
        """
        temp_board = ChessBoard(board_size)
        for x, y in pieces_positions:
            piece = ChessFigure(x, y)
            if not temp_board.place_piece(piece):
                return False
        return True

    def accept(self):
        """
        Обработка нажатия кнопки "OK".
        Извлечение координат из QLineEdit и сохранение в `resFig`.
        Проверка безопасного расположения фигур.
        """
        coordinates = []
        is_valid = True
        board_size = 0

        try:
            board_size = int(self.parent_window.board_size_input.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Неверный формат ввода N.")
            return

        for field in self.coordinate_fields:
            text = field.text().strip()
            try:
                x, y = map(int, text.split())
                if not (0 <= x < board_size and 0 <= y < board_size):
                    QMessageBox.warning(self, "Ошибка", "Координаты выходят за пределы доски.")
                    is_valid = False
                    break
                coordinates.append((x, y))
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Неверный формат ввода координат.")
                is_valid = False
                break

        if is_valid:
            if self._check_safety(coordinates, board_size):
                self.result_positions = coordinates
                super().accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Невозможно расположение, фигуры под ударом")

    def _validate_inputs(self):
        """
        Проверка валидности введенных координат.
        Включение/выключение кнопки "OK" в зависимости от валидности всех полей.
        """
        all_valid = True
        for field in self.coordinate_fields:
            text = field.text().strip()
            if text:
                try:
                    x, y = map(int, text.split())
                    n = int(self.parent_window.board_size_input.text())
                    if not (0 <= x < n and 0 <= y < n):
                        all_valid = False
                except ValueError:
                    all_valid = False
            else:
                all_valid = False

        self.confirm_button.setEnabled(all_valid)
        
class DeskWindow(QDialog):
    """
    Окно для отображения решения на шахматной доске.
    """

    def __init__(self, chess_board: "ChessBoard", solution: List[Tuple[int, int]], parent: Optional[QWidget] = None):
        """
        Инициализация диалогового окна.

        Args:
            table: Объект шахматной доски.
            solution: Решение в виде списка кортежей (x, y).
            Parent: Родительский виджет.
        """
        super().__init__(parent)
        self.chess_board = chess_board
        self.solution = solution
        self.parent_window = parent

        self.main_layout = QVBoxLayout(self)
        self.board_widget = QWidget()
        self.buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("Запись в файл")
        self.save_button.setStyleSheet("background-color: green; font-weight: bold;")
        self.close_button = QPushButton("Выход")
        self.close_button.setStyleSheet("background-color: red; font-weight: bold;")

        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.close_button)

        self.main_layout.addWidget(self.board_widget)
        self.main_layout.addLayout(self.buttons_layout)

        self.board_widget.setStyleSheet("background-color: white;")

        self.save_button.clicked.connect(self._save_solution)
        self.close_button.clicked.connect(self.close)

        self.setWindowTitle("Один из вариантов решения")
        self._display_solution()

    def _display_solution(self):
        """
        Визуализация решения на шахматной доске.
        """
        board_size = len(self.chess_board.cells)
        scene = QGraphicsScene()
        view = QGraphicsView()
        view.setScene(scene)
        view.setRenderHint(QPainter.Antialiasing)
        
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        layout = QVBoxLayout(self.board_widget)
        layout.addWidget(view)

        scene_dimension = board_size * 40
        view.setSceneRect(QRectF(-1, -1, scene_dimension + 2, scene_dimension + 2))
        scene.setSceneRect(QRectF(view.sceneRect()))
        view.setFixedSize(scene_dimension + 2, scene_dimension + 2)

        temporary_pieces = []
        for x, y in self.solution:
            if self.chess_board.is_position_empty(x, y):
                piece = ChessFigure(x, y)
                if self.chess_board.place_piece(piece):
                    temporary_pieces.append(piece)

        for x in range(board_size):
            for y in range(board_size):
                if self.chess_board.cells[y][x]['threatened']:
                    cell = create_board_cell(x, y, 3)
                elif self.chess_board.is_position_empty(x, y) and (y + x) % 2 == 0:
                    cell = create_board_cell(x, y, 0)
                elif self.chess_board.is_position_empty(x, y) and (y + x) % 2 != 0:
                    cell = create_board_cell(x, y, 1)
                else:
                    cell = create_board_cell(x, y, 2)
                scene.addItem(cell)

        for piece in temporary_pieces:
            self.chess_board.remove_piece(piece)

    def _save_solution(self):
        """
        Сохранение решения в файл.
        """
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить решение",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if filename:
            try:
                self.save_thread = SolutionSaver(self.parent_window.solver, self.parent_window.solver.found_solutions, filename)
                self.save_thread.completed.connect(self._handle_save_result)
                self.save_thread.start()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Сохранение не удалось: {e}")

    def _handle_save_result(self, filename: str, error_msg: str):
        """
        Обработчик сигнала `finished` потока сохранения.

        Args:
            filename: Имя файла, в который было сохранено решение.
            error_message: Сообщение об ошибке, если возникла.
        """
        print(len(self.parent_window.solver.found_solutions))
        if error_msg:
            QMessageBox.critical(self, "Ошибка", f"Сохранение не удалось: {error_msg}")
        else:
            QMessageBox.information(
                self,
                "Успешно",
                f"Результат сохранен в {filename}"
            )


class SolutionSaver(QThread):
    """
    Поток для сохранения решения в файл.
    """
    completed = Signal(str, str)

    def __init__(self, solver: "ChessSolver", solutions: Set[frozenset], filename: str):
        """
        Инициализация потока.

        Args:
            solver: Объект решателя.
            solutions: Множество решений.
            filename: Имя файла для сохранения.
        """
        super().__init__()
        self.solver = solver
        self.solutions = solutions
        self.filename = filename

    def run(self):
        """
        Выполнение сохранения решения в файл.
        """
        try:
            self.solver.save_results(self.filename, self.solutions)
            self.completed.emit(self.filename, "")
        except Exception as e:
            self.completed.emit(self.filename, str(e))


if __name__ == '__main__':
    app = QApplication([])
    window = ChessAppWindow()
    window.show()
    app.exec()