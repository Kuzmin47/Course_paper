from itertools import combinations_with_replacement
from typing import List, Tuple, Set
from PySide6.QtCore import QThread, Signal

class ChessFigure:
    
    def __init__(self, pos_x: int, pos_y: int):
        """
        Инициализация фигуры.

        Args:
            x: Координата X фигуры.
            y: Координата Y фигуры.
            possible_moves: Возможные ходы фигуры.
        """
        self.possible_moves = [(-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0), (0, -2), (0, 2)]
        self.pos_x = pos_x
        self.pos_y = pos_y

class ChessBoard:
    """
    Класс для представления шахматной доски и ее клеток.
    """

    def __init__(self, board_size: int):
        """
        Инициализация доски.

        Args:
            size: Размер доски.
        """
        self.board_size = board_size
        self.cells: List[List[dict]] = [[{'x': x, 'y': y, 'piece': None, 'threatened': False} for x in range(board_size)] for y in range(board_size)]
        self.placed_pieces: List[ChessFigure] = []

    def is_position_empty(self, pos_x: int, pos_y: int) -> bool:
        """
        Проверяет, пуста ли клетка.

        Args:
            x: Координата X клетки.
            y: Координата Y клетки.

        Returns:
            True, если клетка пуста, иначе False.
        """
        return self.cells[pos_y][pos_x]['piece'] is None

    def place_piece(self, piece: ChessFigure) -> bool:
        """
        Добавляет фигуру на доску с проверкой безопасности.

        Args:
            piece: Фигура для добавления.

        Returns:
            True, если фигура успешно добавлена, иначе False.
        """
        if not self.is_position_empty(piece.pos_x, piece.pos_y) or not self.is_position_safe(piece):
            return False

        self.cells[piece.pos_y][piece.pos_x]['piece'] = piece
        self.placed_pieces.append(piece)
        self.update_threatened_cells()
        return True

    def remove_piece(self, piece: ChessFigure):
        """
        Удаляет фигуру с доски.
        
        Args:
            piece: Фигура для удаления.
        """
        cell = self.cells[piece.pos_y][piece.pos_x]
        if cell['piece'] == piece:
            cell['piece'] = None
            self.placed_pieces.remove(piece)
            self.update_threatened_cells()

    def is_position_safe(self, piece: ChessFigure) -> bool:
        """
        Проверка безопасности позиции для фигуры.

        Args:
            piece: Фигура для проверки.

        Returns:
            True, если позиция безопасна, иначе False.
        """
        if not (0 <= piece.pos_x < self.board_size and 0 <= piece.pos_y < self.board_size):
            return False

        if not self.is_position_empty(piece.pos_x, piece.pos_y):
            return False

        for other_piece in self.placed_pieces:
            for dx, dy in other_piece.possible_moves:
                if other_piece.pos_x + dx == piece.pos_x and other_piece.pos_y + dy == piece.pos_y:
                    return False
        return True

    def update_threatened_cells(self):
        """
        Обновляет клетки под боем на доске.
        """
        # Сброс всех клеток под боем
        for row in self.cells:
            for cell in row:
                cell['threatened'] = False

        # Установка клеток под боем всех фигур
        for piece in self.placed_pieces:
            for dx, dy in piece.possible_moves:
                new_x, new_y = piece.pos_x + dx, piece.pos_y + dy
                if 0 <= new_x < self.board_size and 0 <= new_y < self.board_size:
                    self.cells[new_y][new_x]['threatened'] = True

class ChessSolver(QThread):
    """
    Класс для решения задачи расстановки фигур на шахматной доске.
    """
    solving_complete = Signal(object, object)

    def __init__(self):
        """
        Инициализация расстановщика.
        """
        super().__init__()
        self.found_solutions: Set[frozenset] = set()
    
    @staticmethod
    def save_results(output_path: str, solutions: Set[frozenset]):
        """
        Записывает результаты в файл.
        
        Args:
            file_path: Путь к файлу для записи.
            solutions: Множество решений.
        """
        with open(output_path, 'w') as output_file:
            if solutions:
                for solution in solutions:
                    output_file.write(" ".join(f"({x}, {y})" for x, y in solution) + "\n")
            else:
                output_file.write("no solutions\n")

    def find_solutions(self, board: ChessBoard, piece_arrangements: List[str]):
        """
        Находит все решения с помощью рекурсии.

        Args:
            board: Шахматная доска.
            combinations: Список комбинаций фигур для размещения.
        """
        def recursive_solver(remaining_pieces: List[str]):
            if not remaining_pieces:
                self.found_solutions.add(frozenset((p.pos_x, p.pos_y) for p in board.placed_pieces))
                return

            current_piece = remaining_pieces[0]
            for y in range(board.board_size):
                for x in range(board.board_size):
                    new_piece = ChessFigure(x, y)
                    if board.place_piece(new_piece):
                        recursive_solver(remaining_pieces[1:])
                        board.remove_piece(new_piece)

        for arrangement in piece_arrangements:
            recursive_solver(arrangement)

    def start_solving(self, board: ChessBoard, piece_arrangements: List[str]):
        """
        Запускает решение задачи в отдельном потоке.

        Args:
            board: Шахматная доска.
            combinations: Список комбинаций фигур для размещения.
        """
        self.chess_board = board
        self.piece_arrangements = piece_arrangements
        self.start()

    def run(self):
        """
        Выполнение решения задачи расстановки фигур на шахматной доске.
        """
        self.find_solutions(self.chess_board, self.piece_arrangements)
        self.solving_complete.emit(self.chess_board, self.found_solutions)

    @staticmethod
    def create_board(n: int, l: int, k: int, initial_pieces: List[Tuple[int, int]]) -> Tuple[ChessBoard, List[str]]:
        """
        Генерирует шахматную доску и список комбинаций фигур для размещения.

        Args:
            n: Размер доски.
            l: Количество фигур для размещения.
            k: Количество предварительно размещенных фигур.
            pieces: Координаты предварительно размещенных фигур.

        Returns:
            Кортеж (шахматная доска, список комбинаций фигур).
        """
        board = ChessBoard(n)
        # Добавляем предварительно размещенные фигуры
        if k > 0:
            for coordinates in initial_pieces:
                piece = ChessFigure(coordinates[0], coordinates[1])
                board.place_piece(piece)

        # Генерация вариантов расстановки фигур для размещения
        placement_options = set(combinations_with_replacement(' ', l))
        return board, list(placement_options)