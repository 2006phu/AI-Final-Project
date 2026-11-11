import random
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine import GameEngine
from task2_tank.entities import Action
from task2_tank.game_state import GameState
from task2_tank.heuristic import TankEvaluator


class RusherAgent(BaseAgent):
    """Agent chien thuat: Chien than Tan cong (Aggressive Rusher).
    
    Uu tien cao do tan cong can cu doi phuong, chu dong ban pha tuong gach de mo duong,
    khong bao gio rut lui, luon ap sat muc tieu bang duong ngan nhat.
    """
    name = "Rusher (Tan Cong)"

    def __init__(self, depth: int = 2):
        super().__init__(self.name)
        self.depth = depth
        self.nodes_explored = 0

    def get_action(self, state: GameState, player_id: int) -> Action:
        self.nodes_explored = 0
        legal_actions = GameEngine.get_legal_actions(state, player_id)
        if len(legal_actions) == 1:
            return legal_actions[0]

        tank = state.tanks.get(player_id)
        if not tank or not tank.is_alive:
            return Action.STAY

        opp_id = 1 - player_id
        opp_actions = GameEngine.get_legal_actions(state, opp_id)

        best_score = float("-inf")
        best_actions = []

        for a_max in legal_actions:
            # 1. Phat truc tiep cac hanh dong dam vao tuong thep hoac lap lai dam tuong gach
            d = a_max.to_direction()
            if d:
                cand = (tank.r + d.dr, tank.c + d.dc)
                if not state.is_inside(*cand):
                    continue
                w = state.walls.get(cand)
                if w and w.is_alive:
                    if w.is_steel or tank.direction == d:
                        continue  # Bo qua tuong thep hoac khi da xoay mat san vao tuong gach
                b = state.bases.get(0) if state.bases.get(0) and state.bases.get(0).pos == cand else None
                if b or (state.bases.get(1) and state.bases.get(1).pos == cand):
                    continue

            min_val = float("inf")
            for a_min in opp_actions:
                self.nodes_explored += 1
                next_s = GameEngine.step(
                    state,
                    a_max if player_id == 0 else a_min,
                    a_min if player_id == 0 else a_max,
                )
                score = self._eval_rusher(next_s, player_id)
                if a_max == Action.STAY:
                    score -= 40.0
                elif a_max == Action.FIRE and not TankEvaluator.has_useful_fire_target(state, player_id):
                    score -= 45.0
                if score < min_val:
                    min_val = score

            if min_val > best_score:
                best_score = min_val
                best_actions = [a_max]
            elif abs(min_val - best_score) < 1e-4:
                best_actions.append(a_max)

        return random.choice(best_actions) if best_actions else Action.STAY

    def _eval_rusher(self, state: GameState, player_id: int) -> float:
        # Danh gia theo triet ly Tan cong tong luc
        if GameEngine.is_terminal(state):
            winner = GameEngine.get_winner(state)
            if winner == player_id:
                return 1000.0
            elif winner == (1 - player_id):
                return -1000.0
            return 0.0

        my_tank = state.tanks.get(player_id)
        opp_tank = state.tanks.get(1 - player_id)
        my_base = state.bases.get(player_id)
        opp_base = state.bases.get(1 - player_id)

        if not my_tank or not my_tank.is_alive or not opp_base:
            return -900.0

        score = 0.0
        # 1. Chenh lech HP
        score += (my_tank.hp - (opp_tank.hp if opp_tank else 0)) * 20.0
        score += (my_base.hp - opp_base.hp) * 50.0

        # 2. Ap sat Base dich voi trong so sieu manh
        bfs_map = TankEvaluator.get_bfs_dist_map(state, opp_base.pos)
        dist_to_opp_base = bfs_map.get(my_tank.pos, 30)
        score -= dist_to_opp_base * 10.0  # Cang gan cang diem cao

        # 3. Ngam ban Base dich
        if TankEvaluator._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_base.pos):
            score += 150.0

        # 4. Ban pha tuong gach chan duong ve phia can cu dich
        front_pos = (my_tank.r + my_tank.direction.dr, my_tank.c + my_tank.direction.dc)
        w = state.walls.get(front_pos)
        if w and w.is_alive and not w.is_steel:
            dist_wall_to_opp = abs(front_pos[0] - opp_base.r) + abs(front_pos[1] - opp_base.c)
            dist_tank_to_opp = abs(my_tank.r - opp_base.r) + abs(my_tank.c - opp_base.c)
            if dist_wall_to_opp <= dist_tank_to_opp:
                score += 40.0  # Chi khuyen khich pha tuong mo duong tien cong

        # 5. Thuong khi dan cua minh dang lao thang vao dich hoac can cu dich
        for b in state.bullets:
            if b.is_active and b.owner_id == player_id:
                if (opp_tank and TankEvaluator._bullet_threatens_target(state, b, opp_tank.pos)) or TankEvaluator._bullet_threatens_target(state, b, opp_base.pos):
                    score += 65.0

        return max(-899.0, min(899.0, score))
