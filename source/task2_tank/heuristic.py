from task2_tank.entities import Direction, Tank, Base, Wall, Bullet
from task2_tank.game_state import GameState


class TankEvaluator:
    # Gia tri cuc dai cho trang thai thang/thua tuyet doi trong Zero-Sum Game
    WIN_SCORE = 1000.0
    LOSE_SCORE = -1000.0
    DRAW_SCORE = 0.0

    # Cac trong so danh gia the tran
    WEIGHT_TANK_HP = 25.0
    WEIGHT_BASE_HP = 50.0
    WEIGHT_DIST_ENEMY_BASE = 3.0
    WEIGHT_AIM_ENEMY_TANK = 20.0
    WEIGHT_AIM_ENEMY_BASE = 35.0
    WEIGHT_BULLET_THREAT = 40.0

    @classmethod
    def evaluate(cls, state: GameState, player_id: int = 0) -> float:
        # Ham danh gia the tran Zero-Sum chuan: eval(s, 0) == -eval(s, 1)
        opp_id = 1 - player_id

        my_tank = state.tanks.get(player_id)
        opp_tank = state.tanks.get(opp_id)
        my_base = state.bases.get(player_id)
        opp_base = state.bases.get(opp_id)

        # 1. Kiem tra trang thai ket thuc (Terminal States)
        my_alive = my_tank and my_tank.is_alive and my_base and my_base.is_alive
        opp_alive = opp_tank and opp_tank.is_alive and opp_base and opp_base.is_alive

        if not my_alive and not opp_alive:
            return cls.DRAW_SCORE
        if not opp_alive:
            return cls.WIN_SCORE
        if not my_alive:
            return cls.LOSE_SCORE

        # 2. Chenh lech mau (HP Differential)
        score = 0.0
        score += (my_tank.hp - opp_tank.hp) * cls.WEIGHT_TANK_HP
        score += (my_base.hp - opp_base.hp) * cls.WEIGHT_BASE_HP

        # 3. Chenh lech khoang cach toi can cu doi phuong (Distance Differential)
        # Cang gan can cu dich hon so voi dich gan can cu minh thi cang co loi the
        my_dist_to_opp_base = abs(my_tank.r - opp_base.r) + abs(my_tank.c - opp_base.c)
        opp_dist_to_my_base = abs(opp_tank.r - my_base.r) + abs(opp_tank.c - my_base.c)
        score += (opp_dist_to_my_base - my_dist_to_opp_base) * cls.WEIGHT_DIST_ENEMY_BASE

        # 4. Kiem tra duong ngam ban (Line of Fire Differential)
        # Loi the khi minh ngam duoc dich
        if cls._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_base.pos):
            score += cls.WEIGHT_AIM_ENEMY_BASE
        if cls._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_tank.pos):
            score += cls.WEIGHT_AIM_ENEMY_TANK

        # Bat loi khi dich dang ngam vao minh
        if cls._has_line_of_fire(state, opp_tank.pos, opp_tank.direction, my_base.pos):
            score -= cls.WEIGHT_AIM_ENEMY_BASE
        if cls._has_line_of_fire(state, opp_tank.pos, opp_tank.direction, my_tank.pos):
            score -= cls.WEIGHT_AIM_ENEMY_TANK

        # 5. Nguy co tu dan dang bay (Bullet Threats Differential)
        for bullet in state.bullets:
            if not bullet.is_active:
                continue
            if bullet.owner_id == opp_id:
                # Dan dich de doa minh
                if cls._bullet_threatens_target(bullet, my_tank.pos) or cls._bullet_threatens_target(bullet, my_base.pos):
                    score -= cls.WEIGHT_BULLET_THREAT
            else:
                # Dan minh de doa dich
                if cls._bullet_threatens_target(bullet, opp_tank.pos) or cls._bullet_threatens_target(bullet, opp_base.pos):
                    score += cls.WEIGHT_BULLET_THREAT

        # Gioi han heuristic trong khoang [-899, 899] de khong lan át trang thai thang/thua tuyet doi (1000)
        return max(-899.0, min(899.0, score))

    @staticmethod
    def _has_line_of_fire(
        state: GameState,
        start_pos: tuple[int, int],
        direction: Direction,
        target_pos: tuple[int, int],
    ) -> bool:
        r, c = start_pos
        dr, dc = direction.dr, direction.dc

        while True:
            r += dr
            c += dc
            if not state.is_inside(r, c):
                return False
            if (r, c) == target_pos:
                return True
            # Neu gap tuong thep hoac can cu thi chan dan
            wall = state.walls.get((r, c))
            if wall and wall.is_alive and wall.is_steel:
                return False

    @staticmethod
    def _bullet_threatens_target(bullet: Bullet, target_pos: tuple[int, int]) -> bool:
        br, bc = bullet.r, bullet.c
        tr, tc = target_pos
        dr, dc = bullet.direction.dr, bullet.direction.dc

        if dr == 0:
            return br == tr and (tc - bc) * dc > 0
        else:
            return bc == tc and (tr - br) * dr > 0
