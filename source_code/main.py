"""
Chương trình chơi cờ Caro qua console.
Người chơi (X) đấu với AI (O), chọn thuật toán và độ sâu tìm kiếm.
"""

from pathlib import Path

from ai import find_best_move_alpha_beta, find_best_move_minimax
from board import AI, HUMAN, check_winner, create_board, is_full, is_valid_move, make_move, print_board


LOG_PATH = Path(__file__).with_name("game_log.txt")


def choose_algorithm():
    """Cho người chơi chọn thuật toán AI sử dụng."""
    while True:
        print("Chọn thuật toán AI:")
        print("1. Minimax")
        print("2. Alpha-Beta")

        choice = input("Nhập lựa chọn: ").strip()
        if choice == "1":
            return "minimax", "Minimax"
        if choice == "2":
            return "alphabeta", "Alpha-Beta"

        print("Lựa chọn không hợp lệ, hãy nhập 1 hoặc 2.\n")


def choose_depth():
    """Cho người chơi chọn độ sâu tìm kiếm."""
    while True:
        try:
            depth = int(input("Nhập độ sâu tìm kiếm 1-5 (khuyến nghị 2 hoặc 3): "))
            if 1 <= depth <= 5:
                return depth
            print("Độ sâu phải trong khoảng 1 đến 5.")
        except ValueError:
            print("Vui lòng nhập số nguyên.")


def get_human_move(board):
    """Nhận nước đi từ người chơi qua console."""
    while True:
        raw = input("Nhập nước đi theo dạng 'hàng cột' (ví dụ: 4 5): ")
        parts = raw.replace(",", " ").split()

        if len(parts) != 2:
            print("Vui lòng nhập đúng 2 số: hàng cột.")
            continue

        try:
            row = int(parts[0])
            col = int(parts[1])
        except ValueError:
            print("Vui lòng nhập số nguyên.")
            continue

        if is_valid_move(board, row, col):
            return row, col

        print("Ô không hợp lệ hoặc đã có quân, hãy nhập lại.")


def find_ai_move(board, algorithm, depth):
    """Gọi thuật toán AI tương ứng để tìm nước đi."""
    if algorithm == "minimax":
        return find_best_move_minimax(board, depth)
    return find_best_move_alpha_beta(board, depth)


def save_game_log(lines):
    """Lưu lịch sử ván đấu vào file."""
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Đã lưu log vào: source_code/game_log.txt")


def play_game():
    """Chạy một ván cờ Caro giữa người chơi và AI."""
    algorithm, algorithm_name = choose_algorithm()
    depth = choose_depth()
    board = create_board()
    game_log = [
        "===== CARO AI GAME LOG =====",
        f"Thuật toán: {algorithm_name}",
        f"Độ sâu: {depth}",
        "",
    ]

    while True:
        print_board(board)
        print("\nLượt người chơi (X)")

        row, col = get_human_move(board)
        make_move(board, row, col, HUMAN)
        game_log.append(f"Người X đánh: ({row}, {col})")

        if check_winner(board, HUMAN):
            print_board(board)
            print("\nNgười chơi thắng!")
            game_log.append("Kết quả: Người chơi thắng")
            break

        if is_full(board):
            print_board(board)
            print("\nHòa!")
            game_log.append("Kết quả: Hòa")
            break

        print("\nLượt máy (O)")
        result = find_ai_move(board, algorithm, depth)
        ai_move = result["move"]

        if ai_move is None:
            print_board(board)
            print("\nHòa!")
            game_log.append("Kết quả: Hòa")
            break

        ai_row, ai_col = ai_move
        make_move(board, ai_row, ai_col, AI)

        log_line = (
            f"Máy O đánh: ({ai_row}, {ai_col}) | "
            f"Thuật toán: {algorithm_name} | "
            f"Điểm: {result['score']} | "
            f"Độ sâu: {result['depth']} | "
            f"Số trạng thái: {result['nodes']} | "
            f"Thời gian: {result['time']:.6f}s"
        )
        game_log.append(log_line)

        print(f"Máy đánh tại: ({ai_row}, {ai_col})")
        print(f"Thuật toán: {algorithm_name}")
        print("Độ sâu:", result["depth"])
        print("Điểm đánh giá:", result["score"])
        print("Số trạng thái đã xét:", result["nodes"])
        print(f"Thời gian chạy: {result['time']:.6f}s")

        if check_winner(board, AI):
            print_board(board)
            print("\nMáy thắng!")
            game_log.append("Kết quả: Máy thắng")
            break

        if is_full(board):
            print_board(board)
            print("\nHòa!")
            game_log.append("Kết quả: Hòa")
            break

    save_game_log(game_log)


def main():
    """Vòng lặp chính cho phép chơi nhiều ván."""
    while True:
        play_game()
        play_again = input("\nChơi lại? (y/n): ").strip().lower()

        if play_again != "y":
            print("Kết thúc game.")
            break


if __name__ == "__main__":
    main()
