from collections import deque
from task3_kakuro.csp import KakuroCSP
from task3_kakuro.puzzle import Run


class PropagationResult:
    """Ket qua sau khi thuc hien lan truyen rang buoc."""

    def __init__(self, success: bool, pruned: list[tuple[tuple[int, int], int]]):
        self.success = success
        self.pruned = pruned  # Danh sach cac cap (var, value) bi loai bo de khoi phuc khi backtrack

    def __repr__(self) -> str:
        return f"PropagationResult(success={self.success}, pruned_count={len(self.pruned)})"


class ConstraintPropagator:
    """Lop xu ly cac thuat toan lan truyen rang buoc: GAC (AC-3), Forward Checking (FC), va MAC."""

    @staticmethod
    def can_match(
        digits: list[int],
        cells: list[tuple[int, int]],
        domains: dict[tuple[int, int], set[int]],
    ) -> bool:
        """Kiem tra xem co the ghep cap (bipartite matching) giua tap chu so va tap o khong.
        
        Su dung thuat toan duyet duong tang (Augmenting Paths) dam bao dieu kien dinh ly Hall.
        """
        n = len(cells)
        if len(digits) != n:
            return False
        if n == 0:
            return True
        if n == 1:
            return digits[0] in domains[cells[0]]

        match_digit: dict[int, tuple[int, int]] = {}

        def dfs(cell: tuple[int, int], visited: set[tuple[int, int]]) -> bool:
            for d in digits:
                if d in domains[cell]:
                    if d not in match_digit:
                        match_digit[d] = cell
                        return True
                    elif match_digit[d] not in visited:
                        visited.add(match_digit[d])
                        if dfs(match_digit[d], visited):
                            match_digit[d] = cell
                            return True
            return False

        for cell in cells:
            if not dfs(cell, set()):
                return False
        return True

    @classmethod
    def run_gac(
        cls,
        csp: KakuroCSP,
        initial_runs: list[Run] | None = None,
        assignment: dict[tuple[int, int], int] | None = None,
    ) -> PropagationResult:
        """Thuat toan Generalized Arc Consistency (GAC / AC-3 cho rang buoc n-ngoi)."""
        if assignment is None:
            assignment = {}

        queue: deque[Run] = deque(initial_runs if initial_runs is not None else csp.puzzle.runs)
        pruned_history: list[tuple[tuple[int, int], int]] = []

        while queue:
            run = queue.popleft()

            # Revise tung bien chua gan trong run
            for var in run.cells:
                if var in assignment:
                    continue

                to_remove: set[int] = set()
                other_cells = [c for c in run.cells if c != var and c not in assignment]
                assigned_cells = [c for c in run.cells if c in assignment]
                assigned_digits = {assignment[c] for c in assigned_cells}

                combos = csp.comb_table.get_combinations(run.target_sum, run.length)

                for v in list(csp.domains[var]):
                    # 1. Vi pham AllDifferent voi cac o da gan trong cung run
                    if v in assigned_digits:
                        to_remove.add(v)
                        continue

                    # 2. Tim to hop ho tro (supporting combination)
                    has_support = False
                    needed_digits = assigned_digits | {v}
                    for combo in combos:
                        if needed_digits.issubset(combo):
                            rem_digits = list(combo - needed_digits)
                            if cls.can_match(rem_digits, other_cells, csp.domains):
                                has_support = True
                                break

                    if not has_support:
                        to_remove.add(v)

                # Tien hanh loai bo gia tri khong duoc ho tro
                if to_remove:
                    for v in to_remove:
                        csp.domains[var].remove(v)
                        pruned_history.append((var, v))

                    # Neu mien bi rong (Domain Wipeout) -> Mau thuan!
                    if len(csp.domains[var]) == 0:
                        return PropagationResult(success=False, pruned=pruned_history)

                    # Dua run truc giao (orthogonal run) chua var vao hang doi de lan truyen tiep
                    other_run = csp.puzzle.cell_to_runs[var]["V" if run.direction == "H" else "H"]
                    if other_run not in queue:
                        queue.append(other_run)

        return PropagationResult(success=True, pruned=pruned_history)

    @classmethod
    def forward_check(
        cls,
        csp: KakuroCSP,
        var: tuple[int, int],
        value: int,
        assignment: dict[tuple[int, int], int],
    ) -> PropagationResult:
        """Forward Checking (FC): Thu hep mien cua cac bien lang gieng ngay sau khi gan var = value."""
        pruned_history: list[tuple[tuple[int, int], int]] = []

        # 1. Rang buoc AllDifferent: Xoa value khoi mien tat ca lang gieng chua gan
        for neighbor in csp.neighbors[var]:
            if neighbor not in assignment and value in csp.domains[neighbor]:
                csp.domains[neighbor].remove(value)
                pruned_history.append((neighbor, value))
                if len(csp.domains[neighbor]) == 0:
                    return PropagationResult(success=False, pruned=pruned_history)

        # 2. Rang buoc Run: Kiem tra cac o chua gan trong 2 run chua var
        for run in csp.get_runs_for_var(var):
            unassigned_cells = [c for c in run.cells if c not in assignment and c != var]
            if not unassigned_cells:
                continue

            assigned_digits = {
                assignment[c] if c in assignment else value
                for c in run.cells
                if c in assignment or c == var
            }
            combos = csp.comb_table.get_combinations(run.target_sum, run.length)
            possible_combos = [c for c in combos if assigned_digits.issubset(c)]

            if not possible_combos:
                return PropagationResult(success=False, pruned=pruned_history)

            valid_digits_in_run: set[int] = set()
            for c in possible_combos:
                valid_digits_in_run.update(c - assigned_digits)

            # Loai bo cac chu so khong con to hop ho tro khoi cac o chua gan trong run
            for cell in unassigned_cells:
                to_remove = csp.domains[cell] - valid_digits_in_run
                for v in to_remove:
                    csp.domains[cell].remove(v)
                    pruned_history.append((cell, v))
                if len(csp.domains[cell]) == 0:
                    return PropagationResult(success=False, pruned=pruned_history)

        return PropagationResult(success=True, pruned=pruned_history)

    @classmethod
    def mac(
        cls,
        csp: KakuroCSP,
        var: tuple[int, int],
        value: int,
        assignment: dict[tuple[int, int], int],
    ) -> PropagationResult:
        """Maintaining Arc Consistency (MAC): Chay GAC lan truyen toan dien bat dau tu cac run chua var."""
        pruned_history: list[tuple[tuple[int, int], int]] = []

        # Dat mien cua var thanh duy nhat {value}
        other_values = [v for v in csp.domains[var] if v != value]
        for v in other_values:
            csp.domains[var].remove(v)
            pruned_history.append((var, v))

        # Lan truyen GAC bat dau tu 2 run chua var
        initial_runs = csp.get_runs_for_var(var)
        gac_res = cls.run_gac(csp, initial_runs=initial_runs, assignment=assignment)
        pruned_history.extend(gac_res.pruned)

        return PropagationResult(success=gac_res.success, pruned=pruned_history)

    @staticmethod
    def restore_pruned(
        csp: KakuroCSP, pruned: list[tuple[tuple[int, int], int]]
    ) -> None:
        """Khoi phuc cac gia tri da bi cat tia ve lai mien gia tri khi quay lui (Backtrack)."""
        for var, value in reversed(pruned):
            csp.domains[var].add(value)
