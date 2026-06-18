# Calculations.py
import copy
from Depth import MAX_DEPTH, PAWN_VALUE, KNIGHT_VALUE, BISHOP_VALUE, ROOK_VALUE, QUEEN_VALUE, KING_VALUE, USE_MOVE_SORTING
from AlphaSort import MoveSorter

# ------------------- Вспомогательные функции -------------------
def popcount(x):
    return x.bit_count() if hasattr(int, "bit_count") else bin(x).count("1")

FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
RANK_1 = 0x00000000000000FF
RANK_2 = 0x000000000000FF00
RANK_7 = 0x00FF000000000000
RANK_8 = 0xFF00000000000000
ALL_SQUARES = 0xFFFFFFFFFFFFFFFF

def sq_to_str(sq):
    return chr(ord('a') + (sq % 8)) + str(8 - sq // 8)

# ------------------- Класс доски --------------------------------------------
class Board:
    def __init__(self):
        self.pawns   = [0, 0]
        self.knights = [0, 0]
        self.bishops = [0, 0]
        self.rooks   = [0, 0]
        self.queens  = [0, 0]
        self.kings   = [0, 0]
        self.white_pieces = 0
        self.black_pieces = 0
        self.all_pieces = 0
        self.turn = 'w'
        self.en_passant = -1
        self.castle = {'w': {'k': True, 'q': True}, 'b': {'k': True, 'q': True}}
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.history = []
        self._setup_initial()

    def _setup_initial(self):
        # Доска перевёрнута: белые сверху (7-я и 8-я горизонтали), чёрные снизу (1-я и 2-я)
        # Белые пешки на 7-й горизонтали (индексы 48-55)
        self.pawns[0] = 0x00FF000000000000
        # Чёрные пешки на 2-й горизонтали (индексы 8-15)
        self.pawns[1] = 0x000000000000FF00
        self.knights[0] = 0x4200000000000000
        self.knights[1] = 0x0000000000000042
        self.bishops[0] = 0x2400000000000000
        self.bishops[1] = 0x0000000000000024
        self.rooks[0]   = 0x8100000000000000
        self.rooks[1]   = 0x0000000000000081
        self.queens[0]  = 0x0800000000000000
        self.queens[1]  = 0x0000000000000008
        self.kings[0]   = 0x1000000000000000
        self.kings[1]   = 0x0000000000000010
        self._update_all_pieces()

    def _update_all_pieces(self):
        self.white_pieces = (self.pawns[0] | self.knights[0] | self.bishops[0] |
                             self.rooks[0] | self.queens[0] | self.kings[0])
        self.black_pieces = (self.pawns[1] | self.knights[1] | self.bishops[1] |
                             self.rooks[1] | self.queens[1] | self.kings[1])
        self.all_pieces = self.white_pieces | self.black_pieces

    def get_piece(self, sq):
        bit = 1 << sq
        if self.white_pieces & bit:
            if self.pawns[0] & bit: return 'P'
            if self.knights[0] & bit: return 'N'
            if self.bishops[0] & bit: return 'B'
            if self.rooks[0] & bit: return 'R'
            if self.queens[0] & bit: return 'Q'
            if self.kings[0] & bit: return 'K'
        elif self.black_pieces & bit:
            if self.pawns[1] & bit: return 'p'
            if self.knights[1] & bit: return 'n'
            if self.bishops[1] & bit: return 'b'
            if self.rooks[1] & bit: return 'r'
            if self.queens[1] & bit: return 'q'
            if self.kings[1] & bit: return 'k'
        return '.'

    def is_empty(self, sq):
        return not (self.all_pieces & (1 << sq))

    # ---------- Генерация ходов пешек (без изменений, вы уверены что работает) ----------
    def _generate_pawn_moves(self, color):
        moves = []
        color_idx = 0 if color == 'w' else 1
        pawns = self.pawns[color_idx]
        enemy = self.black_pieces if color == 'w' else self.white_pieces
        empty = ~self.all_pieces & ALL_SQUARES

        if color == 'w':
            direction = -8
            start_rank = RANK_7
            promo_rank = RANK_1
            cap_left_shift = -9
            cap_right_shift = -7
        else:
            direction = +8
            start_rank = RANK_2
            promo_rank = RANK_8
            cap_left_shift = +9
            cap_right_shift = +7

        if direction > 0:
            single = (pawns << direction) & empty
            double = ((pawns & start_rank) << direction) & empty
            double = (double << direction) & empty
        else:
            single = (pawns >> (-direction)) & empty
            double = ((pawns & start_rank) >> (-direction)) & empty
            double = (double >> (-direction)) & empty

        if direction > 0:
            cap_left = (pawns << cap_left_shift) & ~FILE_H & enemy
            cap_right = (pawns << cap_right_shift) & ~FILE_A & enemy
        else:
            cap_left = (pawns >> (-cap_left_shift)) & ~FILE_H & enemy
            cap_right = (pawns >> (-cap_right_shift)) & ~FILE_A & enemy
        captures = cap_left | cap_right

        promo_single = single & promo_rank
        single &= ~promo_rank
        promo_cap = captures & promo_rank
        captures &= ~promo_rank

        bits = single
        while bits:
            lsb = bits & -bits
            to = (lsb.bit_length() - 1)
            from_sq = to - direction
            moves.append((from_sq, to, None))
            bits ^= lsb

        bits = double
        while bits:
            lsb = bits & -bits
            to = (lsb.bit_length() - 1)
            from_sq = to - 2 * direction
            moves.append((from_sq, to, None))
            bits ^= lsb

        bits = captures
        while bits:
            lsb = bits & -bits
            to = (lsb.bit_length() - 1)
            from_sq = -1
            if color == 'w':
                if (to + 7) < 64 and (self.pawns[0] & (1 << (to + 7))):
                    from_sq = to + 7
                elif (to + 9) < 64 and (self.pawns[0] & (1 << (to + 9))):
                    from_sq = to + 9
            else:
                if (to - 9) >= 0 and (self.pawns[1] & (1 << (to - 9))):
                    from_sq = to - 9
                elif (to - 7) >= 0 and (self.pawns[1] & (1 << (to - 7))):
                    from_sq = to - 7
            if from_sq != -1:
                moves.append((from_sq, to, None))
            bits ^= lsb

        for promo in ('q', 'r', 'b', 'n'):
            bits = promo_single
            while bits:
                lsb = bits & -bits
                to = (lsb.bit_length() - 1)
                from_sq = to - direction
                moves.append((from_sq, to, promo))
                bits ^= lsb
            bits = promo_cap
            while bits:
                lsb = bits & -bits
                to = (lsb.bit_length() - 1)
                from_sq = -1
                if color == 'w':
                    if (to + 7) < 64 and (self.pawns[0] & (1 << (to + 7))):
                        from_sq = to + 7
                    elif (to + 9) < 64 and (self.pawns[0] & (1 << (to + 9))):
                        from_sq = to + 9
                else:
                    if (to - 9) >= 0 and (self.pawns[1] & (1 << (to - 9))):
                        from_sq = to - 9
                    elif (to - 7) >= 0 and (self.pawns[1] & (1 << (to - 7))):
                        from_sq = to - 7
                if from_sq != -1:
                    moves.append((from_sq, to, promo))
                bits ^= lsb

        if self.en_passant != -1:
            ep_sq = self.en_passant
            for dc in (-1, 1):
                from_sq = ep_sq + dc
                if 0 <= from_sq < 64:
                    if color == 'w' and (from_sq // 8) == 4 and (self.pawns[0] & (1 << from_sq)):
                        moves.append((from_sq, ep_sq, None))
                    elif color == 'b' and (from_sq // 8) == 3 and (self.pawns[1] & (1 << from_sq)):
                        moves.append((from_sq, ep_sq, None))
        return moves

    # ---------- Генерация ходов коня (без изменений) ----------
    def _generate_knight_moves(self, color):
        moves = []
        knight_attacks = self._precomputed_knight_attacks()
        color_idx = 0 if color == 'w' else 1
        knights = self.knights[color_idx]
        own = self.white_pieces if color == 'w' else self.black_pieces
        while knights:
            lsb = knights & -knights
            from_sq = (lsb.bit_length() - 1)
            attacks = knight_attacks[from_sq] & ~own
            bits = attacks
            while bits:
                lsb2 = bits & -bits
                to = (lsb2.bit_length() - 1)
                moves.append((from_sq, to, None))
                bits ^= lsb2
            knights ^= lsb
        return moves

    # ---------- Генерация ходов короля (включая рокировку) ----------
    def _generate_king_moves(self, color):
        moves = []
        king_attacks = self._precomputed_king_attacks()
        color_idx = 0 if color == 'w' else 1
        king = self.kings[color_idx]
        own = self.white_pieces if color == 'w' else self.black_pieces
        from_sq = (king.bit_length() - 1)
        attacks = king_attacks[from_sq] & ~own
        bits = attacks
        while bits:
            lsb = bits & -bits
            to = (lsb.bit_length() - 1)
            moves.append((from_sq, to, None))
            bits ^= lsb

        if color == 'w':
            if self.castle['w']['k']:
                if not (self.all_pieces & (1 << 5)) and not (self.all_pieces & (1 << 6)):
                    if not self.is_square_attacked(4, 'b') and not self.is_square_attacked(5, 'b') and not self.is_square_attacked(6, 'b'):
                        moves.append((4, 6, None))
            if self.castle['w']['q']:
                if not (self.all_pieces & (1 << 3)) and not (self.all_pieces & (1 << 2)) and not (self.all_pieces & (1 << 1)):
                    if not self.is_square_attacked(4, 'b') and not self.is_square_attacked(3, 'b') and not self.is_square_attacked(2, 'b'):
                        moves.append((4, 2, None))
        else:
            if self.castle['b']['k']:
                if not (self.all_pieces & (1 << 61)) and not (self.all_pieces & (1 << 62)):
                    if not self.is_square_attacked(60, 'w') and not self.is_square_attacked(61, 'w') and not self.is_square_attacked(62, 'w'):
                        moves.append((60, 62, None))
            if self.castle['b']['q']:
                if not (self.all_pieces & (1 << 59)) and not (self.all_pieces & (1 << 58)) and not (self.all_pieces & (1 << 57)):
                    if not self.is_square_attacked(60, 'w') and not self.is_square_attacked(59, 'w') and not self.is_square_attacked(58, 'w'):
                        moves.append((60, 58, None))
        return moves

    # ---------- Генерация скользящих фигур (без изменений) ----------
    def _generate_sliding_moves(self, color, directions, piece_mask, own_mask):
        moves = []
        pieces = piece_mask
        while pieces:
            lsb = pieces & -pieces
            from_sq = (lsb.bit_length() - 1)
            for dr, dc in directions:
                sq = from_sq
                while True:
                    row = sq // 8 + dr
                    col = sq % 8 + dc
                    if row < 0 or row >= 8 or col < 0 or col >= 8:
                        break
                    to = row * 8 + col
                    bit = 1 << to
                    if self.all_pieces & bit:
                        if own_mask & bit:
                            break
                        else:
                            moves.append((from_sq, to, None))
                            break
                    else:
                        moves.append((from_sq, to, None))
                    sq = to
            pieces ^= lsb
        return moves

    # ---------- Генерация псевдолегальных ходов ----------
    def generate_pseudo_legal_moves(self, color):
        moves = []
        color_idx = 0 if color == 'w' else 1
        own = self.white_pieces if color == 'w' else self.black_pieces

        moves.extend(self._generate_pawn_moves(color))
        moves.extend(self._generate_knight_moves(color))
        moves.extend(self._generate_sliding_moves(color, [(-1,-1),(-1,1),(1,-1),(1,1)], self.bishops[color_idx], own))
        moves.extend(self._generate_sliding_moves(color, [(-1,0),(1,0),(0,-1),(0,1)], self.rooks[color_idx], own))
        moves.extend(self._generate_sliding_moves(color, [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)], self.queens[color_idx], own))
        moves.extend(self._generate_king_moves(color))
        return moves

    # ---------- Предвычисленные таблицы атак ----------
    @staticmethod
    def _precomputed_knight_attacks():
        attacks = [0] * 64
        for sq in range(64):
            r, c = sq // 8, sq % 8
            mask = 0
            for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    mask |= 1 << (nr*8+nc)
            attacks[sq] = mask
        return attacks

    @staticmethod
    def _precomputed_king_attacks():
        attacks = [0] * 64
        for sq in range(64):
            r, c = sq // 8, sq % 8
            mask = 0
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr == 0 and dc == 0: continue
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        mask |= 1 << (nr*8+nc)
            attacks[sq] = mask
        return attacks

    # ---------- Проверка атаки на клетку (без изменений) ----------
    def is_square_attacked(self, sq, attacker_color):
        # Пешки
        if attacker_color == 'w':
            if (sq % 8) > 0 and (self.pawns[0] & (1 << (sq + 9))):
                return True
            if (sq % 8) < 7 and (self.pawns[0] & (1 << (sq + 7))):
                return True
        else:
            if (sq % 8) > 0 and (self.pawns[1] & (1 << (sq - 7))):
                return True
            if (sq % 8) < 7 and (self.pawns[1] & (1 << (sq - 9))):
                return True

        knight_attacks = self._precomputed_knight_attacks()
        knights = self.knights[0] if attacker_color == 'w' else self.knights[1]
        if knight_attacks[sq] & knights:
            return True

        king_attacks = self._precomputed_king_attacks()
        king = self.kings[0] if attacker_color == 'w' else self.kings[1]
        if king_attacks[sq] & king:
            return True

        # Скользящие фигуры
        directions = [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]
        for dr, dc in directions:
            r = sq // 8 + dr
            c = sq % 8 + dc
            while 0 <= r < 8 and 0 <= c < 8:
                to = r * 8 + c
                bit = 1 << to
                if self.all_pieces & bit:
                    if attacker_color == 'w':
                        if self.white_pieces & bit:
                            if dr != 0 and dc != 0:
                                if self.bishops[0] & bit or self.queens[0] & bit:
                                    return True
                            else:
                                if self.rooks[0] & bit or self.queens[0] & bit:
                                    return True
                        break
                    else:
                        if self.black_pieces & bit:
                            if dr != 0 and dc != 0:
                                if self.bishops[1] & bit or self.queens[1] & bit:
                                    return True
                            else:
                                if self.rooks[1] & bit or self.queens[1] & bit:
                                    return True
                        break
                r += dr
                c += dc
        return False

    def is_king_attacked(self, color):
        color_idx = 0 if color == 'w' else 1
        king_bit = self.kings[color_idx]
        if king_bit == 0:
            return False
        sq = (king_bit.bit_length() - 1)
        attacker = 'b' if color == 'w' else 'w'
        return self.is_square_attacked(sq, attacker)

    # ---------- make_move / undo_move (без изменений) ----------
    def make_move(self, move):
        from_sq, to_sq, promo = move
        state = {
            'from': from_sq, 'to': to_sq, 'promo': promo,
            'captured': self.get_piece(to_sq),
            'en_passant': self.en_passant,
            'castle': copy.deepcopy(self.castle),
            'halfmove': self.halfmove_clock,
            'fullmove': self.fullmove_number,
            'turn': self.turn,
            'ep_triggered': False
        }

        color = self.turn
        color_idx = 0 if color == 'w' else 1
        enemy_idx = 1 - color_idx
        piece = self.get_piece(from_sq)
        if piece == '.':
            return False

        self._clear_bit(from_sq, piece, color_idx)
        captured = self.get_piece(to_sq)
        if captured != '.':
            self._clear_bit(to_sq, captured, enemy_idx)
        self._set_bit(to_sq, piece, color_idx)

        if promo is not None:
            self._clear_bit(to_sq, piece, color_idx)
            new_piece = promo.upper() if color == 'w' else promo.lower()
            self._set_bit(to_sq, new_piece, color_idx)

        if piece.lower() == 'p' and to_sq == self.en_passant:
            ep_sq = self.en_passant
            if color == 'w':
                self._clear_bit(ep_sq + 8, 'p', 1)
            else:
                self._clear_bit(ep_sq - 8, 'P', 0)
            state['ep_triggered'] = True

        if piece.lower() == 'k':
            if from_sq == 4 and to_sq == 6:
                self._clear_bit(7, 'R', 0)
                self._set_bit(5, 'R', 0)
            elif from_sq == 4 and to_sq == 2:
                self._clear_bit(0, 'R', 0)
                self._set_bit(3, 'R', 0)
            elif from_sq == 60 and to_sq == 62:
                self._clear_bit(63, 'r', 1)
                self._set_bit(61, 'r', 1)
            elif from_sq == 60 and to_sq == 58:
                self._clear_bit(56, 'r', 1)
                self._set_bit(59, 'r', 1)
            self.castle[color]['k'] = False
            self.castle[color]['q'] = False

        if piece.lower() == 'r':
            if color == 'w':
                if from_sq == 7: self.castle['w']['k'] = False
                if from_sq == 0: self.castle['w']['q'] = False
            else:
                if from_sq == 63: self.castle['b']['k'] = False
                if from_sq == 56: self.castle['b']['q'] = False

        if captured.lower() == 'r':
            if color == 'w':
                if to_sq == 7: self.castle['w']['k'] = False
                if to_sq == 0: self.castle['w']['q'] = False
            else:
                if to_sq == 63: self.castle['b']['k'] = False
                if to_sq == 56: self.castle['b']['q'] = False

        self.en_passant = -1
        if piece.lower() == 'p' and abs(to_sq - from_sq) == 16:
            self.en_passant = (from_sq + to_sq) // 2

        if piece.lower() == 'p' or captured != '.':
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        self.turn = 'b' if color == 'w' else 'w'
        if self.turn == 'w':
            self.fullmove_number += 1

        self._update_all_pieces()

        if self.is_king_attacked(color):
            self.undo_move(state)
            return False

        self.history.append(state)
        return True

    def undo_move(self, state=None):
        if not self.history and state is None:
            return
        if state is None:
            state = self.history.pop()
        from_sq = state['from']
        to_sq = state['to']
        promo = state['promo']
        captured = state['captured']
        old_en_passant = state['en_passant']
        old_castle = state['castle']
        old_halfmove = state['halfmove']
        old_fullmove = state['fullmove']
        old_turn = state['turn']
        ep_triggered = state.get('ep_triggered', False)

        color = old_turn
        color_idx = 0 if color == 'w' else 1
        enemy_idx = 1 - color_idx

        piece = self.get_piece(to_sq)
        if promo is not None:
            self._clear_bit(to_sq, piece, color_idx)
            self._set_bit(from_sq, 'P' if color == 'w' else 'p', color_idx)
        else:
            self._clear_bit(to_sq, piece, color_idx)
            self._set_bit(from_sq, piece, color_idx)

        if captured != '.':
            self._set_bit(to_sq, captured, enemy_idx)

        if ep_triggered:
            ep_sq = old_en_passant
            if color == 'w':
                self._set_bit(ep_sq + 8, 'p', 1)
            else:
                self._set_bit(ep_sq - 8, 'P', 0)

        if piece.lower() == 'k' or promo is not None:
            if from_sq == 4 and to_sq == 6:
                self._clear_bit(5, 'R', 0)
                self._set_bit(7, 'R', 0)
            elif from_sq == 4 and to_sq == 2:
                self._clear_bit(3, 'R', 0)
                self._set_bit(0, 'R', 0)
            elif from_sq == 60 and to_sq == 62:
                self._clear_bit(61, 'r', 1)
                self._set_bit(63, 'r', 1)
            elif from_sq == 60 and to_sq == 58:
                self._clear_bit(59, 'r', 1)
                self._set_bit(56, 'r', 1)

        self.en_passant = old_en_passant
        self.castle = old_castle
        self.halfmove_clock = old_halfmove
        self.fullmove_number = old_fullmove
        self.turn = old_turn
        self._update_all_pieces()

    def _clear_bit(self, sq, piece_char, color_idx):
        bit = 1 << sq
        p = piece_char.lower()
        if p == 'p': self.pawns[color_idx] &= ~bit
        elif p == 'n': self.knights[color_idx] &= ~bit
        elif p == 'b': self.bishops[color_idx] &= ~bit
        elif p == 'r': self.rooks[color_idx] &= ~bit
        elif p == 'q': self.queens[color_idx] &= ~bit
        elif p == 'k': self.kings[color_idx] &= ~bit

    def _set_bit(self, sq, piece_char, color_idx):
        bit = 1 << sq
        p = piece_char.lower()
        if p == 'p': self.pawns[color_idx] |= bit
        elif p == 'n': self.knights[color_idx] |= bit
        elif p == 'b': self.bishops[color_idx] |= bit
        elif p == 'r': self.rooks[color_idx] |= bit
        elif p == 'q': self.queens[color_idx] |= bit
        elif p == 'k': self.kings[color_idx] |= bit

    # ---------- Легальные ходы ----------
    def get_legal_moves(self, color=None):
        if color is None:
            color = self.turn
        pseudo = self.generate_pseudo_legal_moves(color)
        legal = []
        for move in pseudo:
            if self.make_move(move):
                legal.append(move)
                self.undo_move()
        return legal

    def get_legal_moves_for_sq(self, sq):
        color = self.turn
        piece = self.get_piece(sq)
        if piece == '.':
            return []
        if (color == 'w' and piece.islower()) or (color == 'b' and piece.isupper()):
            return []
        legal = self.get_legal_moves(color)
        return [m for m in legal if m[0] == sq]

    def is_checkmate(self):
        if not self.is_king_attacked(self.turn):
            return False
        return len(self.get_legal_moves()) == 0

    def is_stalemate(self):
        if self.is_king_attacked(self.turn):
            return False
        return len(self.get_legal_moves()) == 0

    # ---------- Оценка ----------
    def evaluate(self):
        score = 0
        score += popcount(self.pawns[0]) * PAWN_VALUE
        score += popcount(self.knights[0]) * KNIGHT_VALUE
        score += popcount(self.bishops[0]) * BISHOP_VALUE
        score += popcount(self.rooks[0]) * ROOK_VALUE
        score += popcount(self.queens[0]) * QUEEN_VALUE
        score += popcount(self.kings[0]) * KING_VALUE

        score -= popcount(self.pawns[1]) * PAWN_VALUE
        score -= popcount(self.knights[1]) * KNIGHT_VALUE
        score -= popcount(self.bishops[1]) * BISHOP_VALUE
        score -= popcount(self.rooks[1]) * ROOK_VALUE
        score -= popcount(self.queens[1]) * QUEEN_VALUE
        score -= popcount(self.kings[1]) * KING_VALUE

        # Бонус за центр
        center_mask = 0x0000001818000000
        score += popcount(self.pawns[0] & center_mask) * 10
        score -= popcount(self.pawns[1] & center_mask) * 10
        return score

# ------------------- Класс Engine (ИСПРАВЛЕН) --------------------------------
class Engine:
    def __init__(self, max_depth=MAX_DEPTH):
        self.max_depth = max_depth
        self.nodes = 0
        self.sorter = MoveSorter()

    def alpha_beta(self, board, depth, alpha, beta, maximizing):
        self.nodes += 1
        if depth == 0:
            return board.evaluate()
        moves = board.get_legal_moves()
        if not moves:
            if board.is_king_attacked(board.turn):
                return -999999 if maximizing else 999999
            return 0
        if USE_MOVE_SORTING:
            moves = self.sorter.sort_moves(board, moves)

        if maximizing:
            value = -float('inf')
            for move in moves:
                if board.make_move(move):
                    score = self.alpha_beta(board, depth-1, alpha, beta, False)
                    board.undo_move()
                    if score > value:
                        value = score
                    alpha = max(alpha, value)
                    if beta <= alpha:
                        break
            return value
        else:
            value = float('inf')
            for move in moves:
                if board.make_move(move):
                    score = self.alpha_beta(board, depth-1, alpha, beta, True)
                    board.undo_move()
                    if score < value:
                        value = score
                    beta = min(beta, value)
                    if beta <= alpha:
                        break
            return value

    def best_move(self, board):
        # Определяем, максимизирует ли текущий игрок (белые) или минимизирует (чёрные)
        is_maximizing = (board.turn == 'w')
        best = None
        best_val = -float('inf') if is_maximizing else float('inf')
        moves = board.get_legal_moves()
        if not moves:
            return None
        if USE_MOVE_SORTING:
            moves = self.sorter.sort_moves(board, moves)

        for move in moves:
            if board.make_move(move):
                # После хода ходит оппонент – его режим противоположный
                val = self.alpha_beta(board, self.max_depth-1, -float('inf'), float('inf'), not is_maximizing)
                board.undo_move()
                if is_maximizing:
                    if val > best_val:
                        best_val = val
                        best = move
                else:
                    if val < best_val:
                        best_val = val
                        best = move
        return best