import os
import pytest
from task3_kakuro.puzzle import KakuroPuzzle, CellType


def test_puzzle_parsing_and_integrity_3x3():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "simple_3x3.txt")
    puzzle = KakuroPuzzle.from_file(p_path)

    assert puzzle.rows == 3 and puzzle.cols == 3
    assert len(puzzle.white_cells) == 4
    assert len(puzzle.horizontal_runs) == 2
    assert len(puzzle.vertical_runs) == 2

    is_ok, sum_h, sum_v = puzzle.verify_clue_integrity()
    assert is_ok and sum_h == 10 and sum_v == 10


def test_puzzle_parsing_and_solution_5x5():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "example_5x5.txt")
    puzzle = KakuroPuzzle.from_file(p_path)

    assert puzzle.rows == 5 and puzzle.cols == 5
    assert len(puzzle.white_cells) == 12

    is_ok, sum_h, sum_v = puzzle.verify_clue_integrity()
    assert is_ok and sum_h == 60 and sum_v == 60

    # Kiem tra nghiem hop le
    sol_5x5 = {
        (1, 2): 8, (1, 3): 4,
        (2, 1): 9, (2, 2): 3, (2, 3): 1, (2, 4): 8,
        (3, 1): 5, (3, 2): 1, (3, 3): 2, (3, 4): 3,
        (4, 2): 9, (4, 3): 7,
    }
    is_valid, msg = puzzle.is_solution_valid(sol_5x5)
    assert is_valid

    # Kiem tra phat hien loi sai tong
    sol_invalid_sum = dict(sol_5x5)
    sol_invalid_sum[(1, 2)] = 7  # 7 + 4 = 11 != 12
    is_valid, msg = puzzle.is_solution_valid(sol_invalid_sum)
    assert not is_valid and "tong" in msg.lower()

    # Kiem tra phat hien loi trung lap (AllDifferent)
    sol_duplicate = dict(sol_5x5)
    sol_duplicate[(1, 2)] = 6
    sol_duplicate[(1, 3)] = 6  # 6 + 6 = 12 nhung trung so
    is_valid, msg = puzzle.is_solution_valid(sol_duplicate)
    assert not is_valid and "trung" in msg.lower()


def test_puzzle_parsing_and_solution_complex_9x9():
    p_path = os.path.join(os.path.dirname(__file__), "..", "puzzles", "complex_9x9.txt")
    puzzle = KakuroPuzzle.from_file(p_path)

    assert puzzle.rows == 9 and puzzle.cols == 9
    assert len(puzzle.white_cells) == 48

    is_ok, sum_h, sum_v = puzzle.verify_clue_integrity()
    assert is_ok and sum_h == 249 and sum_v == 249


def test_clue_integrity_failure_detection():
    # De sai tong H != V phai nem ValueError
    invalid_content = """
    #     4\\     6\\
    \\3     .      .
    \\8     .      .
    """
    with pytest.raises(ValueError, match="Kiem tra tinh hop le cua de that bai"):
        KakuroPuzzle.from_string(invalid_content)
