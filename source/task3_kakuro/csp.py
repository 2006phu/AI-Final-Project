import itertools
from task3_kakuro.puzzle import KakuroPuzzle, Run


class CombinationTable:
    """Bang tra cuu to hop cac chu so (1..9) cho truoc tong va do dai.
    
    Tien xu ly 1 lan duy nhat de tra cuu O(1) cac tap chu so hop le.
    """

    def __init__(self):
        # (target_sum, length) -> list[frozenset[int]]
        self._table: dict[tuple[int, int], list[frozenset[int]]] = {}
        # (target_sum, length) -> frozenset[int] (hop tat ca chu so xuat hien trong cac to hop)
        self._digits_cache: dict[tuple[int, int], frozenset[int]] = {}

        for length in range(1, 10):
            for combo in itertools.combinations(range(1, 10), length):
                s = sum(combo)
                key = (s, length)
                if key not in self._table:
                    self._table[key] = []
                self._table[key].append(frozenset(combo))

        for key, combos in self._table.items():
            all_digits: set[int] = set()
            for c in combos:
                all_digits.update(c)
            self._digits_cache[key] = frozenset(all_digits)

    def get_combinations(self, target_sum: int, length: int) -> list[frozenset[int]]:
        return self._table.get((target_sum, length), [])

    def get_possible_digits(self, target_sum: int, length: int) -> frozenset[int]:
        return self._digits_cache.get((target_sum, length), frozenset())

    def filter_combinations(
        self,
        target_sum: int,
        length: int,
        assigned_digits: set[int],
        available_digits: set[int],
    ) -> list[frozenset[int]]:
        valid_combos = []
        for combo in self.get_combinations(target_sum, length):
            # Phai chua tat ca cac chu so da gan
            if not assigned_digits.issubset(combo):
                continue
            # Cac chu so con lai trong combo phai nam trong tap chu so kha dung
            rem_digits = combo - assigned_digits
            if not rem_digits.issubset(available_digits):
                continue
            valid_combos.append(combo)
        return valid_combos


class KakuroCSP:
    """Mo hinh hoa bai toan Kakuro duoi dang Constraint Satisfaction Problem (CSP)."""

    def __init__(self, puzzle: KakuroPuzzle, apply_preprocessing: bool = True):
        self.puzzle = puzzle
        self.variables = list(puzzle.white_cells)
        self.comb_table = CombinationTable()

        # Xay dung do thi lang gieng (neighbors)
        # Lang gieng cua 1 o trang la tat ca cac o cung thuoc H_run hoac V_run
        self.neighbors: dict[tuple[int, int], set[tuple[int, int]]] = {
            var: set() for var in self.variables
        }
        for run in puzzle.runs:
            for cell_a in run.cells:
                for cell_b in run.cells:
                    if cell_a != cell_b:
                        self.neighbors[cell_a].add(cell_b)

        # Khoi tao mien gia tri (domains)
        self.domains: dict[tuple[int, int], set[int]] = {
            var: set(range(1, 10)) for var in self.variables
        }

        # Tien xu ly thu hep mien gia tri ban dau bang bang to hop
        if apply_preprocessing:
            self.apply_initial_preprocessing()

    def apply_initial_preprocessing(self) -> bool:
        """Thu hep mien ban dau: Domain(var) = Digits(H_run) ∩ Digits(V_run)."""
        for var in self.variables:
            h_run = self.puzzle.cell_to_runs[var]["H"]
            v_run = self.puzzle.cell_to_runs[var]["V"]

            h_digits = self.comb_table.get_possible_digits(h_run.target_sum, h_run.length)
            v_digits = self.comb_table.get_possible_digits(v_run.target_sum, v_run.length)

            intersect = self.domains[var] & h_digits & v_digits
            if not intersect:
                return False
            self.domains[var] = set(intersect)
        return True

    def get_runs_for_var(self, var: tuple[int, int]) -> list[Run]:
        return [self.puzzle.cell_to_runs[var]["H"], self.puzzle.cell_to_runs[var]["V"]]

    def get_unassigned_neighbors(
        self, var: tuple[int, int], assignment: dict[tuple[int, int], int]
    ) -> list[tuple[int, int]]:
        return [n for n in self.neighbors[var] if n not in assignment]

    def is_consistent(
        self, var: tuple[int, int], value: int, assignment: dict[tuple[int, int], int]
    ) -> bool:
        # 1. Kiem tra rang buoc AllDifferent voi cac bien lang gieng da gan
        for neighbor in self.neighbors[var]:
            if neighbor in assignment and assignment[neighbor] == value:
                return False

        # 2. Kiem tra rang buoc tong tren ca run ngang va run doc chua bien nay
        for run in self.get_runs_for_var(var):
            assigned_in_run: list[int] = []
            unassigned_count = 0

            for cell in run.cells:
                if cell == var:
                    assigned_in_run.append(value)
                elif cell in assignment:
                    assigned_in_run.append(assignment[cell])
                else:
                    unassigned_count += 1

            current_sum = sum(assigned_in_run)

            # Truong hop 1: Run da duoc gan du toan bo cac o
            if unassigned_count == 0:
                if current_sum != run.target_sum:
                    return False
            # Truong hop 2: Run con cac o chua gan
            else:
                if current_sum >= run.target_sum:
                    return False

                remaining_sum = run.target_sum - current_sum
                # Tap cac chu so con lai chua dung trong run
                used_set = set(assigned_in_run)
                available = [d for d in range(1, 10) if d not in used_set]

                if len(available) < unassigned_count:
                    return False

                # Tong nho nhat co the co cua unassigned_count chu so con lai
                min_sum = sum(available[:unassigned_count])
                # Tong lon nhat co the co cua unassigned_count chu so con lai
                max_sum = sum(available[-unassigned_count:])

                if remaining_sum < min_sum or remaining_sum > max_sum:
                    return False

                # Kiem tra xem co ton tai to hop hop le nao trong CombinationTable chua day du tap used_set khong
                combos = self.comb_table.get_combinations(run.target_sum, run.length)
                has_supporting_combo = False
                for combo in combos:
                    if used_set.issubset(combo):
                        has_supporting_combo = True
                        break
                if not has_supporting_combo:
                    return False

        return True

    def is_complete(self, assignment: dict[tuple[int, int], int]) -> bool:
        return len(assignment) == len(self.variables)

    def clone(self) -> "KakuroCSP":
        new_csp = KakuroCSP.__new__(KakuroCSP)
        new_csp.puzzle = self.puzzle
        new_csp.variables = self.variables
        new_csp.neighbors = self.neighbors
        new_csp.comb_table = self.comb_table
        new_csp.domains = {var: set(vals) for var, vals in self.domains.items()}
        return new_csp
