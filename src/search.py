import chess
import chess.polyglot
import time
from chess import polyglot
from .evaluation import evaluate_board
from .board import GameState
from .constant import MVV_LVA_SCORES

# ==============================================================================
# Tập hợp các biến toàn cục phục vụ cho quá trình tìm kiếm nước đi tối ưu
# trong engine cờ vua theo thuật toán Negamax + Alpha-Beta pruning nâng cao.
# ==============================================================================

position_count = 0                 # Đếm số lượng vị trí đã được duyệt trong tìm kiếm
MAX_DEPTH = 64                     # Giới hạn độ sâu tối đa (phòng tránh tràn ngăn xếp)
MATE_VALUE = 100000                # Giá trị ước lượng cho thế chiếu hết (mate score)

# 🧠 Cờ trong bảng băm (Transposition Table Flags)
TT_EXACT, TT_LOWERBOUND, TT_UPPERBOUND = 0, 1, 2
# TT_EXACT: giá trị chính xác (tốt nhất trong khoảng alpha-beta)
# TT_LOWERBOUND: giá trị là giới hạn dưới (score >= value)
# TT_UPPERBOUND: giá trị là giới hạn trên (score <= value)

# 🗡️ Killer Moves: Lưu 2 nước “giết” mạnh nhất trong mỗi độ sâu
# (được dùng lại trong quá trình sắp xếp nước đi để tăng tốc độ cắt tỉa)
killer_moves = [[None, None] for _ in range(MAX_DEPTH)]

# 🧩 History Heuristic:
# Bộ nhớ thống kê độ hiệu quả của từng nước đi trong quá khứ (theo chiều đi và màu quân)
# Dạng mảng [color][from_square][to_square]
history_heuristic = [[[0] * 64 for _ in range(64)] for _ in range(2)]

# 🌳 Hằng số cho Null Move Pruning (bỏ qua 1 lượt để kiểm tra cắt tỉa nhanh)
NULL_MOVE_REDUCTION = 2


# ==============================================================================
# 🔹 HÀM HỖ TRỢ CƠ BẢN
# ==============================================================================

def has_non_pawn_material(board: chess.Board) -> bool:
    """Kiểm tra xem bên đang đi có quân nào khác ngoài Tốt không.
    Dùng để quyết định có thể áp dụng Null Move Pruning (vì endgame thường ít hiệu quả)."""
    for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
        if len(board.pieces(pt, board.turn)) > 0:
            return True
    return False


def is_mate_score(score: float) -> bool:
    """Xác định xem điểm đánh giá có tương ứng với thế chiếu hết (Mate) hay không."""
    return abs(score) > MATE_VALUE - 1000


# ==============================================================================
# 🔸 LỚP VÀ BẢNG BĂM (TRANSPOSITION TABLE)
# ==============================================================================

class TTEntry:
    """Một phần tử trong Transposition Table (Bảng băm lưu kết quả đã tính)."""
    __slots__ = ('depth', 'score', 'flag', 'best_move')

    def __init__(self, depth, score, flag, best_move):
        self.depth = depth        # Độ sâu khi lưu
        self.score = score        # Giá trị đánh giá của vị trí
        self.flag = flag          # Kiểu giá trị (EXACT / LOWERBOUND / UPPERBOUND)
        self.best_move = best_move  # Nước đi tốt nhất tìm được tại node đó


# Bảng băm toàn cục dùng để lưu kết quả tìm kiếm đã xử lý
transposition_table = {}


# ==============================================================================
# 🔹 SẮP XẾP NƯỚC ĐI (Move Ordering)
# ==============================================================================

def score_move(board: chess.Board, move: chess.Move, depth: int, tt_move: chess.Move = None) -> int:
    """Đánh giá mức độ ưu tiên của nước đi để sắp xếp thứ tự duyệt.
    Các tiêu chí ưu tiên:
    1️ Nước từ Transposition Table (TT move)
    2️ Nước phong cấp
    3️ Nước ăn quân (MVV-LVA: Most Valuable Victim - Least Valuable Attacker)
    4️ Killer move
    5️ History heuristic (hiệu quả lịch sử)
    """
    # Ưu tiên 1: TT move
    if tt_move and move == tt_move:
        return 10_000_000

    # Ưu tiên 2: Nước phong cấp (promotion)
    if move.promotion:
        return 9_500_000 + move.promotion

    # Ưu tiên 3: Ăn quân (capture)
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim and attacker:
            return 9_000_000 + MVV_LVA_SCORES[attacker.piece_type][victim.piece_type]
        return 9_000_000  # Ăn chéo (en passant)
    else:
        # Ưu tiên 4: Killer moves
        if killer_moves[depth][0] == move:
            return 8_000_000
        if killer_moves[depth][1] == move:
            return 7_900_000

    # Ưu tiên 5: History heuristic
    return history_heuristic[board.turn][move.from_square][move.to_square]


def order_moves(board: chess.Board, moves: list[chess.Move], depth: int, tt_move: chess.Move = None) -> list[chess.Move]:
    """Sắp xếp danh sách nước đi theo điểm ưu tiên để tối ưu hóa việc cắt tỉa."""
    return sorted(moves, key=lambda m: score_move(board, m, depth, tt_move), reverse=True)



# ==============================================================================
# Giúp tránh "hiệu ứng cắt sai" (horizon effect) khi vị trí chưa ổn định (ví dụ có thể ăn lại).
# Thuật toán chỉ mở rộng thêm các nước ăn/quân hoặc phong cấp để ổn định vị trí.
# ==============================================================================

def quiescence_search(gamestate: GameState, alpha: float, beta: float, max_qdepth=32, qdepth=0) -> float:
    global position_count
    position_count += 1

    # Giới hạn độ sâu yên tĩnh
    if qdepth > max_qdepth:
        return evaluate_board(gamestate.board)

    # Đánh giá ban đầu (stand pat)
    stand_pat = evaluate_board(gamestate.board)
    if stand_pat >= beta:
        return beta
    alpha = max(alpha, stand_pat)

    # Lấy các nước capture + promotion để mở rộng
    capture_moves = list(gamestate.board.generate_legal_captures())
    for move in gamestate.board.generate_legal_moves():
        if move.promotion and not gamestate.board.is_capture(move):
            capture_moves.append(move)

    # Sắp xếp các nước ăn
    capture_moves = order_moves(gamestate.board, capture_moves, qdepth)

    # Duyệt từng nước capture
    for move in capture_moves:
        gamestate.make_move(move)
        score = -quiescence_search(gamestate, -beta, -alpha, max_qdepth, qdepth + 1)
        gamestate.unmake_move()

        if score >= beta:
            return beta
        alpha = max(alpha, score)

    return alpha


# ==============================================================================
# 🔹 NEGAMAX TÌM KIẾM (với Alpha-Beta + TT + Killers + History + Null Move)
# ==============================================================================
# Đây là lõi của công cụ tìm kiếm nước đi. Negamax là biến thể của Minimax:
#     score = -negamax(child, -beta, -alpha)
# Engine sử dụng kỹ thuật tối ưu:
#   - Alpha-Beta Pruning (cắt tỉa nhánh không cần thiết)
#   - Null Move Pruning
#   - Killer Move / History Heuristic
#   - Transposition Table caching
# ==============================================================================

def negamax(gamestate: GameState, depth: int, alpha: float, beta: float, ply: int, do_null: bool = True) -> float:
    global position_count, killer_moves, history_heuristic

    # Kiểm tra điều kiện kết thúc ván cờ
    if gamestate.board.is_game_over():
        if gamestate.board.is_checkmate():
            return -MATE_VALUE + ply
        return 0

    # Khi đạt độ sâu 0 thì chuyển sang quiescence search
    if depth <= 0:
        return quiescence_search(gamestate, alpha, beta)

    position_count += 1

    # Hòa do lặp lại hoặc luật 50 nước
    if ply > 0 and (gamestate.board.is_repetition() or gamestate.board.is_fifty_moves()):
        return 0

    # Giới hạn phòng tràn
    if ply >= MAX_DEPTH:
        return evaluate_board(gamestate.board)

    original_alpha = alpha
    zobrist_key = chess.polyglot.zobrist_hash(gamestate.board)
    tt_entry = transposition_table.get(zobrist_key)
    tt_move = None

    # Kiểm tra bảng băm (Transposition Table)
    if tt_entry and tt_entry.depth >= depth:
        tt_score = tt_entry.score

        # Hiệu chỉnh điểm Mate theo độ sâu (để tránh sai lệch)
        if is_mate_score(tt_score):
            if tt_score > 0:
                tt_score -= ply
            else:
                tt_score += ply

        # Áp dụng theo loại flag
        if tt_entry.flag == TT_EXACT:
            return tt_score
        elif tt_entry.flag == TT_LOWERBOUND:
            alpha = max(alpha, tt_score)
        elif tt_entry.flag == TT_UPPERBOUND:
            beta = min(beta, tt_score)

        if alpha >= beta:
            return tt_score
        tt_move = tt_entry.best_move

    # 🌀 Null Move Pruning: bỏ qua lượt đi để kiểm tra xem có thể cắt tỉa hay không
    if (do_null and depth >= 3 and not gamestate.board.is_check() and
        has_non_pawn_material(gamestate.board) and not is_mate_score(beta)):

        gamestate.board.push(chess.Move.null())
        score = -negamax(gamestate, depth - 1 - NULL_MOVE_REDUCTION, -beta, -beta + 1, ply + 1, False)
        gamestate.board.pop()

        if score >= beta:
            return beta

    # Khởi tạo giá trị tốt nhất
    best_score = float('-inf')
    best_move = None

    # Sắp xếp nước đi
    ordered_moves = order_moves(gamestate.board, list(gamestate.get_legal_moves()), depth, tt_move)

    # Duyệt từng nước đi
    for move in ordered_moves:
        gamestate.make_move(move)
        score = -negamax(gamestate, depth - 1, -beta, -alpha, ply + 1)
        gamestate.unmake_move()

        # Cập nhật nếu tốt hơn
        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        # 💥 Cắt tỉa beta
        if alpha >= beta:
            if not gamestate.board.is_capture(move) and depth < MAX_DEPTH:
                # Cập nhật Killer Move + History Heuristic
                if killer_moves[depth][0] != move:
                    killer_moves[depth][1] = killer_moves[depth][0]
                    killer_moves[depth][0] = move
                history_heuristic[gamestate.board.turn][move.from_square][move.to_square] += depth * depth
            break

    # Chuẩn bị lưu vào bảng băm
    score_to_store = best_score
    if is_mate_score(best_score):
        if best_score > 0:
            score_to_store += ply
        else:
            score_to_store -= ply

    # Chọn flag tương ứng
    flag = TT_EXACT
    if best_score <= original_alpha:
        flag = TT_UPPERBOUND
    elif best_score >= beta:
        flag = TT_LOWERBOUND

    # 🧱 Lưu vào Transposition Table
    transposition_table[zobrist_key] = TTEntry(depth, best_score, flag, best_move)

    return best_score


# ==============================================================================
# 🔹 HÀM GỐC (Root Search) — tìm nước tốt nhất ở mức cao nhất
# ==============================================================================

def search_root(gamestate: GameState, depth: int, pv_move: chess.Move = None) -> tuple[chess.Move, float]:
    """Tìm nước đi tốt nhất tại root với độ sâu cụ thể (có hỗ trợ PV move ưu tiên)."""
    alpha, beta = float('-inf'), float('inf')

    legal_moves = list(gamestate.get_legal_moves())
    if not legal_moves:
        return None, evaluate_board(gamestate.board)

    # Ưu tiên PV move (nếu có) bằng cách đưa lên đầu danh sách
    if pv_move and pv_move in legal_moves:
        legal_moves.insert(0, legal_moves.pop(legal_moves.index(pv_move)))

    start_index = 1 if pv_move and pv_move in legal_moves else 0
    sorted_part = order_moves(gamestate.board, legal_moves[start_index:], depth)
    legal_moves = legal_moves[:start_index] + sorted_part

    best_move = legal_moves[0]
    best_score = float('-inf')

    # Duyệt từng nước ở root
    for move in legal_moves:
        gamestate.make_move(move)
        score = -negamax(gamestate, depth - 1, -beta, -alpha, 1)
        gamestate.unmake_move()

        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)

    return best_move, best_score


# ==============================================================================
# 🔹 LÃO HÓA HISTORY HEURISTIC (Ageing)
# ==============================================================================
# Khi giá trị History tăng quá cao, ta chia đôi để tránh tràn hoặc sai lệch.
# ==============================================================================

def age_history_heuristic():
    """Giảm bớt giá trị History Heuristic khi nó quá lớn để tránh tràn số."""
    global history_heuristic
    max_value = max(max(max(row) for row in color_table) for color_table in history_heuristic)
    if max_value > 10000:
        history_heuristic = [[[val // 2 for val in row] for row in color_table] for color_table in history_heuristic]


# ==============================================================================
# 🔹 TÌM NƯỚC ĐI TỐT NHẤT (Iterative Deepening)
# ==============================================================================
# Đây là điểm khởi đầu chính của engine khi tìm nước đi.
# Gồm các giai đoạn:
#   1️⃣ Tra sách mở (Opening Book)
#   2️⃣ Khởi tạo lại các bảng heuristic
#   3️⃣ Lặp sâu dần (Iterative Deepening) để cải thiện kết quả
#   4️⃣ In thông tin tìm kiếm theo chuẩn UCI
# ==============================================================================

def find_best_move(gamestate: GameState, max_depth: int=  3, time_limit_seconds: int = None) -> chess.Move:
    global position_count, killer_moves, history_heuristic, transposition_table

    #  Kiểm tra sách khai cuộc (Opening Book)
    try:
        with polyglot.MemoryMappedReader("src/Cerebellum3Merge.bin") as reader:
            entry = reader.get(gamestate.board)
            if entry is not None:
                print(f"Book move: {entry.move}")
                return entry.move
    except FileNotFoundError:
        pass

    #  Reset lại bộ nhớ tìm kiếm
    position_count = 0
    killer_moves = [[None, None] for _ in range(MAX_DEPTH)]
    history_heuristic = [[[0] * 64 for _ in range(64)] for _ in range(2)]
    transposition_table.clear()

    best_move_overall = None
    start_time = time.time()

    # ♻️ Tìm kiếm sâu dần (Iterative Deepening)
    for depth in range(1, max_depth + 1):
        move, score = search_root(gamestate, depth, best_move_overall)

        if move:
            best_move_overall = move

        elapsed_ms = (time.time() - start_time) * 1000
        nps = int(position_count / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0

        # In thông tin theo chuẩn UCI
        score_info = "mate" if score in (float('inf'), float('-inf')) else f"cp {int(score)}"
        print(f"info depth {depth} score {score_info} time {int(elapsed_ms)} nodes {position_count} nps {nps} pv {move.uci() if move else 'none'}")

        # Giảm giá trị history sau mỗi 5 tầng để tránh tràn
        if depth % 5 == 0:
            age_history_heuristic()

        # ⏱️ Giới hạn thời gian tìm kiếm
        if time_limit_seconds and elapsed_ms / 1000 > time_limit_seconds:
            print("Time limit reached!")
            break

        # Nếu phát hiện thế chiếu hết bắt buộc (forced mate)
        if is_mate_score(score) and abs(score) > MATE_VALUE - 100:
            print(f"Mate found at depth {depth}")
            break

    return best_move_overall
