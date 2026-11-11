import random
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine import GameEngine
from task2_tank.entities import Action
from task2_tank.game_state import GameState
from task2_tank.heuristic import TankEvaluator


class FlankerAgent(BaseAgent):
    """Agent chien thuat: Xa thu Du kich & Boc suon (Flanking Sniper).
    
    Khong bao gio doi dau truc dien, luon tim goc khuat va loi di hai ben
    de ban vao man suon hoac sau lung dich, danh xong la co the ne dan.
    """
    name = "Flanker (Boc Suon)"

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
                    if w.is_steel or tank.direction == d:
                        continue  # Bo qua tuong thep hoac khi da xoay mat san vao tuong gach
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
                score = self._eval_flanker(next_s, player_id)
                if a_max == Action.STAY:
                    score -= 30.0
                elif a_max == Action.FIRE and not TankEvaluator.has_useful_fire_target(state, player_id):
                    score -= 35.0
                if score < min_val:
                    min_val = score
            if min_val > best_score:
                best_score = min_val
                best_actions = [a_max]
            elif abs(min_val - best_score) < 1e-4:
                best_actions.append(a_max)

        return random.choice(best_actions) if best_actions else Action.STAY

    def _eval_flanker(self, state: GameState, player_id: int) -> float:
        # Danh gia theo triet ly Du kich: Danh bat ngo & Ne tranh doi dau
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
        score += (my_tank.hp - (opp_tank.hp if opp_tank else 0)) * 30.0
        score += (my_base.hp - opp_base.hp) * 40.0

        # 2. Thuong cuc lon cho Boc suon (Minh ngam duoc dich ma dich khong ngam duoc minh)
        my_aim_opp = opp_tank and TankEvaluator._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_tank.pos)
        opp_aim_me = opp_tank and TankEvaluator._has_line_of_fire(state, opp_tank.pos, opp_tank.direction, my_tank.pos)
        my_aim_base = TankEvaluator._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_base.pos)

        if my_aim_base:
            score += 90.0
        if my_aim_opp and not opp_aim_me:
            score += 120.0  # Hoan hao! Ban len tu goc khuat

        if opp_aim_me:
            score -= 80.0  # Nguy hiem! Dang bi dich ngam, phai ne ngay!

        # 3. Thuong khi dan cua minh dang lao thang vao dich hoac can cu dich, phat khi bi dan dich de doa
        for b in state.bullets:
            if not b.is_active:
                continue
            if b.owner_id == player_id:
                if (opp_tank and TankEvaluator._bullet_threatens_target(state, b, opp_tank.pos)) or TankEvaluator._bullet_threatens_target(state, b, opp_base.pos):
                    score += 65.0
            else:
                if TankEvaluator._bullet_threatens_target(state, b, my_tank.pos) or (my_base and TankEvaluator._bullet_threatens_target(state, b, my_base.pos)):
                    score -= 90.0

        # 4. Ne duong truc dien voi dich
        if opp_tank and opp_tank.is_alive:
            # Phat khi dung cung hang hoac cung cot voi xe dich ma khong ban duoc
            if (my_tank.r == opp_tank.r or my_tank.c == opp_tank.c) and not my_aim_opp:
                score -= 30.0

        # 5. Tien ve Base dich theo duong vong
        bfs_map = TankEvaluator.get_bfs_dist_map(state, opp_base.pos)
        score -= bfs_map.get(my_tank.pos, 30) * 8.0

        return max(-899.0, min(899.0, score))
