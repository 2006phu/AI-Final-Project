import importlib.util
import inspect
import math
import os
import random
import sys
import pygame

# Dam bao import duoc task2_tank khi chay truc tiep file gui.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.human_agent import HumanAgent
from task2_tank.agents.random_agent import RandomAgent
from task2_tank.agents.search_agent import SearchAgent
from task2_tank.engine import GameEngine
from task2_tank.entities import Action, Direction, Tank, Base, Wall, Bullet
from task2_tank.game_state import GameState

# Bat High-DPI Awareness tren Windows de font chu va do hoa khong bi mo
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


CORE_AGENT_FILES = {"base_agent.py", "search_agent.py", "random_agent.py", "human_agent.py"}


def discover_custom_agents(agents_dir: str) -> dict[str, type]:
    """Quet dong cac file trong agents_dir va tra ve dict[ten_lop, class]."""
    custom_agents = {}
    if os.path.exists(agents_dir):
        for fname in sorted(os.listdir(agents_dir)):
            if fname.endswith(".py") and not fname.startswith("__") and fname not in CORE_AGENT_FILES:
                filepath = os.path.join(agents_dir, fname)
                if not os.path.isfile(filepath):
                    continue
                mod_name = f"dynamic_agent_{fname[:-3]}"
                try:
                    spec = importlib.util.spec_from_file_location(mod_name, filepath)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        for attr_name in dir(mod):
                            cls = getattr(mod, attr_name)
                            if (
                                inspect.isclass(cls)
                                and issubclass(cls, BaseAgent)
                                and cls.__name__ not in ("BaseAgent", "SearchAgent", "RandomAgent", "HumanAgent")
                            ):
                                name = getattr(cls, "name", None) or cls.__name__
                                custom_agents[name] = cls
                except Exception as e:
                    print(f"Khong the nap agent tu {fname}: {e}")
    return custom_agents


def discover_all_agent_factories(agents_dir: str) -> list[tuple[str, any]]:
    # Danh sach cac agent tieu chuan va cac agent nap dong tu agents/
    factories = [
        ("Heuristic Alpha-Beta", lambda: SearchAgent.create_heuristic_alpha_beta(depth=2)),
        ("Heuristic Minimax", lambda: SearchAgent.create_heuristic_minimax(depth=2)),
        ("Alpha-Beta", lambda: SearchAgent.create_alpha_beta(depth=2)),
        ("Minimax", lambda: SearchAgent.create_minimax(depth=2)),
        ("RandomAgent", lambda: RandomAgent()),
        ("HumanPlayer (Keyboard)", lambda: HumanAgent()),
    ]

    # Quet dong cac custom agents
    custom_agents = discover_custom_agents(agents_dir)
    for c_name, c_cls in custom_agents.items():
        factories.append((f"Custom: {c_name}", c_cls))

    return factories


def discover_all_maps(maps_dir: str) -> list[tuple[str, str]]:
    maps = []
    if os.path.exists(maps_dir):
        for fname in sorted(os.listdir(maps_dir)):
            if fname.endswith(".txt"):
                display_name = fname.replace(".txt", "").replace("_", " ").title()
                maps.append((display_name, os.path.join(maps_dir, fname)))
    return maps


class TankBattleGUI:
    CELL_SIZE = 48
    PANEL_WIDTH = 420
    FPS_DEFAULT = 6

    # Bang mau chien truong Cyber Arcade
    COLOR_BG = (14, 16, 22)
    COLOR_GRID = (28, 34, 46)
    COLOR_GRID_DOT = (45, 55, 75)
    COLOR_PANEL_BG = (22, 26, 36)
    COLOR_PANEL_CARD = (30, 36, 50)
    COLOR_PANEL_CARD_HOVER = (38, 46, 64)
    COLOR_BORDER = (48, 58, 80)
    COLOR_TEXT = (245, 248, 255)
    COLOR_TEXT_MUTED = (165, 175, 195)
    COLOR_ACCENT = (52, 152, 219)
    COLOR_GOLD = (241, 196, 15)

    COLOR_P1 = (46, 204, 113)       # Cyber Emerald (Player 1)
    COLOR_P1_DARK = (26, 120, 65)
    COLOR_P1_GLOW = (80, 235, 145)
    COLOR_P2 = (231, 76, 60)        # Crimson Strike (Player 2)
    COLOR_P2_DARK = (145, 38, 28)
    COLOR_P2_GLOW = (255, 105, 85)

    COLOR_BASE_P1 = (41, 128, 185)  # Can cu xanh P1
    COLOR_BASE_P2 = (211, 84, 0)    # Can cu cam P2
    COLOR_BRICK = (185, 75, 45)     # Gach do terracotta
    COLOR_BRICK_DARK = (125, 45, 25)
    COLOR_STEEL = (115, 130, 152)   # Thep titan
    COLOR_STEEL_LIGHT = (210, 225, 245)
    COLOR_STEEL_DARK = (45, 52, 65)

    COLOR_BTN_NORMAL = (40, 48, 64)
    COLOR_BTN_HOVER = (58, 68, 92)

    def __init__(self, maps_dir: str, agents_dir: str, initial_map: str | None = None, initial_p1: str | None = None, initial_p2: str | None = None):
        pygame.init()
        pygame.font.init()

        self.maps_dir = maps_dir
        self.agents_dir = agents_dir

        self.available_maps = discover_all_maps(maps_dir)
        if not self.available_maps:
            raise RuntimeError("Khong tim thay ban do nao trong thu muc maps/")

        self.available_agents = discover_all_agent_factories(agents_dir)

        self.current_map_idx = 0
        if initial_map:
            target_base = os.path.basename(initial_map).lower()
            for idx, (_, path) in enumerate(self.available_maps):
                if os.path.basename(path).lower() == target_base:
                    self.current_map_idx = idx
                    break

        self.current_p1_idx = 0
        if initial_p1:
            for idx, (lbl, _) in enumerate(self.available_agents):
                if initial_p1.lower() in lbl.lower():
                    self.current_p1_idx = idx
                    break

        self.current_p2_idx = 0
        if initial_p2:
            for idx, (lbl, _) in enumerate(self.available_agents):
                if initial_p2.lower() in lbl.lower():
                    self.current_p2_idx = idx
                    break

        self.logs: list[str] = ["Battle City Engine San Sang! Nhan [PLAY] de bat dau tran chien."]

        # Cac muc lua chon so buoc toi da (Max Turns)
        self.max_turns_options = [50, 100, 150, 200, 300, 500, 1000]
        self.current_turns_idx = 3  # Mac dinh 200 buoc
        self.max_turns = self.max_turns_options[self.current_turns_idx]

        self.p1_agent = self._instantiate_agent(self.current_p1_idx)
        self.p2_agent = self._instantiate_agent(self.current_p2_idx)

        # Su dung he thong font he thong ro net ho tro Unicode va doc thoai mai tren High-DPI
        font_family = "segoeui,tahoma,arial,consolas"
        self.font = pygame.font.SysFont(font_family, 13)
        self.font_bold = pygame.font.SysFont(font_family, 14, bold=True)
        self.font_title = pygame.font.SysFont(font_family, 19, bold=True)
        self.font_mini = pygame.font.SysFont(font_family, 12)
        self.font_tag = pygame.font.SysFont(font_family, 11, bold=True)
        self.clock = pygame.time.Clock()

        # Nap ban do dau tien
        self._load_current_map()

        self.is_running = True
        self.is_paused = True
        self.fps = self.FPS_DEFAULT

        self.last_a0 = Action.STAY
        self.last_a1 = Action.STAY
        self.p1_time = 0.0
        self.p2_time = 0.0

        # He thong Hat Hieu ung Chay no (Particle Sparks)
        self.particles: list[dict] = []
        self.radar_angle = 0.0

        # Danh sach nut bam UI tuong tac tren man hinh
        self.buttons = {}

    def _instantiate_agent(self, idx: int) -> BaseAgent:
        label, factory = self.available_agents[idx]
        try:
            return factory()
        except Exception as e:
            self.add_log(f"Loi khoi tao {label}: {e} -> dung RandomAgent")
            return RandomAgent()

    def _load_current_map(self):
        map_path = self.available_maps[self.current_map_idx][1]
        max_turns = getattr(self, "max_turns", 200)
        self.state = GameState.from_file(map_path, max_turns=max_turns)
        self.grid_width = self.state.cols * self.CELL_SIZE
        self.grid_height = self.state.rows * self.CELL_SIZE
        self.window_width = self.grid_width + self.PANEL_WIDTH
        self.window_height = max(self.grid_height, 720)

        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Tank Battle Simulator - Adversarial Search (AI Final Project)")

    def add_log(self, text: str):
        self.logs.append(text)
        if len(self.logs) > 7:
            self.logs.pop(0)

    def spawn_explosion(self, cell_c: int, cell_r: int, color=(255, 160, 40), count: int = 14):
        px = cell_c * self.CELL_SIZE + self.CELL_SIZE // 2
        py = cell_r * self.CELL_SIZE + self.CELL_SIZE // 2
        for _ in range(count):
            angle = random.random() * 2 * math.pi
            speed = random.uniform(1.2, 4.5)
            self.particles.append({
                "x": px + (random.random() - 0.5) * 8,
                "y": py + (random.random() - 0.5) * 8,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": color,
                "radius": random.uniform(3.0, 6.0),
                "life": random.randint(10, 20),
                "max_life": 20,
            })

    def restart_game(self):
        self._load_current_map()
        self.p1_agent = self._instantiate_agent(self.current_p1_idx)
        self.p2_agent = self._instantiate_agent(self.current_p2_idx)
        self.is_paused = True
        self.last_a0 = Action.STAY
        self.last_a1 = Action.STAY
        self.particles.clear()
        self.add_log("Khoi dong lai tran dau moi!")

    def step_game(self):
        if GameEngine.is_terminal(self.state):
            winner = GameEngine.get_winner(self.state)
            if winner == 0:
                self.add_log("KET THUC: Player 1 (Green) CHIEN THANG!")
            elif winner == 1:
                self.add_log("KET THUC: Player 2 (Crimson) CHIEN THANG!")
            else:
                self.add_log("KET THUC: HOA CO!")
            self.is_paused = True
            return

        old_t0_hp = self.state.tanks[0].hp if 0 in self.state.tanks and self.state.tanks[0].is_alive else 0
        old_t1_hp = self.state.tanks[1].hp if 1 in self.state.tanks and self.state.tanks[1].is_alive else 0
        old_b0_hp = self.state.bases[0].hp if 0 in self.state.bases and self.state.bases[0].is_alive else 0
        old_b1_hp = self.state.bases[1].hp if 1 in self.state.bases and self.state.bases[1].is_alive else 0
        old_walls = {pos: w.hp for pos, w in self.state.walls.items() if w.is_alive}

        try:
            t0 = pygame.time.get_ticks()
            a0 = self.p1_agent.get_action(self.state, player_id=0)
            self.p1_time = pygame.time.get_ticks() - t0
        except Exception as e:
            a0 = Action.STAY
            self.add_log(f"Loi P1: {e}")

        try:
            t1 = pygame.time.get_ticks()
            a1 = self.p2_agent.get_action(self.state, player_id=1)
            self.p2_time = pygame.time.get_ticks() - t1
        except Exception as e:
            a1 = Action.STAY
            self.add_log(f"Loi P2: {e}")

        self.last_a0 = a0
        self.last_a1 = a1

        self.state = GameEngine.step(self.state, a0, a1)
        self.add_log(f"Turn {self.state.turn_count}: P1={a0.name}, P2={a1.name}")

        # Phat hien sat thuong de tao hieu ung no hat
        if 0 in self.state.tanks and self.state.tanks[0].hp < old_t0_hp:
            self.spawn_explosion(self.state.tanks[0].c, self.state.tanks[0].r, (231, 76, 60), 16)
        if 1 in self.state.tanks and self.state.tanks[1].hp < old_t1_hp:
            self.spawn_explosion(self.state.tanks[1].c, self.state.tanks[1].r, (46, 204, 113), 16)
        if 0 in self.state.bases and self.state.bases[0].hp < old_b0_hp:
            self.spawn_explosion(self.state.bases[0].c, self.state.bases[0].r, (241, 196, 15), 20)
        if 1 in self.state.bases and self.state.bases[1].hp < old_b1_hp:
            self.spawn_explosion(self.state.bases[1].c, self.state.bases[1].r, (230, 126, 34), 20)
        for pos, old_hp in old_walls.items():
            w = self.state.walls.get(pos)
            if w is None or not w.is_alive or w.hp < old_hp:
                self.spawn_explosion(pos[1], pos[0], (230, 126, 34), 8)

    def run(self) -> str:
        while self.is_running:
            self._handle_events()
            if not self.is_paused:
                self.step_game()
            self._render()
            self.clock.tick(self.fps if not self.is_paused else 30)

        return "menu"

    def _handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn_id, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        self._handle_button_click(btn_id)
                        break

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                elif event.key == pygame.K_SPACE:
                    self.is_paused = not self.is_paused
                    self.add_log("PLAY" if not self.is_paused else "PAUSE")
                elif event.key == pygame.K_s:
                    self.is_paused = True
                    self.step_game()
                elif event.key == pygame.K_r:
                    self.restart_game()
                elif event.key == pygame.K_UP:
                    self.fps = min(60, self.fps + 2)
                elif event.key == pygame.K_DOWN:
                    self.fps = max(1, self.fps - 2)

                # Ban phim cho HumanAgent
                if isinstance(self.p1_agent, HumanAgent):
                    if event.key == pygame.K_w:
                        self.p1_agent.set_action(Action.MOVE_UP)
                    elif event.key == pygame.K_s:
                        self.p1_agent.set_action(Action.MOVE_DOWN)
                    elif event.key == pygame.K_a:
                        self.p1_agent.set_action(Action.MOVE_LEFT)
                    elif event.key == pygame.K_d:
                        self.p1_agent.set_action(Action.MOVE_RIGHT)
                    elif event.key in (pygame.K_f, pygame.K_j):
                        self.p1_agent.set_action(Action.FIRE)

                if isinstance(self.p2_agent, HumanAgent):
                    if event.key == pygame.K_UP:
                        self.p2_agent.set_action(Action.MOVE_UP)
                    elif event.key == pygame.K_DOWN:
                        self.p2_agent.set_action(Action.MOVE_DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.p2_agent.set_action(Action.MOVE_LEFT)
                    elif event.key == pygame.K_RIGHT:
                        self.p2_agent.set_action(Action.MOVE_RIGHT)
                    elif event.key in (pygame.K_RCTRL, pygame.K_KP0):
                        self.p2_agent.set_action(Action.FIRE)

    def _handle_button_click(self, btn_id: str):
        if btn_id == "menu":
            self.is_running = False

        elif btn_id == "play_pause":
            self.is_paused = not self.is_paused
            self.add_log("PLAY" if not self.is_paused else "PAUSE")

        elif btn_id == "step":
            self.is_paused = True
            self.step_game()

        elif btn_id == "restart":
            self.restart_game()

        elif btn_id == "speed_down":
            self.fps = max(1, self.fps - 2)

        elif btn_id == "speed_up":
            self.fps = min(60, self.fps + 2)

        elif btn_id == "turns_prev":
            self.current_turns_idx = (self.current_turns_idx - 1) % len(self.max_turns_options)
            self.max_turns = self.max_turns_options[self.current_turns_idx]
            self.state.max_turns = self.max_turns
            self.add_log(f"Gioi han luot: {self.max_turns} turns")

        elif btn_id == "turns_next":
            self.current_turns_idx = (self.current_turns_idx + 1) % len(self.max_turns_options)
            self.max_turns = self.max_turns_options[self.current_turns_idx]
            self.state.max_turns = self.max_turns
            self.add_log(f"Gioi han luot: {self.max_turns} turns")

        elif btn_id == "map_prev":
            self.current_map_idx = (self.current_map_idx - 1) % len(self.available_maps)
            self.restart_game()

        elif btn_id == "map_next":
            self.current_map_idx = (self.current_map_idx + 1) % len(self.available_maps)
            self.restart_game()

        elif btn_id == "p1_prev":
            self.current_p1_idx = (self.current_p1_idx - 1) % len(self.available_agents)
            self.p1_agent = self._instantiate_agent(self.current_p1_idx)
            self.add_log(f"P1 doi thanh: {self.available_agents[self.current_p1_idx][0]}")

        elif btn_id == "p1_next":
            self.current_p1_idx = (self.current_p1_idx + 1) % len(self.available_agents)
            self.p1_agent = self._instantiate_agent(self.current_p1_idx)
            self.add_log(f"P1 doi thanh: {self.available_agents[self.current_p1_idx][0]}")

        elif btn_id == "p2_prev":
            self.current_p2_idx = (self.current_p2_idx - 1) % len(self.available_agents)
            self.p2_agent = self._instantiate_agent(self.current_p2_idx)
            self.add_log(f"P2 doi thanh: {self.available_agents[self.current_p2_idx][0]}")

        elif btn_id == "p2_next":
            self.current_p2_idx = (self.current_p2_idx + 1) % len(self.available_agents)
            self.p2_agent = self._instantiate_agent(self.current_p2_idx)
            self.add_log(f"P2 doi thanh: {self.available_agents[self.current_p2_idx][0]}")

    def _render(self):
        self.screen.fill(self.COLOR_BG)

        # 1. Ve luoi ban do chien truong (Tactical Battlefield Grid)
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                rect = pygame.Rect(
                    c * self.CELL_SIZE,
                    r * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                pygame.draw.rect(self.screen, self.COLOR_GRID, rect, 1)
                # Cham toa do radar tai giao diem
                pygame.draw.circle(self.screen, self.COLOR_GRID_DOT, rect.topleft, 2)

        # 2. Ve tuong (Walls)
        for (r, c), wall in self.state.walls.items():
            if not wall.is_alive:
                continue
            rect = pygame.Rect(
                c * self.CELL_SIZE + 2,
                r * self.CELL_SIZE + 2,
                self.CELL_SIZE - 4,
                self.CELL_SIZE - 4,
            )
            if wall.is_steel:
                self._draw_steel_wall(rect)
            else:
                self._draw_brick_wall(rect, wall)

        # 2.5. Ve Rung cay xanh / Bui co (Forest / Trees)
        for (r, c) in self.state.forests:
            f_rect = pygame.Rect(
                c * self.CELL_SIZE,
                r * self.CELL_SIZE,
                self.CELL_SIZE,
                self.CELL_SIZE,
            )
            self._draw_forest(f_rect, overlay=False)

        # 3. Ve can cu quan su (Command Fortress Bases)
        for pid, base in self.state.bases.items():
            if not base.is_alive:
                continue
            self._draw_base(base, pid)

        # 4. Ve xe tang Cyber Tank
        for pid, tank in self.state.tanks.items():
            if not tank.is_alive:
                continue
            self._draw_tank(tank, pid)
            # Neu xe dang trong rung: ve lop la cay phu tren tao hieu ung nguy trang an nap
            if (tank.r, tank.c) in self.state.forests:
                f_rect = pygame.Rect(
                    tank.c * self.CELL_SIZE,
                    tank.r * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                self._draw_forest(f_rect, overlay=True)

        # 5. Ve dan bay phat sang (Plasma Projectiles)
        for bullet in self.state.bullets:
            if not bullet.is_active:
                continue
            self._draw_bullet(bullet)

        # 6. Cap nhat va ve hieu ung hat no (Particles)
        self._update_and_draw_particles()

        # 7. Ve Side Panel dieu khien Arcade
        self._render_side_panel()

        pygame.display.flip()

    def _draw_forest(self, rect: pygame.Rect, overlay: bool = False):
        # Ve bui cay / rung ram xanh (Forest / Trees) - Chuan Battle City 1990
        base_color = (34, 150, 60)
        leaf_hi = (76, 217, 100)
        leaf_dark = (18, 92, 38)

        if not overlay:
            pygame.draw.rect(self.screen, leaf_dark, rect)

        # 4 chum la dac trung cua Battle City 1990
        sub_w = rect.width // 2
        sub_h = rect.height // 2
        for r_idx in range(2):
            for c_idx in range(2):
                cx = rect.left + c_idx * sub_w + sub_w // 2
                cy = rect.top + r_idx * sub_h + sub_h // 2
                rad = min(sub_w, sub_h) // 2 + 1
                pygame.draw.circle(self.screen, base_color, (cx, cy), rad)
                pygame.draw.circle(self.screen, leaf_hi, (cx - 1, cy - 1), max(2, rad - 3))
                pygame.draw.circle(self.screen, leaf_dark, (cx, cy), rad, 1)

    def _draw_brick_wall(self, rect: pygame.Rect, wall: Wall):
        # 1. Nen gach terracotta
        pygame.draw.rect(self.screen, self.COLOR_BRICK, rect, border_radius=2)
        pygame.draw.rect(self.screen, self.COLOR_BRICK_DARK, rect, 1, border_radius=2)

        # 2. Duong chi vua gach so le (3 hang gach)
        y1 = rect.top + rect.height // 3
        y2 = rect.top + 2 * rect.height // 3
        mortar_color = (65, 30, 20)
        pygame.draw.line(self.screen, mortar_color, (rect.left, y1), (rect.right, y1), 1)
        pygame.draw.line(self.screen, mortar_color, (rect.left, y2), (rect.right, y2), 1)

        # Cac ranh doc so le
        mid_x = rect.centerx
        pygame.draw.line(self.screen, mortar_color, (mid_x, rect.top), (mid_x, y1), 1)
        w3 = rect.width // 3
        pygame.draw.line(self.screen, mortar_color, (rect.left + w3, y1), (rect.left + w3, y2), 1)
        pygame.draw.line(self.screen, mortar_color, (rect.right - w3, y1), (rect.right - w3, y2), 1)
        pygame.draw.line(self.screen, mortar_color, (mid_x, y2), (mid_x, rect.bottom), 1)

        # 3. Vet nut vo do sat thuong khi HP giam
        if wall.hp <= 2:
            crack_color = (25, 12, 10)
            pygame.draw.line(self.screen, crack_color, (rect.left + 6, rect.top + 4), (rect.centerx, y1 + 3), 2)
            pygame.draw.line(self.screen, crack_color, (rect.centerx, y1 + 3), (rect.right - 8, y2 - 2), 2)

        if wall.hp == 1:
            pygame.draw.line(self.screen, (20, 10, 8), (rect.centerx - 4, y1), (rect.centerx + 6, rect.bottom - 4), 2)
            # Vet sut me goc
            pygame.draw.polygon(self.screen, self.COLOR_BG, [
                (rect.right - 8, rect.top),
                (rect.right, rect.top + 8),
                (rect.right, rect.top),
            ])

        # Badge HP nho o goc
        hp_badge = pygame.Rect(rect.right - 14, rect.bottom - 12, 12, 10)
        pygame.draw.rect(self.screen, (25, 12, 10), hp_badge, border_radius=2)
        txt = self.font_tag.render(str(wall.hp), True, (240, 240, 240))
        self.screen.blit(txt, (hp_badge.x + 2, hp_badge.y))

    def _draw_steel_wall(self, rect: pygame.Rect):
        # 1. Tam thep titan vat goc 3D
        pygame.draw.rect(self.screen, self.COLOR_STEEL, rect, border_radius=3)

        # 2. Vien noi sang o Top/Left va do bong o Bottom/Right
        pygame.draw.line(self.screen, self.COLOR_STEEL_LIGHT, (rect.left, rect.top), (rect.right, rect.top), 2)
        pygame.draw.line(self.screen, self.COLOR_STEEL_LIGHT, (rect.left, rect.top), (rect.left, rect.bottom), 2)
        pygame.draw.line(self.screen, self.COLOR_STEEL_DARK, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom), 2)
        pygame.draw.line(self.screen, self.COLOR_STEEL_DARK, (rect.left, rect.bottom - 1), (rect.right, rect.bottom - 1), 2)

        # 3. Tam kim loai noi o giua (Diamond / Cross embossed)
        inner = rect.inflate(-10, -10)
        pygame.draw.rect(self.screen, (90, 105, 125), inner, border_radius=2)
        pygame.draw.line(self.screen, self.COLOR_STEEL_LIGHT, inner.topleft, inner.bottomright, 1)
        pygame.draw.line(self.screen, self.COLOR_STEEL_LIGHT, inner.topright, inner.bottomleft, 1)

        # 4. 4 Dinh tan kim loai tai 4 goc (Silver Rivets)
        rivet_color = (225, 235, 250)
        for rx, ry in [
            (rect.left + 5, rect.top + 5),
            (rect.right - 6, rect.top + 5),
            (rect.left + 5, rect.bottom - 6),
            (rect.right - 6, rect.bottom - 6),
        ]:
            pygame.draw.circle(self.screen, (40, 48, 60), (rx, ry), 2)
            pygame.draw.circle(self.screen, rivet_color, (rx - 1, ry - 1), 1)

    def _draw_base(self, base: Base, pid: int):
        cx = base.c * self.CELL_SIZE + self.CELL_SIZE // 2
        cy = base.r * self.CELL_SIZE + self.CELL_SIZE // 2
        color = self.COLOR_P1 if pid == 0 else self.COLOR_P2
        base_color = self.COLOR_BASE_P1 if pid == 0 else self.COLOR_BASE_P2

        rect = pygame.Rect(cx - 20, cy - 20, 40, 40)

        # 1. Bo mong be tong cong su kien co
        pygame.draw.rect(self.screen, (35, 40, 52), rect, border_radius=8)
        pygame.draw.rect(self.screen, base_color, rect, 2, border_radius=8)

        # 2. Vach ke soc canh bao mau vang/den (Hazard Chevrons) o goc
        for offset in [-16, 12]:
            pygame.draw.line(self.screen, self.COLOR_GOLD, (cx + offset, cy - 18), (cx + offset + 4, cy - 18), 2)
            pygame.draw.line(self.screen, self.COLOR_GOLD, (cx + offset, cy + 18), (cx + offset + 4, cy + 18), 2)

        # 3. Vong bao ve nang luong (Energy Shield Ring)
        shield_ratio = base.hp / base.max_hp
        shield_r = 17
        pygame.draw.circle(self.screen, (40, 48, 62), (cx, cy), shield_r, 2)
        if shield_ratio > 0:
            # Ve cung nang luong
            arc_rect = pygame.Rect(cx - shield_r, cy - shield_r, shield_r * 2, shield_r * 2)
            start_angle = -math.pi / 2
            end_angle = start_angle + 2 * math.pi * shield_ratio
            pygame.draw.arc(self.screen, color, arc_rect, start_angle, end_angle, 3)

        # 4. Quet Radar xoay theo thoi gian
        self.radar_angle = (pygame.time.get_ticks() / 200.0) % (2 * math.pi)
        rx = cx + int(math.cos(self.radar_angle) * (shield_r - 4))
        ry = cy + int(math.sin(self.radar_angle) * (shield_r - 4))
        pygame.draw.line(self.screen, color, (cx, cy), (rx, ry), 2)
        pygame.draw.circle(self.screen, color, (cx, cy), 4)

        # 5. Crest chi huy
        crest_txt = "A" if pid == 0 else "B"
        t_surf = self.font_tag.render(crest_txt, True, (255, 255, 255))
        self.screen.blit(t_surf, t_surf.get_rect(center=(cx, cy + 10)))

        # 6. Thanh mau HP Base phia duoi
        bar_w = 34
        bar_h = 4
        bx = cx - bar_w // 2
        by = cy + 22
        pygame.draw.rect(self.screen, (30, 34, 44), (bx, by, bar_w, bar_h), border_radius=2)
        fill_w = max(2, int(bar_w * shield_ratio))
        pygame.draw.rect(self.screen, color, (bx, by, fill_w, bar_h), border_radius=2)

    def _draw_tank(self, tank: Tank, pid: int):
        cx = tank.c * self.CELL_SIZE + self.CELL_SIZE // 2
        cy = tank.r * self.CELL_SIZE + self.CELL_SIZE // 2

        color = self.COLOR_P1 if pid == 0 else self.COLOR_P2
        color_dark = self.COLOR_P1_DARK if pid == 0 else self.COLOR_P2_DARK
        color_glow = self.COLOR_P1_GLOW if pid == 0 else self.COLOR_P2_GLOW

        d = tank.direction

        # 1. Banh xich Tank hai ben (Caterpillar Treads)
        tread_color = (24, 26, 32)
        rib_color = (55, 62, 75)

        if d in (Direction.UP, Direction.DOWN):
            # Xich nam hai ben Trai & Phai
            tread_w = 7
            tread_h = 34
            t_left = pygame.Rect(cx - 17, cy - 17, tread_w, tread_h)
            t_right = pygame.Rect(cx + 10, cy - 17, tread_w, tread_h)
            for tr in (t_left, t_right):
                pygame.draw.rect(self.screen, tread_color, tr, border_radius=2)
                for step_y in range(tr.top + 3, tr.bottom - 2, 5):
                    pygame.draw.line(self.screen, rib_color, (tr.left, step_y), (tr.right - 1, step_y), 1)

            # Than xe (Chassis Hull)
            hull = pygame.Rect(cx - 11, cy - 15, 22, 30)
            pygame.draw.rect(self.screen, color, hull, border_radius=4)
            pygame.draw.rect(self.screen, color_dark, hull.inflate(-4, -4), border_radius=2)

        else:
            # Xich nam hai ben Tren & Duoi
            tread_w = 34
            tread_h = 7
            t_top = pygame.Rect(cx - 17, cy - 17, tread_w, tread_h)
            t_bottom = pygame.Rect(cx - 17, cy + 10, tread_w, tread_h)
            for tr in (t_top, t_bottom):
                pygame.draw.rect(self.screen, tread_color, tr, border_radius=2)
                for step_x in range(tr.left + 3, tr.right - 2, 5):
                    pygame.draw.line(self.screen, rib_color, (step_x, tr.top), (step_x, tr.bottom - 1), 1)

            # Than xe (Chassis Hull)
            hull = pygame.Rect(cx - 15, cy - 11, 30, 22)
            pygame.draw.rect(self.screen, color, hull, border_radius=4)
            pygame.draw.rect(self.screen, color_dark, hull.inflate(-4, -4), border_radius=2)

        # 2. Nong phao dai & Khuyen ham giat (Heavy Cannon Barrel)
        barrel_len = 18
        bx = cx + d.dc * barrel_len
        by = cy + d.dr * barrel_len
        pygame.draw.line(self.screen, (220, 230, 245), (cx, cy), (bx, by), 5)
        pygame.draw.line(self.screen, (50, 55, 68), (cx, cy), (bx, by), 1)

        # Muzzle Brake o dau nong phao
        if d in (Direction.UP, Direction.DOWN):
            pygame.draw.line(self.screen, (255, 255, 255), (bx - 3, by), (bx + 3, by), 3)
        else:
            pygame.draw.line(self.screen, (255, 255, 255), (bx, by - 3), (bx, by + 3), 3)

        # 3. Thap phao hinh tron (Armored Turret Dome)
        turret_r = 8
        pygame.draw.circle(self.screen, (32, 38, 48), (cx, cy), turret_r + 1)
        pygame.draw.circle(self.screen, color_glow, (cx, cy), turret_r)
        pygame.draw.circle(self.screen, color_dark, (cx, cy), turret_r - 2)

        # Cua cupola chi huy
        hatch_x = cx - d.dc * 3
        hatch_y = cy - d.dr * 3
        pygame.draw.circle(self.screen, (240, 245, 255), (hatch_x, hatch_y), 2)

        # 4. Thanh mau Sci-Fi 6 pips loi tren dau xe
        bar_w = 30
        bar_h = 5
        bar_x = cx - bar_w // 2
        bar_y = cy - 24
        pygame.draw.rect(self.screen, (15, 18, 24), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=2)

        pip_w = 4
        gap = 1
        for i in range(tank.max_hp):
            pip_x = bar_x + i * (pip_w + gap)
            pip_color = color if i < tank.hp else (45, 50, 60)
            pygame.draw.rect(self.screen, pip_color, (pip_x, bar_y, pip_w, bar_h), border_radius=1)

    def _draw_bullet(self, bullet: Bullet):
        cx = bullet.c * self.CELL_SIZE + self.CELL_SIZE // 2
        cy = bullet.r * self.CELL_SIZE + self.CELL_SIZE // 2

        # 1. Duoi lua / khoi phia sau dan
        d = bullet.direction
        tail_x = cx - d.dc * 6
        tail_y = cy - d.dr * 6
        pygame.draw.circle(self.screen, (255, 120, 20), (tail_x, tail_y), 4)

        # 2. Vien dan plasma phat sang ruc ro
        pygame.draw.circle(self.screen, (255, 180, 40), (cx, cy), 6)
        pygame.draw.circle(self.screen, (255, 255, 220), (cx, cy), 3)

        # Sinh hat khoi nhe
        if random.random() < 0.4:
            self.particles.append({
                "x": tail_x + (random.random() - 0.5) * 4,
                "y": tail_y + (random.random() - 0.5) * 4,
                "vx": (random.random() - 0.5) * 0.8,
                "vy": (random.random() - 0.5) * 0.8,
                "color": (255, 140, 30),
                "radius": 2.5,
                "life": 6,
                "max_life": 6,
            })

    def _update_and_draw_particles(self):
        surviving = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            p["radius"] = max(0.5, p["radius"] * 0.88)
            if p["life"] > 0 and p["radius"] > 0.5:
                ratio = p["life"] / p["max_life"]
                c = tuple(int(channel * ratio) for channel in p["color"])
                pygame.draw.circle(self.screen, c, (int(p["x"]), int(p["y"])), int(p["radius"]))
                surviving.append(p)
        self.particles = surviving

    def _draw_button(self, btn_id: str, text: str, rect: pygame.Rect, bg_color=None, text_color=None):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)

        if bg_color is None:
            bg_color = self.COLOR_BTN_HOVER if is_hover else self.COLOR_BTN_NORMAL
        elif is_hover:
            bg_color = tuple(min(255, c + 20) for c in bg_color)

        if text_color is None:
            text_color = (255, 255, 255) if is_hover else self.COLOR_TEXT

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
        pygame.draw.rect(self.screen, self.COLOR_BORDER, rect, 1, border_radius=5)

        txt_surf = self.font_bold.render(text, True, text_color)
        txt_rect = txt_surf.get_rect(center=rect.center)
        self.screen.blit(txt_surf, txt_rect)

        self.buttons[btn_id] = rect

    def _render_side_panel(self):
        panel_x = self.grid_width
        panel_w = self.PANEL_WIDTH
        pygame.draw.rect(self.screen, self.COLOR_PANEL_BG, (panel_x, 0, panel_w, self.window_height))
        pygame.draw.line(self.screen, self.COLOR_BORDER, (panel_x, 0), (panel_x, self.window_height), 2)

        y = 12
        # 1. Nut quay ve Menu chinh
        self._draw_button("menu", "< MENU CHINH", pygame.Rect(panel_x + 18, y, 130, 28), bg_color=(192, 57, 43))
        y += 34

        # 2. Tieu de Arcade Neon Game
        title = self.font_title.render("TANK BATTLE ARENA", True, (255, 255, 255))
        self.screen.blit(title, (panel_x + 18, y))
        y += 24
        sub_title = self.font_mini.render("ZERO-SUM ADVERSARIAL AI ENGINE", True, self.COLOR_GOLD)
        self.screen.blit(sub_title, (panel_x + 18, y))
        y += 26

        # 3. LIVE COMBAT SCOREBOARD (P1 vs P2 Cards)
        card_w = (panel_w - 46) // 2
        card_h = 96
        t0 = self.state.tanks.get(0)
        t1 = self.state.tanks.get(1)
        b0 = self.state.bases.get(0)
        b1 = self.state.bases.get(1)

        t0_hp = t0.hp if t0 and t0.is_alive else 0
        t1_hp = t1.hp if t1 and t1.is_alive else 0
        b0_hp = b0.hp if b0 and b0.is_alive else 0
        b1_hp = b1.hp if b1 and b1.is_alive else 0

        # Card P1 (Emerald)
        c1_rect = pygame.Rect(panel_x + 18, y, card_w, card_h)
        pygame.draw.rect(self.screen, self.COLOR_PANEL_CARD, c1_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.COLOR_P1, c1_rect, 1, border_radius=6)
        self.screen.blit(self.font_bold.render("PLAYER 1", True, self.COLOR_P1), (c1_rect.left + 8, c1_rect.top + 6))
        self.screen.blit(self.font_mini.render(f"Tank: {t0_hp}/6 HP", True, (240, 240, 240)), (c1_rect.left + 8, c1_rect.top + 28))
        self.screen.blit(self.font_mini.render(f"Base: {b0_hp}/9 HP", True, self.COLOR_ACCENT), (c1_rect.left + 8, c1_rect.top + 48))
        act1_lbl = self.font_tag.render(f"MOVE: {self.last_a0.name}", True, self.COLOR_GOLD)
        self.screen.blit(act1_lbl, (c1_rect.left + 8, c1_rect.top + 70))

        # Card P2 (Crimson)
        c2_rect = pygame.Rect(panel_x + 28 + card_w, y, card_w, card_h)
        pygame.draw.rect(self.screen, self.COLOR_PANEL_CARD, c2_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.COLOR_P2, c2_rect, 1, border_radius=6)
        self.screen.blit(self.font_bold.render("PLAYER 2", True, self.COLOR_P2), (c2_rect.left + 8, c2_rect.top + 6))
        self.screen.blit(self.font_mini.render(f"Tank: {t1_hp}/6 HP", True, (240, 240, 240)), (c2_rect.left + 8, c2_rect.top + 28))
        self.screen.blit(self.font_mini.render(f"Base: {b1_hp}/9 HP", True, (230, 126, 34)), (c2_rect.left + 8, c2_rect.top + 48))
        act2_lbl = self.font_tag.render(f"MOVE: {self.last_a1.name}", True, self.COLOR_GOLD)
        self.screen.blit(act2_lbl, (c2_rect.left + 8, c2_rect.top + 70))

        y += card_h + 12

        # 4. CHON BAN DO & AGENTS TREN GUI
        # Ban do
        map_name = self.available_maps[self.current_map_idx][0]
        self.screen.blit(self.font_mini.render("BAN DO THI DAU:", True, self.COLOR_TEXT_MUTED), (panel_x + 18, y))
        y += 18
        self._draw_button("map_prev", "<", pygame.Rect(panel_x + 18, y, 26, 28))
        map_box = pygame.Rect(panel_x + 48, y, panel_w - 92, 28)
        pygame.draw.rect(self.screen, self.COLOR_PANEL_CARD, map_box, border_radius=4)
        m_txt = self.font_bold.render(map_name, True, (255, 255, 255))
        self.screen.blit(m_txt, m_txt.get_rect(center=map_box.center))
        self._draw_button("map_next", ">", pygame.Rect(panel_x + panel_w - 40, y, 26, 28))
        y += 34

        # Agent P1
        p1_name = self.available_agents[self.current_p1_idx][0]
        self.screen.blit(self.font_mini.render("THUAT TOAN P1 (GREEN):", True, self.COLOR_P1), (panel_x + 18, y))
        y += 18
        self._draw_button("p1_prev", "<", pygame.Rect(panel_x + 18, y, 26, 28))
        p1_box = pygame.Rect(panel_x + 48, y, panel_w - 92, 28)
        pygame.draw.rect(self.screen, self.COLOR_PANEL_CARD, p1_box, border_radius=4)
        p1_txt = self.font_bold.render(p1_name, True, self.COLOR_P1)
        self.screen.blit(p1_txt, p1_txt.get_rect(center=p1_box.center))
        self._draw_button("p1_next", ">", pygame.Rect(panel_x + panel_w - 40, y, 26, 28))
        y += 34

        # Agent P2
        p2_name = self.available_agents[self.current_p2_idx][0]
        self.screen.blit(self.font_mini.render("THUAT TOAN P2 (CRIMSON):", True, self.COLOR_P2), (panel_x + 18, y))
        y += 18
        self._draw_button("p2_prev", "<", pygame.Rect(panel_x + 18, y, 26, 28))
        p2_box = pygame.Rect(panel_x + 48, y, panel_w - 92, 28)
        pygame.draw.rect(self.screen, self.COLOR_PANEL_CARD, p2_box, border_radius=4)
        p2_txt = self.font_bold.render(p2_name, True, self.COLOR_P2)
        self.screen.blit(p2_txt, p2_txt.get_rect(center=p2_box.center))
        self._draw_button("p2_next", ">", pygame.Rect(panel_x + panel_w - 40, y, 26, 28))
        y += 38

        # 5. DIEU KHIEN TRAN DAU (Controls)
        btn_w = (panel_w - 48) // 3
        play_txt = "PAUSE" if not self.is_paused else "PLAY"
        play_color = (192, 57, 43) if not self.is_paused else (39, 174, 96)
        self._draw_button("play_pause", play_txt, pygame.Rect(panel_x + 18, y, btn_w, 34), bg_color=play_color)
        self._draw_button("step", "STEP >", pygame.Rect(panel_x + 24 + btn_w, y, btn_w, 34), bg_color=(41, 128, 185))
        self._draw_button("restart", "RESET", pygame.Rect(panel_x + 30 + 2 * btn_w, y, btn_w, 34), bg_color=(125, 60, 150))
        y += 42

        # Toc do FPS
        self.screen.blit(self.font.render(f"Toc do: {self.fps} FPS", True, self.COLOR_TEXT), (panel_x + 18, y + 4))
        self._draw_button("speed_down", "- FPS", pygame.Rect(panel_x + panel_w - 145, y, 58, 26))
        self._draw_button("speed_up", "+ FPS", pygame.Rect(panel_x + panel_w - 80, y, 58, 26))
        y += 32

        # Dieu chinh So buoc toi da (Max Turns)
        turn_str = f"Luot: {self.state.turn_count}/{self.state.max_turns}"
        self.screen.blit(self.font.render(f"Gioi han luot ({turn_str}):", True, self.COLOR_TEXT), (panel_x + 18, y + 4))
        self._draw_button("turns_prev", "<", pygame.Rect(panel_x + panel_w - 145, y, 28, 26))
        turns_box = pygame.Rect(panel_x + panel_w - 113, y, 58, 26)
        pygame.draw.rect(self.screen, self.COLOR_PANEL_CARD, turns_box, border_radius=4)
        t_val = self.font_bold.render(str(self.state.max_turns), True, self.COLOR_GOLD)
        self.screen.blit(t_val, t_val.get_rect(center=turns_box.center))
        self._draw_button("turns_next", ">", pygame.Rect(panel_x + panel_w - 51, y, 28, 26))
        y += 34

        # 6. LUOC DO SO SANH THUAT TOAN TRUC QUAN (Pruning Comparison Bar)
        pygame.draw.line(self.screen, self.COLOR_BORDER, (panel_x + 18, y), (panel_x + panel_w - 18, y), 1)
        y += 8
        self.screen.blit(self.font_bold.render("Luoc do so sanh Search Nodes (d=2):", True, (255, 255, 255)), (panel_x + 18, y))
        y += 20

        max_bar = panel_w - 36
        # Alpha-Beta (11 nodes)
        ab_w = int(max_bar * (11 / 36))
        pygame.draw.rect(self.screen, (38, 44, 56), (panel_x + 18, y, max_bar, 10), border_radius=2)
        pygame.draw.rect(self.screen, self.COLOR_P1, (panel_x + 18, y, ab_w, 10), border_radius=2)
        self.screen.blit(self.font_mini.render("Alpha-Beta: 11 nodes (Cat tia ~70% nut)", True, self.COLOR_P1), (panel_x + 18, y + 12))
        y += 26

        # Minimax (36 nodes)
        pygame.draw.rect(self.screen, (38, 44, 56), (panel_x + 18, y, max_bar, 10), border_radius=2)
        pygame.draw.rect(self.screen, self.COLOR_P2, (panel_x + 18, y, max_bar, 10), border_radius=2)
        self.screen.blit(self.font_mini.render("Minimax: 36 nodes (Duyet can toan bo)", True, self.COLOR_TEXT_MUTED), (panel_x + 18, y + 12))
        y += 28

        # 7. NHAT KY LOGS CHIEN TRUONG
        pygame.draw.line(self.screen, self.COLOR_BORDER, (panel_x + 18, y), (panel_x + panel_w - 18, y), 1)
        y += 8
        self.screen.blit(self.font_bold.render("Nhat ky tran dau (Combat Log):", True, self.COLOR_GOLD), (panel_x + 18, y))
        y += 18

        log_box = pygame.Rect(panel_x + 18, y, panel_w - 36, min(120, self.window_height - y - 12))
        pygame.draw.rect(self.screen, (16, 18, 24), log_box, border_radius=4)
        pygame.draw.rect(self.screen, self.COLOR_BORDER, log_box, 1, border_radius=4)

        log_y = log_box.top + 6
        for line in self.logs[-5:]:
            color = self.COLOR_P1 if "P1=" in line else (self.COLOR_P2 if "P2=" in line else self.COLOR_TEXT_MUTED)
            if "CHIEN THANG" in line or "KET THUC" in line:
                color = self.COLOR_GOLD
            self.screen.blit(self.font_mini.render(line[:54], True, color), (log_box.left + 8, log_y))
            log_y += 18


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gui = TankBattleGUI(
        maps_dir=os.path.join(base_dir, "maps"),
        agents_dir=os.path.join(base_dir, "agents"),
    )
    gui.run()
    pygame.quit()
