"""
Mô-đun AI cho cờ Caro.

Cài đặt hai thuật toán tìm kiếm có đối thủ:
    1. Minimax với giới hạn độ sâu
    2. Alpha-Beta Pruning (cải tiến Minimax bằng cắt nhánh)

Cả hai thuật toán dùng chung hàm đánh giá và cùng cơ chế
sinh nước đi hợp lệ để đảm bảo so sánh công bằng.

Cải tiến đã áp dụng:
    - Chỉ sinh nước đi gần quân đã đặt (giảm branching factor)
    - Sắp xếp nước đi ưu tiên nước tốt trước (move ordering)
    - Depth penalty: ưu tiên thắng nhanh, thua chậm
"""

import time

from board import AI, EMPTY, HUMAN, check_winner, is_full
from evaluation import WIN_SCORE, evaluate

# Biến toàn cục đếm số trạng thái đã duyệt trong mỗi lần tìm kiếm
nodes_count = 0


# ============================================================
#  SINH VÀ SẮP XẾP NƯỚC ĐI HỢP LỆ
# ============================================================

def get_valid_moves(board, radius=1):
    """
    Sinh danh sách nước đi hợp lệ, chỉ xét các ô trống
    nằm trong bán kính 'radius' quanh các quân đã đặt.

    Tối ưu: thay vì xét tất cả 81 ô (bàn 9×9), chỉ xét
    các ô lân cận quân đã có → giảm đáng kể không gian tìm kiếm.

    Sau đó sắp xếp nước đi theo thứ tự ưu tiên:
        1. Nước có tiềm năng tạo/chặn chuỗi dài (điểm cao nhất)
        2. Nước gần trung tâm bàn cờ (khoảng cách Manhattan nhỏ)

    Việc sắp xếp giúp Alpha-Beta cắt nhánh hiệu quả hơn
    vì xét nước tốt trước sẽ thu hẹp cửa sổ [alpha, beta] sớm.
    """
    size = len(board)

    # Thu thập tất cả ô đã có quân
    occupied_cells = [
        (row, col)
        for row in range(size)
        for col in range(size)
        if board[row][col] != EMPTY
    ]

    # Bàn cờ trống → đặt quân vào trung tâm (chiến lược tối ưu)
    if not occupied_cells:
        center = size // 2
        return [(center, center)]

    # Chỉ xét các ô trống trong bán kính radius quanh quân đã đặt
    moves = set()
    for row, col in occupied_cells:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                next_row = row + dr
                next_col = col + dc

                if (
                    0 <= next_row < size
                    and 0 <= next_col < size
                    and board[next_row][next_col] == EMPTY
                ):
                    moves.add((next_row, next_col))

    # Fallback: nếu không tìm được (trường hợp hiếm), xét tất cả ô trống
    if not moves:
        moves = {
            (row, col)
            for row in range(size)
            for col in range(size)
            if board[row][col] == EMPTY
        }

    # Sắp xếp: ưu tiên nước có tiềm năng cao, gần trung tâm
    center = size // 2
    return sorted(
        moves,
        key=lambda move: (
            -_score_candidate_move(board, move[0], move[1]),
            abs(move[0] - center) + abs(move[1] - center),
            move[0],
            move[1],
        ),
    )


def _score_candidate_move(board, row, col):
    """
    Ước lượng nhanh tiềm năng của nước đi tại (row, col).
    Tính cho cả hai bên (tấn công AI + chặn HUMAN).
    Dùng để sắp xếp thứ tự xét nước đi (move ordering).
    """
    ai_potential = _line_potential_after_move(board, row, col, AI)
    human_potential = _line_potential_after_move(board, row, col, HUMAN)
    return ai_potential + human_potential


def _line_potential_after_move(board, row, col, player):
    """
    Tính chuỗi dài nhất có thể tạo được nếu player đặt quân tại (row, col).
    Kiểm tra 4 hướng, đếm quân cùng loại liền kề theo cả 2 chiều.
    """
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    best_line = 1
    for dr, dc in directions:
        line_length = 1
        line_length += _count_same_direction(board, row, col, dr, dc, player)
        line_length += _count_same_direction(board, row, col, -dr, -dc, player)
        best_line = max(best_line, line_length)

    # Gán điểm theo độ dài chuỗi tiềm năng
    if best_line >= 4:
        return WIN_SCORE * 2    # Thắng ngay → ưu tiên tuyệt đối
    if best_line == 3:
        return 6000             # Sắp hoàn thành chuỗi thắng
    if best_line == 2:
        return 700              # Chuỗi có tiềm năng phát triển
    return 20                   # Nước đi đơn lẻ


def _count_same_direction(board, row, col, dr, dc, player):
    """Đếm số quân cùng loại liên tiếp theo hướng (dr, dc) từ (row, col)."""
    size = len(board)
    count = 0
    current_row = row + dr
    current_col = col + dc

    while (
        0 <= current_row < size
        and 0 <= current_col < size
        and board[current_row][current_col] == player
    ):
        count += 1
        current_row += dr
        current_col += dc

    return count


# ============================================================
#  ĐÁNH GIÁ TRẠNG THÁI KẾT THÚC (có Depth Penalty)
# ============================================================

def _terminal_score(board, depth):
    """
    Trả về điểm nếu trạng thái là kết thúc (thắng/thua/hòa),
    ngược lại trả về None.

    Cải tiến Depth Penalty:
        - Thắng: WIN_SCORE + depth  → ưu tiên thắng NHANH (depth còn lại lớn)
        - Thua: -WIN_SCORE - depth  → ưu tiên thua CHẬM
    Nhờ đó AI sẽ không "lười biếng" khi thấy đường thắng chắc chắn
    mà chọn đường thắng ngắn nhất có thể.
    """
    if check_winner(board, AI):
        return WIN_SCORE + depth

    if check_winner(board, HUMAN):
        return -WIN_SCORE - depth

    if is_full(board):
        return 0

    return None


# ============================================================
#  THUẬT TOÁN MINIMAX
# ============================================================

def minimax(board, depth, is_maximizing):
    """
    Thuật toán Minimax với giới hạn độ sâu.

    Ý tưởng: giả sử cả hai bên đều chơi tối ưu.
        - Lượt MAX (AI): chọn nước đi có giá trị LỚN NHẤT
        - Lượt MIN (HUMAN): chọn nước đi có giá trị NHỎ NHẤT

    Tham số:
        board:          trạng thái bàn cờ hiện tại
        depth:          số tầng còn lại được phép tìm kiếm
        is_maximizing:  True nếu đang là lượt MAX (AI)

    Trả về: giá trị đánh giá tốt nhất tìm được
    """
    global nodes_count
    nodes_count += 1

    # Kiểm tra trạng thái kết thúc (thắng/thua/hòa)
    score = _terminal_score(board, depth)
    if score is not None:
        return score

    # Đạt giới hạn độ sâu → dùng hàm đánh giá heuristic
    if depth == 0:
        return evaluate(board)

    moves = get_valid_moves(board)
    if not moves:
        return 0

    if is_maximizing:
        # Lượt AI (MAX): tìm giá trị lớn nhất
        best_score = -float("inf")
        for row, col in moves:
            board[row][col] = AI
            best_score = max(best_score, minimax(board, depth - 1, False))
            board[row][col] = EMPTY
        return best_score

    # Lượt HUMAN (MIN): tìm giá trị nhỏ nhất
    best_score = float("inf")
    for row, col in moves:
        board[row][col] = HUMAN
        best_score = min(best_score, minimax(board, depth - 1, True))
        board[row][col] = EMPTY
    return best_score


def find_best_move_minimax(board, depth):
    """
    Tìm nước đi tốt nhất cho AI bằng thuật toán Minimax.

    Trả về dict chứa:
        move:   tọa độ (row, col) nước đi tốt nhất
        score:  giá trị đánh giá
        nodes:  tổng số trạng thái đã duyệt
        time:   thời gian chạy (giây)
        depth:  độ sâu tìm kiếm đã dùng
    """
    global nodes_count
    nodes_count = 1
    depth = max(1, depth)
    start_time = time.perf_counter()

    best_score = -float("inf")
    best_move = None

    for row, col in get_valid_moves(board):
        board[row][col] = AI
        score = minimax(board, depth - 1, False)
        board[row][col] = EMPTY

        if score > best_score:
            best_score = score
            best_move = (row, col)

    return {
        "move": best_move,
        "score": best_score,
        "nodes": nodes_count,
        "time": time.perf_counter() - start_time,
        "depth": depth,
    }


# ============================================================
#  THUẬT TOÁN ALPHA-BETA PRUNING
# ============================================================

def alpha_beta(board, depth, alpha, beta, is_maximizing):
    """
    Thuật toán Alpha-Beta Pruning – cải tiến Minimax bằng cắt nhánh.

    Ý tưởng: duy trì cửa sổ [alpha, beta] biểu diễn khoảng giá trị
    mà cả hai bên chấp nhận được.
        - alpha: giá trị tốt nhất mà MAX (AI) đã tìm được
        - beta:  giá trị tốt nhất mà MIN (HUMAN) đã tìm được

    Khi beta <= alpha → cắt nhánh (prune), vì nhánh còn lại chắc chắn
    không tốt hơn cho bên đang chọn → tiết kiệm thời gian tính toán.

    Tham số:
        board:          trạng thái bàn cờ hiện tại
        depth:          số tầng còn lại được phép tìm kiếm
        alpha:          giá trị tốt nhất của MAX (khởi tạo = -∞)
        beta:           giá trị tốt nhất của MIN (khởi tạo = +∞)
        is_maximizing:  True nếu đang là lượt MAX (AI)

    Trả về: giá trị đánh giá tốt nhất tìm được
    """
    global nodes_count
    nodes_count += 1

    # Kiểm tra trạng thái kết thúc
    score = _terminal_score(board, depth)
    if score is not None:
        return score

    # Đạt giới hạn độ sâu → dùng hàm đánh giá heuristic
    if depth == 0:
        return evaluate(board)

    moves = get_valid_moves(board)
    if not moves:
        return 0

    if is_maximizing:
        # Lượt AI (MAX): tìm giá trị lớn nhất
        best_score = -float("inf")
        for row, col in moves:
            board[row][col] = AI
            best_score = max(
                best_score,
                alpha_beta(board, depth - 1, alpha, beta, False),
            )
            board[row][col] = EMPTY

            # Cập nhật alpha và kiểm tra cắt nhánh
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break  # Cắt nhánh beta (β cutoff)
        return best_score

    # Lượt HUMAN (MIN): tìm giá trị nhỏ nhất
    best_score = float("inf")
    for row, col in moves:
        board[row][col] = HUMAN
        best_score = min(
            best_score,
            alpha_beta(board, depth - 1, alpha, beta, True),
        )
        board[row][col] = EMPTY

        # Cập nhật beta và kiểm tra cắt nhánh
        beta = min(beta, best_score)
        if beta <= alpha:
            break  # Cắt nhánh alpha (α cutoff)
    return best_score


def find_best_move_alpha_beta(board, depth):
    """
    Tìm nước đi tốt nhất cho AI bằng thuật toán Alpha-Beta Pruning.

    Trả về dict chứa:
        move:   tọa độ (row, col) nước đi tốt nhất
        score:  giá trị đánh giá
        nodes:  tổng số trạng thái đã duyệt
        time:   thời gian chạy (giây)
        depth:  độ sâu tìm kiếm đã dùng
    """
    global nodes_count
    nodes_count = 1
    depth = max(1, depth)
    start_time = time.perf_counter()

    best_score = -float("inf")
    best_move = None
    alpha = -float("inf")
    beta = float("inf")

    for row, col in get_valid_moves(board):
        board[row][col] = AI
        score = alpha_beta(board, depth - 1, alpha, beta, False)
        board[row][col] = EMPTY

        if score > best_score:
            best_score = score
            best_move = (row, col)

        # Cập nhật alpha tại tầng gốc
        alpha = max(alpha, best_score)

    return {
        "move": best_move,
        "score": best_score,
        "nodes": nodes_count,
        "time": time.perf_counter() - start_time,
        "depth": depth,
    }
