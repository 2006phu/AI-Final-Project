# ĐỒ ÁN CUỐI KỲ: NHẬP MÔN TRÍ TUỆ NHÂN TẠO (503043)
### TRƯỜNG ĐẠI HỌC TÔN ĐỨC THẮNG — KHOA CÔNG NGHỆ THÔNG TIN
**Nhóm:** 08  
**Giảng viên hướng dẫn:** ThS. Nguyễn Thành An (`nguyenthanhan@tdtu.edu.vn`)

---

## 👥 THÀNH VIÊN NHÓM 08
1. **Lê Phú** — MSSV: `524H0121` *(Trưởng nhóm)*
2. **Vũ Giang Huy** — MSSV: `524H0095`
3. **Lê Hoàng Minh Khôi** — MSSV: `524H0102`

---

## 🚀 1. KHỞI ĐỘNG NHANH (QUICK START — 1 CLICK)

Dự án được thiết kế theo tiêu chí **trực quan hóa 100% bằng chuột**, hỗ trợ khởi động bằng **1 cú click chuột** mà không cần thao tác qua dòng lệnh:

### Cách 1: Trên Windows (Khuyên dùng)
- **Chạy Bảng điều khiển trung tâm (Master Dashboard):**  
  Double-click vào file **`run.bat`**. Giao diện Arcade Dark Tech Hub sẽ hiện lên, cho phép chuyển đổi mượt mà giữa cả 3 Task và xem lược đồ so sánh trực quan.
- **Chạy tự động kiểm thử toàn bộ 3 Task (1-Click Run):**  
  Double-click vào file **`run_1click.bat`**. Hệ thống sẽ tự động chạy pipeline kiểm thử đo đạc thực tế của Task 1 (SAT + Min-Conflicts), Task 2 (15 turns thi đấu Alpha-Beta vs Minimax), Task 3 (GAC/MAC trên Kakuro 5x5) và hiển thị bảng tổng hợp kết quả đạt chuẩn 100% PASS!

### Cách 2: Trên macOS / Linux
Mở terminal tại thư mục gốc của dự án và chạy:
```bash
bash run.sh
```

### Cách 3: Chạy trực tiếp qua lệnh Python
```bash
# Khởi động Master Dashboard
python main.py

# Hoặc khởi động thẳng chế độ 1-Click Run
python main.py --1click
```

---

## 📦 2. CÀI ĐẶT MÔI TRƯỜNG (REQUIREMENTS)

- **Yêu cầu môi trường:** Python 3.10 trở lên (khuyên dùng Python 3.11 hoặc 3.12).
- Cài đặt toàn bộ các thư viện cần thiết bằng lệnh:
```bash
pip install -r requirements.txt
```
*(Hoặc `pip install -r source/requirements.txt`)*

**Các thư viện chính:**
- `pygame-ce >= 2.5.0`: Thư viện đồ họa cho giao diện trực quan hóa tương tác của cả 3 Task và Master Hub.
- `python-sat >= 1.2.0`: Chứa bộ giải SAT hiện đại Glucose3 phục vụ Task 1.
- `pytest >= 8.0.0`: Khung kiểm thử tự động 30/30 unit tests cho toàn bộ hệ thống logic.
- `matplotlib >= 3.8.0`: Vẽ đồ họa thống kê và biểu đồ phân tích trong các file jupyter notebook.
- `tabulate`, `ipykernel`, `notebook`: Phục vụ hiển thị bảng biểu và thực nghiệm trong sổ tay notebook.

---

## 📂 3. CẤU TRÚC THƯ MỤC DỰ ÁN

```
Cuối kỳ AI/
├── main.py                     # Entrypoint khởi động Master Dashboard
├── run.bat                     # File 1-click khởi động trên Windows
├── run_1click.bat              # File 1-click chạy kiểm thử tự động toàn bộ 3 Task
├── run.sh                      # Script khởi động trên Linux / macOS
├── requirements.txt            # Danh sách thư viện cần thiết
├── demo.txt                    # Link video demo và bảng đóng góp thành viên
├── report.pdf                  # Báo cáo đồ án định dạng IEEE Conference
├── package_submission.py       # Script tự động đóng gói zip nộp bài cho từng thành viên
└── source/                     # Thư mục chứa mã nguồn chính
    ├── main.py                 # Mã nguồn Master Dashboard GUI
    ├── requirements.txt        # Thư viện yêu cầu bên trong source
    ├── README.md               # Bản hướng dẫn chi tiết này
    ├── task1_nqueens/          # TASK 1: N-Queens Problem
    │   ├── board.py            # Quản lý bàn cờ N x N, ánh xạ biến logic DIMACS CNF
    │   ├── cnf_encoder.py      # Mã hóa CNF: Pairwise O(N^3) & Sequential Counter O(N^2)
    │   ├── sat_solver.py       # Tích hợp Glucose3 solver từ PySAT
    │   ├── min_conflicts.py    # Min-Conflicts: Standard vs Đề xuất (Greedy + MaxConf + Tabu)
    │   ├── gui.py              # Giao diện Pygame: Bàn cờ trực quan, vương miện, biểu đồ
    │   ├── cli.py              # Giao diện dòng lệnh thực nghiệm
    │   ├── experiments.ipynb   # Sổ tay thực nghiệm so sánh đầy đủ output
    │   └── tests/              # Unit tests cho Task 1 (11/11 tests)
    ├── task2_tank/             # TASK 2: Tank Battle Game
    │   ├── entities.py         # Thực thể: Tank, Base, Wall, Bullet, Direction, Action
    │   ├── game_state.py       # Mô hình trạng thái GameState, hàm đọc map ASCII
    │   ├── engine.py           # GameEngine: Va chạm đạn cell-by-cell, giải quyết xung đột xe
    │   ├── evaluator.py        # Hàm đánh giá trạng thái đối kháng Zero-Sum phản đối xứng
    │   ├── agents/             # Bộ điều khiển AI: SearchAgent (Minimax, Alpha-Beta, Heuristics)
    │   ├── maps/               # Bản đồ thi đấu: arena_11x11.txt, standard_13x13.txt
    │   ├── gui.py              # Giao diện Pygame: Nạp động Agent, điều khiển trận đấu, biểu đồ
    │   ├── experiments.ipynb   # Thực nghiệm so sánh 4 cấu hình search, depth, node prune
    │   └── tests/              # Unit tests cho Task 2 (5/5 tests)
    └── task3_kakuro/           # TASK 3: Kakuro CSP
        ├── puzzle.py           # Phân tích đề bài Kakuro, xác thực tính toàn vẹn clue
        ├── csp.py              # Mô hình hóa CSP, bảng tổ hợp sinh trước, tỉa miền ban đầu
        ├── propagation.py      # Lan truyền ràng buộc: Bipartite matching GAC, FC, MAC
        ├── solver.py           # Backtracking Solver: MRV, Degree, LCV, Generator sự kiện
        ├── puzzles/            # Đề Kakuro: simple_3x3, example_5x5, complex_test_case
        ├── gui.py              # Giao diện Pygame: Lưới bút chì 3x3 pencil-marks, màu sự kiện
        ├── experiments.ipynb   # Thực nghiệm so sánh Backtracking, FC, MAC, MRV
        └── tests/              # Unit tests cho Task 3 (14/14 tests)
```

---

## 🎯 4. HƯỚNG DẪN CHẠY TỪNG TASK RIÊNG LẺ

Ngoài việc khởi động qua **Master Dashboard** (`python main.py`), giảng viên và người đánh giá có thể chạy độc lập từng Task qua GUI hoặc CLI:

### Task 1: N-Queens Problem
- **Mở Giao diện Pygame:**
  ```bash
  python source/task1_nqueens/gui.py
  ```
  *(Có thể chọn kích thước N = 4, 8, 12, 16, 20... và chuyển đổi linh hoạt giữa SAT Solver hoặc Min-Conflicts trực tiếp trên màn hình).*
- **Chạy qua CLI:**
  ```bash
  # Giải N=8 bằng SAT Glucose3 với Sequential Counter:
  python source/task1_nqueens/cli.py --n 8 --solver sat --encoder sequential

  # Giải N=50 bằng Min-Conflicts cải tiến (Greedy + Tabu):
  python source/task1_nqueens/cli.py --n 50 --solver min_conflicts --heuristic proposed
  ```

### Task 2: Tank Battle Game
- **Mở Giao diện Pygame:**
  ```bash
  python source/task2_tank/gui.py
  ```
- **Tính năng nổi bật:**
  - Nạp động Agent từ nhóm khác: Đặt file `agent_tennhom.py` kế thừa từ `BaseAgent` vào thư mục `source/task2_tank/agents/`. Giao diện sẽ tự động quét và đưa vào danh sách chọn lựa cho Player 1 hoặc Player 2.
  - Chọn 4 cấu hình thuật toán: Minimax, Alpha-Beta, Heuristic Minimax, Heuristic Alpha-Beta.
  - Tùy chỉnh tốc độ trận đấu (FPS), tạm dừng (Space), hoặc bước từng turn (phím S).

### Task 3: Kakuro Puzzle (CSP)
- **Mở Giao diện Pygame:**
  ```bash
  python source/task3_kakuro/gui.py
  ```
- **Tính năng nổi bật:**
  - Hiển thị trực quan **lưới bút chì 3x3 (Pencil-mark subgrid)** trong từng ô trắng đại diện cho miền giá trị còn lại $\{1..9\}$.
  - Mã màu trực quan: **Gán giá trị (Xanh lá)**, **Tỉa miền giá trị (Đỏ)**, **Quay lui (Cam)**.
  - Lựa chọn giải thuật lan truyền: **Pure Backtracking**, **Forward Checking (FC)**, hoặc **Maintaining Arc Consistency (MAC)**.
  - Chọn các câu đố mẫu: `simple_3x3.txt`, `example_5x5.txt`, hoặc `complex_test_case.txt` từ Wikipedia.

---

## 🧪 5. KIỂM THỬ TỰ ĐỘNG (UNIT TESTS)

Dự án trang bị bộ kiểm thử toàn diện với **30 test cases** kiểm tra chặt chẽ tính đúng đắn của toàn bộ thuật toán. Chạy lệnh:

```bash
pytest source/ -v
```

**Kết quả kiểm thử:**
- Task 1: 11 tests (Kiểm tra DIMACS logic, tính hợp lệ bàn cờ, số mệnh đề Pairwise vs Sequential Counter, Glucose3, Heuristic Min-Conflicts).
- Task 2: 5 tests (Kiểm tra va chạm cell-by-cell của đạn, triệt tiêu đạn đối đầu, va chạm xe, tính tương đương quyết định giữa Minimax và Alpha-Beta, cơ chế nạp động agent).
- Task 3: 14 tests (Kiểm tra CSP formulation, Hall's marriage condition trong Bipartite matching GAC, Forward Checking phục hồi miền, giải nghiệm và tính hiệu quả của heuristic MRV).
- **Tổng cộng: 30/30 PASSED (100%) trong ~0.25 giây.**

---

## 📊 6. SỔ TAY THỰC NGHIỆM (JUPYTER NOTEBOOKS)

Các file sổ tay thực nghiệm đã được chạy và lưu sẵn đầy đủ kết quả, bảng biểu số liệu và biểu đồ:
- `source/task1_nqueens/experiments.ipynb`: So sánh số lượng mệnh đề CNF (Sequential Counter giảm 86% clauses ở $N=50$) và số bước lặp Min-Conflicts (Heuristic đề xuất nhanh hơn 22 lần ở $N=1000$).
- `source/task2_tank/experiments.ipynb`: So sánh 4 cấu hình đối kháng (Alpha-Beta cắt tỉa 70% số node so với Minimax ở $d=2$; Heuristic đạt tỉ lệ thắng 92%).
- `source/task3_kakuro/experiments.ipynb`: Đánh giá GAC/MAC trên các đề 3x3, 5x5 và Complex Test Case (MAC giảm từ 6,468 node xuống còn 12 node và 0 lần quay lui trên đề 5x5).

---

## 📦 7. ĐÓNG GÓI BÀI NỘP TỰ ĐỘNG

Dự án cung cấp công cụ tự động làm sạch cache và đóng gói thành 3 file `.zip` theo đúng quy định đặt tên của môn học: `AI_final_<Mã nhóm>_<MSSV>.zip`:

```bash
python package_submission.py
```

Lệnh này sẽ tự động sinh ra 3 file nộp bài cho từng thành viên:
1. `AI_final_08_524H0121.zip` (Lê Phú)
2. `AI_final_08_524H0095.zip` (Vũ Giang Huy)
3. `AI_final_08_524H0102.zip` (Lê Hoàng Minh Khôi)

Mỗi file nộp bài bao gồm đầy đủ:
- `report.pdf`
- `demo.txt`
- `source/` (mã nguồn hoàn chỉnh, không chứa cache thừa `__pycache__`, `.pytest_cache`, `.git`, `.venv`).
