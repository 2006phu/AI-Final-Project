from task2_tank.entities import Action, Direction, Tank, Base, Wall, Bullet
from task2_tank.game_state import GameState


class GameEngine:
    @staticmethod
    def get_legal_actions(state: GameState, player_id: int) -> list[Action]:
        tank = state.tanks.get(player_id)
        if tank is None or not tank.is_alive:
            return [Action.STAY]
        return [
            Action.MOVE_UP,
            Action.MOVE_DOWN,
            Action.MOVE_LEFT,
            Action.MOVE_RIGHT,
            Action.FIRE,
            Action.STAY,
        ]

    @staticmethod
    def is_terminal(state: GameState) -> bool:
        t0_dead = 0 not in state.tanks or not state.tanks[0].is_alive
        b0_dead = 0 not in state.bases or not state.bases[0].is_alive
        t1_dead = 1 not in state.tanks or not state.tanks[1].is_alive
        b1_dead = 1 not in state.bases or not state.bases[1].is_alive

        if t0_dead or b0_dead or t1_dead or b1_dead:
            return True

        return state.turn_count >= state.max_turns

    @staticmethod
    def get_winner(state: GameState) -> int | None:
        # Tra ve:
        # 0 neu Player 1 thang
        # 1 neu Player 2 thang
        # -1 neu Hoa
        # None neu chua ket thuc
        if not GameEngine.is_terminal(state):
            return None

        p0_lost = (
            0 not in state.tanks
            or not state.tanks[0].is_alive
            or 0 not in state.bases
            or not state.bases[0].is_alive
        )
        p1_lost = (
            1 not in state.tanks
            or not state.tanks[1].is_alive
            or 1 not in state.bases
            or not state.bases[1].is_alive
        )

        if p0_lost and p1_lost:
            return -1  # Hoa (ca hai cung bi tieu diet trong cung 1 chu ky)
        elif p1_lost:
            return 0   # Player 1 thang
        elif p0_lost:
            return 1   # Player 2 thang
        else:
            return -1  # Hoa do het luot (max_turns)

    @classmethod
    def step(cls, state: GameState, a0: Action, a1: Action) -> GameState:
        # Nhan ban trang thai de tinh toan chu ky tiep theo
        new_state = state.clone()
        new_state.turn_count += 1

        tank0 = new_state.tanks.get(0)
        tank1 = new_state.tanks.get(1)

        # -------------------------------------------------------------
        # 1. XU LY DI CHUYEN & XOAY HUONG TANK
        # -------------------------------------------------------------
        cls._resolve_tank_movements(new_state, tank0, a0, tank1, a1)

        # -------------------------------------------------------------
        # 2. XU LY BAN DAN (FIRE)
        # -------------------------------------------------------------
        cls._resolve_firing(new_state, tank0, a0, 0)
        cls._resolve_firing(new_state, tank1, a1, 1)

        # -------------------------------------------------------------
        # 3. XU LY DAN BAY 3 NHIP (CELL-BY-CELL COLLISION)
        # -------------------------------------------------------------
        cls._resolve_bullet_flights(new_state)

        # Don dep tuong da bi pha huy khoi ban do
        new_state.walls = {pos: w for pos, w in new_state.walls.items() if w.is_alive}
        new_state.bullets = [b for b in new_state.bullets if b.is_active]

        return new_state

    @classmethod
    def _resolve_tank_movements(
        cls,
        state: GameState,
        tank0: Tank | None,
        a0: Action,
        tank1: Tank | None,
        a1: Action,
    ):
        target_pos0 = tank0.pos if tank0 and tank0.is_alive else None
        target_pos1 = tank1.pos if tank1 and tank1.is_alive else None

        dir0 = a0.to_direction()
        dir1 = a1.to_direction()

        # Tinh vi tri du dinh di chuyen
        if tank0 and tank0.is_alive and dir0:
            tank0.rotate(dir0)
            candidate = (tank0.r + dir0.dr, tank0.c + dir0.dc)
            if state.is_inside(*candidate):
                target_pos0 = candidate

        if tank1 and tank1.is_alive and dir1:
            tank1.rotate(dir1)
            candidate = (tank1.r + dir1.dr, tank1.c + dir1.dc)
            if state.is_inside(*candidate):
                target_pos1 = candidate

        # Kiem tra tranh chap giua 2 tank
        conflict0 = False
        conflict1 = False

        if tank0 and tank1 and tank0.is_alive and tank1.is_alive:
            # 2 xe cung lao vao 1 o
            if dir0 and dir1 and target_pos0 == target_pos1:
                conflict0 = True
                conflict1 = True
            # 2 xe doi cho cho nhau (head-on collision)
            elif dir0 and dir1 and target_pos0 == tank1.pos and target_pos1 == tank0.pos:
                conflict0 = True
                conflict1 = True

        # Kiem tra vat can cho tank 0
        if tank0 and tank0.is_alive and dir0 and not conflict0:
            entity = state.get_entity_at(*target_pos0)
            if entity is None or entity == tank0:
                tank0.move_to(*target_pos0, dir0)
            # Neu vuong chuong ngai vat: chi xoay huong dir0, dung yen vi tri cu

        # Kiem tra vat can cho tank 1
        if tank1 and tank1.is_alive and dir1 and not conflict1:
            entity = state.get_entity_at(*target_pos1)
            if entity is None or entity == tank1:
                tank1.move_to(*target_pos1, dir1)

    @classmethod
    def _resolve_firing(cls, state: GameState, tank: Tank | None, action: Action, player_id: int):
        if not (tank and tank.is_alive and action == Action.FIRE):
            return

        # Luat: moi tank chi co toi da 1 vien dan dang hoat dong tren ban do
        if state.has_active_bullet(player_id):
            return

        spawn_r = tank.r + tank.direction.dr
        spawn_c = tank.c + tank.direction.dc

        # Neu huong ban quay ra ngoai bien ban do thi vien dan tieu tan ngay
        if not state.is_inside(spawn_r, spawn_c):
            return

        # Khoi tao dan tai vi tri nong phao; _resolve_bullet_flights se cho dan tien dung 3 o (cell-by-cell)
        bullet = Bullet(player_id, tank.r, tank.c, tank.direction)
        state.bullets.append(bullet)

    @classmethod
    def _resolve_bullet_flights(cls, state: GameState):
        # Dan di chuyen 3 o moi chu ky, kiem tra va cham sau tung buoc di chuyen
        for _ in range(Bullet.SPEED):
            active_bullets = [b for b in state.bullets if b.is_active]
            if not active_bullets:
                break

            # 1. Kiem tra 2 vien dan bay nguoc chieu nhau va cham tren duong bay (head-on)
            for i in range(len(active_bullets)):
                b1 = active_bullets[i]
                if not b1.is_active:
                    continue
                for j in range(i + 1, len(active_bullets)):
                    b2 = active_bullets[j]
                    if not b2.is_active or b1.owner_id == b2.owner_id:
                        continue
                    # Neu bay nguoc chieu va cach nhau 1 buoc di chuyen
                    next_r1, next_c1 = b1.r + b1.direction.dr, b1.c + b1.direction.dc
                    next_r2, next_c2 = b2.r + b2.direction.dr, b2.c + b2.direction.dc
                    if (next_r1, next_c1) == b2.pos and (next_r2, next_c2) == b1.pos:
                        # Triet tieu ca hai vien dan
                        b1.is_active = False
                        b2.is_active = False

            # 2. Tien cac vien dan them 1 o
            for b in active_bullets:
                if b.is_active:
                    b.step_forward()

            # 3. Kiem tra dan ra ngoai bien hoac 2 dan gap nhau tai cung 1 o
            occupied_bullets: dict[tuple[int, int], list[Bullet]] = {}
            for b in active_bullets:
                if not b.is_active:
                    continue
                if not state.is_inside(b.r, b.c):
                    b.is_active = False
                    continue
                occupied_bullets.setdefault(b.pos, []).append(b)

            # Triet tieu cac vien dan o cung 1 o
            for pos, b_list in occupied_bullets.items():
                if len(b_list) > 1:
                    for b in b_list:
                        b.is_active = False

            # 4. Kiem tra va cham voi Thuc the (Wall, Tank, Base)
            for b in active_bullets:
                if not b.is_active:
                    continue
                entity = state.get_entity_at(b.r, b.c)
                if entity is not None and entity.is_alive:
                    # Bao ve can cu dong minh: Dan cua mot phe khong gay sat thuong len can cu cua chinh phe do
                    if isinstance(entity, Base) and entity.player_id == b.owner_id:
                        b.is_active = False
                        continue
                    entity.take_damage(1)
                    b.is_active = False
