import chess
import chess.polyglot
import time
from chess import polyglot
from .evaluation import evaluate_board
from .board import GameState
from .constant import MVV_LVA_SCORES
import copy
# ==============================================================================
# DATA STRUCTURES AND ADVANCED CONSTANTS
# ==============================================================================

position_count = 0
MAX_DEPTH = 64
MATE_VALUE = 100000

# Time management
search_start_time = 0
search_time_limit = 0

# Transposition Table Flags
TT_EXACT, TT_LOWERBOUND, TT_UPPERBOUND = 0, 1, 2

# Killer Moves and History Heuristic
killer_moves = [[None, None] for _ in range(MAX_DEPTH)]
history_heuristic = [[[0] * 64 for _ in range(64)] for _ in range(2)]

# Pruning constants
NULL_MOVE_REDUCTION = 2


class TimeoutException(Exception):
    """Raised when search time limit is exceeded"""
    pass


def check_time():
    global search_start_time, search_time_limit
    if search_time_limit <= 0:
        return
    elapsed = time.time() - search_start_time
    remaining = search_time_limit - elapsed
    # Kiểm tra thường xuyên hơn khi sắp hết giờ
    if remaining < 0:
        raise TimeoutException()
    elif remaining < 0.1 and position_count % 256 == 0:
        raise TimeoutException()
    elif position_count % 1024 == 0 and elapsed > search_time_limit * 0.9:
        raise TimeoutException()

def has_non_pawn_material(board: chess.Board) -> bool:
    """Return True if side to move has non-pawn material."""
    for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
        if len(board.pieces(pt, board.turn)) > 0:
            return True
    return False


def is_mate_score(score: float) -> bool:
    """Check if a score represents a mate."""
    return abs(score) > MATE_VALUE - 1000


class TTEntry:
    _slots_ = ('depth', 'score', 'flag', 'best_move')

    def __init__(self, depth, score, flag, best_move):
        self.depth, self.score, self.flag, self.best_move = depth, score, flag, best_move


transposition_table = {}


# ==============================================================================
# MOVE ORDERING
# ==============================================================================

def score_move(board: chess.Board, move: chess.Move, depth: int, tt_move: chess.Move = None) -> int:
    """Assign score to move: TT > Captures > Promotions > Killers > History."""
    if tt_move and move == tt_move:
        return 10_000_000
    if move.promotion:
        return 9_500_000 + move.promotion
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim and attacker:
            return 9_000_000 + MVV_LVA_SCORES[attacker.piece_type][victim.piece_type]
        return 9_000_000  # En-passant
    else:  # Quiet moves
        if depth < MAX_DEPTH:
            if killer_moves[depth][0] == move:
                return 8_000_000
            if killer_moves[depth][1] == move:
                return 7_900_000
    return history_heuristic[board.turn][move.from_square][move.to_square]


def order_moves(board: chess.Board, moves: list[chess.Move], depth: int, tt_move: chess.Move = None) -> list[
    chess.Move]:
    return sorted(moves, key=lambda m: score_move(board, m, depth, tt_move), reverse=True)


# ==============================================================================
# SEARCH ALGORITHMS
# ==============================================================================

def quiescence_search(gamestate: GameState, alpha: float, beta: float, max_qdepth=32, qdepth=0) -> float:
    global position_count
    position_count += 1

    # Check time less frequently in qsearch for performance (every 2048 nodes)
    if position_count % 2048 == 0:
        check_time()

    if qdepth > max_qdepth:
        return evaluate_board(gamestate.board)

    stand_pat = evaluate_board(gamestate.board)
    if stand_pat >= beta:
        return beta
    alpha = max(alpha, stand_pat)

    capture_moves = list(gamestate.board.generate_legal_captures())
    for move in gamestate.board.generate_legal_moves():
        if move.promotion and not gamestate.board.is_capture(move):
            capture_moves.append(move)

    capture_moves = order_moves(gamestate.board, capture_moves, qdepth)

    for move in capture_moves:
        gamestate.make_move(move)
        score = -quiescence_search(gamestate, -beta, -alpha, max_qdepth, qdepth + 1)
        gamestate.unmake_move()

        if score >= beta:
            return beta
        alpha = max(alpha, score)

    return alpha


def negamax(gamestate: GameState, depth: int, alpha: float, beta: float, ply: int, do_null: bool = True) -> float:
    global position_count, killer_moves, history_heuristic

    # Check time less frequently for performance (every 2048 nodes)
    if position_count % 2048 == 0:
        check_time()

    # Terminal conditions
    if gamestate.board.is_game_over():
        if gamestate.board.is_checkmate():
            return -MATE_VALUE + ply
        return 0

    if depth <= 0:
        return quiescence_search(gamestate, alpha, beta)

    position_count += 1

    # Draw detection
    if ply > 0 and (gamestate.board.is_repetition() or gamestate.board.is_fifty_moves()):
        return 0

    if ply >= MAX_DEPTH:
        return evaluate_board(gamestate.board)

    original_alpha = alpha
    zobrist_key = chess.polyglot.zobrist_hash(gamestate.board)
    tt_entry = transposition_table.get(zobrist_key)
    tt_move = None

    # Retrieve from TT with mate score adjustment
    if tt_entry and tt_entry.depth >= depth:
        tt_score = tt_entry.score

        if is_mate_score(tt_score):
            if tt_score > 0:
                tt_score -= ply
            else:
                tt_score += ply

        if tt_entry.flag == TT_EXACT:
            return tt_score
        elif tt_entry.flag == TT_LOWERBOUND:
            alpha = max(alpha, tt_score)
        elif tt_entry.flag == TT_UPPERBOUND:
            beta = min(beta, tt_score)
        if alpha >= beta:
            return tt_score
        tt_move = tt_entry.best_move

    # Null Move Pruning
    if (do_null and
            depth >= 3 and
            not gamestate.board.is_check() and
            has_non_pawn_material(gamestate.board) and
            not is_mate_score(beta)):

        gamestate.board.push(chess.Move.null())
        score = -negamax(gamestate, depth - 1 - NULL_MOVE_REDUCTION, -beta, -beta + 1, ply + 1, False)
        gamestate.board.pop()

        if score >= beta:
            return beta

    best_score = float('-inf')
    best_move = None
    ordered_moves = order_moves(gamestate.board, list(gamestate.get_legal_moves()), depth, tt_move)

    for move in ordered_moves:
        gamestate.make_move(move)
        score = -negamax(gamestate, depth - 1, -beta, -alpha, ply + 1)
        gamestate.unmake_move()

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        if alpha >= beta:
            # Update killer moves and history for quiet moves
            if not gamestate.board.is_capture(move) and depth < MAX_DEPTH:
                if killer_moves[depth][0] != move:
                    killer_moves[depth][1] = killer_moves[depth][0]
                    killer_moves[depth][0] = move
                history_heuristic[gamestate.board.turn][move.from_square][move.to_square] += depth * depth
            break

    # Store in TT with mate score adjustment
    score_to_store = best_score
    if is_mate_score(best_score):
        if best_score > 0:
            score_to_store += ply
        else:
            score_to_store -= ply

    flag = TT_EXACT
    if best_score <= original_alpha:
        flag = TT_UPPERBOUND
    elif best_score >= beta:
        flag = TT_LOWERBOUND
    transposition_table[zobrist_key] = TTEntry(depth, score_to_store, flag, best_move)

    return best_score


def search_root(gamestate, depth, pv_move=None):
    alpha, beta = float('-inf'), float('inf')
    legal_moves = list(gamestate.get_legal_moves())
    if not legal_moves:
        return None, evaluate_board(gamestate.board)

    best_move = None
    best_score = float('-inf')

    for move in legal_moves:
        try:
            gamestate.make_move(move)
            score = -negamax(gamestate, depth - 1, -beta, -alpha, 1)
            gamestate.unmake_move()
        except TimeoutException:
            gamestate.unmake_move()
            raise  # propagate to upper level

        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)

    return best_move, best_score

def age_history_heuristic():
    """Prevent history scores from overflowing."""
    global history_heuristic
    max_value = max(max(max(row) for row in color_table) for color_table in history_heuristic)
    if max_value > 10000:
        history_heuristic = [[[val // 2 for val in row] for row in color_table] for color_table in history_heuristic]


def find_best_move(gamestate: GameState, max_depth: int, time_limit_seconds: float = None) -> chess.Move:
    """
    Phiên bản an toàn với board: tránh bug 'AI returned illegal move'
    và giữ nguyên cấu trúc gốc của bạn.
    """
    global position_count, killer_moves, history_heuristic, transposition_table
    global search_start_time, search_time_limit

    # 1️⃣ Opening book
    try:
        with polyglot.MemoryMappedReader(
            r"Cerebellum_Light_3Merge_200916\Cerebellum3Merge.bin"
        ) as reader:
            entry = reader.get(gamestate.board)
            if entry is not None and gamestate.board.is_legal(entry.move):
                print(f"Book move: {entry.move}")
                return entry.move
    except FileNotFoundError:
        pass

    # 2️⃣ Initialize search
    position_count = 0
    killer_moves = [[None, None] for _ in range(MAX_DEPTH)]
    history_heuristic = [[[0] * 64 for _ in range(64)] for _ in range(2)]
    transposition_table.clear()

    # 3️⃣ Time management setup
    search_start_time = time.time()
    if time_limit_seconds:
        search_time_limit = time_limit_seconds * 2.0  # extra for depth 1
    else:
        search_time_limit = 0.0

    best_move_overall = None
    last_completed_depth = 0

    # 4️⃣ Iterative Deepening
    for depth in range(1, max_depth + 1):
        try:
            # Sau độ sâu 1 -> trở về giới hạn bình thường
            if depth == 2 and time_limit_seconds:
                search_time_limit = time_limit_seconds * 0.95

            # ⚠️ Dùng bản copy của gamestate để tránh phá board gốc
            temp_state = copy.deepcopy(gamestate)

            move, score = search_root(temp_state, depth, best_move_overall)

            if move and gamestate.board.is_legal(move):
                best_move_overall = move
                last_completed_depth = depth

            elapsed_ms = (time.time() - search_start_time) * 1000
            nps = int(position_count / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0

            # UCI-formatted score
            if is_mate_score(score):
                mate_in = (MATE_VALUE - abs(score) + 1) // 2
                mate_in = -mate_in if score < 0 else mate_in
                score_info = f"mate {mate_in}"
            else:
                score_info = f"cp {int(score)}"

            print(
                f"info depth {depth} score {score_info} time {int(elapsed_ms)} "
                f"nodes {position_count} nps {nps} pv {move.uci() if move else 'none'}"
            )

            if depth % 5 == 0:
                age_history_heuristic()

            if is_mate_score(score) and abs(score) > MATE_VALUE - 100:
                print(f"Mate found at depth {depth}")
                break

            # Thông minh dừng sớm nếu depth tiếp theo quá lâu
            if time_limit_seconds and depth > 1:
                elapsed = time.time() - search_start_time
                estimated_next = elapsed * 3
                if elapsed + estimated_next > time_limit_seconds:
                    print(f"Time management: stopping before depth {depth + 1}")
                    break

        except TimeoutException:
            elapsed_ms = (time.time() - search_start_time) * 1000
            print(f"⚠️ Timeout at depth {depth} after {int(elapsed_ms)}ms")
            print(f"⚠️ Completed depth: {last_completed_depth}")
            if best_move_overall is None:
                print("⚠️ Emergency: selecting first legal move")
                legal_moves = list(gamestate.get_legal_moves())
                if legal_moves:
                    best_move_overall = legal_moves[0]
            break

        except Exception as e:
            print(f"❌ Exception during search depth {depth}: {e}")
            break

    # 5️⃣ Fallback nếu chưa có move hợp lệ
    if not best_move_overall or not gamestate.board.is_legal(best_move_overall):
        print("⚠️ Fallback: picking first legal move from board")
        legal_moves = list(gamestate.board.legal_moves)
        if legal_moves:
            best_move_overall = legal_moves[0]
            print(f"✅ Fallback move used: {best_move_overall.uci()}")
        else:
            print("❌ No legal moves (checkmate or stalemate).")
            best_move_overall = None

    print(f"✅ Best move: {best_move_overall.uci() if best_move_overall else 'none'} (depth {last_completed_depth})")
    return best_move_overall