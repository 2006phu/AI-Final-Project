from abc import ABC, abstractmethod
from task2_tank.entities import Action
from task2_tank.game_state import GameState


class BaseAgent(ABC):
    # Lop co so truu tuong cho moi Agent trong Tank Battle
    # Cac nhom sinh vien khac chi can ke thua lop nay va override ham get_action
    name: str = "BaseAgent"

    def __init__(self, name: str | None = None):
        if name:
            self.name = name

    @abstractmethod
    def get_action(self, state: GameState, player_id: int) -> Action:
        # Nhap vao trang thai hien tai va ID nguoi choi (0 hoac 1)
        # Tra ve 1 trong 6 hanh dong cua Action
        pass

    def __repr__(self) -> str:
        return f"<{self.name}>"
