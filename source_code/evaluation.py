"""
Mô-đun hàm đánh giá trạng thái bàn cờ.

Dùng khi thuật toán Minimax/Alpha-Beta đạt giới hạn độ sâu
mà trò chơi chưa kết thúc, cần ước lượng bên nào đang có lợi thế.

Cách tiếp cận: duyệt tất cả "cửa sổ" gồm WIN_LENGTH ô liên tiếp
theo 4 hướng, chấm điểm dựa trên số quân mỗi bên trong cửa sổ.
"""

from board import AI, EMPTY, HUMAN, WIN_LENGTH, check_winner

# Điểm tuyệt đối khi thắng/thua (giá trị rất lớn để phân biệt với điểm heuristic)
WIN_SCORE = 100_000


def evaluate(board):
    """
    Đánh giá trạng thái bàn cờ hiện tại.

    Trả về:
        - Điểm dương lớn → AI đang có lợi thế
        - Điểm âm lớn   → Người chơi đang có lợi thế
        - Gần 0         → Cân bằng
    """
    # Trạng thái kết thúc → trả về điểm tuyệt đối
    if check_winner(board, AI):
        return WIN_SCORE
    if check_winner(board, HUMAN):
        return -WIN_SCORE

    # Tính tổng điểm từ tất cả các cửa sổ trên bàn cờ
    score = 0
    for window in _iter_windows(board):
        score += _score_window(window)
    return score


def _iter_windows(board):
    """
    Sinh tất cả các cửa sổ gồm WIN_LENGTH ô liên tiếp trên bàn cờ.
    Duyệt 4 hướng: ngang →, dọc ↓, chéo chính ↘, chéo phụ ↙.
    Mỗi cửa sổ là một list chứa WIN_LENGTH phần tử (AI / HUMAN / EMPTY).
    """
    size = len(board)
    directions = [
        (0, 1),   # ngang
        (1, 0),   # dọc
        (1, 1),   # chéo chính
        (1, -1),  # chéo phụ
    ]

    for row in range(size):
        for col in range(size):
            for dr, dc in directions:
                end_row = row + dr * (WIN_LENGTH - 1)
                end_col = col + dc * (WIN_LENGTH - 1)

                if 0 <= end_row < size and 0 <= end_col < size:
                    yield [
                        board[row + dr * step][col + dc * step]
                        for step in range(WIN_LENGTH)
                    ]


def _score_window(window):
    """
    Chấm điểm một cửa sổ WIN_LENGTH ô.

    Bảng điểm (thiết kế bất đối xứng, ưu tiên phòng thủ):
        ┌─────────────────────────────┬───────────┐
        │ Tình huống                  │ Điểm      │
        ├─────────────────────────────┼───────────┤
        │ 4 quân AI    (thắng)        │ +100.000  │
        │ 4 quân HUMAN (thua)         │ -100.000  │
        │ 3 AI   + 1 trống (sắp thắng)│ +5.000   │
        │ 3 HUMAN + 1 trống (chặn gấp)│ -7.000   │
        │ 2 AI   + 2 trống           │ +600      │
        │ 2 HUMAN + 2 trống          │ -800      │
        │ 1 AI   + 3 trống           │ +30       │
        │ 1 HUMAN + 3 trống          │ -30       │
        │ Hỗn hợp (cả 2 bên)         │ 0         │
        └─────────────────────────────┴───────────┘

    Lưu ý: Điểm phòng thủ (chặn HUMAN) cao hơn tấn công cùng mức
    để AI ưu tiên chặn đối thủ khi cần thiết.
    """
    ai_count = window.count(AI)
    human_count = window.count(HUMAN)
    empty_count = window.count(EMPTY)

    # Cửa sổ có quân cả 2 bên → bị chặn, không có giá trị
    if ai_count > 0 and human_count > 0:
        return 0

    # --- Trạng thái kết thúc ---
    if ai_count == WIN_LENGTH:
        return WIN_SCORE
    if human_count == WIN_LENGTH:
        return -WIN_SCORE

    # --- 3 quân + 1 trống: sắp thắng / cần chặn gấp ---
    if ai_count == 3 and empty_count == 1:
        return 5000
    if human_count == 3 and empty_count == 1:
        return -7000

    # --- 2 quân + 2 trống: tiềm năng mở rộng ---
    if ai_count == 2 and empty_count == 2:
        return 600
    if human_count == 2 and empty_count == 2:
        return -800

    # --- 1 quân + 3 trống: khởi đầu nhẹ ---
    if ai_count == 1 and empty_count == 3:
        return 30
    if human_count == 1 and empty_count == 3:
        return -30

    return 0
