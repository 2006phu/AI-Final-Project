import os
import pytest
from task3_kakuro.puzzle import KakuroPuzzle
from task3_kakuro.solver import BacktrackingSolver, EventType


def test_solver_all_strategies_on_3x3():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "simple_3x3.txt")
    puzzle = KakuroPuzzle.from_file(p_path)

    for strat in ["none", "fc", "mac"]:
        solver = BacktrackingSolver(puzzle, strategy=strat, use_mrv=True, use_lcv=True)
        res = solver.solve()
        assert res.is_solved, f"Strategy {strat} failed to solve 3x3"
        valid, msg = puzzle.is_solution_valid(res.solution)
        assert valid, f"Strategy {strat} produced invalid solution: {msg}"


def test_solver_all_strategies_on_5x5():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "example_5x5.txt")
    puzzle = KakuroPuzzle.from_file(p_path)

    # 1. Pure Backtracking (none)
    solver_bt = BacktrackingSolver(puzzle, strategy="none", use_mrv=True)
    res_bt = solver_bt.solve()
    assert res_bt.is_solved
    assert puzzle.is_solution_valid(res_bt.solution)[0]

    # 2. Forward Checking (fc)
    solver_fc = BacktrackingSolver(puzzle, strategy="fc", use_mrv=True)
    res_fc = solver_fc.solve()
    assert res_fc.is_solved
    assert puzzle.is_solution_valid(res_fc.solution)[0]

    # 3. Maintaining Arc Consistency (mac)
    solver_mac = BacktrackingSolver(puzzle, strategy="mac", use_mrv=True)
    res_mac = solver_mac.solve()
    assert res_mac.is_solved
    assert puzzle.is_solution_valid(res_mac.solution)[0]

    # Kiem chung: MAC va FC giam dang ke so node so voi Pure BT
    assert res_mac.nodes_explored <= res_bt.nodes_explored
    assert res_mac.backtracks <= res_bt.backtracks


def test_mrv_heuristic_efficiency():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "example_5x5.txt")
    puzzle = KakuroPuzzle.from_file(p_path)

    # 1. Chay tren Pure BT: Khong dung MRV vs Co dung MRV
    solver_no_mrv = BacktrackingSolver(
        puzzle, strategy="none", use_mrv=False, apply_preprocessing=True
    )
    res_no_mrv = solver_no_mrv.solve()
    assert res_no_mrv.is_solved

    solver_mrv = BacktrackingSolver(
        puzzle, strategy="none", use_mrv=True, apply_preprocessing=True
    )
    res_mrv = solver_mrv.solve()
    assert res_mrv.is_solved

    # MRV giam vuot troi so nodes (1183 nodes -> 71 nodes, giam hon 16 lan)
    assert res_mrv.nodes_explored < res_no_mrv.nodes_explored
    assert res_mrv.backtracks < res_no_mrv.backtracks

    # 2. Chay tren FC (ngay ca khi khong bat tien xu ly): MRV giam manh tu 691 xuong 176 nodes
    s_fc_no = BacktrackingSolver(puzzle, strategy="fc", use_mrv=False, apply_preprocessing=False)
    r_fc_no = s_fc_no.solve()
    s_fc = BacktrackingSolver(puzzle, strategy="fc", use_mrv=True, apply_preprocessing=False)
    r_fc = s_fc.solve()
    assert r_fc.nodes_explored < r_fc_no.nodes_explored


def test_solver_stepwise_generator():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "simple_3x3.txt")
    puzzle = KakuroPuzzle.from_file(p_path)

    solver = BacktrackingSolver(puzzle, strategy="mac", use_mrv=True)
    events = list(solver.solve_stepwise())

    assert len(events) >= 3
    assert events[0].event_type == EventType.DOMAIN_INIT

    # Su kien cuoi cung phai la SOLVED
    last_event = events[-1]
    assert last_event.event_type == EventType.SOLVED

    # Nghiem cuoi cung phai hop le 100%
    is_valid, msg = puzzle.is_solution_valid(last_event.assignment_snapshot)
    assert is_valid, msg
