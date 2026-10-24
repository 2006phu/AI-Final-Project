from task2_tank.agents.base_agent import BaseAgent
from task2_tank.entities import Action
from task2_tank.game_state import GameState


class HumanAgent(BaseAgent):
    name = "HumanAgent"

    def __init__(self, name: str | None = None):
        super().__init__(name or "HumanPlayer")
        self.queued_action: Action = Action.STAY

    def set_action(self, action: Action):
        self.queued_action = action

    def get_action(self, state: GameState, player_id: int) -> Action:
        action = self.queued_action
        self.queued_action = Action.STAY
        return action
