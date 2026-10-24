import os
import sys
import pygame
from task3_kakuro.csp import KakuroCSP
from task3_kakuro.propagation import ConstraintPropagator
from task3_kakuro.puzzle import KakuroPuzzle, CellType
from task3_kakuro.solver import BacktrackingSolver, EventType, SolverEvent


def discover_all_puzzles(puzzles_dir: str) -> list[tuple[str, str]]:
    """Tim tat ca cac file de .txt trong thu muc puzzles."""
    puzzles = []
    if os.path.exists(puzzles_dir):
        for fname in sorted(os.listdir(puzzles_dir)):
            if fname.endswith(".txt"):
                label = fname.replace(".txt", "").replace("_", " ").title()
                puzzles.append((label, os.path.join(puzzles_dir, fname)))
    return puzzles


CONFIG_OPTIONS = [
    ("BT + MAC + MRV + LCV", {"strategy": "mac", "use_mrv": True, "use_degree": True, "use_lcv": True}),
    ("BT + MAC (MRV)", {"strategy": "mac", "use_mrv": True, "use_degree": True, "use_lcv": False}),
    ("BT + FC (MRV)", {"strategy": "fc", "use_mrv": True, "use_degree": True, "use_lcv": False}),
    ("BT + FC (Thuong)", {"strategy": "fc", "use_mrv": False, "use_degree": False, "use_lcv": False}),
    ("BT Thuan (Co MRV)", {"strategy": "none", "use_mrv": True, "use_degree": True, "use_lcv": False}),
    ("BT Thuan (Khong MRV)", {"strategy": "none", "use_mrv": False, "use_degree": False, "use_lcv": False}),
]


class KakuroGUI:
    """Giao dien do hoa Pygame truc quan hoa tung buoc giai Kakuro (CSP).
    
    100% thao tac bang chuot tren man hinh: Chon de, chon thuat toan, Play, Step, Reset, Chinh toc do.
    """

    PANEL_WIDTH = 380
    FPS_DEFAULT = 5

    # Bang mau arcade sang trong
    COLOR_BG = (22, 24, 28)
    COLOR_GRID_LINE = (55, 60, 72)
    COLOR_PANEL_BG = (30, 33, 40)
    COLOR_PANEL_HEADER = (42, 46, 56)
    COLOR_TEXT = (235, 238, 245)
    COLOR_TEXT_MUTED = (150, 155, 168)

    COLOR_BLACK_CELL = (35, 38, 46)
    COLOR_CLUE_LINE = (75, 82, 98)
    COLOR_CLUE_TEXT = (241, 196, 15)  # Vang gold sang trong
    COLOR_WHITE_CELL = (248, 249, 252)
    COLOR_ASSIGNED_TEXT = (25, 30, 42)

    # Mau hieu ung trang thai thuat toan
    COLOR_HIGHLIGHT_ASSIGN = (46, 204, 113)    # Xanh la: vua gan gia tri
    COLOR_HIGHLIGHT_BACKTRACK = (230, 126, 34) # Cam: quay lui hoan tac
    COLOR_PRUNED_TEXT = (231, 76, 60)          # Do: gia tri vua bi cat tia
    COLOR_SOLVED_BORDER = (46, 204, 113)

    COLOR_BTN_NORMAL = (48, 54, 66)
    COLOR_BTN_HOVER = (68, 76, 92)

    def __init__(self, puzzles_dir: str, initial_puzzle_path: str | None = None):
        pygame.init()
        pygame.font.init()

        self.puzzles_dir = puzzles_dir
        self.available_puzzles = discover_all_puzzles(puzzles_dir)
        if not self.available_puzzles:
            raise RuntimeError(f"Khong tim thay file de .txt nao trong: {puzzles_dir}")

        self.current_puzzle_idx = 0
        if initial_puzzle_path:
            target_base = os.path.basename(initial_puzzle_path).lower()
            for idx, (_, ppath) in enumerate(self.available_puzzles):
                if os.path.basename(ppath).lower() == target_base:
                    self.current_puzzle_idx = idx
                    break

        self.current_config_idx = 0

        # Khoi tao font chu
        self.font_main = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_clue = pygame.font.SysFont("consolas", 13, bold=True)
        self.font_pencil = pygame.font.SysFont("consolas", 11)
        self.font_panel = pygame.font.SysFont("consolas", 13)
        self.font_panel_bold = pygame.font.SysFont("consolas", 14, bold=True)
        self.font_title = pygame.font.SysFont("consolas", 17, bold=True)

        self.clock = pygame.time.Clock()
        self.fps = self.FPS_DEFAULT
        self.is_running = True
        self.is_paused = True

        self.buttons: dict[str, pygame.Rect] = {}
        self.logs: list[str] = ["He thong san sang! Nhan STEP hoac PLAY de bat dau giai."]

        self._load_current_puzzle()

    def _load_current_puzzle(self):
        puzzle_path = self.available_puzzles[self.current_puzzle_idx][1]
        self.puzzle = KakuroPuzzle.from_file(puzzle_path)

        # Chon kich thuoc o phu hop voi kich thuoc ma tran
        max_dim = max(self.puzzle.rows, self.puzzle.cols)
        if max_dim <= 5:
            self.cell_size = 80
        elif max_dim <= 7:
            self.cell_size = 70
        else:
            self.cell_size = 58

        self.grid_width = self.puzzle.cols * self.cell_size
        self.grid_height = self.puzzle.rows * self.cell_size
        self.window_width = self.grid_width + self.PANEL_WIDTH
        self.window_height = max(self.grid_height, 620)

        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Kakuro CSP Visualizer - Constraint Propagation (AI Final Project)")

        self.reset_solver()

    def reset_solver(self):
        cfg_name, cfg_kwargs = CONFIG_OPTIONS[self.current_config_idx]
        self.solver = BacktrackingSolver(self.puzzle, **cfg_kwargs)
        self.generator = self.solver.solve_stepwise()

        self.assignment: dict[tuple[int, int], int] = {}
        self.domains: dict[tuple[int, int], set[int]] = {
            v: set(range(1, 10)) for v in self.puzzle.white_cells
        }
        self.highlighted_cell: tuple[int, int] | None = None
        self.highlight_type = "normal"
        self.recently_pruned: list[tuple[tuple[int, int], int]] = []

        self.nodes_explored = 0
        self.backtracks = 0
        self.prunings_count = 0
        self.is_solved = False
        self.is_paused = True

        # Lay su kien dau tien (DOMAIN_INIT)
        try:
            init_event = next(self.generator)
            if init_event.domains_snapshot:
                self.domains = {v: set(d) for v, d in init_event.domains_snapshot.items()}
            self.add_log(init_event.message)
        except StopIteration:
            pass

    def add_log(self, text: str):
        self.logs.append(text)
        if len(self.logs) > 6:
            self.logs.pop(0)

    def step_solver(self):
        if self.is_solved:
            self.is_paused = True
            return

        try:
            event: SolverEvent = next(self.generator)
            self.assignment = dict(event.assignment_snapshot)
            if event.domains_snapshot:
                self.domains = {v: set(d) for v, d in event.domains_snapshot.items()}

            self.highlighted_cell = event.var
            self.recently_pruned = event.pruned

            if event.event_type == EventType.ASSIGN:
                self.highlight_type = "assign"
                self.nodes_explored += 1
            elif event.event_type == EventType.UNASSIGN:
                self.highlight_type = "backtrack"
                self.backtracks += 1
            elif event.event_type == EventType.PRUNE:
                self.highlight_type = "prune"
                self.prunings_count += len(event.pruned)
            elif event.event_type == EventType.SOLVED:
                self.highlight_type = "solved"
                self.is_solved = True
                self.is_paused = True
            elif event.event_type == EventType.FAILED:
                self.is_paused = True

            self.add_log(event.message)

        except StopIteration:
            self.is_paused = True
            self.add_log("Qua trinh giai hoan tat!")

    def run(self):
        while self.is_running:
            self._handle_events()
            if not self.is_paused and not self.is_solved:
                self.step_solver()
            self._render()
            self.clock.tick(self.fps if not self.is_paused else 30)

        pygame.quit()

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
                if event.key == pygame.K_SPACE:
                    self.is_paused = not self.is_paused
                    self.add_log("PLAY" if not self.is_paused else "PAUSE")
                elif event.key == pygame.K_s:
                    self.is_paused = True
                    self.step_solver()
                elif event.key == pygame.K_r:
                    self.reset_solver()
                elif event.key == pygame.K_UP:
                    self.fps = min(60, self.fps + 2)
                elif event.key == pygame.K_DOWN:
                    self.fps = max(1, self.fps - 2)

    def _handle_button_click(self, btn_id: str):
        if btn_id == "play_pause":
            self.is_paused = not self.is_paused
            self.add_log("PLAY" if not self.is_paused else "PAUSE")

        elif btn_id == "step":
            self.is_paused = True
            self.step_solver()

        elif btn_id == "reset":
            self.reset_solver()

        elif btn_id == "speed_down":
            self.fps = max(1, self.fps - 2)

        elif btn_id == "speed_up":
            self.fps = min(60, self.fps + 2)

        elif btn_id == "puzzle_prev":
            self.current_puzzle_idx = (self.current_puzzle_idx - 1) % len(self.available_puzzles)
            self._load_current_puzzle()

        elif btn_id == "puzzle_next":
            self.current_puzzle_idx = (self.current_puzzle_idx + 1) % len(self.available_puzzles)
            self._load_current_puzzle()

        elif btn_id == "config_prev":
            self.current_config_idx = (self.current_config_idx - 1) % len(CONFIG_OPTIONS)
            self.reset_solver()

        elif btn_id == "config_next":
            self.current_config_idx = (self.current_config_idx + 1) % len(CONFIG_OPTIONS)
            self.reset_solver()

    def _render(self):
        self.screen.fill(self.COLOR_BG)

        # 1. Ve luoi ban co Kakuro
        for r in range(self.puzzle.rows):
            for c in range(self.puzzle.cols):
                cell = self.puzzle.grid[(r, c)]
                cell_rect = pygame.Rect(
                    c * self.cell_size,
                    r * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )

                if cell.is_white:
                    self._draw_white_cell(r, c, cell_rect)
                else:
                    self._draw_clue_cell(cell, cell_rect)

                # Ve duong vien o
                pygame.draw.rect(self.screen, self.COLOR_GRID_LINE, cell_rect, 1)

        # 2. Ve bang dieu khien thao tac ben phai
        self._render_side_panel()

        pygame.display.flip()

    def _draw_clue_cell(self, cell, rect: pygame.Rect):
        pygame.draw.rect(self.screen, self.COLOR_BLACK_CELL, rect)

        if cell.is_clue:
            # Ve duong cheo tu goc tren-trai xuong goc duoi-phai
            pygame.draw.line(self.screen, self.COLOR_CLUE_LINE, rect.topleft, rect.bottomright, 2)

            # Manh moi doc (Down clue) o tam giac duoi-trai
            if cell.down_clue is not None:
                d_surf = self.font_clue.render(str(cell.down_clue), True, self.COLOR_CLUE_TEXT)
                d_rect = d_surf.get_rect(center=(rect.left + rect.width * 0.28, rect.top + rect.height * 0.72))
                self.screen.blit(d_surf, d_rect)

            # Manh moi ngang (Across clue) o tam giac tren-phai
            if cell.across_clue is not None:
                a_surf = self.font_clue.render(str(cell.across_clue), True, self.COLOR_CLUE_TEXT)
                a_rect = a_surf.get_rect(center=(rect.left + rect.width * 0.72, rect.top + rect.height * 0.28))
                self.screen.blit(a_surf, a_rect)

    def _draw_white_cell(self, r: int, c: int, rect: pygame.Rect):
        coord = (r, c)
        is_highlight = (coord == self.highlighted_cell)

        # Mau nen cua o trang
        if self.is_solved:
            bg_color = (235, 252, 240)
        elif is_highlight and self.highlight_type == "assign":
            bg_color = (210, 248, 225)
        elif is_highlight and self.highlight_type == "backtrack":
            bg_color = (254, 235, 218)
        else:
            bg_color = self.COLOR_WHITE_CELL

        pygame.draw.rect(self.screen, bg_color, rect)

        # Neu o da duoc gan gia tri: ve so lon giua o
        if coord in self.assignment:
            val_str = str(self.assignment[coord])
            color = (39, 174, 96) if is_highlight else self.COLOR_ASSIGNED_TEXT
            val_surf = self.font_main.render(val_str, True, color)
            val_rect = val_surf.get_rect(center=rect.center)
            self.screen.blit(val_surf, val_rect)

        # Neu o chua gan: ve mien gia tri dang luoi 3x3 chu so nho (Pencil-mark subgrid)
        else:
            dom = self.domains.get(coord, set())
            margin = 5
            sub_w = (rect.width - 2 * margin) / 3
            sub_h = (rect.height - 2 * margin) / 3

            for digit in range(1, 10):
                sub_r = (digit - 1) // 3
                sub_c = (digit - 1) % 3
                dx = rect.left + margin + sub_c * sub_w + sub_w / 2
                dy = rect.top + margin + sub_r * sub_h + sub_h / 2

                if digit in dom:
                    p_surf = self.font_pencil.render(str(digit), True, (75, 85, 105))
                    p_rect = p_surf.get_rect(center=(dx, dy))
                    self.screen.blit(p_surf, p_rect)
                elif (coord, digit) in self.recently_pruned:
                    # Hien thi chu so vua bi cat tia mau do
                    p_surf = self.font_pencil.render(str(digit), True, self.COLOR_PRUNED_TEXT)
                    p_rect = p_surf.get_rect(center=(dx, dy))
                    self.screen.blit(p_surf, p_rect)
                    # Gach cheo the hien bi loai
                    pygame.draw.line(self.screen, self.COLOR_PRUNED_TEXT, (dx - 4, dy - 4), (dx + 4, dy + 4), 1)

        # Ve vien nhan manh neu dang thao tac
        if is_highlight:
            h_color = (
                self.COLOR_HIGHLIGHT_ASSIGN
                if self.highlight_type == "assign"
                else self.COLOR_HIGHLIGHT_BACKTRACK
            )
            pygame.draw.rect(self.screen, h_color, rect, 3)

    def _draw_button(self, btn_id: str, text: str, rect: pygame.Rect, bg_color=None, text_color=None):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)

        if bg_color is None:
            bg_color = self.COLOR_BTN_HOVER if is_hover else self.COLOR_BTN_NORMAL
        if text_color is None:
            text_color = (255, 255, 255) if is_hover else self.COLOR_TEXT

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=4)
        pygame.draw.rect(self.screen, (70, 78, 95), rect, 1, border_radius=4)

        txt_surf = self.font_panel_bold.render(text, True, text_color)
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
            self.COLOR_GRID_LINE,
            (panel_x, 0),
            (panel_x, self.window_height),
            2,
        )

        y = 15
        # Title
        title = self.font_title.render("KAKURO CSP VISUALIZER", True, (255, 255, 255))
        self.screen.blit(title, (panel_x + 18, y))
        y += 30

        # --- SECTION 1: CHON DE TREN GUI ---
        puz_lbl = self.font_panel_bold.render("File de:", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(puz_lbl, (panel_x + 18, y + 5))

        self._draw_button("puzzle_prev", "<", pygame.Rect(panel_x + 85, y, 28, 26))
        puz_name = self.available_puzzles[self.current_puzzle_idx][0]
        puz_box = pygame.Rect(panel_x + 117, y, 195, 26)
        pygame.draw.rect(self.screen, (38, 42, 52), puz_box, border_radius=3)
        puz_surf = self.font_panel.render(puz_name, True, self.COLOR_TEXT)
        self.screen.blit(puz_surf, puz_surf.get_rect(center=puz_box.center))
        self._draw_button("puzzle_next", ">", pygame.Rect(panel_x + 316, y, 28, 26))
        y += 36

        # --- SECTION 2: CHON THUAT TOAN TREN GUI ---
        cfg_lbl = self.font_panel_bold.render("Thuat toan:", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(cfg_lbl, (panel_x + 18, y + 5))

        self._draw_button("config_prev", "<", pygame.Rect(panel_x + 105, y, 28, 26))
        cfg_name = CONFIG_OPTIONS[self.current_config_idx][0]
        cfg_box = pygame.Rect(panel_x + 137, y, 175, 26)
        pygame.draw.rect(self.screen, (38, 42, 52), cfg_box, border_radius=3)
        cfg_surf = self.font_panel.render(cfg_name[:20], True, (52, 152, 219))
        self.screen.blit(cfg_surf, cfg_surf.get_rect(center=cfg_box.center))
        self._draw_button("config_next", ">", pygame.Rect(panel_x + 316, y, 28, 26))
        y += 42

        # --- SECTION 3: CAC NUT BAM DIEU KHIEN CHINH ---
        play_txt = "PAUSE" if not self.is_paused else "PLAY"
        play_color = (192, 57, 43) if not self.is_paused else (39, 174, 96)
        self._draw_button("play_pause", play_txt, pygame.Rect(panel_x + 18, y, 105, 32), bg_color=play_color)
        self._draw_button("step", "STEP >", pygame.Rect(panel_x + 133, y, 105, 32))
        self._draw_button("reset", "RESET", pygame.Rect(panel_x + 248, y, 105, 32))
        y += 42

        # --- SECTION 4: TOC DO FPS ---
        speed_label = self.font_panel.render(f"Toc do buoc: {self.fps} buoc/s", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(speed_label, (panel_x + 18, y + 5))
        self._draw_button("speed_down", "- Speed", pygame.Rect(panel_x + 185, y, 80, 26))
        self._draw_button("speed_up", "+ Speed", pygame.Rect(panel_x + 273, y, 80, 26))
        y += 36

        # --- SECTION 5: THONG KE THUAT TOAN (REAL-TIME METRICS) ---
        pygame.draw.line(self.screen, self.COLOR_GRID_LINE, (panel_x + 18, y), (panel_x + self.PANEL_WIDTH - 18, y), 1)
        y += 10

        status_text = "SOLVED (HOAN TAT)" if self.is_solved else ("RUNNING..." if not self.is_paused else "PAUSED")
        status_color = (46, 204, 113) if self.is_solved else ((52, 152, 219) if not self.is_paused else (241, 196, 15))
        st_surf = self.font_panel_bold.render(f"Trang thai: {status_text}", True, status_color)
        self.screen.blit(st_surf, (panel_x + 18, y))
        y += 24

        n_assigned = len(self.assignment)
        n_total = len(self.puzzle.white_cells)
        pct = int(n_assigned / n_total * 100) if n_total > 0 else 0
        progress_surf = self.font_panel.render(f"Tien do: {n_assigned}/{n_total} o ({pct}%)", True, self.COLOR_TEXT)
        self.screen.blit(progress_surf, (panel_x + 18, y))
        y += 20

        nodes_surf = self.font_panel.render(f"Nodes explored (Gan thu) : {self.nodes_explored}", True, self.COLOR_TEXT)
        self.screen.blit(nodes_surf, (panel_x + 18, y))
        y += 20

        bts_surf = self.font_panel.render(f"Backtracks (Quay lui)    : {self.backtracks}", True, (230, 126, 34))
        self.screen.blit(bts_surf, (panel_x + 18, y))
        y += 20

        prune_surf = self.font_panel.render(f"Prunings (Gia tri cat)   : {self.prunings_count}", True, (231, 76, 60))
        self.screen.blit(prune_surf, (panel_x + 18, y))
        y += 28

        # --- SECTION 6: CHU GIAI TRUC QUAN (LEGEND) ---
        pygame.draw.line(self.screen, self.COLOR_GRID_LINE, (panel_x + 18, y), (panel_x + self.PANEL_WIDTH - 18, y), 1)
        y += 8
        leg_title = self.font_panel_bold.render("Chu giai mau sac:", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(leg_title, (panel_x + 18, y))
        y += 20

        # Item 1: Xanh la
        pygame.draw.rect(self.screen, (46, 204, 113), (panel_x + 18, y + 2, 12, 12), border_radius=2)
        l1 = self.font_panel.render("Xanh la: Vua duoc gan gia tri", True, self.COLOR_TEXT)
        self.screen.blit(l1, (panel_x + 36, y))
        y += 18

        # Item 2: Do
        pygame.draw.rect(self.screen, (231, 76, 60), (panel_x + 18, y + 2, 12, 12), border_radius=2)
        l2 = self.font_panel.render("Do (gach): Gia tri bi cat tia khoi mien", True, self.COLOR_TEXT)
        self.screen.blit(l2, (panel_x + 36, y))
        y += 18

        # Item 3: Cam
        pygame.draw.rect(self.screen, (230, 126, 34), (panel_x + 18, y + 2, 12, 12), border_radius=2)
        l3 = self.font_panel.render("Cam: Quay lui hoan tac gia tri", True, self.COLOR_TEXT)
        self.screen.blit(l3, (panel_x + 36, y))
        y += 24

        # --- SECTION 7: NHAT KY LOGS ---
        pygame.draw.line(self.screen, self.COLOR_GRID_LINE, (panel_x + 18, y), (panel_x + self.PANEL_WIDTH - 18, y), 1)
        y += 8
        log_title = self.font_panel_bold.render("Nhat ky thuat toan (Logs):", True, (255, 255, 255))
        self.screen.blit(log_title, (panel_x + 18, y))
        y += 20

        for line in self.logs[-5:]:
            log_line = self.font_panel.render(line[:42], True, self.COLOR_TEXT_MUTED)
            self.screen.blit(log_line, (panel_x + 18, y))
            y += 18
