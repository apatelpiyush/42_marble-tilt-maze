import pygame
from .marble import Marble
from .wall import Wall

# Game Engine

WHITE = (255, 255, 255)
DARK = (40, 40, 50)
WALL_COLOR = (90, 90, 110)
GOAL_COLOR = (60, 200, 120)
RED = (220, 70, 70)

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.marble = Marble(50, 50)
        self.tilt_strength = 0.6
        self.friction = 0.02
        self.max_speed = 9

        self.walls = self._build_maze()
        self.goal_x, self.goal_y, self.goal_radius = width - 60, height - 60, 22

        self.time_limit_ms = 45000
        self.start_ticks = pygame.time.get_ticks()

        self.font = pygame.font.SysFont("Arial", 26)
        self.title_font = pygame.font.SysFont("Arial", 52, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 24)
        self.game_over = False
        self.result = None  # "solved" or "timeout"
        self.finish_time_ms = None

    def _build_maze(self):
        walls = []
        t = 16  # wall thickness

        # outer boundary
        walls.append(Wall(0, 0, self.width, t))
        walls.append(Wall(0, self.height - t, self.width, t))
        walls.append(Wall(0, 0, t, self.height))
        walls.append(Wall(self.width - t, 0, t, self.height))

        # a few internal walls forming a simple winding path
        walls.append(Wall(0, 140, self.width - 140, t))
        walls.append(Wall(140, 260, self.width - 140, t))
        walls.append(Wall(0, 380, self.width - 140, t))

        return walls

    def handle_event(self, event):
        if self.game_over and event.type == pygame.KEYDOWN:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_input(self):
        if self.game_over:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.width // 2
        dy = mouse_y - self.height // 2
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        ax = (dx / dist) * self.tilt_strength
        ay = (dy / dist) * self.tilt_strength
        self.marble.vx += ax
        self.marble.vy += ay

    def update(self):
        if self.game_over:
            return

        elapsed = pygame.time.get_ticks() - self.start_ticks
        if elapsed >= self.time_limit_ms:
            self.game_over = True
            self.result = "timeout"
            return

        self.marble.vx *= (1 - self.friction)
        self.marble.vy *= (1 - self.friction)

        speed = (self.marble.vx ** 2 + self.marble.vy ** 2) ** 0.5
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.marble.vx *= scale
            self.marble.vy *= scale

        self.marble.x += self.marble.vx
        self.marble.y += self.marble.vy

        self._resolve_wall_collisions()

        gx = self.goal_x - self.marble.x
        gy = self.goal_y - self.marble.y
        if (gx ** 2 + gy ** 2) ** 0.5 <= self.goal_radius:
            self.game_over = True
            self.result = "solved"
            self.finish_time_ms = elapsed

    def _resolve_wall_collisions(self):
        radius = self.marble.radius
        for wall in self.walls:
            wall_rect = wall.rect()

            closest_x = max(wall_rect.left, min(self.marble.x, wall_rect.right))
            closest_y = max(wall_rect.top, min(self.marble.y, wall_rect.bottom))

            dx = self.marble.x - closest_x
            dy = self.marble.y - closest_y
            dist_sq = dx * dx + dy * dy

            if dist_sq >= radius * radius:
                continue

            if dist_sq > 0:
                dist = dist_sq ** 0.5
                nx = dx / dist
                ny = dy / dist
                penetration = radius - dist
            else:
                gaps = {
                    "left": self.marble.x - wall_rect.left,
                    "right": wall_rect.right - self.marble.x,
                    "top": self.marble.y - wall_rect.top,
                    "bottom": wall_rect.bottom - self.marble.y,
                }
                side = min(gaps, key=gaps.get)
                nx, ny = {
                    "left": (-1, 0),
                    "right": (1, 0),
                    "top": (0, -1),
                    "bottom": (0, 1),
                }[side]
                penetration = gaps[side] + radius

            self.marble.x += nx * penetration
            self.marble.y += ny * penetration

            velocity_along_normal = self.marble.vx * nx + self.marble.vy * ny
            if velocity_along_normal < 0:
                restitution = 0.3
                self.marble.vx -= (1 + restitution) * velocity_along_normal * nx
                self.marble.vy -= (1 + restitution) * velocity_along_normal * ny

    def render(self, screen):
        screen.fill(DARK)

        for wall in self.walls:
            pygame.draw.rect(screen, WALL_COLOR, wall.rect())

        pygame.draw.circle(screen, GOAL_COLOR, (self.goal_x, self.goal_y), self.goal_radius)
        pygame.draw.circle(screen, WHITE, (int(self.marble.x), int(self.marble.y)), self.marble.radius)

        if self.result == "solved":
            elapsed = self.finish_time_ms
        else:
            elapsed = pygame.time.get_ticks() - self.start_ticks
        seconds_left = max(0, (self.time_limit_ms - elapsed) // 1000)
        timer_text = self.font.render(f"Time: {seconds_left}s", True, WHITE)
        screen.blit(timer_text, (10, 10))

        if self.game_over:
            self._render_end_screen(screen)

    def _render_end_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        if self.result == "solved":
            title = "Maze Solved!"
            title_color = GOAL_COLOR
            detail = f"Finish time: {self.finish_time_ms / 1000:.1f}s"
        else:
            title = "Time's Up!"
            title_color = RED
            detail = "The maze was not solved."

        title_surf = self.title_font.render(title, True, title_color)
        detail_surf = self.font.render(detail, True, WHITE)
        prompt_surf = self.small_font.render("Press any key to exit", True, WHITE)

        cx = self.width // 2
        cy = self.height // 2
        screen.blit(title_surf, title_surf.get_rect(center=(cx, cy - 50)))
        screen.blit(detail_surf, detail_surf.get_rect(center=(cx, cy + 10)))
        screen.blit(prompt_surf, prompt_surf.get_rect(center=(cx, cy + 70)))
