import random
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.entities import Action
from task2_tank.engine import GameEngine
from task2_tank.game_state import GameState


class RandomAgent(BaseAgent):
    name = "RandomAgent"

    def __init__(self, seed: int | None = None, name: str | None = None):
        super().__init__(name or "RandomAgent")
        self.rng = random.Random(seed)

    def get_action(self, state: GameState, player_id: int) -> Action:
        legal_actions = GameEngine.get_legal_actions(state, player_id)
        return self.rng.choice(legal_actions)
