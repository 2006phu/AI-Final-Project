from enum import Enum
import os


class CellType(Enum):
    WHITE = "white"
    BLACK = "black"
    CLUE = "clue"


class Cell:
    def __init__(
        self,
        r: int,
        c: int,
        cell_type: CellType,
        down_clue: int | None = None,
        across_clue: int | None = None,
        value: int | None = None,
    ):
        self.r = r
        self.c = c
        self.cell_type = cell_type
        self.down_clue = down_clue
        self.across_clue = across_clue
        self.value = value

    @property
    def pos(self) -> tuple[int, int]:
        return (self.r, self.c)

    @property
    def is_white(self) -> bool:
        return self.cell_type == CellType.WHITE

    @property
    def is_clue(self) -> bool:
        return self.cell_type == CellType.CLUE

    @property
    def is_black(self) -> bool:
        return self.cell_type == CellType.BLACK

    def __repr__(self) -> str:
        if self.is_white:
            return f"Cell.White({self.r},{self.c}, val={self.value})"
        elif self.is_clue:
            d_str = str(self.down_clue) if self.down_clue is not None else ""
            a_str = str(self.across_clue) if self.across_clue is not None else ""
            return f"Cell.Clue({self.r},{self.c}, {d_str}\\{a_str})"
        return f"Cell.Black({self.r},{self.c})"


class Run:
    def __init__(
        self,
        run_id: str,
        direction: str,
        clue_coord: tuple[int, int],
        target_sum: int,
        cells: list[tuple[int, int]],
    ):
        self.run_id = run_id
        self.direction = direction.upper()  # "H" hoac "V"
        self.clue_coord = clue_coord
        self.target_sum = target_sum
        self.cells = list(cells)

    @property
    def length(self) -> int:
        return len(self.cells)

    def contains(self, r: int, c: int) -> bool:
        return (r, c) in self.cells

    def __repr__(self) -> str:
        return (
            f"Run({self.run_id}, dir={self.direction}, clue={self.clue_coord}, "
            f"sum={self.target_sum}, len={self.length}, cells={self.cells})"
        )


class KakuroPuzzle:
    def __init__(
        self,
        rows: int,
        cols: int,
        grid: dict[tuple[int, int], Cell],
        white_cells: list[tuple[int, int]],
        horizontal_runs: list[Run],
        vertical_runs: list[Run],
    ):
        self.rows = rows
        self.cols = cols
        self.grid = grid
        self.white_cells = white_cells
        self.horizontal_runs = horizontal_runs
        self.vertical_runs = vertical_runs
        self.runs = horizontal_runs + vertical_runs

        # Anh xa tu o trang toi 2 run chua no: (r, c) -> {"H": h_run, "V": v_run}
        self.cell_to_runs: dict[tuple[int, int], dict[str, Run]] = {}
        for r, c in self.white_cells:
            self.cell_to_runs[(r, c)] = {}

        for h_run in self.horizontal_runs:
            for coord in h_run.cells:
                self.cell_to_runs[coord]["H"] = h_run

        for v_run in self.vertical_runs:
            for coord in v_run.cells:
                self.cell_to_runs[coord]["V"] = v_run

        for coord, run_dict in self.cell_to_runs.items():
            if "H" not in run_dict or "V" not in run_dict:
                raise ValueError(
                    f"O trang {coord} khong thuoc du ca 2 run ngang va doc! H={('H' in run_dict)}, V={('V' in run_dict)}"
                )

        # Kiem tra tinh toan ven tong manh moi (clue integrity)
        is_consistent, sum_h, sum_v = self.verify_clue_integrity()
        if not is_consistent:
            raise ValueError(
                f"Kiem tra tinh hop le cua de that bai: Tong goi y ngang ({sum_h}) != Tong goi y doc ({sum_v})"
            )

    def verify_clue_integrity(self) -> tuple[bool, int, int]:
        sum_h = sum(r.target_sum for r in self.horizontal_runs)
        sum_v = sum(r.target_sum for r in self.vertical_runs)
        return (sum_h == sum_v, sum_h, sum_v)

    def is_solution_valid(self, assignment: dict[tuple[int, int], int]) -> tuple[bool, str]:
        # Kiem tra da gan du cac o trang chua
        for coord in self.white_cells:
            if coord not in assignment:
                return False, f"O {coord} chua duoc gan gia tri"
            val = assignment[coord]
            if not isinstance(val, int) or val < 1 or val > 9:
                return False, f"O {coord} co gia tri khong hop le: {val}"

        # Kiem tra tung run (sum va all-different)
        for run in self.runs:
            vals = [assignment[coord] for coord in run.cells]
            # 1. AllDifferent
            if len(vals) != len(set(vals)):
                return False, f"Run {run.run_id} bi trung chu so: {vals}"
            # 2. Sum
            if sum(vals) != run.target_sum:
                return False, f"Run {run.run_id} tong la {sum(vals)} != muc tieu {run.target_sum}"

        return True, "Loi giai hop le 100%"

    @classmethod
    def from_string(cls, content: str) -> "KakuroPuzzle":
        lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
        if not lines:
            raise ValueError("Du lieu de Kakuro rong")

        grid_tokens = [line.split() for line in lines]
        rows = len(grid_tokens)
        cols = len(grid_tokens[0])

        for r_idx, row in enumerate(grid_tokens):
            if len(row) != cols:
                raise ValueError(
                    f"Hang {r_idx} co so cot ({len(row)}) khong dong nhat voi hang dau ({cols})"
                )

        grid: dict[tuple[int, int], Cell] = {}
        white_cells: list[tuple[int, int]] = []

        for r in range(rows):
            for c in range(cols):
                token = grid_tokens[r][c]
                if token == ".":
                    cell = Cell(r, c, CellType.WHITE)
                    grid[(r, c)] = cell
                    white_cells.append((r, c))
                elif token == "#":
                    cell = Cell(r, c, CellType.BLACK)
                    grid[(r, c)] = cell
                elif "\\" in token:
                    parts = token.split("\\")
                    d_str, a_str = parts[0], parts[1]
                    d_clue = int(d_str) if d_str else None
                    a_clue = int(a_str) if a_str else None
                    if d_clue is None and a_clue is None:
                        cell = Cell(r, c, CellType.BLACK)
                    else:
                        cell = Cell(r, c, CellType.CLUE, down_clue=d_clue, across_clue=a_clue)
                    grid[(r, c)] = cell
                else:
                    raise ValueError(f"Ky tu khong hop le tai ({r}, {c}): '{token}'")

        # 1. Trích xuất các horizontal runs (hàng ngang)
        horizontal_runs: list[Run] = []
        for r in range(rows):
            c = 0
            while c < cols:
                if not grid[(r, c)].is_white:
                    c += 1
                    continue
                start_c = c
                cells: list[tuple[int, int]] = []
                while c < cols and grid[(r, c)].is_white:
                    cells.append((r, c))
                    c += 1
                clue_c = start_c - 1
                if clue_c < 0 or not grid[(r, clue_c)].is_clue or grid[(r, clue_c)].across_clue is None:
                    raise ValueError(
                        f"Day o trang hang {r}, cot {start_c}..{c-1} khong co goi y ngang hop le tai ({r}, {clue_c})"
                    )
                h_run = Run(
                    run_id=f"H_{r}_{clue_c}",
                    direction="H",
                    clue_coord=(r, clue_c),
                    target_sum=grid[(r, clue_c)].across_clue,
                    cells=cells,
                )
                horizontal_runs.append(h_run)

        # 2. Trích xuất các vertical runs (cột dọc)
        vertical_runs: list[Run] = []
        for c in range(cols):
            r = 0
            while r < rows:
                if not grid[(r, c)].is_white:
                    r += 1
                    continue
                start_r = r
                cells: list[tuple[int, int]] = []
                while r < rows and grid[(r, c)].is_white:
                    cells.append((r, c))
                    r += 1
                clue_r = start_r - 1
                if clue_r < 0 or not grid[(clue_r, c)].is_clue or grid[(clue_r, c)].down_clue is None:
                    raise ValueError(
                        f"Day o trang cot {c}, hang {start_r}..{r-1} khong co goi y doc hop le tai ({clue_r}, {c})"
                    )
                v_run = Run(
                    run_id=f"V_{clue_r}_{c}",
                    direction="V",
                    clue_coord=(clue_r, c),
                    target_sum=grid[(clue_r, c)].down_clue,
                    cells=cells,
                )
                vertical_runs.append(v_run)

        return cls(rows, cols, grid, white_cells, horizontal_runs, vertical_runs)

    @classmethod
    def from_file(cls, filepath: str) -> "KakuroPuzzle":
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Khong tim thay file de Kakuro: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return cls.from_string(content)

    def render(self, assignment: dict[tuple[int, int], int] | None = None) -> str:
        lines: list[str] = []
        for r in range(self.rows):
            tokens: list[str] = []
            for c in range(self.cols):
                cell = self.grid[(r, c)]
                if cell.is_white:
                    if assignment and (r, c) in assignment:
                        tokens.append(f"[{assignment[(r, c)]}]")
                    elif cell.value is not None:
                        tokens.append(f"[{cell.value}]")
                    else:
                        tokens.append(" . ")
                elif cell.is_clue:
                    d = str(cell.down_clue) if cell.down_clue is not None else ""
                    a = str(cell.across_clue) if cell.across_clue is not None else ""
                    tokens.append(f"{d}\\{a}")
                else:
                    tokens.append("###")
            lines.append(" ".join(f"{t:>6}" for t in tokens))
        return "\n".join(lines)
