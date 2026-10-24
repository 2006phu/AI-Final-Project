import time
from dataclasses import dataclass
from pysat.solvers import Glucose3
from task1_nqueens.cnf_encoder import CNFEncoder


@dataclass
class SATResult:
    is_satisfiable: bool
    solution: list[tuple[int, int]] | None
    queens_per_col: list[int] | None
    clauses_count: int
    variables_count: int
    solve_time_ms: float
    encoder_name: str

    def render(self, board) -> str:
        if not self.is_satisfiable or self.solution is None:
            return "Khong tim thay loi giai (UNSAT)"
        return board.render(self.solution)


class SATNQueensSolver:
    def __init__(self, encoder: CNFEncoder):
        # Ap dung Dependency Injection: nhan doi tuong ke thua tu CNFEncoder
        self.encoder = encoder
        self.board = encoder.board
        self.n = encoder.n

    def solve(self) -> SATResult:
        clauses = self.encoder.encode()
        clauses_count = len(clauses)
        variables_count = self.encoder.total_variables()

        # Su dung solver Glucose3 tu thu vien PySAT
        with Glucose3() as solver:
            solver.append_formula(clauses)

            start_time = time.perf_counter()
            is_sat = solver.solve()
            solve_time_ms = (time.perf_counter() - start_time) * 1000.0

            if not is_sat:
                return SATResult(
                    is_satisfiable=False,
                    solution=None,
                    queens_per_col=None,
                    clauses_count=clauses_count,
                    variables_count=variables_count,
                    solve_time_ms=solve_time_ms,
                    encoder_name=self.encoder.__class__.__name__,
                )

            model = solver.get_model()
            solution = []
            queens_per_col = [-1] * self.n

            # Loc cac bien duong trong pham vi ban co 1 .. N*N
            # (Loai bo cac bien phu s_i cua Sequential Counter)
            board_var_limit = self.n * self.n
            for lit in model:
                if 1 <= lit <= board_var_limit:
                    r, c = self.board.coords(lit)
                    solution.append((r, c))
                    queens_per_col[c] = r

            # Kiem tra tinh toan ven cua loi giai qua NQueensBoard
            if not self.board.is_valid(solution):
                raise RuntimeError("Loi giai sinh ra tu SAT Solver khong thoa man rang buoc N-Queens!")

            return SATResult(
                is_satisfiable=True,
                solution=solution,
                queens_per_col=queens_per_col,
                clauses_count=clauses_count,
                variables_count=variables_count,
                solve_time_ms=solve_time_ms,
                encoder_name=self.encoder.__class__.__name__,
            )
