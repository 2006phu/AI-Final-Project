import random
from collections import deque
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine import GameEngine
from task2_tank.entities import Action, Direction
from task2_tank.game_state import GameState
from task2_tank.heuristic import TankEvaluator


class GuardianAgent(BaseAgent):
    """Agent chien thuat: Phao dai Phong ngu (Defensive Guardian).
    
    Tuan tra va bao ve can cu phe nha, ngan chan xe dich dot nhap,
    chan dung dan ban vao base, danh tra quyet liet khi can cu bi uy hiep.
    """
    name = "Guardian (Phong Thu)"

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
            d = a_max.to_direction()
            if d:
                cand = (tank.r + d.dr, tank.c + d.dc)
                if not state.is_inside(*cand):
                    continue
                w = state.walls.get(cand)
                if w and w.is_alive:
                    continue  # Khong di vao tuong
                if (state.bases.get(0) and state.bases.get(0).pos == cand) or (state.bases.get(1) and state.bases.get(1).pos == cand):
                    continue

            min_val = float("inf")
            for a_min in opp_actions:
                self.nodes_explored += 1
                next_s = GameEngine.step(
                    state,
                    a_max if player_id == 0 else a_min,
                    a_min if player_id == 0 else a_max,
                )
                score = self._eval_guardian(next_s, player_id)
                if score < min_val:
                    min_val = score
            if min_val > best_score:
                best_score = min_val
                best_actions = [a_max]
            elif abs(min_val - best_score) < 1e-4:
                best_actions.append(a_max)

        return random.choice(best_actions) if best_actions else Action.STAY

    def _eval_guardian(self, state: GameState, player_id: int) -> float:
        # Danh gia theo triet ly Bao ve can cu tuyet doi
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

        if not my_tank or not my_tank.is_alive or not my_base:
            return -900.0

        score = 0.0
        # 1. Chenh lech HP (Uu tien giu mau Base phe nha)
        score += (my_tank.hp - (opp_tank.hp if opp_tank else 0)) * 25.0
        score += my_base.hp * 60.0 - (opp_base.hp if opp_base else 0) * 30.0

        # 2. Khoang cach giu chan gan Base phe nha (Patrol Perimeter <= 3 cells)
        dist_to_my_base = abs(my_tank.r - my_base.r) + abs(my_tank.c - my_base.c)
        if dist_to_my_base > 4:
            score -= (dist_to_my_base - 4) * 15.0  # Phat khi chay qua xa can cu

        # 3. Ngan chan dich tiep can can cu phe minh
        if opp_tank and opp_tank.is_alive:
            dist_opp_to_my_base = abs(opp_tank.r - my_base.r) + abs(opp_tank.c - my_base.c)
            if dist_opp_to_my_base <= 4:
                score -= 100.0  # Bao dong do! Dich dang qua gan can cu

            # Uu tien tieu diet xe dich khi o gan nha
            if TankEvaluator._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_tank.pos):
                score += 80.0

        # 4. Triet tieu dan dich bay vao can cu
        for b in state.bullets:
            if b.is_active and b.owner_id != player_id:
                if TankEvaluator._bullet_threatens_target(b, my_base.pos):
                    score -= 150.0  # Nguy hiem cuc do

        return max(-899.0, min(899.0, score))
