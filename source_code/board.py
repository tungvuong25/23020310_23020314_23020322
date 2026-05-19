"""
Mô-đun quản lý bàn cờ Caro.
Bao gồm: biểu diễn bàn cờ, kiểm tra nước đi hợp lệ,
kiểm tra điều kiện thắng/thua/hòa.
"""

BOARD_SIZE = 9      # Kích thước mặc định của bàn cờ (9×9)
WIN_LENGTH = 4      # Số quân liên tiếp cần có để thắng
EMPTY = "."         # Ký hiệu ô trống
HUMAN = "X"         # Ký hiệu quân người chơi
AI = "O"            # Ký hiệu quân máy


def create_board(size=BOARD_SIZE):
    """Tạo bàn cờ trống kích thước size × size."""
    if size < WIN_LENGTH:
        raise ValueError(f"Kích thước bàn cờ phải >= {WIN_LENGTH}")
    return [[EMPTY for _ in range(size)] for _ in range(size)]


def print_board(board):
    """In bàn cờ ra console với chỉ số hàng và cột."""
    size = len(board)
    cell_width = len(str(size - 1))

    # In dòng tiêu đề cột
    header = " " * (cell_width + 2)
    header += " ".join(f"{i:>{cell_width}}" for i in range(size))
    print(header)

    # In từng hàng kèm chỉ số hàng
    for i in range(size):
        row_text = " ".join(f"{cell:>{cell_width}}" for cell in board[i])
        print(f"{i:>{cell_width}}  {row_text}")


def is_valid_move(board, row, col):
    """Kiểm tra nước đi có hợp lệ không (trong phạm vi bàn cờ và ô trống)."""
    size = len(board)
    return 0 <= row < size and 0 <= col < size and board[row][col] == EMPTY


def make_move(board, row, col, player):
    """Đặt quân vào ô (row, col). Trả về True nếu thành công."""
    if is_valid_move(board, row, col):
        board[row][col] = player
        return True
    return False


def is_full(board):
    """Kiểm tra bàn cờ đã đầy chưa (điều kiện hòa)."""
    return all(EMPTY not in row for row in board)


def check_winner(board, player):
    """
    Kiểm tra người chơi 'player' đã thắng chưa.
    Duyệt tất cả các ô, kiểm tra 4 hướng:
    ngang →, dọc ↓, chéo chính ↘, chéo phụ ↙.
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
            if board[row][col] != player:
                continue
            for dr, dc in directions:
                if _has_line_from(board, row, col, dr, dc, player):
                    return True
    return False


def get_winning_cells(board, player):
    """
    Tìm và trả về danh sách các ô tạo thành chuỗi thắng.
    Trả về list[(row, col)] nếu tìm thấy, ngược lại trả về [].
    Dùng để giao diện tô sáng các ô thắng.
    """
    size = len(board)
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for row in range(size):
        for col in range(size):
            if board[row][col] != player:
                continue
            for dr, dc in directions:
                cells = []
                valid = True
                for step in range(WIN_LENGTH):
                    r = row + dr * step
                    c = col + dc * step
                    if not (0 <= r < size and 0 <= c < size):
                        valid = False
                        break
                    if board[r][c] != player:
                        valid = False
                        break
                    cells.append((r, c))
                if valid and len(cells) == WIN_LENGTH:
                    return cells
    return []


def _has_line_from(board, row, col, dr, dc, player):
    """Kiểm tra có WIN_LENGTH quân liên tiếp từ (row, col) theo hướng (dr, dc)."""
    size = len(board)
    for step in range(WIN_LENGTH):
        r = row + dr * step
        c = col + dc * step
        if not (0 <= r < size and 0 <= c < size):
            return False
        if board[r][c] != player:
            return False
    return True


def is_game_over(board):
    """Kiểm tra trò chơi đã kết thúc chưa (thắng/thua/hòa)."""
    return check_winner(board, HUMAN) or check_winner(board, AI) or is_full(board)
