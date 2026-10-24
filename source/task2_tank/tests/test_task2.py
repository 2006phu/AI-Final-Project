import os
import pytest
from task2_tank.agents.random_agent import RandomAgent
from task2_tank.agents.search_agent import SearchAgent
from task2_tank.engine import GameEngine
from task2_tank.entities import Action, Direction, Tank, Base, Wall, Bullet
from task2_tank.game_state import GameState
from task2_tank.gui import discover_custom_agents


def test_entities_and_damage():
    tank = Tank(player_id=0, r=2, c=2, direction=Direction.UP)
    assert tank.hp == 6 and tank.is_alive
    tank.take_damage(2)
    assert tank.hp == 4

    wall = Wall(r=1, c=1, hp=3, is_steel=False)
    wall.take_damage(1)
    assert wall.hp == 2

    steel = Wall(r=1, c=2, hp=3, is_steel=True)
    steel.take_damage(1)
    assert steel.hp == 3  # Tuong thep mien nhiem sat thuong


def test_bullet_cell_by_cell_and_neutralization():
    state = GameState(7, 7)
    state.tanks[0] = Tank(0, r=5, c=3, direction=Direction.UP)
    state.tanks[1] = Tank(1, r=1, c=3, direction=Direction.DOWN)
    state.bases[0] = Base(0, r=6, c=3)
    state.bases[1] = Base(1, r=0, c=3)

    # 1. Ban dan doi dau -> triet tieu
    next_s = GameEngine.step(state, Action.FIRE, Action.FIRE)
    assert len(next_s.bullets) == 0
    assert next_s.tanks[0].hp == 6
    assert next_s.tanks[1].hp == 6

    # 2. Ban trung tuong gach o giua
    state.walls[(3, 3)] = Wall(3, 3, hp=3)
    s_hit = GameEngine.step(state, Action.FIRE, Action.STAY)
    assert (3, 3) in s_hit.walls
    assert s_hit.walls[(3, 3)].hp == 2


def test_tank_collision_resolution():
    state = GameState(5, 5)
    state.tanks[0] = Tank(0, r=2, c=1, direction=Direction.RIGHT)
    state.tanks[1] = Tank(1, r=2, c=2, direction=Direction.LEFT)
    state.bases[0] = Base(0, r=4, c=2)
    state.bases[1] = Base(1, r=0, c=2)

    # 2 xe doi cho cho nhau -> conflict -> dung yen
    s_next = GameEngine.step(state, Action.MOVE_RIGHT, Action.MOVE_LEFT)
    assert s_next.tanks[0].pos == (2, 1)
    assert s_next.tanks[1].pos == (2, 2)


def test_search_agent_equivalence():
    map_path = os.path.join(os.path.dirname(__file__), "..", "maps", "arena_11x11.txt")
    state = GameState.from_file(map_path)

    # 1. Minimax vs Alpha-Beta (d=2) phai tra ve cung hanh dong
    mm = SearchAgent.create_minimax(depth=2)
    ab = SearchAgent.create_alpha_beta(depth=2)
    act_mm = mm.get_action(state, player_id=0)
    act_ab = ab.get_action(state, player_id=0)
    assert act_mm == act_ab
    assert ab.nodes_explored <= mm.nodes_explored

    # 2. Heuristic Minimax vs Heuristic Alpha-Beta (d=2) phai tra ve cung hanh dong
    hmm = SearchAgent.create_heuristic_minimax(depth=2)
    hab = SearchAgent.create_heuristic_alpha_beta(depth=2)
    act_hmm = hmm.get_action(state, player_id=0)
    act_hab = hab.get_action(state, player_id=0)
    assert act_hmm == act_hab
    assert hab.nodes_explored <= hmm.nodes_explored


def test_dynamic_agent_discovery():
    agents_dir = os.path.join(os.path.dirname(__file__), "..", "agents")
    custom = discover_custom_agents(agents_dir)
    # Khong ném ngoai le, tra ve dict
    assert isinstance(custom, dict)
