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
        self.recent_positions: list[tuple[int, int]] = []
        self.last_action: Action | None = None
        self.last_my_hp: int | None = None
        self.last_opp_hp: int | None = None
        self.neutralize_streak: int = 0

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

        tank = state.tanks.get(player_id)
        opp_id = 1 - player_id
        opp_tank = state.tanks.get(opp_id)

        # Theo doi chuoi triet tieu dan doi dau (Neutralization Streak)
        if tank and opp_tank and self.last_action == Action.FIRE:
            if self.last_my_hp == tank.hp and self.last_opp_hp == opp_tank.hp:
                self.neutralize_streak += 1
            else:
                self.neutralize_streak = 0
        else:
            self.neutralize_streak = 0

        self.last_my_hp = tank.hp if tank else None
        self.last_opp_hp = opp_tank.hp if opp_tank else None

        # Ghi nhan vi tri de chong dung im tai cho (Anti-Stagnation)
        if tank and tank.is_alive:
            self.recent_positions.append(tank.pos)
            if len(self.recent_positions) > 6:
                self.recent_positions.pop(0)

        legal_actions = GameEngine.get_legal_actions(state, player_id)
        if len(legal_actions) == 1:
            self.last_action = legal_actions[0]
            return legal_actions[0]

        ordered_actions = self._order_actions(state, legal_actions, player_id)

        best_score = float("-inf")
        best_action = ordered_actions[0]
        alpha = float("-inf")

        opp_actions = self._order_actions(
            state, GameEngine.get_legal_actions(state, opp_id), opp_id
        )

        stagnant_count = sum(1 for p in self.recent_positions[-3:] if p == tank.pos) if tank else 0

        # Kiem tra xem turn truoc hanh dong di chuyen co bi chan khong (Collision / Clash Deadlock)
        last_move_failed = (
            self.last_action in (Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT)
            and len(self.recent_positions) >= 2
            and self.recent_positions[-1] == self.recent_positions[-2]
        )

        for a_max in ordered_actions:
            # MIN se chon hanh dong phan ung te nhat cho MAX trong chu ky nay
            min_val = float("inf")
            curr_beta = float("inf")
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
                    beta=curr_beta,
                )

                # 1. Phat nang hanh dong dung yen STAY de luon chu dong tan cong hoac co dong
                if a_max == Action.STAY:
                    score -= 50.0

                # 2. Phat hanh dong ban tieu hao vo nghia hoac triet tieu dan gay be tac (Neutralization Penalty)
                if a_max == Action.FIRE and (self.neutralize_streak >= 1 or stagnant_count >= 2):
                    opp_t_old = state.tanks.get(opp_id)
                    opp_t_new = next_state.tanks.get(opp_id)
                    opp_b_old = state.bases.get(opp_id)
                    opp_b_new = next_state.bases.get(opp_id)
                    hit_t = opp_t_old and opp_t_new and opp_t_new.hp < opp_t_old.hp
                    hit_b = opp_b_old and opp_b_new and opp_b_new.hp < opp_b_old.hp
                    hit_w = any(w.hp < state.walls[p].hp for p, w in next_state.walls.items() if p in state.walls and not state.walls[p].is_steel)
                    if not hit_t and not hit_b and not hit_w:
                        score -= 40.0 * max(self.neutralize_streak, stagnant_count - 1)

                # 3. Phat va cham (Collision Penalty) va Chống rung lắc (Anti-Oscillation)
                if a_max in (Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT):
                    # Neu hanh dong nay vua bi chan / dung im o turn truoc, khong duoc tiep tuc dam vao
                    if last_move_failed and a_max == self.last_action:
                        score -= 60.0

                    my_t_new = next_state.tanks.get(player_id)
                    if my_t_new and my_t_new.pos == tank.pos:
                        d_act = a_max.to_direction()
                        front_cell = (tank.r + d_act.dr, tank.c + d_act.dc) if d_act else None
                        w_front = state.walls.get(front_cell) if front_cell else None
                        my_b = state.bases.get(player_id)
                        opp_b = state.bases.get(opp_id)
                        is_impassable = (
                            not front_cell
                            or not state.is_inside(*front_cell)
                            or (w_front and w_front.is_steel and w_front.is_alive)
                            or (my_b and front_cell == my_b.pos)
                        )
                        if is_impassable:
                            score -= 50.0
                        elif (w_front and not w_front.is_steel and w_front.is_alive) or (opp_b and front_cell == opp_b.pos):
                            if tank.direction == d_act:
                                score -= 30.0
                    elif my_t_new:
                        # Phat rung lac da buoc (Anti-Cycle Oscillation)
                        past_visits = sum(1 for p in self.recent_positions[-4:] if p == my_t_new.pos)
                        if past_visits >= 1:
                            score -= 20.0 * past_visits

                if score < min_val:
                    min_val = score

                if self.use_alpha_beta:
                    curr_beta = min(curr_beta, min_val)
                    if curr_beta <= alpha:
                        self.pruning_count += 1
                        break

            if min_val > best_score:
                best_score = min_val
                best_action = a_max

            if self.use_alpha_beta:
                alpha = max(alpha, best_score)

        self.last_action = best_action
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
                # Minimax thuan: tinh chenh lech mau va khoang cach BFS thuc te de tranh mu quang
                my_t = state.tanks.get(player_id)
                opp_b = state.bases.get(1 - player_id)
                opp_t = state.tanks.get(1 - player_id)
                my_b = state.bases.get(player_id)
                if my_t and opp_b and opp_t and my_b:
                    score = (my_t.hp - opp_t.hp) * 10.0 + (my_b.hp - opp_b.hp) * 20.0
                    bfs_opp = TankEvaluator.get_bfs_dist_map(state, opp_b.pos)
                    bfs_my = TankEvaluator.get_bfs_dist_map(state, my_b.pos)
                    my_d = bfs_opp.get(my_t.pos, 50)
                    opp_d = bfs_my.get(opp_t.pos, 50)
                    score += float(opp_d - my_d) * 0.5
                    return score
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
            curr_beta = beta
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
                    beta=curr_beta,
                )

                if score < min_val:
                    min_val = score

                if self.use_alpha_beta:
                    curr_beta = min(curr_beta, min_val)
                    if curr_beta <= alpha:
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
        # Sap xep nuoc di (Move Ordering): Dinh huong thong minh theo BFS va ngam ban
        if not self.use_move_ordering or len(actions) <= 1:
            return actions

        tank = state.tanks.get(player_id)
        opp_base = state.bases.get(1 - player_id)
        if not tank or not opp_base:
            return actions

        bfs_map = TankEvaluator.get_bfs_dist_map(state, opp_base.pos)
        curr_dist = bfs_map.get(tank.pos, 99)
        opp_tank = state.tanks.get(1 - player_id)

        # Dem so lan dung im o vi tri hien tai de pha vo be tac (Stagnation Breaker)
        stagnation_count = 0
        if tank and len(self.recent_positions) >= 2:
            stagnation_count = sum(1 for p in self.recent_positions[-3:] if p == tank.pos)

        # Phat hien the doi dau truc dien (Head-on standoff khien 2 xe ban triet tieu dan)
        is_head_on = False
        head_on_axis = None
        if opp_tank and opp_tank.is_alive:
            same_row = (tank.r == opp_tank.r)
            same_col = (tank.c == opp_tank.c)
            if same_row and ((tank.direction == Direction.RIGHT and opp_tank.direction == Direction.LEFT and tank.c < opp_tank.c) or
                             (tank.direction == Direction.LEFT and opp_tank.direction == Direction.RIGHT and tank.c > opp_tank.c)):
                is_head_on = True
                head_on_axis = "row"
            elif same_col and ((tank.direction == Direction.DOWN and opp_tank.direction == Direction.UP and tank.r < opp_tank.r) or
                               (tank.direction == Direction.UP and opp_tank.direction == Direction.DOWN and tank.r > opp_tank.r)):
                is_head_on = True
                head_on_axis = "col"

        # Phat hien dan dich dang bay toi de doa truc tiep (Dodging Reflex)
        threat_bullet = None
        for b in state.bullets:
            if b.is_active and b.owner_id == 1 - player_id:
                if TankEvaluator._bullet_threatens_target(state, b, tank.pos):
                    threat_bullet = b
                    break

        def score_action(action: Action) -> int:
            if action == Action.FIRE:
                # Neu xe da co vien dan dang bay tren ban do: Khong the ban tiep, phai di chuyen!
                if state.has_active_bullet(player_id):
                    return -120

                front_pos = (tank.r + tank.direction.dr, tank.c + tank.direction.dc)
                if not state.is_inside(*front_pos):
                    return -100
                w = state.walls.get(front_pos)
                if w and w.is_alive:
                    if w.is_steel:
                        return -100  # Tuyet doi khong ban vao tuong thep vi khong pha duoc!
                    else:
                        return 115   # Chu dong ban pha tuong gach de mo hanh lang tien cong!
                
                # Kiem tra ban can cu dich
                elif TankEvaluator._has_line_of_fire(state, tank.pos, tank.direction, opp_base.pos):
                    return 120  # Ban thang can cu dich!
                
                # Kiem tra ban xe dich
                elif opp_tank and opp_tank.is_alive and TankEvaluator._has_line_of_fire(state, tank.pos, tank.direction, opp_tank.pos):
                    # Neu dang bi be tac neutralize thi khong ban tiep ma chuyen sang boc suon
                    return -20 if (self.neutralize_streak >= 1 or stagnation_count >= 2) else 110
                
                else:
                    return -40  # Ban vao khong gian trong khong co muc tieu

            elif action == Action.STAY:
                base_stay = -70 - (stagnation_count * 50)
                if threat_bullet:
                    base_stay -= 120  # Tuyet doi khong dung im khi co dan bay thang vao mat
                return base_stay

            else:
                d = action.to_direction()
                if not d:
                    return 0
                new_pos = (tank.r + d.dr, tank.c + d.dc)
                if not state.is_inside(*new_pos):
                    return -150  # Ra ngoai ban do
                
                # Kiem tra thuc the can duong (Tuong, Base, Tank)
                blocking = state.get_entity_at(*new_pos)
                if blocking is not None and blocking != tank and blocking.is_alive:
                    if hasattr(blocking, "is_steel") and not blocking.is_steel:
                        # Neu da quay mat vao tuong gach roi ma van dam vao -> phat de uu tien ban (FIRE)
                        return -60 if tank.direction == d else 75
                    elif hasattr(blocking, "player_id") and blocking.player_id != player_id:
                        return -60 if tank.direction == d else 80
                    else:
                        return -130  # Tuong thep hoac can cu dong minh: khong the di qua

                new_dist = bfs_map.get(new_pos, 99)
                if new_dist < curr_dist:
                    score = 85   # Di chuyen rut ngan khoang cach BFS toi base dich!
                elif new_dist == curr_dist:
                    score = 45   # Di ngang tim duong
                else:
                    score = 10   # Lui lai

                # 1. Cong diem quan tinh (Momentum) de tranh rung lac / dung im tai cho
                if d == tank.direction:
                    score += 20  # Uu tien giu nguyen huong tien cong
                elif d == tank.direction.opposite():
                    score -= 30  # Phat quay xe lui lai o vua di qua de triet tieu giao dong (oscillation)

                # 2. Pha vo doi xung ben canh giua 2 xe (player 0 re trai, player 1 re phai)
                if player_id == 0:
                    if action == Action.MOVE_LEFT:
                        score += 5
                else:
                    if action == Action.MOVE_RIGHT:
                        score += 5

                # 3. Uu tien ne the doi dau truc dien (Flank Maneuver)
                if is_head_on and (self.neutralize_streak >= 1 or stagnation_count >= 1):
                    if head_on_axis == "row" and action in (Action.MOVE_UP, Action.MOVE_DOWN):
                        score += 60  # Buoc sang lan khac de boc suon xe dich!
                    elif head_on_axis == "col" and action in (Action.MOVE_LEFT, Action.MOVE_RIGHT):
                        score += 60  # Buoc sang lan khac de boc suon xe dich!

                # 4. Phan xa ne dan (Bullet Dodging): buoc sang o vuong goc voi duong dan
                if threat_bullet:
                    if threat_bullet.direction.dr != 0 and action in (Action.MOVE_LEFT, Action.MOVE_RIGHT):
                        score += 90
                    elif threat_bullet.direction.dc != 0 and action in (Action.MOVE_UP, Action.MOVE_DOWN):
                        score += 90

                # 5. Thuong manh cho hanh dong di chuyen de pha vo be tac dung im
                score += stagnation_count * 30

                return score

        return sorted(actions, key=score_action, reverse=True)
