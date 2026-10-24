import os
import pytest
from task3_kakuro.csp import CombinationTable, KakuroCSP
from task3_kakuro.puzzle import KakuroPuzzle


def test_combination_table():
    ct = CombinationTable()

    # 1. Cac cap co duy nhat 1 to hop
    c16_2 = ct.get_combinations(16, 2)
    assert len(c16_2) == 1 and frozenset({7, 9}) in c16_2
    assert ct.get_possible_digits(16, 2) == frozenset({7, 9})

    c3_2 = ct.get_combinations(3, 2)
    assert len(c3_2) == 1 and frozenset({1, 2}) in c3_2

    c45_9 = ct.get_combinations(45, 9)
    assert len(c45_9) == 1 and frozenset(range(1, 10)) in c45_9

    # 2. Loc to hop theo cac chu so da gan
    filtered = ct.filter_combinations(
        target_sum=12,
        length=2,
        assigned_digits={4},
        available_digits={3, 4, 5, 7, 8, 9},
    )
    # (12, 2) chua {4} chi co the la {4, 8}
    assert len(filtered) == 1 and frozenset({4, 8}) in filtered


def test_kakuro_csp_initial_pruning():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "example_5x5.txt")
    puzzle = KakuroPuzzle.from_file(p_path)

    csp = KakuroCSP(puzzle, apply_preprocessing=True)

    # O (4, 3): H_run sum 16 (7,9) va V_run sum 14 len 4 (max digit la 8)
    # => Giao mien bat buoc chi con {7}
    assert csp.domains[(4, 3)] == {7}

    # O (4, 2): H_run sum 16 va cot 2 sum 21 len 4
    # Vi (4, 3) chi co the la 7 nen (4, 2) chi con {9}
    assert 9 in csp.domains[(4, 2)]

    # Kiem tra lang gieng cua (1, 2)
    # Cung hang 1: (1, 3); cung cot 2: (2, 2), (3, 2), (4, 2)
    n12 = csp.neighbors[(1, 2)]
    assert (1, 3) in n12
    assert (2, 2) in n12
    assert (3, 2) in n12
    assert (4, 2) in n12
    # Khong chung hang/cot: (2, 1) khong phai lang gieng
    assert (2, 1) not in n12


def test_kakuro_csp_is_consistent():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "example_5x5.txt")
    puzzle = KakuroPuzzle.from_file(p_path)
    csp = KakuroCSP(puzzle)

    assignment = {}

    # 1. Gan gia tri hop le
    assert csp.is_consistent((4, 3), 7, assignment)
    assignment[(4, 3)] = 7

    # 2. Gan (4, 2) = 9 (tong 7 + 9 = 16 hop le cho hang 4)
    assert csp.is_consistent((4, 2), 9, assignment)

    # 3. Gan trung lap cung hang 4 (AllDifferent) -> phai False
    assert not csp.is_consistent((4, 2), 7, assignment)

    # 4. Gan tong vuot qua target_sum -> phai False (7 + 10 khong the, hoac 7 + 8 = 15 < 16 nhung hang chi co 2 o)
    assert not csp.is_consistent((4, 2), 8, assignment)
