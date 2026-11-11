# DO AN CUOI KY: NHAP MON TRI TUE NHAN TAO (503043)

**Truong Dai hoc Ton Duc Thang (TDTU) - Khoa Cong nghe Thong tin**  
**Hoc ky 1 - Nam hoc 2026-2027**  
**Giang vien Huong dan:** ThS. Nguyen Thanh An (`nguyenthanhan@tdtu.edu.vn`)

---

## THONG TIN NHOM THUC HIEN (NHOM 08)

| STT | Ho va Ten | Ma so Sinh vien (MSSV) | Vai tro | Goi nop bai tuong ung |
| :---: | :--- | :---: | :---: | :--- |
| 1 | **Le Phu** | `524H0121` | Truong nhom | `AI_final_08_524H0121.zip` |
| 2 | **Vu Giang Huy** | `524H0095` | Thanh vien | `AI_final_08_524H0095.zip` |
| 3 | **Le Hoang Minh Khoi** | `524H0102` | Thanh vien | `AI_final_08_524H0102.zip` |

---

## TONG QUAN 3 BAI TOAN COT LOI

Do an trien khai day du 3 nhom ky thuat nen tang cua Tri tue Nhan tao tren 3 bai toan doc lap, tich hop trong mot giao dien dieu khien trung tam (**Master Arcade Hub**):

1. **Task 1 - Bai toan N-Queens (Propositional Logic SAT & Heuristic Local Search):**
   - Mo hinh hoa bai toan $N$-Queens duoi dang menh de logic CNF (`Pairwise` $O(N^3)$ va `Sequential Counter` $O(N^2)$) giai bang bo giai SAT `Glucose3` (`python-sat`).
   - Thiet ke va cai dat thuat toan tim kiem cuc bo **Heuristic Min-Conflicts** (ket hop Khoi tao tham lam `Greedy Init`, uu tien chon quan hau xung dot cuc dai va hang doi `Tabu Search` ngan chu trinh lap), giup tang toc do hoi tu gap **22.5 lan** tai $N=1000$ so voi Min-Conflicts tieu chuan.

2. **Task 2 - Tro choi Chien dau Xe tang Battle Tank (Zero-Sum Game & Adversarial Search):**
   - Mo hinh hoa tro choi doi khang 2 nguoi choi tren luoi toan hoc Zero-Sum Game voi day du co che vat ly: dan bay 3 o/chu ky kiem tra va cham tung o (cell-by-cell), hai vien dan doi dau triet tieu nhau, tuong gach 3 HP, tuong thep bat tu (`#`) va dia hinh rung cay (`T`) an nap nguy trang.
   - Cai dat va doi sanh 4 cau hinh tim kiem doi khang: **Minimax**, **Alpha-Beta Pruning**, **Heuristic Minimax**, va **Heuristic Alpha-Beta** (ung dung `BFS Pathfinding`, `Move Ordering`, `Transposition Table`, va co che chong be tac `Anti-Stalemate Flanking` tren cac ban do chien thuat da dang).

3. **Task 3 - Tro choi Kakuro (Constraint Satisfaction Problem & Constraint Propagation):**
   - Mo hinh hoa Kakuro duoi dang bai toan CSP voi bang phan tich to hop (`CombinationTable`) tien xu ly mien gia tri ban dau.
   - Trien khai day du cac chien luoc tim kiem quay lui: **Pure Backtracking (BT)**, **Forward Checking (BT + FC)**, va **Maintaining Arc Consistency (BT + MAC)** su dung cap ghep cuc dai tren do thi hai phia (**Bipartite Matching**) de duy tri **Generalized Arc Consistency (GAC)** tren rang buoc toan cuc `AllDifferent + Sum`, ket hop voi bo 3 heuristics **MRV + Degree + LCV**.

---

## CAU TRUC THU MUC DU AN

```text
source/
├── main.py                      # Giao dien trung tam Master Arcade Hub (1-Click Demo & 3 Task Hubs)
├── requirements.txt             # Danh sach thu vien Python can thiet
├── requirement.txt              # Ban sao tuong thich ten file theo dac ta de bai
├── README.md                    # Tai lieu huong dan cai dat va van hanh he thong
│
├── task1_nqueens/               # [TASK 1] N-Queens: SAT Glucose3 & Heuristic Min-Conflicts
│   ├── board.py                 # bieu dien ban co N x N va kiem tra xung dot O(1)
│   ├── cnf_encoder.py           # Bo ma hoa CNF: Pairwise O(N^3) va Sequential Counter O(N^2)
│   ├── sat_solver.py            # Tich hop bo giai Glucose3 (PySAT)
│   ├── min_conflicts.py         # Standard Min-Conflicts va Heuristic Min-Conflicts (Greedy + Tabu)
│   ├── gui.py                   # Giao dien truc quan hoa N-Queens bang Pygame
│   ├── main.py                  # Giao dien dong lenh (CLI) va khoi chay GUI Task 1
│   ├── experiments.ipynb        # Jupyter Notebook thuc nghiem, bang bieu va do thi Task 1
│   └── tests/                   # Unit Tests kiem dinh Task 1 (11 tests)
│
├── task2_tank/                  # [TASK 2] Battle Tank: Zero-Sum Game & Adversarial Search
│   ├── entities.py              # Dinh nghia Tank, Base, Wall (Brick/Steel), Bullet, Direction, Action
│   ├── game_state.py            # Quan ly trang thai ban do, doc file map va state_key hashing
│   ├── engine.py                # Game Engine xu ly luot di dong thoi va dan bay 3 o/chu ky
│   ├── heuristic.py             # Ham danh gia Zero-Sum TankEvaluator & BFS Pathfinding
│   ├── agents/                  # Cac Agent: SearchAgent (Minimax/Alpha-Beta), Random, Human & 4 Custom Agents
│   ├── maps/                    # 7 ban do chien thuat (.txt), bao gom dia hinh rung cay Battle City
│   ├── gui.py                   # Giao dien dau truong xe tang Pygame + nap dong Custom Agent
│   ├── main.py                  # CLI mo phong headless hoac khoi chay GUI Task 2
│   ├── experiments.ipynb        # Jupyter Notebook thuc nghiem va giai dau vong tron Task 2
│   └── tests/                   # Unit Tests kiem dinh Task 2 (10 tests)
│
└── task3_kakuro/                # [TASK 3] Kakuro CSP: Backtracking, FC, MAC (GAC) & Heuristics
    ├── puzzle.py                # Bo phan tich cu phap ma tran Kakuro (.txt) va kiem tra Clue Integrity
    ├── csp.py                   # Mo hinh CSP, CombinationTable va tien xu ly thu hep mien
    ├── propagation.py           # Lan truyen rang buoc FC, GAC (Bipartite Matching) va MAC
    ├── solver.py                # BacktrackingSolver ho tro MRV, Degree, LCV va Stepwise Generator
    ├── puzzles/                 # Cac de Kakuro chuan (.txt): example_3x3, example_5x5, complex_9x9, medium_7x7
    ├── gui.py                   # Giao dien giai Kakuro tung buoc (Step-by-step Animation) bang Pygame
    ├── main.py                  # CLI giai Kakuro va doi sanh chien luoc hoac mo GUI Task 3
    ├── experiments.ipynb        # Jupyter Notebook thuc nghiem va bieu do Task 3
    └── tests/                   # Unit Tests kiem dinh Task 3 (15 tests)
```

---

## YEU CAU HE THONG VA CAI DAT THU VIEN

- **Phien ban Python:** Python `3.10` tro len (khuyen nghi Python `3.11+`).
- **Cai dat thu vien:** Mo Terminal / PowerShell tai thu muc goc (hoac thu muc `source/`) va chay:

```bash
pip install -r source/requirements.txt
```

*(Hoac `pip install -r requirements.txt` neu dang dung ben trong thu muc `source/`).*

---

## HUONG DAN KHOI CHAY NHANH (QUICK START)

### Cach 1: Khoi chay Master Arcade Hub (Khuyen nghi)
Chay 1 lenh duy nhat de mo bang dieu khien do hoa trung tam tich hop ca 3 Task, bieu do thuc nghiem va che do **1-Click Pipeline Test**:

```bash
python source/main.py
```

Hoac chay truc tiep che do tu dong kiem tra toan bo 3 Task ngay khi mo:

```bash
python source/main.py --1click
```

*(Tren Windows co the nhay dup chuot vao file `run.bat` hoac `run_1click.bat`).*

---

### Cach 2: Khoi chay Giao dien Do hoa (GUI) rieng cho tung Task

```bash
# Giao dien Task 1 (N-Queens Visualizer)
python source/task1_nqueens/gui.py

# Giao dien Task 2 (Battle Tank Arena)
python source/task2_tank/gui.py

# Giao dien Task 3 (Kakuro Step-by-Step CSP Visualizer)
python source/task3_kakuro/gui.py
```

---

### Cach 3: Chay qua Giao dien Dong lenh (CLI / Headless)

#### 1. Task 1 (N-Queens)
```bash
# Giai N-Queens N=8 bang SAT Glucose3 voi ma hoa Sequential Counter
python source/task1_nqueens/main.py -n 8 -m sat_seq

# Giai N-Queens N=100 bang Heuristic Min-Conflicts
python source/task1_nqueens/main.py -n 100 -m mc_heuristic
```

#### 2. Task 2 (Battle Tank)
```bash
# Mo phong tran dau Headless giua Heuristic Alpha-Beta (P1) va RandomAgent (P2)
python source/task2_tank/main.py --headless --p1 heuristic_ab --p2 random --depth 2 --turns 100

# Mo phong tran dau giua Heuristic Alpha-Beta (P1) va Minimax (P2) tren ban do chien thuat Tactical Clash
python source/task2_tank/main.py --headless --map source/task2_tank/maps/tactical_clash_13x13.txt --p1 hab --p2 mm --turns 100
```

#### 3. Task 3 (Kakuro CSP)
```bash
# Giai de 5x5 bang Backtracking + MAC + MRV + LCV
python source/task3_kakuro/main.py --puzzle source/task3_kakuro/puzzles/example_5x5.txt --strategy mac

# Giai de 9x9 phuc tap va so sanh toan bo cac chien luoc CSP
python source/task3_kakuro/main.py --puzzle source/task3_kakuro/puzzles/complex_9x9.txt --compare
```

---

## KIEM THU TU DONG (UNIT TESTS) VA THUC NGHIEM

### 1. Chay bo Unit Tests (36/36 tests)
He thong bao gom **36 unit tests** kiem thu toan dien logic cua ca 3 Task (CNF encoding, SAT solver, Min-Conflicts, Tank physics, 3-cell bullet flight, state hashing, 4 custom agents, Kakuro parser, GAC bipartite matching, FC/MAC restoration):

```bash
python -m pytest source/ -v
```

### 2. Chay lai cac Jupyter Notebooks Thuc nghiem
Ba file `experiments.ipynb` trong tung thu muc task chua toan bo so lieu va bieu do trong bao cao:
- `source/task1_nqueens/experiments.ipynb`
- `source/task2_tank/experiments.ipynb`
- `source/task3_kakuro/experiments.ipynb`
