import chess

PIECE_VALUES_MG = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 90000
}

MATE_SCORE = 10000000

PIECE_VALUES_EG = {
    chess.PAWN: 130,
    chess.KNIGHT: 300,
    chess.BISHOP: 330,
    chess.ROOK: 550,
    chess.QUEEN: 925,
    chess.KING: 1000000
}

PAWN_PST_MG = [
      0,   0,   0,   0,   0,   0,  0,   0,
     98, 134,  61,  95,  68, 126, 34, -11,
     -6,   7,  26,  31,  65,  56, 25, -20,
    -14,  13,   6,  21,  23,  12, 17, -23,
    -27,  -2,  -5,  12,  17,   6, 10, -25,
    -26,  -4,  -4, -10,   3,   3, 33, -12,
    -35,  -1, -20, -23, -15,  24, 38, -22,
      0,   0,   0,   0,   0,   0,  0,   0
]

PAWN_PST_EG = [
      0,   0,   0,   0,   0,   0,   0,   0,
    178, 173, 158, 134, 147, 132, 165, 187,
     94, 100,  85,  67,  56,  53,  82,  84,
     32,  24,  13,   5,  -2,   4,  17,  17,
     13,   9,  -3,  -7,  -7,  -8,   3,  -1,
      4,   7,  -6,   1,   0,  -5,  -1,  -8,
     13,   8,   8,  10,  13,   0,   2,  -7,
      0,   0,   0,   0,   0,   0,   0,   0
]

KNIGHT_PST_MG = [
    -167, -89, -34, -49,  61, -97, -15, -107,
     -73, -41,  72,  36,  23,  62,   7,  -17,
     -47,  60,  37,  65,  84, 129,  73,   44,
      -9,  17,  19,  53,  37,  69,  18,   22,
     -13,   4,  16,  13,  28,  19,  21,   -8,
     -23,  -9,  12,  10,  19,  17,  25,  -16,
     -29, -53, -12,  -3,  -1,  18, -14,  -19,
    -105, -21, -58, -33, -17, -28, -19,  -23
]

KNIGHT_PST_EG = [
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25,  -8, -25,  -2,  -9, -25, -24, -52,
    -24, -20,  10,   9,  -1,  -9, -19, -41,
    -17,   3,  22,  22,  22,  11,   8, -18,
    -18,  -6,  16,  25,  16,  17,   4, -18,
    -23,  -3,  -1,  15,  10,  -3, -20, -22,
    -42, -20, -10,  -5,  -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64
]

BISHOP_PST_MG = [
    -29,   4, -82, -37, -25, -42,   7,  -8,
    -26,  16, -18, -13,  30,  59,  18, -47,
    -16,  37,  43,  40,  35,  50,  37,  -2,
     -4,   5,  19,  50,  37,  37,   7,  -2,
     -6,  13,  13,  26,  34,  12,  10,   4,
      0,  15,  15,  15,  14,  27,  18,  10,
      4,  15,  16,   0,   7,  21,  33,   1,
    -33,  -3, -14, -21, -13, -12, -39, -21
]

BISHOP_PST_EG = [
    -14, -21, -11,  -8, -7,  -9, -17, -24,
     -8,  -4,   7, -12, -3, -13,  -4, -14,
      2,  -8,   0,  -1, -2,   6,   0,   4,
     -3,   9,  12,   9, 14,  10,   3,   2,
     -6,   3,  13,  19,  7,  10,  -3,  -9,
    -12,  -3,   8,  10, 13,   3,  -7, -15,
    -14, -18,  -7,  -1,  4,  -9, -15, -27,
    -23,  -9, -23,  -5, -9, -16,  -5, -17
]

ROOK_PST_MG = [
    32,  42,  32,  51, 63,  9,  31,  43,
     27,  32,  58,  62, 80, 67,  26,  44,
     -5,  19,  26,  36, 17, 45,  61,  16,
    -24, -11,   7,  26, 24, 35,  -8, -20,
    -36, -26, -12,  -1,  9, -7,   6, -23,
    -45, -25, -16, -17,  3,  0,  -5, -33,
    -44, -16, -20,  -9, -1, 11,  -6, -71,
    -19, -13,   1,  17, 16,  7, -37, -26
]

ROOK_PST_EG = [
    13, 10, 18, 15, 12,  12,   8,   5,
    11, 13, 13, 11, -3,   3,   8,   3,
     7,  7,  7,  5,  4,  -3,  -5,  -3,
     4,  3, 13,  1,  2,   1,  -1,   2,
     3,  5,  8,  4, -5,  -6,  -8, -11,
    -4,  0, -5, -1, -7, -12,  -8, -16,
    -6, -6,  0,  2, -9,  -9, -11,  -3,
    -9,  2,  3, -1, -5, -13,   4, -20
]

QUEEN_PST_MG = [
    -28,   0,  29,  12,  59,  44,  43,  45,
    -24, -39,  -5,   1, -16,  57,  28,  54,
    -13, -17,   7,   8,  29,  56,  47,  57,
    -27, -27, -16, -16,  -1,  17,  -2,   1,
     -9, -26,  -9, -10,  -2,  -4,   3,  -3,
    -14,   2, -11,  -2,  -5,   2,  14,   5,
    -35,  -8,  11,   2,   8,  15,  -3,   1,
     -1, -18,  -9,  10, -15, -25, -31, -50
]

QUEEN_PST_EG = [
    -9,  22,  22,  27,  27,  19,  10,  20,
    -17,  20,  32,  41,  58,  25,  30,   0,
    -20,   6,   9,  49,  47,  35,  19,   9,
      3,  22,  24,  45,  57,  40,  57,  36,
    -18,  28,  19,  47,  31,  34,  39,  23,
    -16, -27,  15,   6,   9,  17,  10,   5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43,  -5, -32, -20, -41
]

KING_PST_MG = [
    -65,  23,  16, -25, -56, -34,   2,  13, ##-65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20, -30, -30,  -4, -38, -29, ## 29,  -1, -20,  -7,  -8,  -4, -38, -29
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
      1,   7,  -8, -64, -43, -16,   9,   8,
    -15,  36,  12, -54,   8, -28,  24,  14
]

KING_PST_EG = [
    -74, -35, -18, -18, -11,  15,   4, -17,
    -12,  17,  14,  17,  17,  38,  23,  11,
     10,  17,  23,  15,  20,  45,  44,  13,
     -8,  22,  24,  27,  26,  33,  26,   3,
    -18,  -4,  21,  24,  27,  23,   9, -11,
    -19,  -3,  11,  21,  23,  16,   7,  -9,
    -27, -11,   4,  13,  14,   4,  -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43
]

MG_TABLE = {
    1: PAWN_PST_MG,
    2: KNIGHT_PST_MG,
    3: BISHOP_PST_MG,
    4: ROOK_PST_MG,
    5: QUEEN_PST_MG,
    6: KING_PST_MG
}

EG_TABLE = {
    1: PAWN_PST_EG,
    2: KNIGHT_PST_EG,
    3: BISHOP_PST_EG,
    4: ROOK_PST_EG,
    5: QUEEN_PST_EG,
    6: KING_PST_EG
}

PAWNPHASE = 0
KNIGHTPHASE = 1
BISHOPPHASE = 1
ROOKPHASE = 2
QUEENPHASE = 4

PHASE_VALUES = {
    chess.PAWN: PAWNPHASE,
    chess.KNIGHT: KNIGHTPHASE,
    chess.BISHOP: BISHOPPHASE,
    chess.ROOK: ROOKPHASE,
    chess.QUEEN: QUEENPHASE,
}

TOTAL_PHASE = PAWNPHASE*16 +KNIGHTPHASE*4 +BISHOPPHASE*4 +ROOKPHASE*4 +QUEENPHASE*2

PST = {
    chess.PAWN: (PAWN_PST_MG, PAWN_PST_EG),
    chess.KNIGHT: (KNIGHT_PST_MG, KNIGHT_PST_EG),
    chess.BISHOP: (BISHOP_PST_MG, BISHOP_PST_EG),
    chess.ROOK: (ROOK_PST_MG, ROOK_PST_EG),
    chess.QUEEN: (QUEEN_PST_MG, QUEEN_PST_EG),
    chess.KING: (KING_PST_MG, KING_PST_EG)
}

FILE_MASKS = [
    chess.BB_FILE_A, chess.BB_FILE_B, chess.BB_FILE_C, chess.BB_FILE_D,
    chess.BB_FILE_E, chess.BB_FILE_F, chess.BB_FILE_G, chess.BB_FILE_H
]

ADJACENT_FILES_MASKS = [
    chess.BB_FILE_B,
    chess.BB_FILE_A | chess.BB_FILE_C,
    chess.BB_FILE_B | chess.BB_FILE_D,
    chess.BB_FILE_C | chess.BB_FILE_E,
    chess.BB_FILE_D | chess.BB_FILE_F,
    chess.BB_FILE_E | chess.BB_FILE_G,
    chess.BB_FILE_F | chess.BB_FILE_H,
    chess.BB_FILE_G
]

PROTECTED_PASSED_PAWN_BONUS_MG = [0, 20, 35, 55, 90, 130, 180, 0]
PROTECTED_PASSED_PAWN_BONUS_EG = [0, 30, 50, 80, 120, 180, 250, 0]
UNPROTECTED_PASSED_PAWN_BONUS_MG = [0, 5, 10, 15, 25, 40, 60, 0]
UNPROTECTED_PASSED_PAWN_BONUS_EG = [0, 10, 20, 30, 50, 75, 100, 0]

ISOLATED_PAWNS_SEMI_OPEN_MG = -25
ISOLATED_PAWNS_SEMI_OPEN_EG = -35

ISOLATED_PAWNS_PENALTY_MG = -10
ISOLATED_PAWNS_PENALTY_EG = -20

DOUBLE_PAWNS_PENALTY_MG = -20
DOUBLE_PAWNS_PENALTY_EG = -35

BACKWARD_PAWN_PENALTY_MG = -8
BACKWARD_PAWN_PENALTY_EG = -20

# build passed pawn mask
WHITE_PASSED_PAWN_MASKS = [chess.SquareSet() for _ in range(64)]
BLACK_PASSED_PAWN_MASKS = [chess.SquareSet() for _ in range(64)]

for square in chess.SQUARES:
    file_index = chess.square_file(square)
    rank_index = chess.square_rank(square)

    files_mask = chess.SquareSet(FILE_MASKS[file_index])
    if file_index > 0:
        files_mask |= FILE_MASKS[file_index - 1]
    if file_index < 7:
        files_mask |= FILE_MASKS[file_index + 1]

    ranks_in_front = chess.SquareSet()
    for r in range(rank_index + 1, 8):
        ranks_in_front |= chess.BB_RANKS[r]
    WHITE_PASSED_PAWN_MASKS[square] = files_mask & ranks_in_front

    ranks_in_front = chess.SquareSet()
    for r in range(rank_index - 1, -1, -1):
        ranks_in_front |= chess.BB_RANKS[r]
    BLACK_PASSED_PAWN_MASKS[square] = files_mask & ranks_in_front

ROOK_OPEN_FILES_BONUS_MG = 15
ROOK_OPEN_FILES_BONUS_EG = 20

ROOK_SEMI_OPEN_FILES_BONUS_MG = 15
ROOK_SEMI_OPEN_FILES_BONUS_EG = 15

DOUBLE_BISHOP_BONUS_MG = 40
DOUBLE_BISHOP_BONUS_EG = 50

MISSING_PAWN_SHIELD_PENALTY_MG = -18
MISSING_PAWN_SHIELD_PENALTY_EG = 0

ADVANCED_PAWN_SHIELD_PENALTY_MG = -9
ADVANCED_PAWN_SHIELD_PENALTY_EG = 0

KING_ATTACK_ZONE_WEIGHTS = {
    chess.KNIGHT: 20,
    chess.BISHOP: 20,
    chess.ROOK: 40,
    chess.QUEEN: 80
}

ATTACK_WEIGHT_MULTIPLIER = [
    0,  # 0 attacker
    0,  # 1 attacker
    50, # 2 attackers
    75, # 3
    88, # 4
    94, # 5
    97, # 6
    99  # 7+
]

MVV_LVA_SCORES = [
    [0, 0  , 0  , 0  , 0  , 0  , 0  ],
    [0, 105, 104, 103, 102, 101, 100], # Tốt ăn
    [0, 205, 204, 203, 202, 201, 200], # Mã ăn
    [0, 305, 304, 303, 302, 301, 300], # Tượng ăn
    [0, 405, 404, 403, 402, 401, 400], # Xe ăn
    [0, 505, 504, 503, 502, 501, 500], # Hậu ăn
    [0, 0  , 0  , 0  , 0  , 0  , 0  ] # Vua ăn (ít khi)
]


# Pawn structure
CONNECTED_PAWN_BONUS_MG = 5
CONNECTED_PAWN_BONUS_EG = 3

# Rook
ROOK_SEVENTH_RANK_BONUS_MG = 20
ROOK_SEVENTH_RANK_BONUS_EG = 25

# Knight
KNIGHT_OUTPOST_BONUS_MG = 15
KNIGHT_OUTPOST_BONUS_EG = 15
#
# # King
# KING_ACTIVITY_BONUS_EG = 10

# # Pawn structure
# BLOCKED_PASSED_PAWN_PENALTY_MG = 10
# BLOCKED_PASSED_PAWN_PENALTY_EG = 5
# PAWN_CHAIN_BONUS_MG = 3
# PAWN_CHAIN_BONUS_EG = 2
# PAWN_MAJORITY_BONUS_MG = 5
# PAWN_MAJORITY_BONUS_EG = 3

# # Piece mobility
# KNIGHT_MOBILITY_BONUS_MG = 2
# BISHOP_MOBILITY_BONUS_EG = 2
# ROOK_OPEN_SEVENTH_BONUS_MG = 15
# QUEEN_CONTROL_CENTER_BONUS_MG = 10
# QUEEN_CONTROL_CENTER_BONUS_EG = 8
#
# # King safety
# CENTER_KING_PENALTY_MG = 10
# CENTER_KING_BONUS_EG = 15
# PIN_PENALTY_MG = 3
# FORK_PENALTY_MG = 5

# Endgame
PASSED_PAWN_PROMOTION_BONUS_EG = 20
KING_ACTIVITY_BONUS_EG = 10


# Tấn công các quân đối phương (piece values khi tấn công)
ATTACK_ON_PIECE_MG = {
    chess.PAWN: 10,
    chess.KNIGHT: 30,
    chess.BISHOP: 30,
    chess.ROOK: 50,
    chess.QUEEN: 90,
    chess.KING: 0,  # Không tính trực tiếp
}

ATTACK_ON_PIECE_EG = {
    chess.PAWN: 10,
    chess.KNIGHT: 30,
    chess.BISHOP: 30,
    chess.ROOK: 50,
    chess.QUEEN: 90,
    chess.KING: 0,
}

# Tấn công vua đối phương
ATTACK_ON_KING_MG = {
    chess.QUEEN: 50,
    chess.ROOK: 30,
    chess.BISHOP: 20,
    chess.KNIGHT: 20,
}

ATTACK_ON_KING_EG = {
    chess.QUEEN: 70,
    chess.ROOK: 50,
    chess.BISHOP: 30,
    chess.KNIGHT: 30,
}

# Kiểm soát trung tâm (D4,D5,E4,E5)
CENTER_CONTROL_MG = 15
CENTER_CONTROL_EG = 10

CASTLING_BONUS_MG = 40
CASTLING_BONUS_EG = 10

MIDDLE_KING_PENALTY_MG = -40
MIDDLE_KING_PENALTY_EG = -5

MOVE_WITHOUT_CASTLING_PENALTY_MG = -30
MOVE_WITHOUT_CASTLING_PENALTY_EG = -5

TRAPPED_KING_PENALTY_MG = -10
TRAPPED_KING_PENALTY_EG = -10