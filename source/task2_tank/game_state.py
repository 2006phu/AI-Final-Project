import os
from task2_tank.entities import Direction, Tank, Base, Wall, Bullet, Entity


class GameState:
    def __init__(self, rows: int, cols: int, max_turns: int = 200):
        self.rows = rows
        self.cols = cols
        self.max_turns = max_turns
        self.turn_count = 0

        # Cac thuc the tren ban co
        self.walls: dict[tuple[int, int], Wall] = {}
        self.tanks: dict[int, Tank] = {}
        self.bases: dict[int, Base] = {}
        self.bullets: list[Bullet] = []

    def is_inside(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get_entity_at(self, r: int, c: int) -> Entity | None:
        # Tra ve thuc the (Tank, Base, Wall) tai toa do (r, c) neu co
        for tank in self.tanks.values():
            if tank.is_alive and tank.r == r and tank.c == c:
                return tank

        for base in self.bases.values():
            if base.is_alive and base.r == r and base.c == c:
                return base

        wall = self.walls.get((r, c))
        if wall is not None and wall.is_alive:
            return wall

        return None

    def is_passable_for_tank(self, r: int, c: int) -> bool:
        # O trong khong co chuong ngai vat (tuong, base, tank khac) va nam trong map
        if not self.is_inside(r, c):
            return False
        return self.get_entity_at(r, c) is None

    def has_active_bullet(self, player_id: int) -> bool:
        # Kiem tra nguoi choi da co vien dan nao dang bay tren ban do chua
        for b in self.bullets:
            if b.is_active and b.owner_id == player_id:
                return True
        return False

    def clone(self) -> "GameState":
        # Sao chep trang thai sau phuc vu tim kiem Minimax/Alpha-Beta
        new_state = GameState(self.rows, self.cols, self.max_turns)
        new_state.turn_count = self.turn_count

        new_state.walls = {pos: w.clone() for pos, w in self.walls.items() if w.is_alive}
        new_state.tanks = {pid: t.clone() for pid, t in self.tanks.items()}
        new_state.bases = {pid: b.clone() for pid, b in self.bases.items()}
        new_state.bullets = [b.clone() for b in self.bullets if b.is_active]

        return new_state

    def state_key(self) -> tuple:
        # Tao khoa bam (hashable key) duy nhat phuc vu Transposition Table
        tank_info = []
        for pid in sorted(self.tanks.keys()):
            t = self.tanks[pid]
            tank_info.append((pid, t.r, t.c, t.direction.name, t.hp))

        base_info = []
        for pid in sorted(self.bases.keys()):
            b = self.bases[pid]
            base_info.append((pid, b.hp))

        bullet_info = tuple(
            sorted(
                (b.owner_id, b.r, b.c, b.direction.name)
                for b in self.bullets
                if b.is_active
            )
        )

        # Chi luu tuong gach bi thay doi mau de toi uu toc do bam
        wall_info = tuple(
            sorted(
                (pos, w.hp)
                for pos, w in self.walls.items()
                if w.is_alive and not w.is_steel and w.hp < w.max_hp
            )
        )

        return (
            self.turn_count,
            tuple(tank_info),
            tuple(base_info),
            bullet_info,
            wall_info,
        )

    @classmethod
    def from_string(cls, text: str, max_turns: int = 200) -> "GameState":
        # Khoi tao GameState tu chuoi van ban ky tu
        lines = [line.strip().split() for line in text.strip().splitlines() if line.strip()]
        if not lines:
            raise ValueError("Du lieu ban do rong!")

        rows = len(lines)
        cols = len(lines[0])
        state = cls(rows, cols, max_turns)

        for r in range(rows):
            for c in range(cols):
                char = lines[r][c]
                if char == "#":
                    # Tuong gach
                    state.walls[(r, c)] = Wall(r, c, hp=Wall.INITIAL_HP, is_steel=False)
                elif char == "@":
                    # Tuong thep
                    state.walls[(r, c)] = Wall(r, c, hp=Wall.INITIAL_HP, is_steel=True)
                elif char == "1":
                    # Tank 0 (Player 1) - mac dinh quay len UP
                    state.tanks[0] = Tank(player_id=0, r=r, c=c, direction=Direction.UP)
                elif char == "2":
                    # Tank 1 (Player 2) - mac dinh quay xuong DOWN
                    state.tanks[1] = Tank(player_id=1, r=r, c=c, direction=Direction.DOWN)
                elif char == "A":
                    # Base 0 (Player 1)
                    state.bases[0] = Base(player_id=0, r=r, c=c)
                elif char == "B":
                    # Base 1 (Player 2)
                    state.bases[1] = Base(player_id=1, r=r, c=c)
                elif char == ".":
                    pass  # O trong
                else:
                    raise ValueError(f"Ky tu khong hop le tren ban do: '{char}' tai ({r}, {c})")

        return state

    @classmethod
    def from_file(cls, filepath: str, max_turns: int = 200) -> "GameState":
        # Khoi tao GameState tu tap tin van ban .txt
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Khong tim thay tap tin ban do: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return cls.from_string(f.read(), max_turns)

    def render(self) -> str:
        # Bieu dien trang thai game thanh van ban ASCII
        grid = [["." for _ in range(self.cols)] for _ in range(self.rows)]

        # 1. Ve tuong
        for (r, c), w in self.walls.items():
            if w.is_alive:
                grid[r][c] = "@" if w.is_steel else str(w.hp)

        # 2. Ve base
        for pid, b in self.bases.items():
            if b.is_alive:
                grid[b.r][b.c] = "A" if pid == 0 else "B"

        # 3. Ve dan
        for b in self.bullets:
            if b.is_active and self.is_inside(b.r, b.c):
                grid[b.r][b.c] = "*"

        # 4. Ve tank
        dir_symbols = {
            Direction.UP: "^",
            Direction.DOWN: "v",
            Direction.LEFT: "<",
            Direction.RIGHT: ">",
        }
        for pid, t in self.tanks.items():
            if t.is_alive:
                sym = dir_symbols.get(t.direction, "?")
                grid[t.r][t.c] = f"{pid+1}{sym}"

        lines = [f"Turn: {self.turn_count}/{self.max_turns}"]
        for r in range(self.rows):
            row_str = " ".join(f"{grid[r][c]:>2}" for c in range(self.cols))
            lines.append(row_str)

        t0_hp = self.tanks[0].hp if 0 in self.tanks else 0
        t1_hp = self.tanks[1].hp if 1 in self.tanks else 0
        b0_hp = self.bases[0].hp if 0 in self.bases else 0
        b1_hp = self.bases[1].hp if 1 in self.bases else 0
        lines.append(f"P1: Tank HP={t0_hp}, Base HP={b0_hp} | P2: Tank HP={t1_hp}, Base HP={b1_hp}")
        return "\n".join(lines)
