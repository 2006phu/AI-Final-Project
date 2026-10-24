from abc import ABC, abstractmethod
import itertools
from task1_nqueens.board import NQueensBoard


class CNFEncoder(ABC):
    def __init__(self, n: int):
        if n < 1:
            raise ValueError("Kich thuoc ban co N phai >= 1")
        self.n = n
        self.board = NQueensBoard(n)

    def generate_lines(self) -> dict[str, list[list[int]]]:
        # Thuat toan kham pha cac rang buoc tren ban co N x N
        # Gom nhom cac bien tren cung hang, cot, va 2 duong cheo
        rows = []
        for r in range(self.n):
            rows.append([self.board.var(r, c) for c in range(self.n)])

        cols = []
        for c in range(self.n):
            cols.append([self.board.var(r, c) for r in range(self.n)])

        # Duong cheo chinh: cac o co cung gia tri (r - c)
        main_diags = []
        for diff in range(-(self.n - 1), self.n):
            line = []
            for r in range(self.n):
                c = r - diff
                if 0 <= c < self.n:
                    line.append(self.board.var(r, c))
            if len(line) >= 2:
                main_diags.append(line)

        # Duong cheo phu: cac o co cung gia tri (r + c)
        anti_diags = []
        for total in range(2 * self.n - 1):
            line = []
            for r in range(self.n):
                c = total - r
                if 0 <= c < self.n:
                    line.append(self.board.var(r, c))
            if len(line) >= 2:
                anti_diags.append(line)

        return {
            "rows": rows,
            "cols": cols,
            "main_diags": main_diags,
            "anti_diags": anti_diags,
        }

    @abstractmethod
    def encode(self) -> list[list[int]]:
        # Phuong thuc truu tuong sinh tap menh de CNF
        pass

    @abstractmethod
    def total_variables(self) -> int:
        # Tong so luong bien logic (bao gom bien co ban va bien phu neu co)
        pass


class PairwiseEncoder(CNFEncoder):
    def encode(self) -> list[list[int]]:
        lines_dict = self.generate_lines()
        clauses = []

        # 1. At-Least-Once (ALO): Moi hang phai co it nhat 1 quan hau
        for row in lines_dict["rows"]:
            clauses.append(list(row))

        # 2. At-Most-Once (AMO): Moi duong (hang, cot, 2 duong cheo) co toi da 1 quan hau
        # Ma hoa pairwise: voi moi cap bien (u, v) tren cung duong, sinh (-u v -v)
        all_lines = (
            lines_dict["rows"]
            + lines_dict["cols"]
            + lines_dict["main_diags"]
            + lines_dict["anti_diags"]
        )

        for line in all_lines:
            for u, v in itertools.combinations(line, 2):
                clauses.append([-u, -v])

        return clauses

    def total_variables(self) -> int:
        return self.n * self.n


class SequentialCounterEncoder(CNFEncoder):
    # Ma hoa At-Most-Once theo phuong phap Sequential Counter (Sinz, 2005)
    # Dung bien phu s_i de giam so clause tren moi duong tu O(L^2) xuong O(L)
    def __init__(self, n: int):
        super().__init__(n)
        self._total_vars = self.n * self.n

    def encode(self) -> list[list[int]]:
        lines_dict = self.generate_lines()
        clauses = []

        # 1. At-Least-Once (ALO): Moi hang phai co it nhat 1 quan hau
        for row in lines_dict["rows"]:
            clauses.append(list(row))

        # 2. At-Most-Once (AMO) qua bien phu cho tung duong
        all_lines = (
            lines_dict["rows"]
            + lines_dict["cols"]
            + lines_dict["main_diags"]
            + lines_dict["anti_diags"]
        )

        curr_aux = self.n * self.n
        for line in all_lines:
            k = len(line)
            if k == 2:
                # Duong dai 2 chi can 1 clause pairwise: (-x1 v -x2)
                clauses.append([-line[0], -line[1]])
                continue

            # Khoi tao k - 1 bien phu cho duong dai k >= 3
            s = [curr_aux + i + 1 for i in range(k - 1)]
            curr_aux += k - 1

            # Clause dau tien: (-x1 v s1)
            clauses.append([-line[0], s[0]])

            # Cac clause trung gian i tu 1 den k - 2 (ung voi x_2 den x_{k-1})
            for i in range(1, k - 1):
                # (-x_{i+1} v s_{i+1})
                clauses.append([-line[i], s[i]])
                # (-s_i v s_{i+1})
                clauses.append([-s[i - 1], s[i]])
                # (-x_{i+1} v -s_i)
                clauses.append([-line[i], -s[i - 1]])

            # Clause cuoi cung voi x_k: (-x_k v -s_{k-1})
            clauses.append([-line[k - 1], -s[k - 2]])

        self._total_vars = curr_aux
        return clauses

    def total_variables(self) -> int:
        return self._total_vars
