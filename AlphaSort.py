# AlphaSort.py
from Depth import PAWN_VALUE, KNIGHT_VALUE, BISHOP_VALUE, ROOK_VALUE, QUEEN_VALUE

class MoveSorter:
    def __init__(self):
        self.history = [[0] * 64 for _ in range(64)]   # history[from][to]

    def piece_value(self, piece_char):
        # piece_char: 'p','n','b','r','q','k' (нижний регистр)
        if piece_char == 'p': return PAWN_VALUE
        if piece_char == 'n': return KNIGHT_VALUE
        if piece_char == 'b': return BISHOP_VALUE
        if piece_char == 'r': return ROOK_VALUE
        if piece_char == 'q': return QUEEN_VALUE
        return 0

    def score_move(self, board, move):
        # move: (from_sq, to_sq, promo)
        from_sq, to_sq, promo = move
        piece = board.get_piece(from_sq)        # символ фигуры (K,Q,...)
        captured = board.get_piece(to_sq)       # что стоит на to (или '.')
        score = 0
        if captured != '.':
            # MVV-LVA: ценность взятой минус ценность своей
            score = self.piece_value(captured.lower()) - self.piece_value(piece.lower())
        else:
            score = self.history[from_sq][to_sq]
        # бонус за превращение в ферзя
        if promo == 'q':
            score += QUEEN_VALUE
        return score

    def sort_moves(self, board, moves):
        if not moves:
            return []
        scored = [(self.score_move(board, m), m) for m in moves]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def update_history(self, move, depth):
        from_sq, to_sq, _ = move
        self.history[from_sq][to_sq] += depth * depth