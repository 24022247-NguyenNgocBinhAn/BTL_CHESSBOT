import chess
from .constant import *

# =================================================================================
# CÁC HÀM TIỆN ÍCH VỀ BITBOARD
# Bitboard là một cấu trúc dữ liệu hiệu quả để biểu diễn bàn cờ.
# Mỗi bitboard là một số nguyên 64-bit, trong đó mỗi bit tương ứng với một ô cờ.
# Bit 1 nghĩa là có quân cờ trên ô đó, bit 0 nghĩa là không.
# =================================================================================

def lsb_index(bb: int) -> int:
    """
    Trả về chỉ số (index) của bit 1 có trọng số nhỏ nhất (Least Significant Bit).
    Đây là một kỹ thuật bitwise hiệu quả để tìm vị trí của một quân cờ trong bitboard.
    Ví dụ: nếu bitboard chỉ có một quân ở ô E4 (index 28), hàm này sẽ trả về 28.
    Cách hoạt động:
    - (bb & -bb) sẽ tạo ra một bitboard mới chỉ chứa bit 1 nhỏ nhất của bb.
    - .bit_length() - 1 sẽ trả về chỉ số của bit đó (0-63).
    """
    return (bb & -bb).bit_length() - 1

def bitboard_iter(bb: int):
    """
    Tạo một vòng lặp (iterator) để duyệt qua tất cả các ô (chỉ số) có bit 1 trong bitboard.
    Hàm này cho phép lặp qua tất cả các quân cờ của một loại nào đó một cách hiệu quả.
    Cách hoạt động:
    - Vòng lặp while bb: chạy cho đến khi không còn bit 1 nào.
    - lsb_index(bb) tìm ô đầu tiên.
    - bb &= bb - 1 là một mẹo bitwise để xóa bit 1 nhỏ nhất, chuẩn bị cho vòng lặp tiếp theo.
    """
    while bb:
        sq = lsb_index(bb)
        yield sq
        bb &= bb - 1

def count_bits(bb: int) -> int:
    """
    Đếm số lượng bit 1 được bật trong một bitboard.
    Tương đương với việc đếm số quân cờ trên bàn cờ.
    Sử dụng hàm tích hợp sẵn của Python `bit_count()` cho hiệu suất tối ưu.
    """
    return bb.bit_count()

# =================================================================================
# CÁC HÀM TIỆN ÍCH CHUNG VỀ BÀN CỜ
# =================================================================================

def is_file_open(board: chess.Board, file_i: int) -> bool:
    """
    Kiểm tra xem một cột (file) có "mở" hay không.
    Một cột được coi là mở nếu không có bất kỳ Tốt (pawn) nào (cả trắng và đen) trên đó.
    Cột mở rất quan trọng cho Xe (Rook) và Hậu (Queen).
    """
    # Lấy bitboard của tất cả các Tốt
    all_pawns = int(board.pieces(chess.PAWN, chess.WHITE) | board.pieces(chess.PAWN, chess.BLACK))
    # Kiểm tra xem có Tốt nào trên cột đang xét không bằng cách dùng FILE_MASKS
    return (all_pawns & FILE_MASKS[file_i]) == 0

def is_file_semi_open(board: chess.Board, file_i: int, color: chess.Color) -> bool:
    """
    Kiểm tra xem một cột có "nửa mở" (semi-open) đối với một màu cờ hay không.
    Một cột là nửa mở nếu không có Tốt của phe mình nhưng có Tốt của đối phương.
    Cột nửa mở cũng rất có lợi cho Xe và Hậu.
    """
    my_pawns = int(board.pieces(chess.PAWN, color))
    opponent_pawns = int(board.pieces(chess.PAWN, not color))
    # Điều kiện: không có Tốt của mình VÀ có Tốt của đối phương trên cột đó.
    return (my_pawns & FILE_MASKS[file_i]) == 0 and (opponent_pawns & FILE_MASKS[file_i]) != 0

# =================================================================================
# TÍNH TOÁN GIAI ĐOẠN VÁN CỜ (PHASE)
# =================================================================================

def phase_score_calculator(current_phase_score: int, mg_score: int, eg_score: int) -> float:
    """
    Tính toán điểm số cuối cùng dựa trên giai đoạn của ván cờ (tapered evaluation).
    Ý tưởng là điểm số của một thế cờ sẽ thay đổi tùy thuộc vào việc nó đang ở
    trung cuộc (middlegame - MG) hay tàn cuộc (endgame - EG).
    Ví dụ: Vua an toàn rất quan trọng ở trung cuộc, nhưng Vua hoạt động mạnh lại quan trọng ở tàn cuộc.

    - current_phase_score: Tổng điểm giai đoạn của các quân cờ trên bàn. Càng nhiều quân mạnh, điểm càng cao.
    - mg_score: Điểm đánh giá thế cờ ở trung cuộc.
    - eg_score: Điểm đánh giá thế cờ ở tàn cuộc.
    - TOTAL_PHASE: Hằng số, là điểm giai đoạn tối đa khi tất cả các quân còn trên bàn.

    Công thức này nội suy tuyến tính giữa điểm MG và EG.
    Nếu phase gần TOTAL_PHASE (trung cuộc), kết quả sẽ gần với mg_score.
    Nếu phase gần 0 (tàn cuộc), kết quả sẽ gần với eg_score.
    """
    phase = min(current_phase_score, TOTAL_PHASE) # Đảm bảo phase không vượt quá giá trị tối đa
    return (mg_score * phase + eg_score * (TOTAL_PHASE - phase)) / TOTAL_PHASE

# =================================================================================
# ĐÁNH GIÁ CẤU TRÚC TỐT (PAWN EVALUATION)
# =================================================================================

def get_doubled_pawns_penalty(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm phạt cho Tốt chồng (doubled pawns).
    Tốt chồng là khi có hai hoặc nhiều Tốt cùng màu trên cùng một cột.
    Chúng thường yếu vì không thể bảo vệ lẫn nhau và làm cản trở sự phát triển của các quân khác.
    """
    my_pawns = int(board.pieces(chess.PAWN, color))
    doubled_pawn_count = 0
    # Duyệt qua từng cột (file)
    for file_i in range(8):
        # Đếm số Tốt trên cột hiện tại
        n = count_bits(my_pawns & FILE_MASKS[file_i])
        if n > 1:
            # Nếu có n Tốt, thì có n-1 Tốt bị chồng
            doubled_pawn_count += n - 1
    # Trả về điểm phạt cho trung cuộc (MG) và tàn cuộc (EG)
    return doubled_pawn_count * DOUBLE_PAWNS_PENALTY_MG, doubled_pawn_count * DOUBLE_PAWNS_PENALTY_EG

def get_isolated_pawns_penalty(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm phạt cho Tốt cô lập (isolated pawns).
    Tốt cô lập là Tốt không có Tốt đồng minh nào ở các cột liền kề.
    Chúng là điểm yếu vì không thể được bảo vệ bởi các Tốt khác.
    """
    mg, eg = 0, 0
    my_pawns = int(board.pieces(chess.PAWN, color))
    # Duyệt qua từng Tốt của mình
    for sq in bitboard_iter(my_pawns):
        file_i = chess.square_file(sq)
        adj_mask = ADJACENT_FILES_MASKS[file_i] # Mask cho các cột liền kề
        # Nếu không có Tốt đồng minh nào ở các cột liền kề
        if not (my_pawns & adj_mask):
            # Phạt nặng hơn nếu Tốt cô lập nằm trên cột nửa mở (dễ bị tấn công)
            if is_file_semi_open(board, file_i, color):
                mg += ISOLATED_PAWNS_SEMI_OPEN_MG
                eg += ISOLATED_PAWNS_SEMI_OPEN_EG
            else:
                mg += ISOLATED_PAWNS_PENALTY_MG
                eg += ISOLATED_PAWNS_PENALTY_EG
    return mg, eg

def get_connected_pawns_bonus(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm thưởng cho Tốt liên kết (connected pawns).
    Tốt liên kết là Tốt có Tốt đồng minh ở cột liền kề, có thể hỗ trợ lẫn nhau.
    Đây là một cấu trúc Tốt mạnh mẽ.
    """
    mg, eg = 0, 0
    my_pawns = int(board.pieces(chess.PAWN, color))
    # Duyệt qua từng Tốt
    for sq in bitboard_iter(my_pawns):
        file_i = chess.square_file(sq)
        adj_mask = ADJACENT_FILES_MASKS[file_i]
        # Nếu có Tốt đồng minh ở cột liền kề, cộng điểm thưởng
        if my_pawns & adj_mask:
            mg += CONNECTED_PAWN_BONUS_MG
            eg += CONNECTED_PAWN_BONUS_EG
    return mg, eg

def get_passed_pawn_bonus(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm thưởng cho Tốt thông (passed pawns).
    Tốt thông là Tốt không có Tốt đối phương nào cản đường nó trên cùng cột hoặc các cột liền kề.
    Tốt thông là một vũ khí cực kỳ nguy hiểm, đặc biệt là ở tàn cuộc.
    """
    mg, eg = 0, 0
    my_pawns = int(board.pieces(chess.PAWN, color))
    opponent_pawns = int(board.pieces(chess.PAWN, not color))
    # Chọn mask phù hợp dựa trên màu quân
    ITER_PAWNS_MASK = WHITE_PASSED_PAWN_MASKS if color == chess.WHITE else BLACK_PASSED_PAWN_MASKS
    mask_table = [int(m) for m in ITER_PAWNS_MASK]
    # Duyệt qua từng Tốt
    for sq in bitboard_iter(my_pawns):
        # Kiểm tra xem có Tốt đối phương nào trong vùng mask không
        if not (opponent_pawns & mask_table[sq]):
            # Tốt này là Tốt thông
            # Tính rank tương đối (hàng 1-7) để xác định mức độ nguy hiểm
            rank = chess.square_rank(sq) if color == chess.WHITE else 7 - chess.square_rank(sq)
            # Thưởng nhiều hơn nếu Tốt thông được bảo vệ
            if board.is_attacked_by(color, sq):
                mg += PROTECTED_PASSED_PAWN_BONUS_MG[rank]
                eg += PROTECTED_PASSED_PAWN_BONUS_EG[rank]
            else:
                mg += UNPROTECTED_PASSED_PAWN_BONUS_MG[rank]
                eg += UNPROTECTED_PASSED_PAWN_BONUS_EG[rank]
    return mg, eg

def get_backward_pawn_penalty(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm phạt cho Tốt lạc hậu (backward pawns).
    Tốt lạc hậu là Tốt bị tụt lại phía sau so với các Tốt đồng minh ở cột liền kề
    và không thể tiến lên mà không bị Tốt đối phương bắt. Ô phía trước nó thường là một điểm yếu.
    """
    mg, eg = 0, 0
    my_pawns = int(board.pieces(chess.PAWN, color))

    for sq in bitboard_iter(my_pawns):
        file_i = chess.square_file(sq)
        rank_i = chess.square_rank(sq)
        can_be_supported = False

        # Kiểm tra xem có Tốt đồng minh nào ở phía sau trên các cột liền kề có thể hỗ trợ không
        # Tạo mask cho các ô phía sau Tốt hiện tại
        if color == chess.WHITE:
            behind_mask = sum(chess.BB_RANKS[r] for r in range(0, rank_i))
        else:
            behind_mask = sum(chess.BB_RANKS[r] for r in range(rank_i + 1, 8))

        # Kiểm tra cột bên trái
        if file_i > 0:
            left_file_mask = FILE_MASKS[file_i - 1]
            if my_pawns & left_file_mask & behind_mask:
                can_be_supported = True

        # Kiểm tra cột bên phải
        if file_i < 7 and not can_be_supported:
            right_file_mask = FILE_MASKS[file_i + 1]
            if my_pawns & right_file_mask & behind_mask:
                can_be_supported = True

        # Nếu không có Tốt nào hỗ trợ và ô phía trước bị đối phương tấn công -> Tốt lạc hậu
        if not can_be_supported:
            ahead_sq = sq + 8 if color == chess.WHITE else sq - 8
            if 0 <= ahead_sq <= 63 and board.is_attacked_by(not color, ahead_sq):
                mg += BACKWARD_PAWN_PENALTY_MG
                eg += BACKWARD_PAWN_PENALTY_EG

    return mg, eg

def get_pawn_structure(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Hàm tổng hợp, gọi tất cả các hàm đánh giá cấu trúc Tốt và trả về tổng điểm.
    """
    doubled = get_doubled_pawns_penalty(board, color)
    isolated = get_isolated_pawns_penalty(board, color)
    connected = get_connected_pawns_bonus(board, color)
    passed = get_passed_pawn_bonus(board, color)
    backward = get_backward_pawn_penalty(board, color)
    mg = sum(x[0] for x in [doubled, isolated, connected, passed, backward])
    eg = sum(x[1] for x in [doubled, isolated, connected, passed, backward])
    return mg, eg

# =================================================================================
# ĐÁNH GIÁ QUÂN NHẸ (MINOR PIECES), XE (ROOK)
# =================================================================================

def get_rook_bonus(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm thưởng cho Xe.
    - Xe trên cột nửa mở/mở: Rất mạnh vì có tầm hoạt động rộng.
    - Xe ở hàng 7 (hoặc hàng 2 của đối phương): Cực kỳ nguy hiểm, có thể tấn công Tốt và Vua đối phương.
    """
    mg, eg = 0, 0
    rooks = int(board.pieces(chess.ROOK, color))
    for sq in bitboard_iter(rooks):
        file_i = chess.square_file(sq)
        rank_i = chess.square_rank(sq)
        # Thưởng cho Xe trên cột nửa mở
        if is_file_semi_open(board, file_i, color):
            mg += ROOK_SEMI_OPEN_FILES_BONUS_MG
            eg += ROOK_SEMI_OPEN_FILES_BONUS_EG
        # Thưởng nhiều hơn cho Xe trên cột mở
        if is_file_open(board, file_i):
            mg += ROOK_OPEN_FILES_BONUS_MG
            eg += ROOK_OPEN_FILES_BONUS_EG
        # Thưởng cho Xe ở hàng 7 (đối với Trắng) hoặc hàng 2 (đối với Đen)
        if (color == chess.WHITE and rank_i == 6) or (color == chess.BLACK and rank_i == 1):
            mg += ROOK_SEVENTH_RANK_BONUS_MG
            eg += ROOK_SEVENTH_RANK_BONUS_EG
    return mg, eg

def get_double_bishop_bonus(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm thưởng cho cặp Tượng (bishop pair).
    Sở hữu hai Tượng được coi là một lợi thế chiến lược, đặc biệt trong các thế cờ mở,
    vì chúng có thể kiểm soát các ô cả màu trắng và đen.
    """
    bishops = int(board.pieces(chess.BISHOP, color))
    if count_bits(bishops) == 2:
        return DOUBLE_BISHOP_BONUS_MG, DOUBLE_BISHOP_BONUS_EG
    return 0, 0

def get_knight_outpost_bonus(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm thưởng cho Mã ở tiền đồn (knight outpost).
    Một tiền đồn cho Mã là một ô cờ thỏa mãn 3 điều kiện:
    1. Nằm sâu trong lãnh thổ đối phương (hàng 4-6 cho Trắng, 3-1 cho Đen).
    2. Được bảo vệ bởi một Tốt của mình.
    3. Không thể bị Tốt của đối phương tấn công.
    Mã ở tiền đồn rất mạnh vì nó ổn định và kiểm soát các ô quan trọng.
    """
    mg, eg = 0, 0
    knights = int(board.pieces(chess.KNIGHT, color))

    for sq in bitboard_iter(knights):
        rank_i = chess.square_rank(sq)
        file_i = chess.square_file(sq)

        # 1. Kiểm tra có phải ô cờ nâng cao không
        is_advanced = (color == chess.WHITE and rank_i >= 3) or \
                      (color == chess.BLACK and rank_i <= 4)
        if not is_advanced:
            continue

        # 2. Kiểm tra có được Tốt hỗ trợ không
        supported = False
        support_rank = rank_i - 1 if color == chess.WHITE else rank_i + 1
        if 0 <= support_rank < 8:
            if file_i > 0 and board.piece_at(chess.square(file_i - 1, support_rank)) == chess.Piece(chess.PAWN, color):
                supported = True
            if file_i < 7 and board.piece_at(chess.square(file_i + 1, support_rank)) == chess.Piece(chess.PAWN, color):
                supported = True
        if not supported:
            continue

        # 3. Kiểm tra không bị Tốt đối phương tấn công
        attacked_by_enemy_pawns = False
        attack_rank = rank_i + 1 if color == chess.WHITE else rank_i - 1
        if 0 <= attack_rank < 8:
            if file_i > 0 and board.piece_at(chess.square(file_i - 1, attack_rank)) == chess.Piece(chess.PAWN, not color):
                attacked_by_enemy_pawns = True
            if file_i < 7 and board.piece_at(chess.square(file_i + 1, attack_rank)) == chess.Piece(chess.PAWN, not color):
                attacked_by_enemy_pawns = True

        if supported and not attacked_by_enemy_pawns:
            mg += KNIGHT_OUTPOST_BONUS_MG
            eg += KNIGHT_OUTPOST_BONUS_EG

    return mg, eg

def get_sub_piece_bonus(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Hàm tổng hợp, gọi các hàm đánh giá cho Xe, Tượng, Mã.
    """
    rook = get_rook_bonus(board, color)
    bishop = get_double_bishop_bonus(board, color)
    knight = get_knight_outpost_bonus(board, color)
    return rook[0] + bishop[0] + knight[0], rook[1] + bishop[1] + knight[1]

# =================================================================================
# ĐÁNH GIÁ AN TOÀN VÀ HOẠT ĐỘNG CỦA VUA (KING SAFETY / ACTIVITY)
# =================================================================================

def get_king_zone(board: chess.Board, color: bool) -> set[int]:
    """
    Xác định "vùng an toàn" của Vua, bao gồm ô Vua đang đứng và 8 ô xung quanh.
    Vùng này được sử dụng để đánh giá các mối đe dọa trực tiếp đến Vua.
    """
    king_sq = board.king(color)
    if king_sq is None:
        return set()

    # Tạo bitboard cho Vua và các ô xung quanh
    zone_bb = chess.BB_KING_ATTACKS[king_sq] | (1 << king_sq)
    zone_squares = set(bitboard_iter(zone_bb))
    return zone_squares

def pawn_shield_penalty(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm phạt nếu Vua thiếu lá chắn Tốt.
    Sau khi nhập thành, Vua cần được bảo vệ bởi 3 Tốt phía trước.
    Nếu một trong các Tốt này bị mất hoặc di chuyển, Vua sẽ trở nên yếu hơn.
    Hàm này chỉ áp dụng khi Vua đã nhập thành cánh Vua hoặc cánh Hậu.
    """
    mg, eg = 0, 0
    king_sq = board.king(color)
    if king_sq is None:
        return 0, 0
    king_file = chess.square_file(king_sq)

    # Xác định các cột của lá chắn Tốt dựa trên vị trí Vua (cánh Vua hoặc cánh Hậu)
    if king_file < 3: # Cánh Hậu
        shield_files = [0, 1, 2]
    elif king_file > 4: # Cánh Vua
        shield_files = [5, 6, 7]
    else: # Vua ở trung tâm, không áp dụng
        return 0, 0

    # Hàng của lá chắn Tốt
    pawn_rank = 1 if color == chess.WHITE else 6
    # Kiểm tra từng cột trong lá chắn
    for f in shield_files:
        sq = chess.square(f, pawn_rank)
        # Nếu không có Tốt của mình ở vị trí lá chắn, phạt điểm
        if board.piece_at(sq) != chess.Piece(chess.PAWN, color):
            mg += MISSING_PAWN_SHIELD_PENALTY_MG
            eg += MISSING_PAWN_SHIELD_PENALTY_EG
    return mg, eg

def king_attack_zone_penalty(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Tính điểm phạt dựa trên số lượng và loại quân đối phương đang tấn công vùng an toàn của Vua.
    Càng nhiều quân mạnh tấn công, Vua càng gặp nguy hiểm.
    """
    mg, eg = 0, 0
    king_sq = board.king(color)
    if king_sq is None:
        return 0, 0
    zone_squares = get_king_zone(board, color)
    zone_bb = sum(1 << sq for sq in zone_squares)
    opponent = not color
    attackers, value = 0, 0

    # Duyệt qua các loại quân tấn công của đối phương
    for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        pieces = int(board.pieces(pt, opponent))
        for sq in bitboard_iter(pieces):
            # Lấy các ô mà quân này tấn công và giao với vùng an toàn của Vua
            attacks = int(board.attacks(sq) & zone_bb)
            if attacks:
                attackers += 1 # Tăng số lượng quân tấn công
                # Cộng điểm dựa trên giá trị của quân tấn công và số ô nó kiểm soát trong vùng
                value += count_bits(attacks) * KING_ATTACK_ZONE_WEIGHTS[pt]

    if attackers == 0:
        return 0, 0

    # Nhân với hệ số dựa trên tổng số quân tấn công.
    # Nhiều quân tấn công phối hợp sẽ nguy hiểm hơn tổng giá trị của chúng.
    multiplier = ATTACK_WEIGHT_MULTIPLIER[min(attackers, len(ATTACK_WEIGHT_MULTIPLIER)-1)]
    # Chỉ phạt ở trung cuộc, vì ở tàn cuộc Vua cần hoạt động
    return int(value * multiplier / 100), 0

def king_activity_bonus(board: chess.Board, color: chess.Color):
    """
    Tính điểm thưởng cho Vua hoạt động tích cực ở tàn cuộc.
    Ở tàn cuộc, Vua trở thành một quân cờ tấn công và phòng thủ quan trọng.
    Vua ở gần trung tâm sẽ mạnh hơn.
    """
    mg, eg = 0, 0
    king_sq = board.king(color)
    if king_sq is None:
        return 0, 0
    # Chỉ áp dụng ở giai đoạn cuối ván cờ
    if board.fullmove_number > 30:
        # Tính khoảng cách Manhattan từ Vua đến trung tâm (ô giữa D4, E4, D5, E5)
        center_distance = abs(3.5 - chess.square_file(king_sq)) + abs(3.5 - chess.square_rank(king_sq))
        # Càng gần trung tâm, điểm thưởng càng cao
        bonus = int((7 - center_distance) * KING_ACTIVITY_BONUS_EG)
        eg += bonus
    return mg, eg

def king_attack_bonus(board: chess.Board, color: chess.Color):
    """
    Tính điểm thưởng khi các quân của mình đang trực tiếp tấn công Vua đối phương.
    """
    mg, eg = 0, 0
    opponent_king = board.king(not color)
    if opponent_king is None:
        return 0, 0
    attackers = 0
    # Đếm số quân của mình đang chiếu Vua đối phương (nếu không có quân cản)
    for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
        pieces = int(board.pieces(pt, color))
        for sq in bitboard_iter(pieces):
            if opponent_king in board.attacks(sq):
                attackers += 1
    mg += 50 * attackers
    eg += 50 * attackers
    return mg, eg

def king_additional(board: chess.Board, color: chess.Color) -> tuple[int, int]:
    """
    Các đánh giá bổ sung liên quan đến Vua.
    - Phạt Vua ở trung tâm trong khai cuộc/trung cuộc.
    - Thưởng khi đã nhập thành.
    - Phạt khi di chuyển Vua mà mất quyền nhập thành.
    - Phạt Vua bị "kẹt" ở các vị trí xấu.
    """
    mg, eg = 0, 0
    king_sq = board.king(color)
    if king_sq is None:
        return 0, 0

    file = chess.square_file(king_sq)
    rank = chess.square_rank(king_sq)

    # Phạt Vua ở trung tâm trong khai cuộc và trung cuộc
    if rank in [3, 4] and file in [3, 4]:
        mg += MIDDLE_KING_PENALTY_MG
        eg += MIDDLE_KING_PENALTY_EG

    # Thưởng nếu đã nhập thành (vị trí an toàn)
    if king_sq in [chess.G1, chess.C1, chess.G8, chess.C8]:
        mg += CASTLING_BONUS_MG
        eg += CASTLING_BONUS_EG

    # Phạt nếu Vua di chuyển khỏi vị trí ban đầu mà vẫn còn quyền nhập thành
    starting_sq = chess.E1 if color == chess.WHITE else chess.E8
    if king_sq != starting_sq and (board.has_kingside_castling_rights(color) or board.has_queenside_castling_rights(color)):
        mg += MOVE_WITHOUT_CASTLING_PENALTY_MG

    # Phạt Vua "kẹt" ở các ô gần góc mà không phải do nhập thành
    if (color == chess.BLACK and king_sq in [chess.F8, chess.F7, chess.D8, chess.D7]) or \
       (color == chess.WHITE and king_sq in [chess.F1, chess.F2, chess.D1, chess.D2]):
        mg += TRAPPED_KING_PENALTY_MG
        eg += TRAPPED_KING_PENALTY_EG

    return mg, eg

def get_king_safety(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Hàm tổng hợp, gọi tất cả các hàm đánh giá Vua.
    """
    shield = pawn_shield_penalty(board, color)
    attack = king_attack_zone_penalty(board, color)
    activity = king_activity_bonus(board, color)
    attack_bonus = king_attack_bonus(board, color)
    additional = king_additional(board, color)
    return shield[0] + attack[0] + activity[0] + attack_bonus[0] + additional[0], \
           shield[1] + attack[1] + activity[1] + attack_bonus[1] + additional[1]

# =================================================================================
# ĐÁNH GIÁ TẤN CÔNG VÀ KIỂM SOÁT (ATTACKS & CONTROL)
# =================================================================================

def evaluate_attacks(board: chess.Board, color: chess.Color)-> tuple[int, int]:
    """
    Đánh giá các mối đe dọa và sự kiểm soát không gian.
    - Thưởng điểm khi tấn công quân đối phương (càng giá trị càng tốt).
    - Thưởng điểm khi tấn công Vua đối phương.
    - Thưởng điểm khi kiểm soát các ô trung tâm.
    """
    mg, eg = 0, 0
    opp_color = not color
    attacked_piece_types = set() # Dùng để tránh đếm một cuộc tấn công nhiều lần

    # Tấn công các quân đối phương
    for pt in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        pieces = int(board.pieces(pt, color))
        for sq in bitboard_iter(pieces):
            attacks = board.attacks(sq)
            for target_sq in attacks:
                target_piece = board.piece_at(target_sq)
                if target_piece and target_piece.color == opp_color:
                    # Thêm vào set để đảm bảo mỗi quân địch chỉ bị tính điểm tấn công một lần
                    key = (pt, target_piece.piece_type, target_sq)
                    if key not in attacked_piece_types:
                        attacked_piece_types.add(key)
                        mg += ATTACK_ON_PIECE_MG[target_piece.piece_type]
                        eg += ATTACK_ON_PIECE_EG[target_piece.piece_type]

    # Tấn công Vua đối phương
    opponent_king_sq = board.king(opp_color)
    if opponent_king_sq is not None:
        for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            pieces = int(board.pieces(pt, color))
            for sq in bitboard_iter(pieces):
                if opponent_king_sq in board.attacks(sq):
                    mg += ATTACK_ON_KING_MG[pt]
                    eg += ATTACK_ON_KING_EG[pt]

    # Kiểm soát trung tâm
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    for sq in center_squares:
        piece = board.piece_at(sq)
        if piece and piece.color == color:
            mg += CENTER_CONTROL_MG
            eg += CENTER_CONTROL_EG

    return mg, eg

# =================================================================================
# HÀM ĐÁNH GIÁ CHÍNH (MAIN EVALUATION)
# =================================================================================
def evaluate_board(board: chess.Board) -> float:
    """
    Hàm đánh giá tổng thể, kết hợp tất cả các yếu tố để đưa ra một điểm số duy nhất cho thế cờ.
    Điểm dương là lợi thế cho Trắng, điểm âm là lợi thế cho Đen.
    """
    # 1. Xử lý các trường hợp kết thúc ván cờ (terminal nodes)
    if board.is_checkmate():
        # Nếu bị chiếu hết, trả về điểm số rất thấp (thua cuộc)
        return -MATE_SCORE
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_fifty_moves() or board.is_seventyfive_moves():
        # Các trường hợp hòa cờ
        return 0.0

    # 2. Tính toán giai đoạn ván cờ (Phase)
    total_counts = {pt: count_bits(int(board.pieces(pt, chess.WHITE) | board.pieces(pt, chess.BLACK)))
                    for pt in chess.PIECE_TYPES}
    current_phase_score = sum(total_counts.get(pt, 0) * PHASE_VALUES.get(pt, 0) for pt in total_counts)

    mg_total, eg_total = 0, 0

    # 3. Tính toán các thành phần điểm cho cả hai bên
    for color in [chess.WHITE, chess.BLACK]:
        pawn_mg, pawn_eg = get_pawn_structure(board, color)
        sub_mg, sub_eg = get_sub_piece_bonus(board, color)
        king_mg, king_eg = get_king_safety(board, color)
        attack_mg, attack_eg = evaluate_attacks(board, color)

        # Nếu là quân Đen, điểm sẽ là âm
        multiplier = 1 if color == chess.WHITE else -1
        mg_total += (pawn_mg + sub_mg + king_mg + attack_mg) * multiplier
        eg_total += (pawn_eg + sub_eg + king_eg + attack_eg) * multiplier

    # 4. Cộng điểm vật chất (material) và điểm vị trí (Piece-Square Tables - PST)
    for pt in chess.PIECE_TYPES:
        # Giá trị cơ bản của quân cờ
        score_mg = PIECE_VALUES_MG[pt]
        score_eg = PIECE_VALUES_EG[pt]

        # Bảng điểm vị trí (PST) cho trung cuộc và tàn cuộc
        pst_mg = PST[pt][0]
        pst_eg = PST[pt][1]

        # Cộng điểm cho quân Trắng
        my_pieces = int(board.pieces(pt, chess.WHITE))
        for sq in bitboard_iter(my_pieces):
            mg_total += score_mg + pst_mg[sq]
            eg_total += score_eg + pst_eg[sq]

        # Trừ điểm cho quân Đen
        opponent_pieces = int(board.pieces(pt, chess.BLACK))
        for sq in bitboard_iter(opponent_pieces):
            # Dùng square_mirror để lật ngược bàn cờ cho quân Đen
            mg_total -= (score_mg + pst_mg[chess.square_mirror(sq)])
            eg_total -= (score_eg + pst_eg[chess.square_mirror(sq)])

    # 5. Tính điểm cuối cùng bằng cách nội suy giữa điểm MG và EG dựa trên phase
    final_score = phase_score_calculator(current_phase_score, mg_total, eg_total)

    # 6. Trả về điểm số theo góc nhìn của người chơi hiện tại (Point of View)
    # Đây là quy ước chuẩn cho các thuật toán tìm kiếm như Negamax.
    return final_score if board.turn == chess.WHITE else -final_score