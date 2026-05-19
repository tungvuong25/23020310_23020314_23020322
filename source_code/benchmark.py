"""
Mô-đun benchmark: chạy thực nghiệm so sánh Minimax và Alpha-Beta.

Tự động chạy cả hai thuật toán trên 5 trạng thái bàn cờ khác nhau
với nhiều độ sâu, ghi nhận số trạng thái, thời gian chạy và xuất
bảng kết quả ra file CSV.
"""

from copy import deepcopy
from pathlib import Path

from ai import find_best_move_alpha_beta, find_best_move_minimax
from board import AI, HUMAN, create_board, print_board


RESULT_PATH = Path(__file__).with_name("benchmark_results.csv")
FILE_HEADERS = [
    "state",
    "depth",
    "minimax_move",
    "minimax_score",
    "minimax_nodes",
    "minimax_time",
    "alphabeta_move",
    "alphabeta_score",
    "alphabeta_nodes",
    "alphabeta_time",
    "same_move",
    "node_reduction_percent",
    "time_speedup",
]
FILE_WIDTHS = [18, 5, 12, 13, 13, 12, 14, 15, 15, 14, 9, 22, 18]


# ============================================================
#  CÁC TRẠNG THÁI BÀN CỜ KIỂM THỬ
# ============================================================

def create_test_board_1():
    """Trạng thái 1 – Đầu ván: bàn cờ hoàn toàn trống."""
    return create_board()


def create_test_board_2():
    """Trạng thái 2 – Giữa ván: đã có một số quân trên bàn cờ."""
    board = create_board()
    board[4][4] = HUMAN
    board[4][5] = AI
    board[5][4] = HUMAN
    board[3][4] = AI
    return board


def create_test_board_3():
    """Trạng thái 3 – Máy có thể thắng ngay (3 quân AI liên tiếp)."""
    board = create_board()
    board[2][2] = AI
    board[2][3] = AI
    board[2][4] = AI
    board[2][1] = HUMAN
    return board


def create_test_board_4():
    """Trạng thái 4 – Người chơi sắp thắng, máy cần chặn (3 quân HUMAN)."""
    board = create_board()
    board[6][2] = HUMAN
    board[6][3] = HUMAN
    board[6][4] = HUMAN
    board[6][1] = AI
    return board


def create_test_board_5():
    """Trạng thái 5 – Hai bên đều có cơ hội tấn công."""
    board = create_board()
    board[4][4] = HUMAN
    board[4][5] = HUMAN
    board[5][4] = AI
    board[5][5] = AI
    board[3][3] = HUMAN
    board[6][6] = AI
    return board


# ============================================================
#  CHẠY BENCHMARK VÀ SO SÁNH
# ============================================================

def run_test(name, board, depth):
    """
    Chạy cả Minimax và Alpha-Beta trên cùng trạng thái bàn cờ
    với cùng độ sâu, sau đó so sánh kết quả.
    """
    result_minimax = find_best_move_minimax(deepcopy(board), depth)
    result_alpha_beta = find_best_move_alpha_beta(deepcopy(board), depth)

    minimax_nodes = result_minimax["nodes"]
    alpha_beta_nodes = result_alpha_beta["nodes"]
    minimax_time = result_minimax["time"]
    alpha_beta_time = result_alpha_beta["time"]

    # Tính phần trăm giảm số trạng thái nhờ Alpha-Beta
    reduction = 0.0
    if minimax_nodes:
        reduction = (minimax_nodes - alpha_beta_nodes) * 100 / minimax_nodes

    return {
        "state": name,
        "depth": depth,
        "minimax_move": result_minimax["move"],
        "minimax_score": result_minimax["score"],
        "minimax_nodes": minimax_nodes,
        "minimax_time": minimax_time,
        "alphabeta_move": result_alpha_beta["move"],
        "alphabeta_score": result_alpha_beta["score"],
        "alphabeta_nodes": alpha_beta_nodes,
        "alphabeta_time": alpha_beta_time,
        "same_move": result_minimax["move"] == result_alpha_beta["move"],
        "node_reduction_percent": reduction,
        "time_speedup": _compare_time(minimax_time, alpha_beta_time),
    }


def _compare_time(minimax_time, alpha_beta_time):
    """So sánh thời gian chạy giữa hai thuật toán."""
    if minimax_time == 0 and alpha_beta_time == 0:
        return "Bằng nhau 1.00x"
    if minimax_time == 0:
        return "Minimax inf"
    if alpha_beta_time == 0:
        return "AlphaBeta inf"
    if minimax_time <= alpha_beta_time:
        return f"Minimax {alpha_beta_time / minimax_time:.2f}x"
    return f"AlphaBeta {minimax_time / alpha_beta_time:.2f}x"


# ============================================================
#  HIỂN THỊ VÀ LƯU KẾT QUẢ
# ============================================================

def _print_result_table(results):
    """In bảng kết quả so sánh ra console."""
    headers = [
        "Trạng thái",
        "Độ sâu",
        "MM move",
        "MM nodes",
        "AB move",
        "AB nodes",
        "Giảm (%)",
        "Cùng move",
        "Nhanh hơn",
    ]
    widths = [28, 7, 10, 10, 10, 10, 9, 9, 18]

    print("\n" + _format_row(headers, widths))
    print("-" * len(_format_row(headers, widths)))

    for result in results:
        row = [
            result["state"],
            result["depth"],
            str(result["minimax_move"]),
            result["minimax_nodes"],
            str(result["alphabeta_move"]),
            result["alphabeta_nodes"],
            f"{result['node_reduction_percent']:.2f}",
            "Có" if result["same_move"] else "Không",
            result["time_speedup"],
        ]
        print(_format_row(row, widths))


def _format_row(values, widths):
    """Định dạng một hàng trong bảng kết quả."""
    return "|".join(str(value).ljust(width) for value, width in zip(values, widths))


def _format_result_row(result):
    """Định dạng một hàng để lưu vào file CSV."""
    values = [
        result["state"],
        result["depth"],
        str(result["minimax_move"]),
        result["minimax_score"],
        result["minimax_nodes"],
        f"{result['minimax_time']:.6f}",
        str(result["alphabeta_move"]),
        result["alphabeta_score"],
        result["alphabeta_nodes"],
        f"{result['alphabeta_time']:.6f}",
        result["same_move"],
        f"{result['node_reduction_percent']:.2f}",
        result["time_speedup"],
    ]
    return _format_row(values, FILE_WIDTHS)


def _save_table(results):
    """Lưu bảng kết quả benchmark ra file CSV."""
    rows = [_format_row(FILE_HEADERS, FILE_WIDTHS)]
    rows.extend(_format_result_row(result) for result in results)

    with RESULT_PATH.open("w", encoding="utf-8") as file:
        file.write("\n".join(rows) + "\n")

    print(f"\nĐã lưu bảng kết quả vào: {RESULT_PATH}")


def main():
    """Chạy benchmark trên 5 trạng thái × nhiều độ sâu."""
    depths = list(range(1, 6))
    tests = [
        ("Đầu ván", create_test_board_1()),
        ("Giữa ván", create_test_board_2()),
        ("Máy thắng ngay", create_test_board_3()),
        ("Người sắp thắng", create_test_board_4()),
        ("Hai bên tấn công", create_test_board_5()),
    ]

    print("===== CÁC TRẠNG THÁI KIỂM THỬ =====")
    for name, board in tests:
        print(f"\n{name}")
        print_board(board)

    results = []
    for depth in depths:
        for name, board in tests:
            results.append(run_test(name, board, depth))

    _print_result_table(results)
    _save_table(results)


if __name__ == "__main__":
    main()
