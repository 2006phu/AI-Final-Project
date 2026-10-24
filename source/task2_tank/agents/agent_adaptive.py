import random
from collections import deque
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine import GameEngine
from task2_tank.entities import Action, Direction
from task2_tank.game_state import GameState
from task2_tank.heuristic import TankEvaluator


class AdaptiveAgent(BaseAgent):
    """Agent chien thuat: Dai kien tuong Thich ung (Adaptive Grandmaster).
    
    Tu dong danh gia the tran theo thoi gian thuc de chuyen che do linh hoat:
    - Che do DEFENSE: Khi can cu nha bi nguy hiem (HP thap hoac dich qua gan).
    - Che do ASSAULT: Khi can cu dich bi so ho hoac xe dich bi tieu diet.
    - Che do FLANK: Trinh sat va tim kiem so ho o cac goc khuat.
    """
    name = "Adaptive (Thich Ung)"

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

        # Xac dinh che do chien thuat
        mode = self._determine_mode(state, player_id)

        best_score = float("-inf")
        best_actions = []

        for a_max in legal_actions:
            # Phat/bo qua cac hanh dong dam vao tuong hoac can cu
            d = a_max.to_direction()
            if d:
                cand = (tank.r + d.dr, tank.c + d.dc)
                if not state.is_inside(*cand):
                    continue
                w = state.walls.get(cand)
                if w and w.is_alive:
                    continue  # Khong bao gio di vao tuong
                b0 = state.bases.get(0)
                b1 = state.bases.get(1)
                if (b0 and b0.pos == cand) or (b1 and b1.pos == cand):
                    continue

            min_val = float("inf")
            for a_min in opp_actions:
                self.nodes_explored += 1
                next_s = GameEngine.step(
                    state,
                    a_max if player_id == 0 else a_min,
                    a_min if player_id == 0 else a_max,
                )
                score = self._eval_mode(next_s, player_id, mode)
                if a_max == Action.STAY:
                    score -= 30.0
                if score < min_val:
                    min_val = score
            if min_val > best_score:
                best_score = min_val
                best_actions = [a_max]
            elif abs(min_val - best_score) < 1e-4:
                best_actions.append(a_max)

        return random.choice(best_actions) if best_actions else Action.STAY

    def _determine_mode(self, state: GameState, player_id: int) -> str:
        my_base = state.bases.get(player_id)
        opp_base = state.bases.get(1 - player_id)
        opp_tank = state.tanks.get(1 - player_id)

        # 1. Neu nha minh bi ton thuong nang hoac dich da ap sat nha minh -> Thu
        if my_base and my_base.hp <= 5:
            return "DEFENSE"
        if my_base and opp_tank and opp_tank.is_alive:
            dist = abs(opp_tank.r - my_base.r) + abs(opp_tank.c - my_base.c)
            if dist <= 3:
                return "DEFENSE"

        # 2. Neu nha dich da yeu hoac xe dich da chet -> Cong tong luc
        if opp_base and opp_base.hp <= 5:
            return "ASSAULT"
        if not opp_tank or not opp_tank.is_alive:
            return "ASSAULT"

        # 3. Con lai: Du kich boc suon
        return "FLANK"

    def _eval_mode(self, state: GameState, player_id: int, mode: str) -> float:
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

        if not my_tank or not my_tank.is_alive:
            return -900.0

        score = 0.0
        score += (my_tank.hp - (opp_tank.hp if opp_tank else 0)) * 25.0
        score += (my_base.hp - (opp_base.hp if opp_base else 0)) * 40.0

        bfs_map_opp = TankEvaluator.get_bfs_dist_map(state, opp_base.pos)
        dist_opp_base = bfs_map_opp.get(my_tank.pos, 30)

        my_aim_opp = opp_tank and TankEvaluator._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_tank.pos)
        opp_aim_me = opp_tank and TankEvaluator._has_line_of_fire(state, opp_tank.pos, opp_tank.direction, my_tank.pos)
        my_aim_base = TankEvaluator._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_base.pos)

        if mode == "ASSAULT":
            score -= dist_opp_base * 8.0
            if my_aim_base:
                score += 120.0
        elif mode == "DEFENSE":
            dist_my_base = abs(my_tank.r - my_base.r) + abs(my_tank.c - my_base.c)
            score -= dist_my_base * 6.0
            if my_aim_opp:
                score += 80.0
        else:  # FLANK
            score -= dist_opp_base * 4.0
            if my_aim_opp and not opp_aim_me:
                score += 90.0
            if opp_aim_me:
                score -= 60.0

        return max(-899.0, min(899.0, score))
