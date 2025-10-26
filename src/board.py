import chess

class GameState:
    def __init__(self, fen: str = chess.STARTING_FEN):
        self.board = chess.Board(fen)

    def get_legal_moves(self):
        return self.board.legal_moves

    def make_move(self, move):
        self.board.push(move)

    def unmake_move(self):
        self.board.pop()

    def is_game_over(self):
        return self.board.is_game_over()

    def get_outcome(self):
        return self.board.outcome()

    def is_stalemate(self):
        return self.board.is_stalemate()

    def is_insufficient_material(self):
        return self.board.is_insufficient_material()

    def is_checkmate(self):
        return self.board.is_checkmate()

    def is_repetition(self):
        return self.board.is_repetition()

    @property
    def fen(self):
        return self.board.fen()

    def __str__(self):
        return self.board.__str__()

    def turn(self):
        return self.board.turn