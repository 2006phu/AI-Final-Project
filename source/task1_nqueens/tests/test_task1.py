import pytest
from task1_nqueens.board import NQueensBoard
from task1_nqueens.cnf_encoder import PairwiseEncoder, SequentialCounterEncoder
from task1_nqueens.sat_solver import SATNQueensSolver
from task1_nqueens.min_conflicts import StandardMinConflicts, HeuristicMinConflicts


def test_board_var_coords_mapping():
    board = NQueensBoard(4)
    # var(r, c) = r * N + c + 1
    assert board.var(0, 0) == 1
    assert board.var(0, 3) == 4
    assert board.var(3, 0) == 13
    assert board.var(3, 3) == 16

    assert board.coords(1) == (0, 0)
    assert board.coords(4) == (0, 3)
    assert board.coords(13) == (3, 0)
    assert board.coords(16) == (3, 3)


def test_board_is_valid():
    board4 = NQueensBoard(4)
    # Hop le cho N=4
    assert board4.is_valid([1, 3, 0, 2]) is True
    assert board4.is_valid({(1, 0), (3, 1), (0, 2), (2, 3)}) is True

    # Khong hop le: trung hang
    assert board4.is_valid([1, 1, 0, 2]) is False
    # Khong hop le: trung duong cheo
    assert board4.is_valid([0, 1, 2, 3]) is False
    # Khong hop le: thieu quan
    assert board4.is_valid([1, 3, 0]) is False


def test_pairwise_encoder_clauses_count():
    # N=4 theo ly thuyet: ALO(4) + AMO_row(24) + AMO_col(24) + AMO_diags(28) = 80
    enc4 = PairwiseEncoder(4)
    clauses4 = enc4.encode()
    assert len(clauses4) == 80
    assert enc4.total_variables() == 16

    # Kiem tra cac duong sinh ra
    lines = enc4.generate_lines()
    assert len(lines["rows"]) == 4
    assert len(lines["cols"]) == 4
    assert len(lines["main_diags"]) == 5  # 2 duong o goc dai 1 bi loai
    assert len(lines["anti_diags"]) == 5


def test_sequential_counter_encoder():
    enc4 = SequentialCounterEncoder(4)
    clauses4 = enc4.encode()
    assert len(clauses4) > 0
    # Tong so bien phai lon hon N^2 do co bien phu s_i
    assert enc4.total_variables() > 16


@pytest.mark.parametrize("n", [4, 5, 8])
def test_sat_solver_both_encoders(n):
    # Kiem tra Glucose3 voi PairwiseEncoder
    p_solver = SATNQueensSolver(PairwiseEncoder(n))
    p_res = p_solver.solve()
    assert p_res.is_satisfiable is True
    assert p_solver.board.is_valid(p_res.solution) is True
    assert len(p_res.solution) == n

    # Kiem tra Glucose3 voi SequentialCounterEncoder
    s_solver = SATNQueensSolver(SequentialCounterEncoder(n))
    s_res = s_solver.solve()
    assert s_res.is_satisfiable is True
    assert s_solver.board.is_valid(s_res.solution) is True
    assert len(s_res.solution) == n


@pytest.mark.parametrize("n", [4, 8, 16])
def test_min_conflicts_solvers(n):
    board = NQueensBoard(n)

    # Standard Min-Conflicts
    std_solver = StandardMinConflicts(n, seed=42)
    std_res = std_solver.solve(max_steps=2000)
    assert std_res.is_solved is True
    assert board.is_valid(std_res.solution) is True

    # Heuristic Min-Conflicts
    heu_solver = HeuristicMinConflicts(n, seed=42)
    heu_res = heu_solver.solve(max_steps=2000)
    assert heu_res.is_solved is True
    assert board.is_valid(heu_res.solution) is True


def test_heuristic_efficiency():
    # Heuristic voi khoi tao Greedy giai N=20 nhanh vuot troi so voi Standard
    board20 = NQueensBoard(20)
    heu_solver = HeuristicMinConflicts(20, seed=123)
    heu_res = heu_solver.solve(max_steps=500)
    assert heu_res.is_solved is True
    assert board20.is_valid(heu_res.solution) is True
    # Heuristic giai N=20 thuong duoi 30 buoc
    assert heu_res.steps_taken < 50
