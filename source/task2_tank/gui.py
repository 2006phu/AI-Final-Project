import importlib.util
import inspect
import os
import sys
import pygame
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.human_agent import HumanAgent
from task2_tank.agents.random_agent import RandomAgent
from task2_tank.agents.search_agent import SearchAgent
from task2_tank.engine import GameEngine
from task2_tank.entities import Action, Direction, Tank, Base, Wall, Bullet
from task2_tank.game_state import GameState


def discover_custom_agents(agents_dir: str) -> dict[str, type]:
    """Quét động các file trong agents_dir và trả về dict[tên_lớp, class]."""
    custom_agents = {}
    if os.path.exists(agents_dir):
        for fname in os.listdir(agents_dir):
            if fname.endswith(".py") and not fname.startswith("__"):
                filepath = os.path.join(agents_dir, fname)
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
                                and cls is not BaseAgent
                                and cls is not SearchAgent
                                and cls is not RandomAgent
                                and cls is not HumanAgent
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
    CELL_SIZE = 40
    PANEL_WIDTH = 350
    FPS_DEFAULT = 5

    COLOR_BG = (22, 24, 28)
    COLOR_GRID = (38, 41, 48)
    COLOR_PANEL_BG = (30, 33, 40)
    COLOR_PANEL_HEADER = (42, 46, 56)
    COLOR_TEXT = (235, 238, 245)
    COLOR_TEXT_MUTED = (150, 155, 168)
    COLOR_ACCENT = (52, 152, 219)

    COLOR_P1 = (46, 204, 113)      # Xanh la (Player 1)
    COLOR_P2 = (241, 196, 15)      # Vang (Player 2)
    COLOR_BASE_P1 = (52, 152, 219) # Xanh duong
    COLOR_BASE_P2 = (231, 76, 60)  # Do cam
    COLOR_BRICK = (192, 75, 45)    # Gach do
    COLOR_STEEL = (170, 180, 195)  # Thep xam bac
    COLOR_BULLET = (255, 240, 160) # Dan phat sang

    COLOR_BTN_NORMAL = (48, 54, 66)
    COLOR_BTN_HOVER = (68, 76, 92)
    COLOR_BTN_ACTIVE = (46, 204, 113)

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

        self.p1_agent = self.available_agents[self.current_p1_idx][1]()
        self.p2_agent = self.available_agents[self.current_p2_idx][1]()

        # Nap ban do dau tien
        self._load_current_map()

        self.font = pygame.font.SysFont("consolas", 13)
        self.font_bold = pygame.font.SysFont("consolas", 14, bold=True)
        self.font_title = pygame.font.SysFont("consolas", 18, bold=True)
        self.clock = pygame.time.Clock()

        self.is_running = True
        self.is_paused = True
        self.fps = self.FPS_DEFAULT
        self.logs: list[str] = ["Game san sang! Nhan nut START tren man hinh de bat dau."]

        self.last_a0 = Action.STAY
        self.last_a1 = Action.STAY
        self.p1_time = 0.0
        self.p2_time = 0.0

        # Danh sach nut bam UI tuong tac tren man hinh
        self.buttons = {}

    def _load_current_map(self):
        map_path = self.available_maps[self.current_map_idx][1]
        self.state = GameState.from_file(map_path)
        self.grid_width = self.state.cols * self.CELL_SIZE
        self.grid_height = self.state.rows * self.CELL_SIZE
        self.window_width = self.grid_width + self.PANEL_WIDTH
        self.window_height = max(self.grid_height, 620)

        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Tank Battle Simulator - Adversarial Search (AI Final Project)")

    def add_log(self, text: str):
        self.logs.append(text)
        if len(self.logs) > 6:
            self.logs.pop(0)

    def restart_game(self):
        self._load_current_map()
        self.p1_agent = self.available_agents[self.current_p1_idx][1]()
        self.p2_agent = self.available_agents[self.current_p2_idx][1]()
        self.is_paused = True
        self.last_a0 = Action.STAY
        self.last_a1 = Action.STAY
        self.add_log("Da khoi dong lai van dau!")

    def step_game(self):
        if GameEngine.is_terminal(self.state):
            winner = GameEngine.get_winner(self.state)
            if winner == 0:
                self.add_log("KET THUC: Player 1 (Green) CHIEN THANG!")
            elif winner == 1:
                self.add_log("KET THUC: Player 2 (Yellow) CHIEN THANG!")
            else:
                self.add_log("KET THUC: HOA CO!")
            self.is_paused = True
            return

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

    def run(self):
        while self.is_running:
            self._handle_events()
            if not self.is_paused:
                self.step_game()
            self._render()
            self.clock.tick(self.fps if not self.is_paused else 30)

        pygame.quit()

    def _handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Xu ly click vao cac nut bam tren GUI
                for btn_id, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        self._handle_button_click(btn_id)
                        break

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
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
        if btn_id == "play_pause":
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

        elif btn_id == "map_prev":
            self.current_map_idx = (self.current_map_idx - 1) % len(self.available_maps)
            self.restart_game()

        elif btn_id == "map_next":
            self.current_map_idx = (self.current_map_idx + 1) % len(self.available_maps)
            self.restart_game()

        elif btn_id == "p1_prev":
            self.current_p1_idx = (self.current_p1_idx - 1) % len(self.available_agents)
            self.p1_agent = self.available_agents[self.current_p1_idx][1]()
            self.add_log(f"P1 doi thanh: {self.available_agents[self.current_p1_idx][0]}")

        elif btn_id == "p1_next":
            self.current_p1_idx = (self.current_p1_idx + 1) % len(self.available_agents)
            self.p1_agent = self.available_agents[self.current_p1_idx][1]()
            self.add_log(f"P1 doi thanh: {self.available_agents[self.current_p1_idx][0]}")

        elif btn_id == "p2_prev":
            self.current_p2_idx = (self.current_p2_idx - 1) % len(self.available_agents)
            self.p2_agent = self.available_agents[self.current_p2_idx][1]()
            self.add_log(f"P2 doi thanh: {self.available_agents[self.current_p2_idx][0]}")

        elif btn_id == "p2_next":
            self.current_p2_idx = (self.current_p2_idx + 1) % len(self.available_agents)
            self.p2_agent = self.available_agents[self.current_p2_idx][1]()
            self.add_log(f"P2 doi thanh: {self.available_agents[self.current_p2_idx][0]}")

    def _render(self):
        self.screen.fill(self.COLOR_BG)

        # 1. Ve luoi ban do (Grid)
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                rect = pygame.Rect(
                    c * self.CELL_SIZE,
                    r * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                pygame.draw.rect(self.screen, self.COLOR_GRID, rect, 1)

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
                pygame.draw.rect(self.screen, self.COLOR_STEEL, rect, border_radius=3)
                pygame.draw.rect(self.screen, (220, 230, 245), rect, 2, border_radius=3)
            else:
                pygame.draw.rect(self.screen, self.COLOR_BRICK, rect, border_radius=2)
                pygame.draw.line(self.screen, (130, 45, 30), (rect.left, rect.centery), (rect.right, rect.centery), 1)
                hp_txt = self.font.render(str(wall.hp), True, (255, 255, 255))
                self.screen.blit(hp_txt, (rect.centerx - 4, rect.centery - 6))

        # 3. Ve can cu (Bases)
        for pid, base in self.state.bases.items():
            if not base.is_alive:
                continue
            rect = pygame.Rect(
                base.c * self.CELL_SIZE + 2,
                base.r * self.CELL_SIZE + 2,
                self.CELL_SIZE - 4,
                self.CELL_SIZE - 4,
            )
            color = self.COLOR_BASE_P1 if pid == 0 else self.COLOR_BASE_P2
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=6)
            txt = self.font_bold.render("B" if pid == 1 else "A", True, (255, 255, 255))
            self.screen.blit(txt, (rect.centerx - 4, rect.centery - 7))

        # 4. Ve xe tang (Tanks)
        for pid, tank in self.state.tanks.items():
            if not tank.is_alive:
                continue
            self._draw_tank(tank, pid)

        # 5. Ve dan bay (Bullets)
        for bullet in self.state.bullets:
            if not bullet.is_active:
                continue
            bx = bullet.c * self.CELL_SIZE + self.CELL_SIZE // 2
            by = bullet.r * self.CELL_SIZE + self.CELL_SIZE // 2
            pygame.draw.circle(self.screen, self.COLOR_BULLET, (bx, by), 5)
            pygame.draw.circle(self.screen, (255, 120, 30), (bx, by), 3)

        # 6. Ve Side Panel thao tac GUI
        self._render_side_panel()

        pygame.display.flip()

    def _draw_tank(self, tank: Tank, pid: int):
        cx = tank.c * self.CELL_SIZE + self.CELL_SIZE // 2
        cy = tank.r * self.CELL_SIZE + self.CELL_SIZE // 2
        color = self.COLOR_P1 if pid == 0 else self.COLOR_P2

        body_rect = pygame.Rect(cx - 14, cy - 14, 28, 28)
        pygame.draw.rect(self.screen, color, body_rect, border_radius=4)
        pygame.draw.rect(self.screen, (255, 255, 255), body_rect, 1, border_radius=4)

        pygame.draw.rect(self.screen, (30, 30, 30), (cx - 16, cy - 14, 4, 28))
        pygame.draw.rect(self.screen, (30, 30, 30), (cx + 12, cy - 14, 4, 28))

        barrel_len = 16
        bx = cx + tank.direction.dc * barrel_len
        by = cy + tank.direction.dr * barrel_len
        pygame.draw.line(self.screen, (255, 255, 255), (cx, cy), (bx, by), 4)

        bar_w = 28
        bar_h = 4
        bar_x = cx - bar_w // 2
        bar_y = cy - 20
        fill_w = int(bar_w * (tank.hp / tank.max_hp))
        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h))

    def _draw_button(self, btn_id: str, text: str, rect: pygame.Rect, bg_color=None, text_color=None):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)

        if bg_color is None:
            bg_color = self.COLOR_BTN_HOVER if is_hover else self.COLOR_BTN_NORMAL
        if text_color is None:
            text_color = (255, 255, 255) if is_hover else self.COLOR_TEXT

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=4)
        pygame.draw.rect(self.screen, (70, 78, 95), rect, 1, border_radius=4)

        txt_surf = self.font_bold.render(text, True, text_color)
        txt_rect = txt_surf.get_rect(center=rect.center)
        self.screen.blit(txt_surf, txt_rect)

        self.buttons[btn_id] = rect

    def _render_side_panel(self):
        panel_x = self.grid_width
        pygame.draw.rect(
            self.screen,
            self.COLOR_PANEL_BG,
            (panel_x, 0, self.PANEL_WIDTH, self.window_height),
        )
        pygame.draw.line(
            self.screen,
            self.COLOR_GRID,
            (panel_x, 0),
            (panel_x, self.window_height),
            2,
        )

        y = 15
        # Title
        title = self.font_title.render("TANK BATTLE SIMULATOR", True, (255, 255, 255))
        self.screen.blit(title, (panel_x + 18, y))
        y += 28

        # --- SECTION 1: CHON BAN DO TREN GUI ---
        map_label = self.font_bold.render("Ban do:", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(map_label, (panel_x + 18, y + 5))

        self._draw_button("map_prev", "<", pygame.Rect(panel_x + 75, y, 28, 26))
        map_name = self.available_maps[self.current_map_idx][0]
        # Hien thi ten ban do o giua
        map_box = pygame.Rect(panel_x + 107, y, 170, 26)
        pygame.draw.rect(self.screen, (38, 42, 52), map_box, border_radius=3)
        map_name_surf = self.font.render(map_name, True, self.COLOR_TEXT)
        self.screen.blit(map_name_surf, map_name_surf.get_rect(center=map_box.center))
        self._draw_button("map_next", ">", pygame.Rect(panel_x + 281, y, 28, 26))
        y += 36

        # --- SECTION 2: CHON AGENT P1 TREN GUI ---
        p1_label = self.font_bold.render("P1:", True, self.COLOR_P1)
        self.screen.blit(p1_label, (panel_x + 18, y + 5))

        self._draw_button("p1_prev", "<", pygame.Rect(panel_x + 50, y, 28, 26))
        p1_name = self.available_agents[self.current_p1_idx][0]
        p1_box = pygame.Rect(panel_x + 82, y, 220, 26)
        pygame.draw.rect(self.screen, (38, 42, 52), p1_box, border_radius=3)
        p1_name_surf = self.font.render(p1_name[:26], True, self.COLOR_P1)
        self.screen.blit(p1_name_surf, p1_name_surf.get_rect(center=p1_box.center))
        self._draw_button("p1_next", ">", pygame.Rect(panel_x + 306, y, 28, 26))
        y += 34

        # --- SECTION 3: CHON AGENT P2 TREN GUI ---
        p2_label = self.font_bold.render("P2:", True, self.COLOR_P2)
        self.screen.blit(p2_label, (panel_x + 18, y + 5))

        self._draw_button("p2_prev", "<", pygame.Rect(panel_x + 50, y, 28, 26))
        p2_name = self.available_agents[self.current_p2_idx][0]
        p2_box = pygame.Rect(panel_x + 82, y, 220, 26)
        pygame.draw.rect(self.screen, (38, 42, 52), p2_box, border_radius=3)
        p2_name_surf = self.font.render(p2_name[:26], True, self.COLOR_P2)
        self.screen.blit(p2_name_surf, p2_name_surf.get_rect(center=p2_box.center))
        self._draw_button("p2_next", ">", pygame.Rect(panel_x + 306, y, 28, 26))
        y += 42

        # --- SECTION 4: CAC NUT BAM DIEU KHIEN CHINH TREN GUI ---
        play_txt = "PAUSE" if not self.is_paused else "PLAY"
        play_color = (192, 57, 43) if not self.is_paused else (39, 174, 96)
        self._draw_button("play_pause", play_txt, pygame.Rect(panel_x + 18, y, 95, 32), bg_color=play_color)
        self._draw_button("step", "STEP >", pygame.Rect(panel_x + 123, y, 95, 32))
        self._draw_button("restart", "RESET", pygame.Rect(panel_x + 228, y, 95, 32))
        y += 42

        # --- SECTION 5: TOC DO FPS ---
        speed_label = self.font.render(f"Toc do: {self.fps} FPS", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(speed_label, (panel_x + 18, y + 5))
        self._draw_button("speed_down", "- Speed", pygame.Rect(panel_x + 140, y, 80, 26))
        self._draw_button("speed_up", "+ Speed", pygame.Rect(panel_x + 230, y, 80, 26))
        y += 36

        # --- SECTION 6: THONG TIN TRANG THAI VAN DAU ---
        pygame.draw.line(self.screen, self.COLOR_GRID, (panel_x + 18, y), (panel_x + self.PANEL_WIDTH - 18, y), 1)
        y += 10

        turn_txt = self.font_bold.render(
            f"Turn: {self.state.turn_count}/{self.state.max_turns} [{'PLAYING' if not self.is_paused else 'PAUSED'}]",
            True,
            (46, 204, 113) if not self.is_paused else (241, 196, 15),
        )
        self.screen.blit(turn_txt, (panel_x + 18, y))
        y += 24

        # P1 & P2 Stats Box
        t0_hp = self.state.tanks[0].hp if 0 in self.state.tanks else 0
        b0_hp = self.state.bases[0].hp if 0 in self.state.bases else 0
        t1_hp = self.state.tanks[1].hp if 1 in self.state.tanks else 0
        b1_hp = self.state.bases[1].hp if 1 in self.state.bases else 0

        p1_stats = self.font.render(f"P1 (Green) : Tank={t0_hp}/6 | Base={b0_hp}/9 ({self.last_a0.name})", True, self.COLOR_P1)
        self.screen.blit(p1_stats, (panel_x + 18, y))
        y += 20

        p2_stats = self.font.render(f"P2 (Yellow): Tank={t1_hp}/6 | Base={b1_hp}/9 ({self.last_a1.name})", True, self.COLOR_P2)
        self.screen.blit(p2_stats, (panel_x + 18, y))
        y += 30

        # --- SECTION 7: NHAT KY LOGS ---
        pygame.draw.line(self.screen, self.COLOR_GRID, (panel_x + 18, y), (panel_x + self.PANEL_WIDTH - 18, y), 1)
        y += 10
        log_title = self.font_bold.render("Nhat ky tran dau (Logs):", True, (255, 255, 255))
        self.screen.blit(log_title, (panel_x + 18, y))
        y += 20

        for line in self.logs[-5:]:
            log_line = self.font.render(line, True, self.COLOR_TEXT_MUTED)
            self.screen.blit(log_line, (panel_x + 18, y))
            y += 18
