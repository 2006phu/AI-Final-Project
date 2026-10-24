import argparse
import sys
import os

# Dam bao import duoc task1_nqueens khi chay file truc tiep
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from task1_nqueens.board import NQueensBoard
from task1_nqueens.cnf_encoder import PairwiseEncoder, SequentialCounterEncoder
from task1_nqueens.sat_solver import SATNQueensSolver
from task1_nqueens.min_conflicts import StandardMinConflicts, HeuristicMinConflicts


def main():
    parser = argparse.ArgumentParser(description="N-Queens Solver (SAT & Min-Conflicts)")
    parser.add_argument("-n", "--size", type=int, default=8, help="Kich thuoc ban co N (N >= 4)")
    parser.add_argument(
        "-m",
        "--method",
        type=str,
        default="sat_pairwise",
        choices=["sat_pairwise", "sat_seq", "mc_standard", "mc_heuristic"],
        help="Thuat toan: sat_pairwise, sat_seq, mc_standard, mc_heuristic",
    )
    parser.add_argument("--max-steps", type=int, default=2000, help="So buoc toi da cho Min-Conflicts")
    parser.add_argument("--seed", type=int, default=42, help="Seed ngau nhien")
    args = parser.parse_args()

    n = args.size
    method = args.method
    board = NQueensBoard(n)

    print("=" * 60)
    print(f" GIAI BAI TOAN N-QUEENS (N = {n})")
    print(f" Phuong phap: {method}")
    print("=" * 60)

    if method == "sat_pairwise":
        encoder = PairwiseEncoder(n)
        solver = SATNQueensSolver(encoder)
        res = solver.solve()
        print(f"So clauses (menh de): {res.clauses_count}")
        print(f"So bien logic: {res.variables_count}")
        print(f"Thoi gian giai: {res.solve_time_ms:.3f} ms")
        print(f"Trang thai: {'SAT (Thanh cong)' if res.is_satisfiable else 'UNSAT'}")
        if res.is_satisfiable:
            print("\nVi tri quan hau theo cot:")
            print(res.queens_per_col)
            if n <= 20:
                print("\nBan co:")
                print(res.render(board))

    elif method == "sat_seq":
        encoder = SequentialCounterEncoder(n)
        solver = SATNQueensSolver(encoder)
        res = solver.solve()
        print(f"So clauses (menh de): {res.clauses_count}")
        print(f"So bien logic (kem bien phu): {res.variables_count}")
        print(f"Thoi gian giai: {res.solve_time_ms:.3f} ms")
        print(f"Trang thai: {'SAT (Thanh cong)' if res.is_satisfiable else 'UNSAT'}")
        if res.is_satisfiable:
            print("\nVi tri quan hau theo cot:")
            print(res.queens_per_col)
            if n <= 20:
                print("\nBan co:")
                print(res.render(board))

    elif method == "mc_standard":
        solver = StandardMinConflicts(n, seed=args.seed)
        res = solver.solve(max_steps=args.max_steps)
        print(f"So buoc thuc hien: {res.steps_taken} / {res.max_steps}")
        print(f"Thoi gian giai: {res.solve_time_ms:.3f} ms")
        print(f"Trang thai: {'Thanh cong' if res.is_solved else 'That bai (vuot qua max_steps)'}")
        if res.is_solved:
            print("\nVi tri quan hau theo cot:")
            print(res.solution)
            if n <= 20:
                print("\nBan co:")
                print(res.render(board))

    elif method == "mc_heuristic":
        solver = HeuristicMinConflicts(n, seed=args.seed)
        res = solver.solve(max_steps=args.max_steps)
        print(f"So buoc thuc hien: {res.steps_taken} / {res.max_steps}")
        print(f"Thoi gian giai: {res.solve_time_ms:.3f} ms")
        print(f"Trang thai: {'Thanh cong' if res.is_solved else 'That bai (vuot qua max_steps)'}")
        if res.is_solved:
            print("\nVi tri quan hau theo cot:")
            print(res.solution)
            if n <= 20:
                print("\nBan co:")
                print(res.render(board))


if __name__ == "__main__":
    main()
