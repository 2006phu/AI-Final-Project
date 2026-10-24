import time
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.entities import Action, Direction
from task2_tank.engine import GameEngine
from task2_tank.game_state import GameState
from task2_tank.heuristic import TankEvaluator


class SearchAgent(BaseAgent):
    def __init__(
        self,
        depth: int = 2,
        use_alpha_beta: bool = True,
        use_heuristic: bool = True,
        use_transposition: bool = True,
        use_move_ordering: bool = True,
        name: str | None = None,
    ):
        auto_name = self._generate_name(use_alpha_beta, use_heuristic, depth)
        super().__init__(name or auto_name)

        self.depth = depth
        self.use_alpha_beta = use_alpha_beta
        self.use_heuristic = use_heuristic
        self.use_transposition = use_transposition
        self.use_move_ordering = use_move_ordering

        # Bang chuyen vi (Transposition Table)
        self.transposition_table: dict[tuple, tuple[float, int]] = {}

        # Bo dem thong ke do luong hieu nang thuc nghiem
        self.nodes_explored = 0
        self.pruning_count = 0
        self.last_execution_time_ms = 0.0

    @staticmethod
    def _generate_name(use_ab: bool, use_h: bool, depth: int) -> str:
        if use_h and use_ab:
            return f"HeuristicAlphaBeta(d={depth})"
        elif use_h:
            return f"HeuristicMinimax(d={depth})"
        elif use_ab:
            return f"AlphaBeta(d={depth})"
        else:
            return f"Minimax(d={depth})"

    @classmethod
    def create_minimax(cls, depth: int = 2) -> "SearchAgent":
        return cls(depth=depth, use_alpha_beta=False, use_heuristic=False)

    @classmethod
    def create_alpha_beta(cls, depth: int = 2) -> "SearchAgent":
        return cls(depth=depth, use_alpha_beta=True, use_heuristic=False)

    @classmethod
    def create_heuristic_minimax(cls, depth: int = 2) -> "SearchAgent":
        return cls(depth=depth, use_alpha_beta=False, use_heuristic=True)

    @classmethod
    def create_heuristic_alpha_beta(cls, depth: int = 2) -> "SearchAgent":
        return cls(depth=depth, use_alpha_beta=True, use_heuristic=True)

    def get_action(self, state: GameState, player_id: int) -> Action:
        start_time = time.perf_counter()
        self.nodes_explored = 0
        self.pruning_count = 0

        legal_actions = GameEngine.get_legal_actions(state, player_id)
        if len(legal_actions) == 1:
            return legal_actions[0]

        ordered_actions = self._order_actions(state, legal_actions, player_id)

        best_score = float("-inf")
        best_action = ordered_actions[0]
        alpha = float("-inf")
        beta = float("inf")

        opp_id = 1 - player_id
        opp_actions = self._order_actions(
            state, GameEngine.get_legal_actions(state, opp_id), opp_id
        )

        for a_max in ordered_actions:
            # MIN se chon hanh dong phan ung te nhat cho MAX trong chu ky nay
            min_val = float("inf")
            for a_min in opp_actions:
                self.nodes_explored += 1
                next_state = GameEngine.step(
                    state,
                    a_max if player_id == 0 else a_min,
                    a_min if player_id == 0 else a_max,
                )

                score = self._search(
                    next_state,
                    depth=self.depth - 2,
                    player_id=player_id,
                    alpha=alpha,
                    beta=beta,
                )

                if score < min_val:
                    min_val = score

                if self.use_alpha_beta:
                    beta = min(beta, min_val)
                    if beta <= alpha:
                        self.pruning_count += 1
                        break

            if min_val > best_score:
                best_score = min_val
                best_action = a_max

            if self.use_alpha_beta:
                alpha = max(alpha, best_score)

        self.last_execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        return best_action

    def _search(
        self,
        state: GameState,
        depth: int,
        player_id: int,
        alpha: float,
        beta: float,
    ) -> float:
        self.nodes_explored += 1

        # 1. Kiem tra trang thai ket thuc (Terminal)
        if GameEngine.is_terminal(state):
            winner = GameEngine.get_winner(state)
            if winner == player_id:
                return TankEvaluator.WIN_SCORE
            elif winner == (1 - player_id):
                return TankEvaluator.LOSE_SCORE
            else:
                return TankEvaluator.DRAW_SCORE

        # 2. Cham nguong do sau cat (Cutoff Depth)
        if depth <= 0:
            if self.use_heuristic:
                return TankEvaluator.evaluate(state, player_id)
            else:
                # Minimax thuan khong heuristic: chi danh gia tai terminal (bang 0 neu chua xong)
                return 0.0

        # 3. Kiem tra Transposition Table
        table_key = None
        if self.use_transposition:
            table_key = (state.state_key(), depth, player_id)
            if table_key in self.transposition_table:
                cached_val, cached_depth = self.transposition_table[table_key]
                if cached_depth >= depth:
                    return cached_val

        # 4. Duyet chu ky game tiep theo (2 plies: MAX roi MIN)
        opp_id = 1 - player_id
        max_actions = self._order_actions(
            state, GameEngine.get_legal_actions(state, player_id), player_id
        )
        opp_actions = self._order_actions(
            state, GameEngine.get_legal_actions(state, opp_id), opp_id
        )

        max_val = float("-inf")
        for a_max in max_actions:
            min_val = float("inf")
            for a_min in opp_actions:
                next_state = GameEngine.step(
                    state,
                    a_max if player_id == 0 else a_min,
                    a_min if player_id == 0 else a_max,
                )

                score = self._search(
                    next_state,
                    depth=depth - 2,
                    player_id=player_id,
                    alpha=alpha,
                    beta=beta,
                )

                if score < min_val:
                    min_val = score

                if self.use_alpha_beta:
                    beta = min(beta, min_val)
                    if beta <= alpha:
                        self.pruning_count += 1
                        break

            if min_val > max_val:
                max_val = min_val

            if self.use_alpha_beta:
                alpha = max(alpha, max_val)
                if beta <= alpha:
                    self.pruning_count += 1
                    break

        if self.use_transposition and table_key:
            self.transposition_table[table_key] = (max_val, depth)

        return max_val

    def _order_actions(
        self, state: GameState, actions: list[Action], player_id: int
    ) -> list[Action]:
        # Sap xep nuoc di (Move Ordering): uu tien FIRE va nuoc tien ve muc tieu
        if not self.use_move_ordering or len(actions) <= 1:
            return actions

        tank = state.tanks.get(player_id)
        opp_base = state.bases.get(1 - player_id)
        if not tank or not opp_base:
            return actions

        def score_action(action: Action) -> int:
            if action == Action.FIRE:
                return 100
            elif action == Action.STAY:
                return 0
            else:
                d = action.to_direction()
                if not d:
                    return 10
                # Uu tien nuoc giam khoang cach toi can cu doi phuong
                new_r = tank.r + d.dr
                new_c = tank.c + d.dc
                curr_dist = abs(tank.r - opp_base.r) + abs(tank.c - opp_base.c)
                new_dist = abs(new_r - opp_base.r) + abs(new_c - opp_base.c)
                if new_dist < curr_dist:
                    return 50  # Tien len
                else:
                    return 20  # Lui lai hoac di ngang

        return sorted(actions, key=score_action, reverse=True)
