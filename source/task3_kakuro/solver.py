from collections.abc import Generator
from enum import Enum
import time
from task3_kakuro.csp import KakuroCSP
from task3_kakuro.propagation import ConstraintPropagator, PropagationResult
from task3_kakuro.puzzle import KakuroPuzzle


class PropagationStrategy(Enum):
    NONE = "none"
    FC = "fc"
    MAC = "mac"


class EventType(Enum):
    DOMAIN_INIT = "domain_init"
    ASSIGN = "assign"
    PRUNE = "prune"
    UNASSIGN = "unassign"
    RESTORE = "restore"
    SOLVED = "solved"
    FAILED = "failed"


class SolverEvent:
    """Su kien duoc phat ra boi Generator de dieu khien giao dien truc quan Pygame."""

    def __init__(
        self,
        event_type: EventType,
        var: tuple[int, int] | None = None,
        value: int | None = None,
        pruned: list[tuple[tuple[int, int], int]] | None = None,
        message: str = "",
        assignment_snapshot: dict[tuple[int, int], int] | None = None,
        domains_snapshot: dict[tuple[int, int], set[int]] | None = None,
    ):
        self.event_type = event_type
        self.var = var
        self.value = value
        self.pruned = pruned or []
        self.message = message
        self.assignment_snapshot = dict(assignment_snapshot) if assignment_snapshot else {}
        self.domains_snapshot = (
            {v: set(d) for v, d in domains_snapshot.items()} if domains_snapshot else {}
        )

    def __repr__(self) -> str:
        return f"SolverEvent({self.event_type.name}, var={self.var}, val={self.value}, msg='{self.message}')"


class SolverResult:
    """Dong goi ket qua giai cua thuat toan Backtracking."""

    def __init__(
        self,
        is_solved: bool,
        solution: dict[tuple[int, int], int],
        nodes_explored: int,
        backtracks: int,
        prunings_count: int,
        solve_time_ms: float,
        strategy: str,
        use_mrv: bool,
        use_lcv: bool,
    ):
        self.is_solved = is_solved
        self.solution = solution
        self.nodes_explored = nodes_explored
        self.backtracks = backtracks
        self.prunings_count = prunings_count
        self.solve_time_ms = solve_time_ms
        self.strategy = strategy
        self.use_mrv = use_mrv
        self.use_lcv = use_lcv

    def __repr__(self) -> str:
        return (
            f"SolverResult(solved={self.is_solved}, nodes={self.nodes_explored}, "
            f"backtracks={self.backtracks}, time={self.solve_time_ms:.2f}ms)"
        )


class BacktrackingSolver:
    """Bo giai Backtracking tim kiem loi giai Kakuro ho tro day du FC, MAC, MRV, Degree, LCV."""

    def __init__(
        self,
        puzzle: KakuroPuzzle,
        strategy: str = "mac",
        use_mrv: bool = True,
        use_degree: bool = True,
        use_lcv: bool = True,
        apply_preprocessing: bool = True,
    ):
        self.puzzle = puzzle
        self.strategy = strategy.lower()  # "none", "fc", "mac"
        self.use_mrv = use_mrv
        self.use_degree = use_degree
        self.use_lcv = use_lcv
        self.apply_preprocessing = apply_preprocessing

    def _select_variable(
        self, csp: KakuroCSP, assignment: dict[tuple[int, int], int]
    ) -> tuple[int, int]:
        unassigned = [v for v in csp.variables if v not in assignment]
        if not self.use_mrv:
            return unassigned[0]

        # MRV: Chon bien co mien gia tri con lai it nhat
        # Degree Heuristic: Pha hoa (tie-breaker) bang bien co nhieu lang gieng chua gan nhat
        # Tọa độ (r, c) de dam bao tinh xac dinh (deterministic) tuyet doi
        if self.use_degree:
            return min(
                unassigned,
                key=lambda v: (
                    len(csp.domains[v]),
                    -len(csp.get_unassigned_neighbors(v, assignment)),
                    v[0],
                    v[1],
                ),
            )
        else:
            return min(
                unassigned,
                key=lambda v: (len(csp.domains[v]), v[0], v[1]),
            )

    def _order_values(
        self,
        csp: KakuroCSP,
        var: tuple[int, int],
        assignment: dict[tuple[int, int], int],
    ) -> list[int]:
        vals = sorted(csp.domains[var])
        if not self.use_lcv:
            return vals

        # LCV (Least Constraining Value): Uu tien gia tri it loai bo mien cua lang gieng nhat
        def count_conflicts(val: int) -> int:
            conflicts = 0
            for neighbor in csp.get_unassigned_neighbors(var, assignment):
                if val in csp.domains[neighbor]:
                    conflicts += 1
            return conflicts

        return sorted(vals, key=count_conflicts)

    def solve(self) -> SolverResult:
        """Che do giai truc tiep (Fast Batch Mode) cho thuc nghiem, notebook va benchmark."""
        csp = KakuroCSP(self.puzzle, apply_preprocessing=self.apply_preprocessing)

        nodes_explored = 0
        backtracks = 0
        prunings_count = 0
        t0 = time.perf_counter()

        # Tien xu ly GAC khoi dau neu strategy la MAC
        if self.strategy == "mac":
            gac_res = ConstraintPropagator.run_gac(csp)
            prunings_count += len(gac_res.pruned)
            if not gac_res.success:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                return SolverResult(
                    False, {}, nodes_explored, backtracks, prunings_count, elapsed_ms,
                    self.strategy, self.use_mrv, self.use_lcv
                )

        assignment: dict[tuple[int, int], int] = {}

        def backtrack_recursive() -> bool:
            nonlocal nodes_explored, backtracks, prunings_count

            if csp.is_complete(assignment):
                return True

            var = self._select_variable(csp, assignment)
            for val in self._order_values(csp, var, assignment):
                nodes_explored += 1

                if not csp.is_consistent(var, val, assignment):
                    continue

                assignment[var] = val

                # Lan truyen rang buoc
                if self.strategy == "mac":
                    prop_res = ConstraintPropagator.mac(csp, var, val, assignment)
                elif self.strategy == "fc":
                    prop_res = ConstraintPropagator.forward_check(csp, var, val, assignment)
                else:
                    prop_res = PropagationResult(success=True, pruned=[])

                prunings_count += len(prop_res.pruned)

                if prop_res.success:
                    if backtrack_recursive():
                        return True

                # Quay lui (Backtrack)
                backtracks += 1
                if prop_res.pruned:
                    ConstraintPropagator.restore_pruned(csp, prop_res.pruned)
                del assignment[var]

            return False

        is_solved = backtrack_recursive()
        elapsed_ms = (time.perf_counter() - t0) * 1000

        return SolverResult(
            is_solved,
            assignment if is_solved else {},
            nodes_explored,
            backtracks,
            prunings_count,
            elapsed_ms,
            self.strategy,
            self.use_mrv,
            self.use_lcv,
        )

    def solve_stepwise(self) -> Generator[SolverEvent, None, None]:
        """Che do giai tung buoc (Generator Mode) phat ra SolverEvent de giao dien Pygame ve lai."""
        csp = KakuroCSP(self.puzzle, apply_preprocessing=self.apply_preprocessing)

        # 1. Phat su kien khoi tao mien ban dau
        yield SolverEvent(
            EventType.DOMAIN_INIT,
            message="Khoi tao mien gia tri cac o trang",
            domains_snapshot=csp.domains,
        )

        # 2. Tien xu ly GAC khoi dau neu chon MAC
        if self.strategy == "mac":
            gac_res = ConstraintPropagator.run_gac(csp)
            if gac_res.pruned:
                yield SolverEvent(
                    EventType.PRUNE,
                    pruned=gac_res.pruned,
                    message=f"GAC khoi dau: cat tia {len(gac_res.pruned)} gia tri",
                    domains_snapshot=csp.domains,
                )
            if not gac_res.success:
                yield SolverEvent(EventType.FAILED, message="Domain Wipeout ngay khi chay GAC!")
                return

        assignment: dict[tuple[int, int], int] = {}

        def backtrack_gen() -> Generator[SolverEvent, None, bool]:
            if csp.is_complete(assignment):
                yield SolverEvent(
                    EventType.SOLVED,
                    message="Da tim thay nghiem hop le 100%!",
                    assignment_snapshot=assignment,
                    domains_snapshot=csp.domains,
                )
                return True

            var = self._select_variable(csp, assignment)
            for val in self._order_values(csp, var, assignment):
                if not csp.is_consistent(var, val, assignment):
                    continue

                assignment[var] = val
                yield SolverEvent(
                    EventType.ASSIGN,
                    var=var,
                    value=val,
                    message=f"Gan o {var} = {val}",
                    assignment_snapshot=assignment,
                    domains_snapshot=csp.domains,
                )

                # Lan truyen rang buoc
                if self.strategy == "mac":
                    prop_res = ConstraintPropagator.mac(csp, var, val, assignment)
                elif self.strategy == "fc":
                    prop_res = ConstraintPropagator.forward_check(csp, var, val, assignment)
                else:
                    prop_res = PropagationResult(success=True, pruned=[])

                if prop_res.pruned:
                    yield SolverEvent(
                        EventType.PRUNE,
                        var=var,
                        value=val,
                        pruned=prop_res.pruned,
                        message=f"{self.strategy.upper()}: cat tia {len(prop_res.pruned)} gia tri khoi lang gieng",
                        assignment_snapshot=assignment,
                        domains_snapshot=csp.domains,
                    )

                if prop_res.success:
                    result = yield from backtrack_gen()
                    if result:
                        return True

                # Quay lui (Backtrack)
                yield SolverEvent(
                    EventType.UNASSIGN,
                    var=var,
                    value=val,
                    message=f"Quay lui tai o {var} (huy gia tri {val})",
                    assignment_snapshot=assignment,
                    domains_snapshot=csp.domains,
                )
                if prop_res.pruned:
                    ConstraintPropagator.restore_pruned(csp, prop_res.pruned)
                    yield SolverEvent(
                        EventType.RESTORE,
                        var=var,
                        value=val,
                        pruned=prop_res.pruned,
                        message=f"Khoi phuc {len(prop_res.pruned)} gia tri ve mien",
                        assignment_snapshot=assignment,
                        domains_snapshot=csp.domains,
                    )
                del assignment[var]

            return False

        found = yield from backtrack_gen()
        if not found:
            yield SolverEvent(EventType.FAILED, message="Khong tim thay loi giai nao!")
