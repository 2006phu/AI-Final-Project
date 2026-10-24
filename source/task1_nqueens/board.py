class NQueensBoard:
    def __init__(self, n: int):
        if n < 1:
            raise ValueError("Kich thuoc ban co N phai >= 1")
        self.n = n

    def var(self, r: int, c: int) -> int:
        # Anh xa toa do (r, c) sang chi so bien propositional logic (1-based cho DIMACS CNF)
        # r, c chay tu 0 den n - 1 -> var chay tu 1 den n * n
        return r * self.n + c + 1

    def coords(self, var_id: int) -> tuple[int, int]:
        # Anh xa nguoc tu chi so bien (1-based) ve toa do (r, c)
        var_id -= 1
        return divmod(var_id, self.n)

    def is_valid(self, queens: list[int] | set[tuple[int, int]]) -> bool:
        # Kiem tra mot loi giai co dat du N quan hau va khong quan nao tan cong nhau
        # queens co the la:
        # 1. list[int] dai N, trong do queens[c] = r (1 quan/cot nhu Min-Conflicts)
        # 2. set/list cac cap tuple (r, c) (nhu ket qua trich xuat tu SAT Solver)
        queen_coords = []
        if isinstance(queens, list) and len(queens) > 0 and isinstance(queens[0], int):
            if len(queens) != self.n:
                return False
            queen_coords = [(queens[c], c) for c in range(self.n)]
        else:
            queen_coords = list(queens)
            if len(queen_coords) != self.n:
                return False

        rows = set()
        cols = set()
        diag1 = set()  # r - c (duong cheo chinh)
        diag2 = set()  # r + c (duong cheo phu)

        for r, c in queen_coords:
            if not (0 <= r < self.n and 0 <= c < self.n):
                return False
            if r in rows or c in cols or (r - c) in diag1 or (r + c) in diag2:
                return False
            rows.add(r)
            cols.add(c)
            diag1.add(r - c)
            diag2.add(r + c)

        return True

    def render(self, queens: list[int] | set[tuple[int, int]]) -> str:
        # Chuyen loi giai thanh chuoi bieu dien ban co ASCII
        queen_set = set()
        if isinstance(queens, list) and len(queens) > 0 and isinstance(queens[0], int):
            queen_set = {(queens[c], c) for c in range(len(queens))}
        else:
            queen_set = set(queens)

        lines = []
        border = "+" + "---+" * self.n
        lines.append(border)
        for r in range(self.n):
            row_str = "|"
            for c in range(self.n):
                symbol = " Q " if (r, c) in queen_set else " . "
                row_str += symbol + "|"
            lines.append(row_str)
            lines.append(border)
        return "\n".join(lines)
