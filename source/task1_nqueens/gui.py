import os
import sys
import time
import pygame

# Bat High-DPI Awareness tren Windows
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from task1_nqueens.board import NQueensBoard
from task1_nqueens.cnf_encoder import PairwiseEncoder, SequentialCounterEncoder
from task1_nqueens.min_conflicts import HeuristicMinConflicts, StandardMinConflicts
from task1_nqueens.sat_solver import SATNQueensSolver


N_PRESETS = [4, 6, 8, 10, 12, 16, 20, 30]

ALGORITHMS = [
    ("Min-Conflicts (Heuristic - De xuat)", "mc_heuristic"),
    ("Min-Conflicts (Standard)", "mc_standard"),
    ("SAT Glucose3 (Sequential Counter)", "sat_seq"),
    ("SAT Glucose3 (Pairwise)", "sat_pairwise"),
]


class NQueensGUI:
    """Giao dien do hoa Pygame truc quan hoa bai toan N-Queens.
    
    100% thao tac bang chuot tren man hinh: Chon N, chon thuat toan, Solve, Step, Reset, quay ve Menu.
    """

    PANEL_WIDTH = 380

    COLOR_BG = (22, 24, 28)
    COLOR_GRID_BORDER = (45, 50, 62)
    COLOR_TILE_LIGHT = (238, 238, 210)  # Mau ban co vua truyen thong
    COLOR_TILE_DARK = (118, 150, 86)
    COLOR_PANEL_BG = (30, 33, 40)
    COLOR_PANEL_HEADER = (42, 46, 56)
    COLOR_TEXT = (235, 238, 245)
    COLOR_TEXT_MUTED = (150, 155, 168)

    COLOR_QUEEN = (241, 196, 15)        # Vang gold sang trong
    COLOR_QUEEN_BORDER = (180, 130, 10)
    COLOR_CONFLICT = (231, 76, 60)      # Do: xung dot
    COLOR_CONFLICT_BG = (245, 183, 177)
    COLOR_VALID_BG = (212, 239, 223)

    COLOR_BTN_NORMAL = (48, 54, 66)
    COLOR_BTN_HOVER = (68, 76, 92)
    COLOR_ACCENT = (52, 152, 219)

    def __init__(self, initial_n: int = 8, on_return_menu=None):
        pygame.init()
        pygame.font.init()

        self.on_return_menu = on_return_menu
        self.n_idx = N_PRESETS.index(initial_n) if initial_n in N_PRESETS else 2  # mac dinh N=8
        self.algo_idx = 0  # mac dinh Min-Conflicts Heuristic

        font_family = "segoeui,tahoma,arial,consolas"
        self.font_title = pygame.font.SysFont(font_family, 18, bold=True)
        self.font_panel_bold = pygame.font.SysFont(font_family, 15, bold=True)
        self.font_panel = pygame.font.SysFont(font_family, 13)
        self.font_mini = pygame.font.SysFont(font_family, 12)

        self.clock = pygame.time.Clock()
        self.is_running = True
        self.buttons: dict[str, pygame.Rect] = {}
        self.logs: list[str] = ["He thong san sang! Nhan nut SOLVE tren man hinh de giai."]

        # Tai anh quan Hau (transparent PNG) va bo nho dem theo kich thuoc o co
        self.queen_img_raw: pygame.Surface | None = None
        self._queen_img_cache: dict[int, pygame.Surface] = {}
        queen_asset_path = os.path.join(os.path.dirname(__file__), "assets", "queen.png")
        if os.path.exists(queen_asset_path):
            try:
                self.queen_img_raw = pygame.image.load(queen_asset_path)
            except Exception:
                self.queen_img_raw = None

        self._init_board_state()

    @property
    def current_n(self) -> int:
        return N_PRESETS[self.n_idx]

    def _init_board_state(self):
        n = self.current_n
        self.board = NQueensBoard(n)
        self.queens: list[int | None] = [None] * n  # queens[c] = r
        self.conflicts_per_col = [0] * n
        self.is_solved = False
        self.solve_time_ms = 0.0
        self.steps_taken = 0
        self.clauses_count = 0
        self.vars_count = 0

        self.PANEL_WIDTH = 380

        # Kich thuoc o co tu dong co gian phu hop voi N
        if n <= 8:
            self.cell_size = 65
        elif n <= 12:
            self.cell_size = 46
        elif n <= 16:
            self.cell_size = 35
        elif n <= 20:
            self.cell_size = 28
        else:
            self.cell_size = 19

        self.grid_width = n * self.cell_size
        self.grid_height = n * self.cell_size
        self.window_width = self.grid_width + self.PANEL_WIDTH
        self.window_height = max(self.grid_height, 620)

        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"Task 1: N-Queens Problem (N={n}) - AI Final Project")

        self.font_queen = pygame.font.SysFont(
            "consolas", max(11, int(self.cell_size * 0.6)), bold=True
        )

    def add_log(self, text: str):
        self.logs.append(text)
        if len(self.logs) > 6:
            self.logs.pop(0)

    def solve_problem(self):
        algo_name, algo_code = ALGORITHMS[self.algo_idx]
        n = self.current_n

        self.add_log(f"Dang giai N={n} bang {algo_name[:20]}...")

        try:
            if algo_code == "mc_heuristic":
                solver = HeuristicMinConflicts(n, seed=42)
                res = solver.solve(max_steps=n * 100)
                self.queens = list(res.solution) if res.solution is not None else [None] * n
                self.is_solved = res.is_solved
                self.steps_taken = res.steps_taken
                self.solve_time_ms = res.solve_time_ms
                self.clauses_count = 0
                self.vars_count = n

            elif algo_code == "mc_standard":
                solver = StandardMinConflicts(n, seed=42)
                res = solver.solve(max_steps=n * 100)
                self.queens = list(res.solution) if res.solution is not None else [None] * n
                self.is_solved = res.is_solved
                self.steps_taken = res.steps_taken
                self.solve_time_ms = res.solve_time_ms
                self.clauses_count = 0
                self.vars_count = n

            elif algo_code == "sat_pairwise":
                encoder = PairwiseEncoder(n)
                solver = SATNQueensSolver(encoder)
                res = solver.solve()
                self.queens = list(res.queens_per_col) if res.queens_per_col is not None else [None] * n
                self.is_solved = res.is_satisfiable
                self.steps_taken = 1
                self.solve_time_ms = res.solve_time_ms
                self.clauses_count = res.clauses_count
                self.vars_count = res.variables_count

            elif algo_code == "sat_seq":
                encoder = SequentialCounterEncoder(n)
                solver = SATNQueensSolver(encoder)
                res = solver.solve()
                self.queens = list(res.queens_per_col) if res.queens_per_col is not None else [None] * n
                self.is_solved = res.is_satisfiable
                self.steps_taken = 1
                self.solve_time_ms = res.solve_time_ms
                self.clauses_count = res.clauses_count
                self.vars_count = res.variables_count

            # Tinh toan xung dot
            self._calculate_conflicts()

            if self.is_solved:
                self.add_log(f"Thanh cong! Thoi gian: {self.solve_time_ms:.2f}ms")
            else:
                self.add_log("Khong tim thay nghiem trong gioi han buoc!")

        except Exception as e:
            self.add_log(f"Loi giai thuat: {e}")

    def _calculate_conflicts(self):
        n = self.current_n
        self.conflicts_per_col = [0] * n
        if any(r is None for r in self.queens):
            return

        for c1 in range(n):
            r1 = self.queens[c1]
            for c2 in range(n):
                if c1 == c2:
                    continue
                r2 = self.queens[c2]
                if r1 == r2 or abs(r1 - r2) == abs(c1 - c2):
                    self.conflicts_per_col[c1] += 1

    def run(self) -> str:
        while self.is_running:
            self._handle_events()
            self._render()
            self.clock.tick(30)

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
                    self.solve_problem()
                elif event.key == pygame.K_r:
                    self._init_board_state()

    def _handle_button_click(self, btn_id: str):
        if btn_id == "menu":
            self.is_running = False

        elif btn_id == "solve":
            self.solve_problem()

        elif btn_id == "reset":
            self._init_board_state()

        elif btn_id == "n_prev":
            self.n_idx = (self.n_idx - 1) % len(N_PRESETS)
            self._init_board_state()

        elif btn_id == "n_next":
            self.n_idx = (self.n_idx + 1) % len(N_PRESETS)
            self._init_board_state()

        elif btn_id == "algo_prev":
            self.algo_idx = (self.algo_idx - 1) % len(ALGORITHMS)
            self.add_log(f"Chon: {ALGORITHMS[self.algo_idx][0][:25]}")

        elif btn_id == "algo_next":
            self.algo_idx = (self.algo_idx + 1) % len(ALGORITHMS)
            self.add_log(f"Chon: {ALGORITHMS[self.algo_idx][0][:25]}")

    def _render(self):
        self.screen.fill(self.COLOR_BG)

        # 1. Ve ban co vua N x N
        n = self.current_n

        for r in range(n):
            for c in range(n):
                cell_rect = pygame.Rect(
                    c * self.cell_size,
                    r * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                tile_color = (
                    self.COLOR_TILE_LIGHT if (r + c) % 2 == 0 else self.COLOR_TILE_DARK
                )

                # Neu co quan hau tai (r, c)
                has_queen = self.queens[c] == r

                if has_queen:
                    if self.conflicts_per_col[c] > 0:
                        pygame.draw.rect(self.screen, self.COLOR_CONFLICT_BG, cell_rect)
                    elif self.is_solved:
                        pygame.draw.rect(self.screen, self.COLOR_VALID_BG, cell_rect)
                    else:
                        pygame.draw.rect(self.screen, tile_color, cell_rect)
                else:
                    pygame.draw.rect(self.screen, tile_color, cell_rect)

                # Ve vien o co
                pygame.draw.rect(self.screen, self.COLOR_GRID_BORDER, cell_rect, 1)

                # Ve quan Hau (Gold Queen)
                if has_queen:
                    self._draw_queen(cell_rect, is_conflict=(self.conflicts_per_col[c] > 0))

        # 2. Ve Side Control Panel
        self._render_side_panel()

        pygame.display.flip()

    def _draw_queen(self, rect: pygame.Rect, is_conflict: bool):
        cx, cy = rect.center

        if self.queen_img_raw is not None:
            # Vien sang nhe hoac canh bao xung dot phia sau quan Hau
            if is_conflict:
                halo_radius = max(5, int(rect.width * 0.42))
                pygame.draw.circle(self.screen, (231, 76, 60), (cx, cy), halo_radius, 2)

            icon_size = max(12, int(rect.width * 0.86))
            scaled_queen = self._queen_img_cache.get(icon_size)
            if scaled_queen is None:
                surf = self.queen_img_raw.convert_alpha() if pygame.display.get_init() else self.queen_img_raw
                scaled_queen = pygame.transform.smoothscale(surf, (icon_size, icon_size))
                self._queen_img_cache[icon_size] = scaled_queen

            img_rect = scaled_queen.get_rect(center=(cx, cy))
            self.screen.blit(scaled_queen, img_rect)
            return

        radius = max(6, int(rect.width * 0.38))

        # Hinh tron nen quan hau (fallback)
        bg_col = self.COLOR_CONFLICT if is_conflict else self.COLOR_QUEEN
        border_col = (180, 40, 30) if is_conflict else self.COLOR_QUEEN_BORDER
        pygame.draw.circle(self.screen, bg_col, (cx, cy), radius)
        pygame.draw.circle(self.screen, border_col, (cx, cy), radius, 2)

        # Chu Q hoac vuong mien
        q_surf = self.font_queen.render("Q", True, (255, 255, 255) if is_conflict else (50, 40, 10))
        q_rect = q_surf.get_rect(center=(cx, cy - 1))
        self.screen.blit(q_surf, q_rect)

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
            self.COLOR_GRID_BORDER,
            (panel_x, 0),
            (panel_x, self.window_height),
            2,
        )

        y = 12

        # 0. Nut quay ve Menu trung tam
        self._draw_button("menu", "< MENU CHINH", pygame.Rect(panel_x + 18, y, 120, 26), bg_color=(192, 57, 43))
        y += 34

        # Title
        title = self.font_title.render("TASK 1: N-QUEENS PROBLEM", True, (255, 255, 255))
        self.screen.blit(title, (panel_x + 18, y))
        y += 28

        # --- SECTION 1: CHON KICH THUOC N ---
        n_lbl = self.font_panel_bold.render("Kich thuoc N:", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(n_lbl, (panel_x + 18, y + 5))

        self._draw_button("n_prev", "<", pygame.Rect(panel_x + 125, y, 28, 26))
        n_box = pygame.Rect(panel_x + 157, y, 155, 26)
        pygame.draw.rect(self.screen, (38, 42, 52), n_box, border_radius=3)
        n_surf = self.font_panel_bold.render(f"N = {self.current_n} Queens", True, (241, 196, 15))
        self.screen.blit(n_surf, n_surf.get_rect(center=n_box.center))
        self._draw_button("n_next", ">", pygame.Rect(panel_x + 316, y, 28, 26))
        y += 36

        # --- SECTION 2: CHON THUAT TOAN ---
        algo_lbl = self.font_panel_bold.render("Thuat toan:", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(algo_lbl, (panel_x + 18, y + 5))

        self._draw_button("algo_prev", "<", pygame.Rect(panel_x + 105, y, 28, 26))
        algo_name = ALGORITHMS[self.algo_idx][0]
        algo_box = pygame.Rect(panel_x + 137, y, 175, 26)
        pygame.draw.rect(self.screen, (38, 42, 52), algo_box, border_radius=3)
        algo_surf = self.font_mini.render(algo_name[:22], True, (52, 152, 219))
        self.screen.blit(algo_surf, algo_surf.get_rect(center=algo_box.center))
        self._draw_button("algo_next", ">", pygame.Rect(panel_x + 316, y, 28, 26))
        y += 40

        # --- SECTION 3: CAC NUT THAO TAC ---
        self._draw_button("solve", "SOLVE (GIAI)", pygame.Rect(panel_x + 18, y, 160, 34), bg_color=(39, 174, 96))
        self._draw_button("reset", "RESET (XOA)", pygame.Rect(panel_x + 188, y, 156, 34))
        y += 44

        # --- SECTION 4: THONG SO THUAT TOAN THOI GIAN THUC ---
        pygame.draw.line(self.screen, self.COLOR_GRID_BORDER, (panel_x + 18, y), (panel_x + self.PANEL_WIDTH - 18, y), 1)
        y += 10

        st_col = (46, 204, 113) if self.is_solved else (231, 76, 60)
        st_text = "SOLVED (HOP LE 100%)" if self.is_solved else "CHUA GIAI / CO XUNG DOT"
        st_surf = self.font_panel_bold.render(f"Trang thai: {st_text}", True, st_col)
        self.screen.blit(st_surf, (panel_x + 18, y))
        y += 22

        total_conflicts = sum(self.conflicts_per_col) // 2
        conf_surf = self.font_panel.render(f"Tong so xung dot  : {total_conflicts}", True, self.COLOR_TEXT)
        self.screen.blit(conf_surf, (panel_x + 18, y))
        y += 20

        time_surf = self.font_panel.render(f"Thoi gian thuc thi : {self.solve_time_ms:.2f} ms", True, (241, 196, 15))
        self.screen.blit(time_surf, (panel_x + 18, y))
        y += 20

        if "sat" in ALGORITHMS[self.algo_idx][1]:
            c_surf = self.font_panel.render(f"So clauses CNF     : {self.clauses_count:,}", True, self.COLOR_TEXT)
            self.screen.blit(c_surf, (panel_x + 18, y))
            y += 20
            v_surf = self.font_panel.render(f"So bien DIMACS     : {self.vars_count:,}", True, self.COLOR_TEXT)
            self.screen.blit(v_surf, (panel_x + 18, y))
            y += 24
        else:
            s_surf = self.font_panel.render(f"So buoc tim kiem   : {self.steps_taken} steps", True, self.COLOR_TEXT)
            self.screen.blit(s_surf, (panel_x + 18, y))
            y += 24

        # --- SECTION 5: LƯỢC ĐỒ SO SÁNH TRỰC QUAN (MINI VISUAL BARS) ---
        pygame.draw.line(self.screen, self.COLOR_GRID_BORDER, (panel_x + 18, y), (panel_x + self.PANEL_WIDTH - 18, y), 1)
        y += 8
        comp_title = self.font_panel_bold.render("Luoc do so sanh truc quan:", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(comp_title, (panel_x + 18, y))
        y += 20

        # Bar 1: Heuristic vs Standard (Số bước tại N=1000)
        b1_lbl = self.font_mini.render("Min-Conflicts: So buoc tai N=1000", True, self.COLOR_TEXT)
        self.screen.blit(b1_lbl, (panel_x + 18, y))
        y += 16
        # Ve bar Heuristic
        pygame.draw.rect(self.screen, (46, 204, 113), (panel_x + 18, y, 16, 10), border_radius=2)
        h_txt = self.font_mini.render("Heuristic: 31.6 buoc (Giam 95.6%)", True, (46, 204, 113))
        self.screen.blit(h_txt, (panel_x + 40, y - 2))
        y += 14
        # Ve bar Standard
        pygame.draw.rect(self.screen, (231, 76, 60), (panel_x + 18, y, 160, 10), border_radius=2)
        s_txt = self.font_mini.render("Standard: 713.6 buoc", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(s_txt, (panel_x + 184, y - 2))
        y += 20

        # Bar 2: Sequential Counter vs Pairwise (Số clauses tại N=50)
        b2_lbl = self.font_mini.render("SAT Encoders: So clauses tai N=50", True, self.COLOR_TEXT)
        self.screen.blit(b2_lbl, (panel_x + 18, y))
        y += 16
        pygame.draw.rect(self.screen, (52, 152, 219), (panel_x + 18, y, 35, 10), border_radius=2)
        seq_txt = self.font_mini.render("Seq Counter: 28.9k (Giam 86%)", True, (52, 152, 219))
        self.screen.blit(seq_txt, (panel_x + 60, y - 2))
        y += 14
        pygame.draw.rect(self.screen, (155, 89, 182), (panel_x + 18, y, 180, 10), border_radius=2)
        pw_txt = self.font_mini.render("Pairwise: 203.4k clauses", True, self.COLOR_TEXT_MUTED)
        self.screen.blit(pw_txt, (panel_x + 204, y - 2))
        y += 24

        # --- SECTION 6: NHAT KY LOGS ---
        pygame.draw.line(self.screen, self.COLOR_GRID_BORDER, (panel_x + 18, y), (panel_x + self.PANEL_WIDTH - 18, y), 1)
        y += 8
        log_title = self.font_panel_bold.render("Nhat ky (Logs):", True, (255, 255, 255))
        self.screen.blit(log_title, (panel_x + 18, y))
        y += 18

        for line in self.logs[-4:]:
            log_line = self.font_mini.render(line[:46], True, self.COLOR_TEXT_MUTED)
            self.screen.blit(log_line, (panel_x + 18, y))
            y += 16


if __name__ == "__main__":
    gui = NQueensGUI()
    gui.run()
    pygame.quit()

