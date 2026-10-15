import pygame
from game.board import Board, GRID_SIZE, TILE_SIZE


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        offset_x = (width - (GRID_SIZE * TILE_SIZE)) // 2
        offset_y = (height - (GRID_SIZE * TILE_SIZE)) // 2 + 30

        self.board = Board(offset_x, offset_y, target_score=500, max_moves=20)
        
        self.idle_since = pygame.time.get_ticks()
        self.hint_swap = None

        self.font_big = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 24)

    
    def handle_click(self, mouse_pos):
        self.idle_since = pygame.time.get_ticks()
        self.hint_swap = None
        self.board.hint_swap = None

        if self.board.is_game_over() or self.board.is_animating():
            return

        mx, my = mouse_pos
        bx = mx - self.board.offset_x
        by = my - self.board.offset_y

        if 0 <= bx < GRID_SIZE * TILE_SIZE and 0 <= by < GRID_SIZE * TILE_SIZE:
            col = int(bx // TILE_SIZE)
            row = int(by // TILE_SIZE)

            if self.board.selected is None:
                self.board.selected = (row, col)
            else:
                prev_selected = self.board.selected
                if prev_selected == (row, col):
                    self.board.selected = None
                else:
                    self.board.process_swap(prev_selected, (row, col))
                    self.board.selected = None

    def reset(self):
        self.board.reset()
        self.idle_since = pygame.time.get_ticks()
        self.hint_swap = None
        self.board.hint_swap = None

    def update(self):
        self.board.update()

        if self.board.is_game_over() or self.board.is_animating():
            self.hint_swap = None
            self.board.hint_swap = None
            return

        if pygame.time.get_ticks() - self.idle_since > 5000:
            if self.hint_swap is None:
                self.hint_swap = self.board.find_valid_swap()
                self.board.hint_swap = self.hint_swap

    def render(self, screen):
        screen.fill((32, 34, 40))

        title_surf = self.font_big.render("MATCH-3 GEM SWAP", True, (240, 240, 240))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 10))
        hud_text = (
            f"SCORE: {self.board.score} / {self.board.target_score}   |   "
            f"MOVES LEFT: {self.board.moves_remaining}"
        )
        hud_surf = self.font_small.render(hud_text, True, (80, 220, 180))
        screen.blit(hud_surf, (self.width // 2 - hud_surf.get_width() // 2, 55))

        self.board.render(screen)
        
        if (
            self.board.combo_display is not None
            and pygame.time.get_ticks() < self.board.combo_display_until
        ):
            combo_surf = self.font_big.render(
                f"COMBO x{self.board.combo_display}", True, (255, 220, 80)
            )
            screen.blit(
                combo_surf,
                (
                    self.width // 2 - combo_surf.get_width() // 2,
                    self.board.offset_y - 30,
                ),
            )

        inst_surf = self.font_small.render(
            "Swap gems to match 3+. Press [R] to Restart.",
            True,
            (180, 180, 180),
        )
        screen.blit(
            inst_surf, (self.width // 2 - inst_surf.get_width() // 2, self.height - 25)
        )

        result = self.board.check_result()
        if result:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))

            if result == "WIN":
                msg = "STAGE CLEARED!"
                color = (80, 220, 80)
            else:
                msg = "OUT OF MOVES!"
                color = (240, 80, 80)

            res_surf = self.font_big.render(msg, True, color)
            screen.blit(
                res_surf,
                (self.width // 2 - res_surf.get_width() // 2, self.height // 2 - 40),
            )

            sub_text = f"Final Score: {self.board.score}  |  Press [R] to Play Again"
            sub_surf = self.font_small.render(sub_text, True, (220, 220, 220))
            screen.blit(
                sub_surf,
                (self.width // 2 - sub_surf.get_width() // 2, self.height // 2 + 10),
            )