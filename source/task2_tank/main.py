import argparse
import os
import sys

# Dam bao import duoc task2_tank
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.human_agent import HumanAgent
from task2_tank.agents.random_agent import RandomAgent
from task2_tank.agents.search_agent import SearchAgent
from task2_tank.engine import GameEngine
from task2_tank.game_state import GameState
from task2_tank.gui import TankBattleGUI, discover_custom_agents


def build_agent(agent_name: str, depth: int, agents_dir: str) -> BaseAgent:
    name_lower = agent_name.lower()
    if name_lower in ("hab", "heuristic_ab", "heuristic_alphabeta", "heuristic_alpha_beta"):
        return SearchAgent.create_heuristic_alpha_beta(depth=depth)
    elif name_lower in ("hmm", "heuristic_minimax"):
        return SearchAgent.create_heuristic_minimax(depth=depth)
    elif name_lower in ("ab", "alphabeta", "alpha_beta"):
        return SearchAgent.create_alpha_beta(depth=depth)
    elif name_lower in ("mm", "minimax"):
        return SearchAgent.create_minimax(depth=depth)
    elif name_lower in ("random", "rand"):
        return RandomAgent()
    elif name_lower in ("human", "player"):
        return HumanAgent()

    # Kiem tra nap dong tu custom agents (ho tro ten hien thi, ten class hoac tu khoa ngan)
    custom_agents = discover_custom_agents(agents_dir)
    for c_name, c_cls in custom_agents.items():
        if (
            name_lower == c_name.lower()
            or name_lower == c_cls.__name__.lower()
            or name_lower in c_name.lower()
            or name_lower in c_cls.__name__.lower()
        ):
            return c_cls()

    raise ValueError(f"Khong tim thay Agent: '{agent_name}'. Cac lua chon: hab, hmm, ab, mm, random, human, hoac ten class trong agents/")


def run_headless_simulation(map_path: str, p1: BaseAgent, p2: BaseAgent, max_turns: int = 200):
    state = GameState.from_file(map_path, max_turns=max_turns)
    print("=" * 60)
    print(f" MO PHONG TANK BATTLE (HEADLESS)")
    print(f" Ban do: {os.path.basename(map_path)}")
    print(f" P1 (Green):  {p1.name}")
    print(f" P2 (Yellow): {p2.name}")
    print("=" * 60)

    while not GameEngine.is_terminal(state):
        a0 = p1.get_action(state, player_id=0)
        a1 = p2.get_action(state, player_id=1)
        state = GameEngine.step(state, a0, a1)
        if state.turn_count % 10 == 0:
            t0_hp = state.tanks[0].hp if 0 in state.tanks else 0
            t1_hp = state.tanks[1].hp if 1 in state.tanks else 0
            b0_hp = state.bases[0].hp if 0 in state.bases else 0
            b1_hp = state.bases[1].hp if 1 in state.bases else 0
            print(f"Turn {state.turn_count:>3}: P1 Tank={t0_hp} Base={b0_hp} | P2 Tank={t1_hp} Base={b1_hp}")

    winner = GameEngine.get_winner(state)
    print("=" * 60)
    print(f"KET QUA CUOI CUNG (Sau {state.turn_count} chu ky):")
    if winner == 0:
        print(">> NGUOI CHIEN THANG: PLAYER 1 (GREEN)")
    elif winner == 1:
        print(">> NGUOI CHIEN THANG: PLAYER 2 (YELLOW)")
    else:
        print(">> KET QUA: HOA CO (DRAW)")
    print("=" * 60)


def main():
    base_dir = os.path.dirname(__file__)
    default_map = os.path.join(base_dir, "maps", "standard_13x13.txt")
    agents_dir = os.path.join(base_dir, "agents")

    parser = argparse.ArgumentParser(description="Tank Battle Game (AI Final Project)")
    parser.add_argument("--map", type=str, default=default_map, help="Duong dan file ban do (.txt)")
    parser.add_argument("--p1", type=str, default="hab", help="Thuat toan P1: hab, hmm, ab, mm, random, human, custom")
    parser.add_argument("--p2", type=str, default="hab", help="Thuat toan P2: hab, hmm, ab, mm, random, human, custom")
    parser.add_argument("--depth", type=int, default=2, help="Do sau tim kiem (plies, mac dinh=2)")
    parser.add_argument("--turns", type=int, default=200, help="So chu ky toi da khi mo phong headless (mac dinh=200)")
    parser.add_argument("--headless", action="store_true", help="Chay mo phong khong mo cua so GUI")
    args = parser.parse_args()

    if args.headless:
        p1_agent = build_agent(args.p1, args.depth, agents_dir)
        p2_agent = build_agent(args.p2, args.depth, agents_dir)
        run_headless_simulation(args.map, p1_agent, p2_agent, max_turns=args.turns)
    else:
        # Khoi dong GUI tuong tac: Chi can 1 lenh chay 'python source/task2_tank/main.py'
        # Toan bo lua chon Ban do, Agent P1, Agent P2, Speed, Play/Pause deu thao tac bang chuot tren GUI!
        maps_dir = os.path.join(base_dir, "maps")
        gui = TankBattleGUI(maps_dir, agents_dir, initial_map=args.map, initial_p1=args.p1, initial_p2=args.p2)
        gui.run()


if __name__ == "__main__":
    main()
