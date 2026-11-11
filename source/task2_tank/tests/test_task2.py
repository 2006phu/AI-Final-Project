import os
import pytest
from task2_tank.agents.random_agent import RandomAgent
from task2_tank.agents.search_agent import SearchAgent
from task2_tank.engine import GameEngine
from task2_tank.entities import Action, Direction, Tank, Base, Wall, Bullet
from task2_tank.game_state import GameState
from task2_tank.heuristic import TankEvaluator
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
    # Khong nem ngoai le, tra ve dict khi quet agents_dir
    assert isinstance(custom, dict)


def test_tactical_clash_map_structure_and_symmetry():
    map_path = os.path.join(os.path.dirname(__file__), "..", "maps", "tactical_clash_13x13.txt")
    assert os.path.exists(map_path)
    state = GameState.from_file(map_path)
    assert state.rows == 13 and state.cols == 13
    assert len(state.tanks) == 2
    assert len(state.bases) == 2
    assert 0 in state.bases and state.bases[0].pos == (11, 6)
    assert 1 in state.bases and state.bases[1].pos == (1, 6)
    # Co rung cay o hai ben canh
    assert len(state.forests) > 0
    # Co tuong thep va tuong gach
    steel_count = sum(1 for w in state.walls.values() if w.is_steel)
    brick_count = sum(1 for w in state.walls.values() if not w.is_steel)
    assert steel_count > 0 and brick_count > 0


def test_forest_tile_passable_and_bullet_passthrough():
    map_str = """
    . . .
    1 T 2
    A . B
    """
    state = GameState.from_string(map_str)
    assert len(state.forests) == 1
    assert (1, 1) in state.forests

    # Xe tang co the tien vao rung
    assert state.is_passable_for_tank(1, 1) is True

    # Dan bay xuyen qua rung khong bi triet tieu
    next_s = GameEngine.step(state, Action.MOVE_RIGHT, Action.STAY)
    assert next_s.tanks[0].pos == (1, 1)  # Tank 0 da tien vao o rung

    # Ban dan tu trong rung hoac xuyen qua rung
    shoot_s = GameEngine.step(next_s, Action.FIRE, Action.STAY)
    # Dan bay tu o rung (1, 1) sang phai va tan cong vao Tank 2 o (1, 2)
    assert shoot_s.tanks[1].hp < Tank.INITIAL_HP


def test_adversarial_search_agents_with_active_enemy_bullets():
    state = GameState(9, 9)
    state.tanks[0] = Tank(0, r=7, c=4, direction=Direction.UP)
    state.tanks[1] = Tank(1, r=1, c=4, direction=Direction.DOWN)
    state.bases[0] = Base(0, r=8, c=4)
    state.bases[1] = Base(1, r=0, c=4)
    # Vien dan cua doi phuong dang bay thang ve phia xe va can cu cua Player 0
    state.bullets.append(Bullet(owner_id=1, r=4, c=4, direction=Direction.DOWN))

    agents = [
        SearchAgent.create_minimax(depth=2),
        SearchAgent.create_alpha_beta(depth=2),
        SearchAgent.create_heuristic_minimax(depth=2),
        SearchAgent.create_heuristic_alpha_beta(depth=2),
    ]
    for agent in agents:
        act0 = agent.get_action(state, player_id=0)
        act1 = agent.get_action(state, player_id=1)
        assert isinstance(act0, Action)
        assert isinstance(act1, Action)


def test_state_key_distinguishes_intact_vs_destroyed_brick_walls():
    state1 = GameState(5, 5)
    state1.tanks[0] = Tank(0, r=4, c=2, direction=Direction.UP)
    state1.tanks[1] = Tank(1, r=0, c=2, direction=Direction.DOWN)
    state1.bases[0] = Base(0, r=4, c=0)
    state1.bases[1] = Base(1, r=0, c=4)
    state1.walls[(2, 2)] = Wall(2, 2, hp=3, is_steel=False)

    state2 = state1.clone()
    state2.walls[(2, 2)].take_damage(1)  # hp=2

    state3 = state1.clone()
    del state3.walls[(2, 2)]  # Tuong da bi pha huy hoan toan (hp=0)

    assert state1.state_key() != state2.state_key()
    assert state1.state_key() != state3.state_key()
    assert state2.state_key() != state3.state_key()


def test_bullet_travels_exact_3_cells_per_cycle_and_symmetric_adjacent_fire():
    # 1. Kiem tra dan bay dung 3 o moi chu ky tren ban do trong
    open_state = GameState(9, 9)
    open_state.tanks[0] = Tank(0, r=7, c=4, direction=Direction.UP)
    open_state.tanks[1] = Tank(1, r=0, c=0, direction=Direction.DOWN)
    open_state.bases[0] = Base(0, r=8, c=4)
    open_state.bases[1] = Base(0, r=0, c=8)

    s1 = GameEngine.step(open_state, Action.FIRE, Action.STAY)
    assert len(s1.bullets) == 1
    assert s1.bullets[0].pos == (4, 4)  # Tu r=7 tien len 3 o -> r=4

    # 2. Kiem tra 2 xe tang dung sat nhau (cach 1 o) ban cung luc -> doi xung 100% (2 vien dan triet tieu giua khong trung)
    adj_state = GameState(5, 5)
    adj_state.tanks[0] = Tank(0, r=2, c=2, direction=Direction.UP)
    adj_state.tanks[1] = Tank(1, r=1, c=2, direction=Direction.DOWN)
    adj_state.bases[0] = Base(0, r=4, c=2)
    adj_state.bases[1] = Base(1, r=0, c=2)

    s_adj = GameEngine.step(adj_state, Action.FIRE, Action.FIRE)
    assert s_adj.tanks[0].hp == Tank.INITIAL_HP
    assert s_adj.tanks[1].hp == Tank.INITIAL_HP
    assert len(s_adj.bullets) == 0

    # Neu chi 1 ben ban thi doi phuong nhan dung 1 sat thuong doi xung
    s_p0 = GameEngine.step(adj_state, Action.FIRE, Action.STAY)
    s_p1 = GameEngine.step(adj_state, Action.STAY, Action.FIRE)
    assert s_p0.tanks[1].hp == Tank.INITIAL_HP - 1
    assert s_p1.tanks[0].hp == Tank.INITIAL_HP - 1


def test_agents_can_rotate_toward_destructible_brick_wall():
    state = GameState(5, 5)
    # Tank 0 dang nhin sang phai, bi bao quanh boi 3 tuong thep (trai, phai, duoi) va 1 tuong gach o phia tren (1, 2)
    # Phia sau tuong gach (1, 2) la Base dich (0, 2)
    state.tanks[0] = Tank(0, r=2, c=2, direction=Direction.RIGHT)
    state.tanks[1] = Tank(1, r=0, c=0, direction=Direction.DOWN)
    state.bases[0] = Base(0, r=4, c=4)
    state.bases[1] = Base(1, r=0, c=2)
    state.walls[(1, 2)] = Wall(1, 2, hp=3, is_steel=False)
    state.walls[(2, 3)] = Wall(2, 3, hp=3, is_steel=True)
    state.walls[(2, 1)] = Wall(2, 1, hp=3, is_steel=True)
    state.walls[(3, 2)] = Wall(3, 2, hp=3, is_steel=True)

    # SearchAgent phai nhan dien va xoay nong phao len tren (MOVE_UP) de pha tuong gach thay vi ket cung STAY/MOVE_RIGHT
    search_ab = SearchAgent.create_heuristic_alpha_beta(depth=2)
    ordered = search_ab._order_actions(state, GameEngine.get_legal_actions(state, 0), player_id=0)
    assert ordered[0] == Action.MOVE_UP
    act_ab = search_ab.get_action(state, player_id=0)
    assert act_ab == Action.MOVE_UP


def test_friendly_base_fire_protection_and_agent_safety():
    state = GameState(5, 5)
    # Tank 0 o vi tri (3, 2) dang quay mat xuong duoi (Direction.DOWN), ngay phia truoc la Can cu Base 0 tai (4, 2)
    state.tanks[0] = Tank(0, r=3, c=2, direction=Direction.DOWN)
    state.tanks[1] = Tank(1, r=0, c=0, direction=Direction.DOWN)
    state.bases[0] = Base(0, r=4, c=2)
    state.bases[1] = Base(1, r=0, c=4)

    # 1. Ham would_hit_own_base phai phat hien huong ban vao can cu nha minh
    assert TankEvaluator.would_hit_own_base(state, player_id=0) is True
    assert TankEvaluator.would_hit_own_base(state, player_id=1) is False

    # 2. Cac SearchAgent (Minimax, Alpha-Beta, Heuristic) tuyet doi khong duoc chon hanh dong FIRE
    agents = [
        SearchAgent.create_minimax(depth=2),
        SearchAgent.create_alpha_beta(depth=2),
        SearchAgent.create_heuristic_minimax(depth=2),
        SearchAgent.create_heuristic_alpha_beta(depth=2),
    ]
    for agent in agents:
        act = agent.get_action(state, player_id=0)
        assert act != Action.FIRE, f"Agent {agent.name} khong duoc phep chon FIRE khi ngam vao can cu nha minh!"

    # 3. Kiem tra Friendly Fire tai Engine: Neu dan cua Player 0 bay vao Base 0 thi Base 0 khong bi mat mau
    s_friendly = GameEngine.step(state, Action.FIRE, Action.STAY)
    assert s_friendly.bases[0].hp == Base.INITIAL_HP, "Base nha minh phai mien nhiem voi dan cua dong minh!"

    # 4. Neu dan cua Player 1 bay vao Base 0 thi Base 0 phai bi tru mau binh thuong
    s_enemy_fire = state.clone()
    s_enemy_fire.bullets.append(Bullet(owner_id=1, r=3, c=2, direction=Direction.DOWN))
    s_hit = GameEngine.step(s_enemy_fire, Action.STAY, Action.STAY)
    assert s_hit.bases[0].hp == Base.INITIAL_HP - 1, "Base phai nhan sat thuong tu dan cua ke thu!"





