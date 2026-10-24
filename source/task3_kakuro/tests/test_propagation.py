import os
import pytest
from task3_kakuro.csp import KakuroCSP
from task3_kakuro.propagation import ConstraintPropagator
from task3_kakuro.puzzle import KakuroPuzzle


def test_bipartite_matching():
    # 2 o, mien {1, 2} va {1}
    cells = [(0, 0), (0, 1)]
    domains = {(0, 0): {1, 2}, (0, 1): {1}}
    assert ConstraintPropagator.can_match([1, 2], cells, domains)

    # 2 o deu co mien {1} -> khong the ghep [1, 2]
    domains_invalid = {(0, 0): {1}, (0, 1): {1}}
    assert not ConstraintPropagator.can_match([1, 2], cells, domains_invalid)


def test_run_gac_on_5x5():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "example_5x5.txt")
    puzzle = KakuroPuzzle.from_file(p_path)
    csp = KakuroCSP(puzzle)

    res = ConstraintPropagator.run_gac(csp)
    assert res.success
    assert len(res.pruned) > 0

    # Kiem tra tat ca cac o deu co nghiem don dinh hoac thu hep cuc manh
    for var in csp.variables:
        assert len(csp.domains[var]) >= 1

    # Cac o mau chot duoc xac dinh nghiem don tri
    assert csp.domains[(4, 3)] == {7}
    assert csp.domains[(4, 2)] == {9}
    assert csp.domains[(1, 2)] == {8}
    assert csp.domains[(1, 3)] == {4}


def test_forward_checking_and_restoration():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "example_5x5.txt")
    puzzle = KakuroPuzzle.from_file(p_path)
    csp = KakuroCSP(puzzle)

    var = (1, 2)
    val = 8
    # Snapshot mien ban dau de kiem tra khoi phuc
    initial_domains = {v: set(d) for v, d in csp.domains.items()}

    res = ConstraintPropagator.forward_check(csp, var, val, assignment={var: val})
    assert res.success

    # Hang xom (1, 3) phai khong con so 8 trong mien
    assert val not in csp.domains[(1, 3)]

    # Khoi phuc lai mien gia tri
    ConstraintPropagator.restore_pruned(csp, res.pruned)
    for v in csp.variables:
        assert csp.domains[v] == initial_domains[v]


def test_mac_and_restoration():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "example_5x5.txt")
    puzzle = KakuroPuzzle.from_file(p_path)
    csp = KakuroCSP(puzzle)

    var = (4, 3)
    val = 7
    initial_domains = {v: set(d) for v, d in csp.domains.items()}

    res = ConstraintPropagator.mac(csp, var, val, assignment={var: val})
    assert res.success
    assert csp.domains[(4, 3)] == {7}

    # MAC lan truyen se dan toi (4, 2) buoc phai bang 9
    assert csp.domains[(4, 2)] == {9}

    # Khoi phuc
    ConstraintPropagator.restore_pruned(csp, res.pruned)
    for v in csp.variables:
        assert csp.domains[v] == initial_domains[v]
