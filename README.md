# 23020322_23020310_23020314_CaroAI

Dự án cài đặt trò chơi cờ Caro giữa người chơi và máy tính theo yêu cầu bài tập lập trình giữa kỳ. Người chơi dùng quân `X`, máy dùng quân `O`, ô trống ký hiệu bằng dấu `.`. Máy tính có thể chọn nước đi bằng Minimax hoặc Alpha-Beta pruning với cùng hàm đánh giá và cùng giới hạn độ sâu để so sánh công bằng.

## Yêu Cầu Môi Trường

- Python 3.9 trở lên.
- Không cần cài thêm thư viện ngoài.
- Giao diện đồ họa dùng `tkinter`, thường có sẵn trong bản cài Python chuẩn.

File `requirements.txt` được giữ trong repo theo yêu cầu nộp bài. Dự án hiện không có dependency ngoài thư viện chuẩn của Python.

## Cấu Trúc Thư Mục

```text
source_code/
  board.py        # Biểu diễn bàn cờ, kiểm tra nước đi, thắng/thua/hòa
  evaluation.py   # Hàm đánh giá trạng thái bàn cờ
  ai.py           # Minimax, Alpha-Beta, sinh và sắp xếp nước đi
  main.py         # Phiên bản chơi bằng console
  ui.py           # Giao diện Tkinter
  benchmark.py    # Thực nghiệm so sánh Minimax và Alpha-Beta
  game_log.txt    # Log ván đấu khi người dùng lưu từ chương trình
  benchmark_results.csv # Bảng kết quả benchmark
requirements.txt
README.md
```

## Cách Chạy

Chạy bằng console:

```bash
python source_code/main.py
```

Chạy giao diện đồ họa:

```bash
python source_code/ui.py
```

Chạy benchmark so sánh Minimax và Alpha-Beta:

```bash
python source_code/benchmark.py
```

Trên Windows, nếu máy dùng Python Launcher, có thể thay `python` bằng `py`.

## Luật Chơi

- Bàn cờ mặc định có kích thước `9x9`; giao diện cho phép chọn thêm `11x11`, `13x13`, `15x15`.
- Hai bên lần lượt đánh vào các ô trống.
- Không được đánh vào ô đã có quân.
- Người thắng là người có 4 quân liên tiếp theo hàng ngang, hàng dọc hoặc đường chéo.
- Không xét luật chặn hai đầu.
- Nếu bàn cờ đầy và không có người thắng thì kết quả là hòa.

## Chức Năng Đã Cài Đặt

- Biểu diễn trạng thái bàn cờ bằng mảng hai chiều.
- Sinh nước đi hợp lệ, ưu tiên các ô gần quân đã đánh để giảm không gian tìm kiếm.
- Kiểm tra trạng thái kết thúc: người thắng, máy thắng hoặc hòa.
- AI Minimax có giới hạn độ sâu.
- AI Alpha-Beta pruning dùng cùng hàm đánh giá với Minimax.
- Cho phép chọn thuật toán AI và độ sâu tìm kiếm.
- Ghi nhận nước đi máy chọn, điểm đánh giá, độ sâu, số trạng thái đã xét và thời gian chạy.
- Giao diện Tkinter hỗ trợ ván mới, hoàn tác, xem lịch sử và lưu log.
- Benchmark chạy trên nhiều trạng thái bàn cờ để so sánh số trạng thái và thời gian.

## Hàm Đánh Giá

Hàm đánh giá trong `source_code/evaluation.py` duyệt các cửa sổ 4 ô liên tiếp theo 4 hướng. Điểm số dương thể hiện lợi thế cho máy, điểm số âm thể hiện lợi thế cho người chơi.

Các trường hợp chính:

- Máy có 4 quân liên tiếp: điểm rất lớn.
- Người chơi có 4 quân liên tiếp: điểm rất nhỏ.
- Máy có 3 quân và 1 ô trống: điểm cao.
- Người chơi có 3 quân và 1 ô trống: điểm âm lớn để ưu tiên chặn.
- Chuỗi 2 quân hoặc 1 quân được chấm điểm nhỏ hơn theo mức độ tiềm năng.

## Benchmark Và Kết Quả

`source_code/benchmark.py` chuẩn bị 5 trạng thái kiểm thử:

1. Đầu ván.
2. Giữa ván.
3. Máy có thể thắng ngay.
4. Người chơi sắp thắng, máy cần chặn.
5. Hai bên đều có cơ hội tấn công.

Benchmark chạy Minimax và Alpha-Beta trên cùng trạng thái, cùng độ sâu và cùng hàm đánh giá. Kết quả được lưu tại:

```text
source_code/benchmark_results.csv
```

Các cột chính trong bảng kết quả gồm nước đi được chọn, điểm đánh giá, số trạng thái đã xét, thời gian chạy, hai thuật toán có chọn cùng nước đi hay không và phần trăm giảm số trạng thái của Alpha-Beta.

## Mức Độ Đáp Ứng Yêu Cầu

- Level 1: đã cài đặt Caro người chơi đấu với AI dùng Minimax giới hạn độ sâu.
- Level 2: đã cài đặt Alpha-Beta pruning và cho phép chọn Minimax hoặc Alpha-Beta.
- Level 3: đã có benchmark với 5 trạng thái kiểm thử và bảng kết quả để phục vụ phân tích báo cáo.

## Tài Liệu Tham Khảo

Đề bài có cung cấp các repo mẫu để tham khảo cách tổ chức chương trình và ý tưởng triển khai:

- https://github.com/husus/gomokuAI-py
- https://github.com/MonHauVD/Caro_AI

Dự án này tự cài đặt luật chơi Caro 4 quân liên tiếp, Minimax, Alpha-Beta, hàm đánh giá, benchmark và giao diện theo yêu cầu bài tập.
