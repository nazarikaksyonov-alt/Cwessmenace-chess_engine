import tkinter as tk
from tkinter import messagebox
import os

# -------- Импорт ваших модулей (без изменений) --------
from Calculations import Board, Engine
from Depth import MAX_DEPTH

# -------- Иконки (если есть) --------
try:
    ICON_PATH = "CMicon.png"
    LOGO_PATH = "CMim.png"
except:
    ICON_PATH = None
    LOGO_PATH = None

# -------- Локализация (встроенная) --------
class Localizer:
    """Загружает язык из lang.txt и хранит все строки."""
    def __init__(self):
        self.lang = self._detect_language()
        self.strings = self._get_strings(self.lang)

    def _detect_language(self):
        """Читает lang.txt, возвращает 'ru' или 'en'."""
        try:
            with open('lang.txt', 'r', encoding='utf-8') as f:
                content = f.read().strip().lower()
                if content in ('en', 'eng'):
                    return 'en'
                elif content in ('ru', 'rus'):
                    return 'ru'
                else:
                    return 'ru'   # по умолчанию
        except FileNotFoundError:
            return 'ru'

    def _get_strings(self, lang):
        """Возвращает словарь строк для выбранного языка."""
        if lang == 'en':
            return {
                'app_title': "CwessMenace – Chess Engine (bitboards)",
                'new_game': "New Game",
                'switch_color': "Switch Color",
                'exit': "Exit",
                'your_turn': "Your turn",
                'computer_thinking': "Computer is thinking...",
                'game_over': "Game over",
                'draw': "Draw",
                'checkmate_title': "Checkmate",
                'checkmate_message_white': "White wins!",
                'checkmate_message_black': "Black wins!",
                'stalemate_title': "Stalemate",
                'stalemate_message': "Draw!"
            }
        else:  # русский по умолчанию
            return {
                'app_title': "CwessMenace – Шахматный движок (битборды)",
                'new_game': "Новая игра",
                'switch_color': "Сменить цвет",
                'exit': "Выход",
                'your_turn': "Ваш ход",
                'computer_thinking': "Ход компьютера...",
                'game_over': "Игра окончена",
                'draw': "Ничья",
                'checkmate_title': "Мат",
                'checkmate_message_white': "Белые победили!",
                'checkmate_message_black': "Чёрные победили!",
                'stalemate_title': "Пат",
                'stalemate_message': "Ничья!"
            }

    def get(self, key):
        return self.strings.get(key, key)

# -------- GUI приложения --------
UNICODE_PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    '.': ' '
}

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.localizer = Localizer()          # ← читает lang.txt при создании
        self.root.title(self.localizer.get('app_title'))

        if ICON_PATH:
            try:
                img = tk.PhotoImage(file=ICON_PATH)
                self.root.iconphoto(True, img)
                self.root.icon_image = img
            except:
                pass

        self.board = Board()
        self.engine = Engine(max_depth=MAX_DEPTH)
        self.selected = None
        self.valid_moves = []
        self.player_color = 'w'
        self.game_over = False

        self.canvas = tk.Canvas(root, width=480, height=480, bg='white')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)

        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

        tk.Label(control_frame, text="CwessMenace", font=("Arial", 16)).pack(pady=5)
        self.status_label = tk.Label(control_frame, text=self.localizer.get('your_turn'), font=("Arial", 12))
        self.status_label.pack(pady=5)

        tk.Button(control_frame, text=self.localizer.get('new_game'), command=self.new_game, width=15).pack(pady=2)
        tk.Button(control_frame, text=self.localizer.get('switch_color'), command=self.switch_color, width=15).pack(pady=2)
        tk.Button(control_frame, text=self.localizer.get('exit'), command=root.quit, width=15).pack(pady=2)

        self.draw_board()
        if self.player_color != self.board.turn:
            self.root.after(500, self.computer_move)

    def draw_board(self):
        self.canvas.delete("all")
        cell_size = 60
        for row in range(8):
            for col in range(8):
                x1 = col * cell_size
                y1 = row * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                color = "#F0D9B5" if (row + col) % 2 == 0 else "#B58863"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                sq = (7 - row) * 8 + col
                if self.selected is not None and self.selected == sq:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="yellow", stipple="gray50", outline="")
                for move in self.valid_moves:
                    if move[1] == sq:
                        self.canvas.create_oval(x1+15, y1+15, x2-15, y2-15, fill="lightgreen", outline="green")
        for row in range(8):
            for col in range(8):
                x1 = col * cell_size
                y1 = row * cell_size
                sq = (7 - row) * 8 + col
                piece = self.board.get_piece(sq)
                if piece != '.':
                    self.canvas.create_text(x1+30, y1+30, text=UNICODE_PIECES[piece],
                                            font=("Arial", 40), fill="black" if piece.isupper() else "red")
        self.update_status()

    def update_status(self):
        if self.game_over:
            return
        if self.board.is_checkmate():
            winner = "Чёрные" if self.board.turn == 'w' else "Белые"
            if winner == "Белые":
                msg = self.localizer.get('checkmate_message_white')
            else:
                msg = self.localizer.get('checkmate_message_black')
            messagebox.showinfo(self.localizer.get('checkmate_title'), msg)
            self.game_over = True
            self.status_label.config(text=self.localizer.get('game_over'))
        elif self.board.is_stalemate():
            messagebox.showinfo(self.localizer.get('stalemate_title'), self.localizer.get('stalemate_message'))
            self.game_over = True
            self.status_label.config(text=self.localizer.get('draw'))
        else:
            if self.board.turn == self.player_color:
                self.status_label.config(text=self.localizer.get('your_turn'))
            else:
                self.status_label.config(text=self.localizer.get('computer_thinking'))

    def on_click(self, event):
        if self.game_over or self.board.turn != self.player_color:
            return
        col = event.x // 60
        row = 7 - (event.y // 60)
        if not (0 <= row < 8 and 0 <= col < 8):
            return
        sq = row * 8 + col

        if self.selected is not None:
            for move in self.valid_moves:
                if move[0] == self.selected and move[1] == sq:
                    if self.board.make_move(move):
                        self.selected = None
                        self.valid_moves = []
                        self.draw_board()
                        self.root.update()
                        if self.board.is_checkmate() or self.board.is_stalemate():
                            self.update_status()
                            return
                        self.root.after(100, self.computer_move)
                    else:
                        self.selected = None
                        self.valid_moves = []
                        self.draw_board()
                    return
            piece = self.board.get_piece(sq)
            if piece != '.' and ((self.player_color=='w' and piece.isupper()) or (self.player_color=='b' and piece.islower())):
                self.selected = sq
                self.valid_moves = self.board.get_legal_moves_for_sq(sq)
                self.draw_board()
            else:
                self.selected = None
                self.valid_moves = []
                self.draw_board()
        else:
            piece = self.board.get_piece(sq)
            if piece != '.' and ((self.player_color=='w' and piece.isupper()) or (self.player_color=='b' and piece.islower())):
                self.selected = sq
                self.valid_moves = self.board.get_legal_moves_for_sq(sq)
                self.draw_board()

    def computer_move(self):
        if self.game_over or self.board.turn == self.player_color:
            return
        self.status_label.config(text=self.localizer.get('computer_thinking'))
        self.root.update()
        move = self.engine.best_move(self.board)
        if move:
            self.board.make_move(move)
            self.draw_board()
            self.root.update()
            if self.board.is_checkmate() or self.board.is_stalemate():
                self.update_status()
        else:
            self.update_status()

    def new_game(self):
        self.board = Board()
        self.selected = None
        self.valid_moves = []
        self.game_over = False
        self.draw_board()
        if self.player_color != self.board.turn:
            self.root.after(500, self.computer_move)

    def switch_color(self):
        self.player_color = 'b' if self.player_color == 'w' else 'w'
        self.new_game()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()