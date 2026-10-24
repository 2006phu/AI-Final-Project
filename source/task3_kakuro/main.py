import argparse
import os
import sys

# Dam bao import duoc task3_kakuro tu source/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from task3_kakuro.gui import KakuroGUI
from task3_kakuro.puzzle import KakuroPuzzle
from task3_kakuro.solver import BacktrackingSolver


def run_headless_solver(puzzle_path: str, strategy: str, use_mrv: bool, use_lcv: bool):
    print("=" * 60)
    print(" GIAI KAKURO CSP (HEADLESS / CONSOLE MODE)")
    print(f" File de   : {os.path.basename(puzzle_path)}")
    print(f" Thuat toan: {strategy.upper()} (MRV={use_mrv}, LCV={use_lcv})")
    print("=" * 60)

    puzzle = KakuroPuzzle.from_file(puzzle_path)
    solver = BacktrackingSolver(
        puzzle, strategy=strategy, use_mrv=use_mrv, use_lcv=use_lcv
    )
    result = solver.solve()

    if result.is_solved:
        print(">> KET QUA: TIM THAY LOI GIAI HOP LE 100%!")
        print(f">> So nut da duyet (Nodes)    : {result.nodes_explored}")
        print(f">> So lan quay lui (Backtracks): {result.backtracks}")
        print(f">> So gia tri bi cat (Prunings): {result.prunings_count}")
        print(f">> Thoi gian thuc thi          : {result.solve_time_ms:.2f} ms")
        print("\nBAN CO KET QUA:")
        print(puzzle.render(result.solution))
    else:
        print(">> KET QUA: KHONG TIM THAY LOI GIAI!")
        print(f">> So nut da duyet: {result.nodes_explored}")
        print(f">> Thoi gian     : {result.solve_time_ms:.2f} ms")
    print("=" * 60)


def main():
    base_dir = os.path.dirname(__file__)
    puzzles_dir = os.path.join(base_dir, "puzzles")
    default_puzzle = os.path.join(puzzles_dir, "example_5x5.txt")

    parser = argparse.ArgumentParser(description="Kakuro CSP Solver & Visualizer (AI Final Project)")
    parser.add_argument("--puzzle", type=str, default=default_puzzle, help="Duong dan file de Kakuro (.txt)")
    parser.add_argument("--strategy", type=str, default="mac", choices=["mac", "fc", "none"], help="Chien luoc lan truyen: mac, fc, none")
    parser.add_argument("--no-mrv", action="store_true", help="Tat heuristic MRV + Degree")
    parser.add_argument("--no-lcv", action="store_true", help="Tat heuristic LCV")
    parser.add_argument("--headless", action="store_true", help="Chay console mode khong mo Pygame GUI")
    args = parser.parse_args()

    if args.headless:
        run_headless_solver(
            args.puzzle,
            strategy=args.strategy,
            use_mrv=not args.no_mrv,
            use_lcv=not args.no_lcv,
        )
    else:
        # Khoi dong GUI truc quan: Chi can 1 lenh chay 'python source/task3_kakuro/main.py'
        # Toan bo thao tac chon de, chon thuat toan, Play/Pause, Step, Reset, Chinh toc do
        # deu duoc thao tac 100% truc tiep tren man hinh GUI bang chuot!
        gui = KakuroGUI(puzzles_dir, initial_puzzle_path=args.puzzle)
        gui.run()


if __name__ == "__main__":
    main()
