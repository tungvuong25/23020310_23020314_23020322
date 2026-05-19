"""
Giao diện đồ họa cờ Caro AI sử dụng Tkinter Canvas.

UI giữ phần luật chơi và thuật toán hiện có, đồng thời tách việc tính AI khỏi
main thread để cửa sổ không bị đứng khi chọn độ sâu lớn.
"""

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import messagebox

from ai import find_best_move_alpha_beta, find_best_move_minimax
from board import (
    AI, EMPTY, HUMAN,
    check_winner, create_board, get_winning_cells,
    is_full, is_valid_move, make_move,
)
from evaluation import evaluate


LOG_PATH = Path(__file__).with_name("game_log.txt")

COLORS = {
    "bg": "#15171c",
    "panel": "#20242c",
    "board_bg": "#171b22",
    "grid": "#3c4656",
    "cell_hover": "#263545",
    "x": "#ff6b6b",
    "o": "#4dabf7",
    "text": "#edf2f7",
    "text_dim": "#a0aec0",
    "accent": "#ffd166",
    "success": "#69db7c",
    "warning": "#ffa94d",
    "danger": "#ff8787",
    "btn_bg": "#2d3748",
    "btn_hover": "#3b4658",
    "btn_text": "#edf2f7",
    "win_glow": "#ffd166",
    "last_move": "#ffa94d",
}

PADDING = 30
FONT_FAMILY = "Segoe UI"
MIN_CELL_SIZE = 24
MAX_CELL_SIZE = 58
SIDE_PANEL_WIDTH = 245
AI_POLL_MS = 50
AI_SEARCH_LOCK = threading.Lock()


class CaroGUI:
    """Giao diện chính cho trò chơi cờ Caro."""

    def __init__(self, root):
        self.root = root
        self.root.title("Cờ Caro AI")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("980x680")
        self.root.minsize(820, 640)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.cell_size = 46
        self.board_size = 9

        self.algorithm = tk.StringVar(value="alphabeta")
        self.depth = tk.IntVar(value=2)
        self.ai_first = tk.BooleanVar(value=False)
        self.size_var = tk.IntVar(value=self.board_size)

        self.board = create_board(self.board_size)
        self.move_history = []
        self.game_log = []
        self.game_over = False
        self.hover_cell = None
        self.last_ai_move = None
        self.winning_cells = []

        self.ai_thinking = False
        self._ai_request_id = 0
        self._ai_queue = queue.Queue()
        self._closed = False

        self.action_buttons = {}
        self.stat_labels = {}

        self._build_ui()

    # ================================================================
    # Xây dựng giao diện
    # ================================================================

    def _build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.action_buttons = {}
        self.stat_labels = {}

        header = tk.Frame(self.root, bg=COLORS["panel"], pady=12)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="Cờ Caro AI",
            fg=COLORS["accent"],
            bg=COLORS["panel"],
            font=(FONT_FAMILY, 20, "bold"),
        ).pack()
        tk.Label(
            header,
            text="Minimax / Alpha-Beta Pruning",
            fg=COLORS["text_dim"],
            bg=COLORS["panel"],
            font=(FONT_FAMILY, 10),
        ).pack()

        body = tk.Frame(self.root, bg=COLORS["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            body,
            bg=COLORS["bg"],
            highlightthickness=0,
            bd=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Configure>", self._on_resize)

        right = tk.Frame(body, bg=COLORS["bg"], width=SIDE_PANEL_WIDTH)
        right.grid(row=0, column=1, sticky="ns")
        right.grid_propagate(False)

        self._build_settings(right)
        self._build_stats(right)
        self._build_buttons(right)

        self.status_var = tk.StringVar(value="Lượt của bạn (X). Hãy chọn ô.")
        status = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 10),
            pady=8,
        )
        status.pack(fill=tk.X, side=tk.BOTTOM)

        self._set_controls_state()
        self._draw_board()

    def _build_settings(self, parent):
        group = tk.LabelFrame(
            parent,
            text="  Cài đặt  ",
            fg=COLORS["accent"],
            bg=COLORS["panel"],
            font=(FONT_FAMILY, 10, "bold"),
            labelanchor="n",
            padx=12,
            pady=10,
            bd=1,
        )
        group.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            group,
            text="Thuật toán:",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=(FONT_FAMILY, 9),
        ).pack(anchor=tk.W)

        for value, text in [("minimax", "Minimax"), ("alphabeta", "Alpha-Beta")]:
            tk.Radiobutton(
                group,
                text=text,
                variable=self.algorithm,
                value=value,
                fg=COLORS["text"],
                bg=COLORS["panel"],
                selectcolor=COLORS["btn_bg"],
                activebackground=COLORS["panel"],
                activeforeground=COLORS["accent"],
                font=(FONT_FAMILY, 9),
            ).pack(anchor=tk.W, padx=12)

        tk.Label(
            group,
            text="Độ sâu tìm kiếm:",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=(FONT_FAMILY, 9),
        ).pack(anchor=tk.W, pady=(8, 0))

        tk.Scale(
            group,
            variable=self.depth,
            from_=1,
            to=5,
            orient=tk.HORIZONTAL,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            troughcolor=COLORS["btn_bg"],
            highlightthickness=0,
            length=175,
            font=(FONT_FAMILY, 8),
        ).pack(anchor=tk.W, padx=8)

        tk.Label(
            group,
            text="Kích thước bàn cờ:",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=(FONT_FAMILY, 9),
        ).pack(anchor=tk.W, pady=(8, 0))

        size_frame = tk.Frame(group, bg=COLORS["panel"])
        size_frame.pack(anchor=tk.W, padx=8, pady=(2, 0))

        for size in [9, 11, 13, 15]:
            tk.Radiobutton(
                size_frame,
                text=str(size),
                variable=self.size_var,
                value=size,
                command=self._on_size_option_change,
                fg=COLORS["text"],
                bg=COLORS["panel"],
                selectcolor=COLORS["btn_bg"],
                activebackground=COLORS["panel"],
                activeforeground=COLORS["accent"],
                font=(FONT_FAMILY, 9),
            ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Checkbutton(
            group,
            text="AI đi trước",
            variable=self.ai_first,
            fg=COLORS["text"],
            bg=COLORS["panel"],
            selectcolor=COLORS["btn_bg"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["accent"],
            font=(FONT_FAMILY, 9),
        ).pack(anchor=tk.W, pady=(8, 0))

    def _build_stats(self, parent):
        group = tk.LabelFrame(
            parent,
            text="  Thống kê AI  ",
            fg=COLORS["accent"],
            bg=COLORS["panel"],
            font=(FONT_FAMILY, 10, "bold"),
            labelanchor="n",
            padx=12,
            pady=10,
            bd=1,
        )
        group.pack(fill=tk.X, pady=(0, 10))

        items = [
            ("algo", "Thuật toán:"),
            ("move", "Nước đi:"),
            ("score", "Điểm:"),
            ("nodes", "Trạng thái:"),
            ("time", "Thời gian:"),
            ("eval", "Đánh giá:"),
        ]

        for key, label in items:
            row = tk.Frame(group, bg=COLORS["panel"])
            row.pack(fill=tk.X, pady=2)

            tk.Label(
                row,
                text=label,
                fg=COLORS["text_dim"],
                bg=COLORS["panel"],
                font=(FONT_FAMILY, 9),
                width=12,
                anchor=tk.W,
            ).pack(side=tk.LEFT)

            value = tk.Label(
                row,
                text="-",
                fg=COLORS["text"],
                bg=COLORS["panel"],
                font=(FONT_FAMILY, 9, "bold"),
                anchor=tk.W,
            )
            value.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.stat_labels[key] = value

    def _build_buttons(self, parent):
        group = tk.Frame(parent, bg=COLORS["bg"])
        group.pack(fill=tk.X)

        buttons = [
            ("new", "Ván mới", self._new_game),
            ("undo", "Hoàn tác", self._undo_move),
            ("log", "Lịch sử", self._show_log),
            ("save", "Lưu log", self._save_log),
        ]

        for key, text, command in buttons:
            button = tk.Button(
                group,
                text=text,
                command=command,
                bg=COLORS["btn_bg"],
                fg=COLORS["btn_text"],
                activebackground=COLORS["btn_hover"],
                activeforeground=COLORS["accent"],
                disabledforeground=COLORS["text_dim"],
                font=(FONT_FAMILY, 10),
                relief=tk.FLAT,
                cursor="hand2",
                pady=7,
            )
            button.pack(fill=tk.X, pady=3)
            button.bind("<Enter>", lambda _event, b=button: self._hover_button(b, True))
            button.bind("<Leave>", lambda _event, b=button: self._hover_button(b, False))
            self.action_buttons[key] = button

    def _hover_button(self, button, is_hovering):
        if str(button["state"]) == tk.DISABLED:
            return
        button.config(bg=COLORS["btn_hover"] if is_hovering else COLORS["btn_bg"])

    def _set_controls_state(self):
        if not self.action_buttons:
            return

        can_use_log = bool(self.game_log)
        states = {
            "new": tk.NORMAL,
            "undo": tk.DISABLED if self.ai_thinking else tk.NORMAL,
            "log": tk.NORMAL if can_use_log else tk.DISABLED,
            "save": tk.NORMAL if can_use_log else tk.DISABLED,
        }

        if not self.move_history:
            states["undo"] = tk.DISABLED

        for key, button in self.action_buttons.items():
            button.config(state=states.get(key, tk.NORMAL), bg=COLORS["btn_bg"])

    # ================================================================
    # Vẽ bàn cờ
    # ================================================================

    def _draw_board(self):
        self.canvas.delete("all")
        board_px = self.board_size * self.cell_size
        origin_x, origin_y = self._board_origin()

        self.canvas.create_rectangle(
            origin_x,
            origin_y,
            origin_x + board_px,
            origin_y + board_px,
            fill=COLORS["board_bg"],
            outline="",
        )

        if self.hover_cell and not self.game_over and not self.ai_thinking:
            row, col = self.hover_cell
            if self.board[row][col] == EMPTY:
                self._draw_cell_fill(row, col, COLORS["cell_hover"])

        for row, col in self.winning_cells:
            self._draw_cell_fill(
                row,
                col,
                fill="#3a3320",
                outline=COLORS["win_glow"],
                width=2,
            )

        if self.last_ai_move and self.last_ai_move not in self.winning_cells:
            row, col = self.last_ai_move
            self._draw_cell_fill(
                row,
                col,
                fill="#2b2a21",
                outline=COLORS["last_move"],
                width=1,
            )

        for index in range(self.board_size + 1):
            x = origin_x + index * self.cell_size
            y = origin_y + index * self.cell_size
            self.canvas.create_line(
                x,
                origin_y,
                x,
                origin_y + board_px,
                fill=COLORS["grid"],
                width=1,
            )
            self.canvas.create_line(
                origin_x,
                y,
                origin_x + board_px,
                y,
                fill=COLORS["grid"],
                width=1,
            )

        label_font = (FONT_FAMILY, 8)
        for index in range(self.board_size):
            center = self.cell_size // 2
            self.canvas.create_text(
                origin_x + index * self.cell_size + center,
                origin_y - 13,
                text=str(index),
                fill=COLORS["text_dim"],
                font=label_font,
            )
            self.canvas.create_text(
                origin_x - 15,
                origin_y + index * self.cell_size + center,
                text=str(index),
                fill=COLORS["text_dim"],
                font=label_font,
            )

        for row in range(self.board_size):
            for col in range(self.board_size):
                player = self.board[row][col]
                if player != EMPTY:
                    self._draw_piece(row, col, player)

    def _draw_cell_fill(self, row, col, fill, outline="", width=1):
        x1, y1, x2, y2 = self._cell_bounds(row, col, inset=2)
        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=fill,
            outline=outline,
            width=width,
        )

    def _draw_piece(self, row, col, player):
        piece_pad = max(5, self.cell_size // 4)
        line_width = max(2, self.cell_size // 11)
        x1, y1, x2, y2 = self._cell_bounds(row, col, inset=piece_pad)

        if player == HUMAN:
            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=COLORS["x"],
                width=line_width,
                capstyle=tk.ROUND,
            )
            self.canvas.create_line(
                x1,
                y2,
                x2,
                y1,
                fill=COLORS["x"],
                width=line_width,
                capstyle=tk.ROUND,
            )
            return

        self.canvas.create_oval(
            x1,
            y1,
            x2,
            y2,
            outline=COLORS["o"],
            width=line_width,
        )

    def _cell_bounds(self, row, col, inset=0):
        origin_x, origin_y = self._board_origin()
        x1 = origin_x + col * self.cell_size + inset
        y1 = origin_y + row * self.cell_size + inset
        x2 = origin_x + (col + 1) * self.cell_size - inset
        y2 = origin_y + (row + 1) * self.cell_size - inset
        return x1, y1, x2, y2

    def _board_origin(self):
        board_px = self.board_size * self.cell_size
        width = max(self.canvas.winfo_width(), board_px + 2 * PADDING)
        height = max(self.canvas.winfo_height(), board_px + 2 * PADDING)
        origin_x = max(PADDING, (width - board_px) // 2)
        origin_y = max(PADDING, (height - board_px) // 2)
        return origin_x, origin_y

    # ================================================================
    # Sự kiện chuột và resize
    # ================================================================

    def _on_resize(self, event):
        available_size = min(event.width, event.height) - 2 * PADDING
        if available_size <= 0:
            return

        new_size = available_size // max(self.board_size, 1)
        new_size = max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, int(new_size)))

        if new_size != self.cell_size:
            self.cell_size = new_size

        self._draw_board()

    def _cell_from_pos(self, x, y):
        origin_x, origin_y = self._board_origin()
        board_px = self.board_size * self.cell_size

        if not (origin_x <= x < origin_x + board_px and origin_y <= y < origin_y + board_px):
            return None

        col = (x - origin_x) // self.cell_size
        row = (y - origin_y) // self.cell_size
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return int(row), int(col)
        return None

    def _on_click(self, event):
        if self.game_over or self.ai_thinking:
            return

        cell = self._cell_from_pos(event.x, event.y)
        if cell is None:
            return

        row, col = cell
        if is_valid_move(self.board, row, col):
            self._human_move(row, col)

    def _on_motion(self, event):
        cell = None if self.game_over or self.ai_thinking else self._cell_from_pos(event.x, event.y)
        if cell != self.hover_cell:
            self.hover_cell = cell
            self._draw_board()

    def _on_leave(self, _event):
        if self.hover_cell is not None:
            self.hover_cell = None
            self._draw_board()

    # ================================================================
    # Logic trò chơi
    # ================================================================

    def _human_move(self, row, col):
        if not make_move(self.board, row, col, HUMAN):
            return

        self.move_history.append((row, col, HUMAN))
        self.game_log.append(f"Người (X) đánh: ({row}, {col})")
        self.last_ai_move = None
        self._set_controls_state()

        if self._finish_if_game_over(HUMAN):
            return

        self._draw_board()
        self._schedule_ai_move()

    def _schedule_ai_move(self):
        if self.game_over:
            return

        self.ai_thinking = True
        self.hover_cell = None
        self._ai_request_id += 1

        request_id = self._ai_request_id
        board_snapshot = [row[:] for row in self.board]
        depth = int(self.depth.get())
        algorithm = self.algorithm.get()

        self.status_var.set("AI đang suy nghĩ...")
        self._set_controls_state()
        self._draw_board()

        worker = threading.Thread(
            target=self._compute_ai_move,
            args=(request_id, board_snapshot, depth, algorithm),
            daemon=True,
        )
        worker.start()
        self.root.after(AI_POLL_MS, lambda: self._poll_ai_queue(request_id))

    def _compute_ai_move(self, request_id, board_snapshot, depth, algorithm):
        try:
            with AI_SEARCH_LOCK:
                if self._closed or request_id != self._ai_request_id:
                    return
                if algorithm == "minimax":
                    result = find_best_move_minimax(board_snapshot, depth)
                    algo_name = "Minimax"
                else:
                    result = find_best_move_alpha_beta(board_snapshot, depth)
                    algo_name = "Alpha-Beta"
            self._ai_queue.put(("ok", request_id, result, algo_name))
        except Exception as exc:
            self._ai_queue.put(("error", request_id, exc, None))

    def _poll_ai_queue(self, request_id):
        if self._closed:
            return

        try:
            while True:
                status, result_id, payload, algo_name = self._ai_queue.get_nowait()
                if result_id != self._ai_request_id:
                    continue

                if status == "error":
                    self._handle_ai_error(payload)
                else:
                    self._finish_ai_move(payload, algo_name)
                return
        except queue.Empty:
            pass

        if self.ai_thinking and request_id == self._ai_request_id:
            self.root.after(AI_POLL_MS, lambda: self._poll_ai_queue(request_id))

    def _finish_ai_move(self, result, algo_name):
        self.ai_thinking = False

        move = result.get("move")
        if move is None:
            self._finish_draw()
            return

        row, col = move
        if not is_valid_move(self.board, row, col):
            self.game_over = True
            self.status_var.set("AI trả về nước đi không hợp lệ.")
            self._set_controls_state()
            messagebox.showerror("Lỗi AI", f"Nước đi ({row}, {col}) không hợp lệ.")
            return

        make_move(self.board, row, col, AI)
        self.move_history.append((row, col, AI))
        self.last_ai_move = (row, col)
        self._update_stats(result, algo_name, row, col)

        self.game_log.append(
            f"Máy (O) đánh: ({row}, {col}) | "
            f"Thuật toán: {algo_name} | "
            f"Điểm: {result['score']} | "
            f"Độ sâu: {result['depth']} | "
            f"Số trạng thái: {result['nodes']} | "
            f"Thời gian: {result['time']:.6f}s"
        )

        if self._finish_if_game_over(AI):
            return

        self._draw_board()
        self.status_var.set(f"Lượt bạn (X). AI vừa đánh ({row}, {col}).")
        self._set_controls_state()

    def _finish_if_game_over(self, player):
        if check_winner(self.board, player):
            self.winning_cells = get_winning_cells(self.board, player)
            self.game_over = True
            self.ai_thinking = False
            self._draw_board()

            if player == HUMAN:
                status = "Bạn đã thắng!"
                log_line = "Kết quả: Người chơi thắng"
            else:
                status = "AI đã thắng!"
                log_line = "Kết quả: Máy thắng"

            self.status_var.set(status)
            self.game_log.append(log_line)
            self._set_controls_state()
            messagebox.showinfo("Kết quả", status)
            return True

        if is_full(self.board):
            self._finish_draw()
            return True

        return False

    def _finish_draw(self):
        self.game_over = True
        self.ai_thinking = False
        self._draw_board()
        self.status_var.set("Hòa!")
        self.game_log.append("Kết quả: Hòa")
        self._set_controls_state()
        messagebox.showinfo("Kết quả", "Ván đấu hòa!")

    def _handle_ai_error(self, exc):
        self.ai_thinking = False
        self.game_over = True
        self.status_var.set("Có lỗi khi AI tính nước đi.")
        self._set_controls_state()
        messagebox.showerror("Lỗi AI", f"Không thể tính nước đi:\n{exc}")

    def _update_stats(self, result, algo_name, row, col):
        self.stat_labels["algo"].config(text=algo_name)
        self.stat_labels["move"].config(text=f"({row}, {col})")
        self.stat_labels["score"].config(text=f"{result['score']}")
        self.stat_labels["nodes"].config(text=f"{result['nodes']:,}")
        self.stat_labels["time"].config(text=f"{result['time']:.4f}s")
        self.stat_labels["eval"].config(text=f"{evaluate(self.board)}")

    def _clear_stats(self):
        for label in self.stat_labels.values():
            label.config(text="-")

    # ================================================================
    # Hành động
    # ================================================================

    def _new_game(self):
        if self.ai_thinking:
            self._ai_request_id += 1
            self.ai_thinking = False

        self.board_size = int(self.size_var.get())
        self.board = create_board(self.board_size)
        self.move_history = []
        self.game_log = []
        self.game_over = False
        self.hover_cell = None
        self.last_ai_move = None
        self.winning_cells = []

        self._build_ui()

        if self.ai_first.get():
            self._schedule_ai_move()
        else:
            self.status_var.set("Lượt của bạn (X). Hãy chọn ô.")
            self._set_controls_state()

    def _undo_move(self):
        if self.ai_thinking:
            messagebox.showinfo("Thông báo", "AI đang suy nghĩ, vui lòng chờ.")
            return

        if not self.move_history:
            messagebox.showinfo("Thông báo", "Chưa có nước đi để hoàn tác.")
            return

        for _ in range(2):
            if not self.move_history:
                break
            row, col, _player = self.move_history.pop()
            self.board[row][col] = EMPTY

        self.game_over = False
        self.winning_cells = []
        self._refresh_last_ai_move()
        self._clear_stats()
        self.game_log.append("- Đã hoàn tác -")
        self._draw_board()
        self.status_var.set("Đã hoàn tác. Lượt bạn (X).")
        self._set_controls_state()

    def _refresh_last_ai_move(self):
        self.last_ai_move = None
        for row, col, player in reversed(self.move_history):
            if player == AI:
                self.last_ai_move = (row, col)
                break

    def _save_log(self):
        if not self.game_log:
            messagebox.showinfo("Thông báo", "Chưa có dữ liệu log.")
            return

        content = "===== CARO AI GAME LOG =====\n\n"
        content += "\n".join(self.game_log) + "\n"

        try:
            LOG_PATH.write_text(content, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Lỗi lưu log", f"Không thể lưu log:\n{exc}")
            return

        messagebox.showinfo("Thông báo", f"Đã lưu log vào:\n{LOG_PATH}")

    def _show_log(self):
        if not self.game_log:
            messagebox.showinfo("Lịch sử", "Chưa có dữ liệu log.")
            return

        window = tk.Toplevel(self.root)
        window.title("Lịch sử ván đấu")
        window.geometry("680x430")
        window.configure(bg=COLORS["bg"])

        frame = tk.Frame(window, bg=COLORS["bg"])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text = tk.Text(
            frame,
            wrap=tk.WORD,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 10),
            insertbackground=COLORS["text"],
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        scrollbar = tk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text.insert(tk.END, "===== LỊCH SỬ VÁN ĐẤU =====\n\n")
        for line in self.game_log:
            text.insert(tk.END, line + "\n")
        text.config(state=tk.DISABLED)

    def _on_size_option_change(self):
        if not hasattr(self, "status_var"):
            return
        if self.size_var.get() != self.board_size:
            self.status_var.set("Kích thước mới sẽ áp dụng khi bấm Ván mới.")

    def _on_close(self):
        self._closed = True
        self._ai_request_id += 1
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("+200+60")
    CaroGUI(root)
    root.mainloop()
