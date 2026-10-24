from collections import deque
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
    WEIGHT_DIST_ENEMY_BASE = 15.0  # Tang manh trong so BFS de xe chu dong ap sat tan cong, khong di long vong
    WEIGHT_AIM_ENEMY_TANK = 20.0
    WEIGHT_AIM_ENEMY_BASE = 40.0
    WEIGHT_FLANK_ADVANTAGE = 25.0
    WEIGHT_BULLET_THREAT = 40.0

    @classmethod
    def get_bfs_dist_map(cls, state: GameState, target_pos: tuple[int, int]) -> dict[tuple[int, int], int]:
        """Tinh ban do khoang cach duong di ngan nhat BFS tranh tuong thep va tinh chi phi tuong gach."""
        dist: dict[tuple[int, int], int] = {target_pos: 0}
        queue = deque([(target_pos, 0)])

        while queue:
            (r, c), d = queue.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < state.rows and 0 <= nc < state.cols:
                    # Can cu khong the di xuyen qua (ngoai tru can cu dich la dich den)
                    is_base_blocked = False
                    for b in state.bases.values():
                        if b.is_alive and (nr, nc) == b.pos and (nr, nc) != target_pos:
                            is_base_blocked = True
                            break
                    if is_base_blocked:
                        continue

                    w = state.walls.get((nr, nc))
                    if w and w.is_alive and w.is_steel:
                        continue  # Tuong thep khong the di qua
                    step_cost = 4 if (w and w.is_alive) else 1
                    new_d = d + step_cost
                    if (nr, nc) not in dist or new_d < dist[(nr, nc)]:
                        dist[(nr, nc)] = new_d
                        queue.append(((nr, nc), new_d))
        return dist

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

        # 3. Chenh lech khoang cach BFS thuc te toi can cu doi phuong (Pathfinding Differential)
        # Dung BFS tranh vat can thay vi Manhattan mu quang de xe khong dam vao tuong
        bfs_map_my_base = cls.get_bfs_dist_map(state, my_base.pos)
        bfs_map_opp_base = cls.get_bfs_dist_map(state, opp_base.pos)

        fallback_dist_my = (abs(my_tank.r - opp_base.r) + abs(my_tank.c - opp_base.c)) * 2
        fallback_dist_opp = (abs(opp_tank.r - my_base.r) + abs(opp_tank.c - my_base.c)) * 2

        my_dist_to_opp_base = bfs_map_opp_base.get(my_tank.pos, fallback_dist_my)
        opp_dist_to_my_base = bfs_map_my_base.get(opp_tank.pos, fallback_dist_opp)
        score += (opp_dist_to_my_base - my_dist_to_opp_base) * cls.WEIGHT_DIST_ENEMY_BASE

        # 4. Kiem tra duong ngam ban (Line of Fire & Flanking Differential)
        my_aim_base = cls._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_base.pos)
        my_aim_tank = cls._has_line_of_fire(state, my_tank.pos, my_tank.direction, opp_tank.pos)

        opp_aim_base = cls._has_line_of_fire(state, opp_tank.pos, opp_tank.direction, my_base.pos)
        opp_aim_tank = cls._has_line_of_fire(state, opp_tank.pos, opp_tank.direction, my_tank.pos)

        if my_aim_base:
            score += cls.WEIGHT_AIM_ENEMY_BASE
        if my_aim_tank:
            score += cls.WEIGHT_AIM_ENEMY_TANK

        if opp_aim_base:
            score -= cls.WEIGHT_AIM_ENEMY_BASE
        if opp_aim_tank:
            score -= cls.WEIGHT_AIM_ENEMY_TANK

        # Loi the boc suon (Flanking): ngam duoc dich nhung dich khong ngam duoc minh
        if my_aim_tank and not opp_aim_tank:
            score += cls.WEIGHT_FLANK_ADVANTAGE * 1.5
        elif opp_aim_tank and not my_aim_tank:
            score -= cls.WEIGHT_FLANK_ADVANTAGE * 1.5

        # 5. Nguy co tu dan dang bay (Bullet Threats Differential)
        for bullet in state.bullets:
            if not bullet.is_active:
                continue
            if bullet.owner_id == opp_id:
                # Dan dich de doa minh (chi tinh neu khong co tuong chan va o cu ly gan <= 4 o)
                if cls._bullet_threatens_target(state, bullet, my_tank.pos) or cls._bullet_threatens_target(state, bullet, my_base.pos):
                    score -= cls.WEIGHT_BULLET_THREAT
            else:
                # Dan minh de doa dich
                if cls._bullet_threatens_target(state, bullet, opp_tank.pos) or cls._bullet_threatens_target(state, bullet, opp_base.pos):
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
            # Bat ky tuong nao con song (gach hoac thep) deu chan duong dan
            wall = state.walls.get((r, c))
            if wall and wall.is_alive:
                return False

    @staticmethod
    def _bullet_threatens_target(state: GameState, bullet: Bullet, target_pos: tuple[int, int]) -> bool:
        br, bc = bullet.r, bullet.c
        tr, tc = target_pos
        dr, dc = bullet.direction.dr, bullet.direction.dc

        if dr == 0:
            if br != tr or (tc - bc) * dc <= 0:
                return False
            # Kiem tra co tuong chan giua dan va muc tieu khong
            c_curr = bc + dc
            while c_curr != tc:
                w = state.walls.get((br, c_curr))
                if w and w.is_alive:
                    return False
                c_curr += dc
            # Chi thuc su de doa nguy cap neu cu ly cuc gan (<= 2 o, khong kip ne tranh)
            return abs(tc - bc) <= 2
        else:
            if bc != tc or (tr - br) * dr <= 0:
                return False
            r_curr = br + dr
            while r_curr != tr:
                w = state.walls.get((r_curr, bc))
                if w and w.is_alive:
                    return False
                r_curr += dr
            # Chi thuc su de doa nguy cap neu cu ly cuc gan (<= 2 o, khong kip ne tranh)
            return abs(tr - br) <= 2
