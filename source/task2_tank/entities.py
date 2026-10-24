from abc import ABC, abstractmethod
from enum import Enum


class Direction(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

    @property
    def dr(self) -> int:
        return self.value[0]

    @property
    def dc(self) -> int:
        return self.value[1]

    def opposite(self) -> "Direction":
        if self == Direction.UP:
            return Direction.DOWN
        elif self == Direction.DOWN:
            return Direction.UP
        elif self == Direction.LEFT:
            return Direction.RIGHT
        else:
            return Direction.LEFT


class Action(Enum):
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    FIRE = "FIRE"
    STAY = "STAY"

    def to_direction(self) -> Direction | None:
        mapping = {
            Action.MOVE_UP: Direction.UP,
            Action.MOVE_DOWN: Direction.DOWN,
            Action.MOVE_LEFT: Direction.LEFT,
            Action.MOVE_RIGHT: Direction.RIGHT,
        }
        return mapping.get(self)


class Entity(ABC):
    def __init__(self, r: int, c: int, hp: int, max_hp: int):
        self.r = r
        self.c = c
        self.hp = hp
        self.max_hp = max_hp

    @property
    def pos(self) -> tuple[int, int]:
        return (self.r, self.c)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int = 1):
        self.hp = max(0, self.hp - amount)

    @abstractmethod
    def clone(self) -> "Entity":
        pass


class Tank(Entity):
    INITIAL_HP = 6

    def __init__(
        self,
        player_id: int,
        r: int,
        c: int,
        direction: Direction = Direction.UP,
        hp: int = INITIAL_HP,
    ):
        super().__init__(r, c, hp, max_hp=self.INITIAL_HP)
        self.player_id = player_id
        self.direction = direction

    def rotate(self, new_dir: Direction):
        self.direction = new_dir

    def move_to(self, new_r: int, new_c: int, new_dir: Direction | None = None):
        self.r = new_r
        self.c = new_c
        if new_dir is not None:
            self.direction = new_dir

    def clone(self) -> "Tank":
        return Tank(
            player_id=self.player_id,
            r=self.r,
            c=self.c,
            direction=self.direction,
            hp=self.hp,
        )

    def __repr__(self) -> str:
        return f"Tank(P{self.player_id}, pos=({self.r},{self.c}), dir={self.direction.name}, hp={self.hp})"


class Base(Entity):
    INITIAL_HP = 9

    def __init__(self, player_id: int, r: int, c: int, hp: int = INITIAL_HP):
        super().__init__(r, c, hp, max_hp=self.INITIAL_HP)
        self.player_id = player_id

    def clone(self) -> "Base":
        return Base(player_id=self.player_id, r=self.r, c=self.c, hp=self.hp)

    def __repr__(self) -> str:
        return f"Base(P{self.player_id}, pos=({self.r},{self.c}), hp={self.hp})"


class Wall(Entity):
    INITIAL_HP = 3

    def __init__(self, r: int, c: int, hp: int = INITIAL_HP, is_steel: bool = False):
        super().__init__(r, c, hp, max_hp=self.INITIAL_HP)
        self.is_steel = is_steel

    def take_damage(self, amount: int = 1):
        # Tuong thep khong bi pha huy boi dan thong thuong
        if not self.is_steel:
            super().take_damage(amount)

    def clone(self) -> "Wall":
        return Wall(r=self.r, c=self.c, hp=self.hp, is_steel=self.is_steel)

    def __repr__(self) -> str:
        w_type = "SteelWall" if self.is_steel else "BrickWall"
        return f"{w_type}(pos=({self.r},{self.c}), hp={self.hp})"


class Forest:
    """Dia hinh Bui cay / Rung ram (Trees / Forest) - chuan Battle City 1990.
    
    Xe tang co the di vao va an nap duoi tan cay. Dan bay xuyen qua ma khong pha huy cay.
    """
    def __init__(self, r: int, c: int):
        self.r = r
        self.c = c

    @property
    def pos(self) -> tuple[int, int]:
        return (self.r, self.c)

    def clone(self) -> "Forest":
        return Forest(self.r, self.c)

    def __repr__(self) -> str:
        return f"Forest(pos=({self.r},{self.c}))"


class Bullet:
    SPEED = 3

    def __init__(self, owner_id: int, r: int, c: int, direction: Direction):
        self.owner_id = owner_id
        self.r = r
        self.c = c
        self.direction = direction
        self.is_active = True

    @property
    def pos(self) -> tuple[int, int]:
        return (self.r, self.c)

    def step_forward(self):
        # Dan tien len 1 o theo huong bay
        self.r += self.direction.dr
        self.c += self.direction.dc

    def clone(self) -> "Bullet":
        b = Bullet(
            owner_id=self.owner_id,
            r=self.r,
            c=self.c,
            direction=self.direction,
        )
        b.is_active = self.is_active
        return b

    def __repr__(self) -> str:
        return f"Bullet(owner=P{self.owner_id}, pos=({self.r},{self.c}), dir={self.direction.name})"
