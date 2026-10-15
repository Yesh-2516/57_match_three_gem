import random
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50),   # Red
    (50, 200, 50),   # Green
    (50, 100, 240),  # Blue
    (240, 200, 40),  # Yellow
    (180, 50, 220),  # Purple
    (240, 130, 40),  # Orange
]


class Gem:
    
    def __init__(self, color, target_row, col):
        self.color = color
        self.target_row = target_row
        self.col = col
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0
        self.is_special = False
        self.special_direction = None

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed
            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y


class Board:
  
    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves

        self.combo_multiplier = 1
        self.combo_display = None
        self.combo_display_until = 0
        
        self.hint_swap = None

        self.reset()

    
    def reset(self):
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        self.combo_multiplier = 1
        self.combo_display = None
        self.combo_display_until = 0

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = gem.target_y
                self.grid[r][c] = gem

        self.resolve_matches()

    def is_animating(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and self.grid[r][c].is_animating():
                    return True
        return False

    def swap_gems(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2

        g1, g2 = self.grid[r1][c1], self.grid[r2][c2]
        self.grid[r1][c1], self.grid[r2][c2] = g2, g1

        if self.grid[r1][c1]:
            self.grid[r1][c1].target_row = r1
            self.grid[r1][c1].target_y = r1 * TILE_SIZE
            self.grid[r1][c1].current_y = r1 * TILE_SIZE

        if self.grid[r2][c2]:
            self.grid[r2][c2].target_row = r2
            self.grid[r2][c2].target_y = r2 * TILE_SIZE
            self.grid[r2][c2].current_y = r2 * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_matches(self):
        matched = set()

        for positions, direction in self.find_match_lines():
            matched.update(positions)

        return matched

    def drop_and_refill(self):
        for c in range(GRID_SIZE):
            empty_slots = 0

            for r in range(GRID_SIZE - 1, -1, -1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots > 0:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None

            for r in range(empty_slots):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = -((empty_slots - r) * TILE_SIZE)
                self.grid[r][c] = gem

    
    
    def resolve_matches(self, score_matches=False, protected_special=None):
        total_cleared = 0
        multiplier = 1

        while True:
            lines = self.find_match_lines()
            if not lines:
                break

            to_clear = set()
            for positions, direction in lines:
                to_clear.update(positions)

            triggered_specials = set()
            changed = True

            while changed:
                changed = False

                for r, c in list(to_clear):
                    gem = self.grid[r][c]

                    if (
                        gem is None
                        or not gem.is_special
                        or (r, c) == protected_special
                        or (r, c) in triggered_specials
                    ):
                        continue

                    triggered_specials.add((r, c))

                    if gem.special_direction == "horizontal":
                        to_clear.update((r, col) for col in range(GRID_SIZE))
                    else:
                        to_clear.update((row, c) for row in range(GRID_SIZE))

                    changed = True

            if protected_special is not None:
                to_clear.discard(protected_special)

            cleared_now = {
                (r, c) for r, c in to_clear
                if self.grid[r][c] is not None
            }

            if not cleared_now:
                break

            total_cleared += len(cleared_now)

            if score_matches:
                self.combo_multiplier = multiplier
                self.score += len(cleared_now) * 10 * multiplier

                if multiplier >= 2:
                    self.combo_display = multiplier
                    self.combo_display_until = pygame.time.get_ticks() + 1500

            for r, c in cleared_now:
                self.grid[r][c] = None

            self.drop_and_refill()
            protected_special = None
            multiplier += 1

        return total_cleared
 
    def process_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1, pos2) or self.is_game_over() or self.is_animating():
            return False

        self.combo_multiplier = 1
        self.combo_display = None
        self.combo_display_until = 0

        self.swap_gems(pos1, pos2)
        matches = self.find_matches()

        if not matches:
            self.swap_gems(pos1, pos2)
            return False

        self.moves_remaining -= 1

        self.resolve_matches(score_matches=True)
        return True

    def is_game_over(self):
        return self.score >= self.target_score or self.moves_remaining <= 0

    def check_result(self):
        if self.score >= self.target_score:
            return "WIN"
        if self.moves_remaining <= 0:
            return "LOSS"
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    self.grid[r][c].update()

    def render(self, surface):
        board_rect = pygame.Rect(
            self.offset_x, self.offset_y, GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
        )
        pygame.draw.rect(surface, (20, 22, 28), board_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), board_rect, width=3, border_radius=8)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y
                    tile_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)

                    pygame.draw.rect(surface, gem.color, tile_rect, border_radius=10)
                    pygame.draw.rect(
                        surface, (255, 255, 255), tile_rect, width=1, border_radius=10
                    )
                    
                    if gem.is_special:
                        glow_rect = tile_rect.inflate(8, 8)
                        pygame.draw.rect(
                            surface,
                            (255, 245, 120),
                            glow_rect,
                            width=4,
                            border_radius=13,
                        )
                        pygame.draw.rect(
                            surface,
                            (255, 255, 255),
                            tile_rect.inflate(2, 2),
                            width=2,
                            border_radius=11,
                        )

                if self.selected == (r, c):
                    sel_x = self.offset_x + c * TILE_SIZE
                    sel_y = self.offset_y + r * TILE_SIZE
                    sel_rect = pygame.Rect(sel_x + 2, sel_y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(
                        surface, (255, 255, 255), sel_rect, width=4, border_radius=10
                    )


                
        if self.hint_swap and not self.is_animating():
            pulse = (pygame.time.get_ticks() % 1000) / 1000
            glow_width = 2 if pulse < 0.5 else 3

            for r, c in self.hint_swap:
                x = self.offset_x + c * TILE_SIZE
                y = self.offset_y + r * TILE_SIZE
                hint_rect = pygame.Rect(
                    x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 8
                )
                pygame.draw.rect(
                    surface,
                    (180, 255, 200),
                    hint_rect,
                    width=glow_width,
                    border_radius=10,
                )
    
    def find_match_lines(self):
        lines = []

        for r in range(GRID_SIZE):
            c = 0
            while c < GRID_SIZE:
                start = c
                gem = self.grid[r][c]

                if gem is None:
                    c += 1
                    continue

                while (
                    c + 1 < GRID_SIZE
                    and self.grid[r][c + 1] is not None
                    and self.grid[r][c + 1].color == gem.color
                ):
                    c += 1

                if c - start + 1 >= 3:
                    lines.append(([(r, col) for col in range(start, c + 1)], "horizontal"))

                c += 1

        for c in range(GRID_SIZE):
            r = 0
            while r < GRID_SIZE:
                start = r
                gem = self.grid[r][c]

                if gem is None:
                    r += 1
                    continue

                while (
                    r + 1 < GRID_SIZE
                    and self.grid[r + 1][c] is not None
                    and self.grid[r + 1][c].color == gem.color
                ):
                    r += 1

                if r - start + 1 >= 3:
                    lines.append(([(row, c) for row in range(start, r + 1)], "vertical"))

                r += 1

        return lines

    
    def find_valid_swap(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                for dr, dc in ((0, 1), (1, 0)):
                    nr, nc = r + dr, c + dc

                    if nr >= GRID_SIZE or nc >= GRID_SIZE:
                        continue

                    pos1 = (r, c)
                    pos2 = (nr, nc)

                    self.swap_gems(pos1, pos2)
                    has_match = bool(self.find_matches())
                    self.swap_gems(pos1, pos2)

                    if has_match:
                        return pos1, pos2

        return None
