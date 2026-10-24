import random
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from task1_nqueens.board import NQueensBoard


@dataclass
class MinConflictsResult:
    is_solved: bool
    solution: list[int] | None
    steps_taken: int
    max_steps: int
    solve_time_ms: float
    solver_name: str

    def render(self, board: NQueensBoard) -> str:
        if not self.is_solved or self.solution is None:
            return "Khong tim thay loi giai trong gioi han buoc!"
        return board.render(self.solution)


class MinConflictsSolver(ABC):
    def __init__(self, n: int, seed: int | None = None):
        if n < 4:
            raise ValueError("Min-Conflicts cho N-Queens yeu cau N >= 4")
        self.n = n
        self.board = NQueensBoard(n)
        self.rng = random.Random(seed)

        # 3 mang dem tan suat phuc vu tinh so xung dot trong O(1)
        self.row_counts = [0] * self.n
        self.diag1_counts = [0] * (2 * self.n - 1)  # r - c + n - 1
        self.diag2_counts = [0] * (2 * self.n - 1)  # r + c
        self.queens = [0] * self.n

    def _add_queen(self, r: int, c: int):
        self.row_counts[r] += 1
        self.diag1_counts[r - c + self.n - 1] += 1
        self.diag2_counts[r + c] += 1

    def _remove_queen(self, r: int, c: int):
        self.row_counts[r] -= 1
        self.diag1_counts[r - c + self.n - 1] -= 1
        self.diag2_counts[r + c] -= 1

    def _count_conflicts(self, r: int, c: int) -> int:
        # So quan hau tan cong o (r, c)
        return (
            self.row_counts[r]
            + self.diag1_counts[r - c + self.n - 1]
            + self.diag2_counts[r + c]
        )

    def _get_conflicted_columns(self) -> dict[int, int]:
        # Tra ve dict: {cot: so_xung_dot} cho cac cot dang bi tan cong (> 0 xung dot)
        conflicted = {}
        for c in range(self.n):
            r = self.queens[c]
            # O (r, c) da chua quan hau nen bi dem 3 lan (1 hang, 2 duong cheo)
            attacks = self._count_conflicts(r, c) - 3
            if attacks > 0:
                conflicted[c] = attacks
        return conflicted

    @abstractmethod
    def initialize_state(self):
        # Khoi tao trang thai ban co ban dau
        pass

    @abstractmethod
    def select_variable(self, conflicted_cols: dict[int, int]) -> int:
        # Chien luoc lua chon bien (cot) can thay doi gia tri
        pass

    def on_move_executed(self, col: int, old_row: int, new_row: int):
        # Hook cho phep lop con cap nhat trang thai (vi du: Tabu list)
        pass

    def solve(self, max_steps: int = 1000) -> MinConflictsResult:
        start_time = time.perf_counter()

        # 1. Khoi tao trang thai
        self.row_counts = [0] * self.n
        self.diag1_counts = [0] * (2 * self.n - 1)
        self.diag2_counts = [0] * (2 * self.n - 1)
        self.initialize_state()

        # 2. Vong lap Min-Conflicts
        for step in range(max_steps):
            conflicted_cols = self._get_conflicted_columns()
            if not conflicted_cols:
                solve_time_ms = (time.perf_counter() - start_time) * 1000.0
                return MinConflictsResult(
                    is_solved=True,
                    solution=list(self.queens),
                    steps_taken=step,
                    max_steps=max_steps,
                    solve_time_ms=solve_time_ms,
                    solver_name=self.__class__.__name__,
                )

            # Chon bien (cot) de di chuyen
            col = self.select_variable(conflicted_cols)
            current_row = self.queens[col]

            # Tam thoi bo quan hau khoi cot de danh gia cac hang khac
            self._remove_queen(current_row, col)

            # Tim tap hop cac hang co it xung dot nhat tren cot nay
            min_conflicts = float("inf")
            best_rows = []

            for r in range(self.n):
                conflicts = self._count_conflicts(r, col)
                if conflicts < min_conflicts:
                    min_conflicts = conflicts
                    best_rows = [r]
                elif conflicts == min_conflicts:
                    best_rows.append(r)

            # Pha hoa (tie-break) ngau nhien giua cac hang toi uu nhat
            chosen_row = self.rng.choice(best_rows)
            self._add_queen(chosen_row, col)
            self.queens[col] = chosen_row

            self.on_move_executed(col, current_row, chosen_row)

        # Kiem tra lan cuoi khi het so buoc
        conflicted_cols = self._get_conflicted_columns()
        is_solved = len(conflicted_cols) == 0
        solve_time_ms = (time.perf_counter() - start_time) * 1000.0

        return MinConflictsResult(
            is_solved=is_solved,
            solution=list(self.queens) if is_solved else None,
            steps_taken=max_steps,
            max_steps=max_steps,
            solve_time_ms=solve_time_ms,
            solver_name=self.__class__.__name__,
        )


class StandardMinConflicts(MinConflictsSolver):
    # Thuat toan Min-Conflicts tieu chuan theo bai giang Lecture 08
    # - Khoi tao ngau nhien
    # - Chon ngau nhien 1 bien trong tap cac bien xung dot
    def initialize_state(self):
        for c in range(self.n):
            r = self.rng.randint(0, self.n - 1)
            self.queens[c] = r
            self._add_queen(r, c)

    def select_variable(self, conflicted_cols: dict[int, int]) -> int:
        return self.rng.choice(list(conflicted_cols.keys()))


class HeuristicMinConflicts(MinConflictsSolver):
    # Thuat toan Min-Conflicts cai tien de xuat boi nhom:
    # 1. Greedy Initialization: dat quan lan luot vao hang it xung dot nhat
    # 2. Max-Conflicts Variable Selection: uu tien chon cot co nhieu xung dot nhat
    # 3. Tabu Memory Queue: ngan chan luan phien lap buoc (oscillation)
    def __init__(self, n: int, seed: int | None = None, tabu_size: int = 4):
        super().__init__(n, seed)
        self.tabu_size = tabu_size
        self.tabu_queue = deque(maxlen=tabu_size)

    def initialize_state(self):
        self.tabu_queue.clear()
        # Greedy initialization: dat quan tai hang co it xung dot nhat voi cac quan da dat truoc do
        for c in range(self.n):
            min_c = float("inf")
            best_r = []
            for r in range(self.n):
                conflicts = self._count_conflicts(r, c)
                if conflicts < min_c:
                    min_c = conflicts
                    best_r = [r]
                elif conflicts == min_c:
                    best_r.append(r)
            chosen_r = self.rng.choice(best_r)
            self.queens[c] = chosen_r
            self._add_queen(chosen_r, c)

    def select_variable(self, conflicted_cols: dict[int, int]) -> int:
        # Loc cac cot khong nam trong tabu list
        non_tabu_cols = {
            col: conflicts
            for col, conflicts in conflicted_cols.items()
            if col not in self.tabu_queue
        }

        # Neu tat ca deu bi tabu thi dung lai toan bo conflicted_cols
        candidate_pool = non_tabu_cols if non_tabu_cols else conflicted_cols

        # Chon cot co xung dot lon nhat (Max-Conflicts)
        max_conflict_val = max(candidate_pool.values())
        max_cols = [
            col
            for col, conflicts in candidate_pool.items()
            if conflicts == max_conflict_val
        ]
        return self.rng.choice(max_cols)

    def on_move_executed(self, col: int, old_row: int, new_row: int):
        self.tabu_queue.append(col)
