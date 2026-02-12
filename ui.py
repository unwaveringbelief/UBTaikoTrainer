import pygame

def init_font():
    pygame.font.init()

class Button:
    """Standard UI button with hover effects and text override."""
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.text_override = None
        self.callback = callback
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.callback()
            return True
        return False

    def draw(self, screen):
        color = (120, 120, 120) if self.hovered else (70, 70, 70)
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1, border_radius=5)
        display_text = self.text_override if self.text_override else self.text
        txt_surf = self.font.render(display_text, True, (255, 255, 255))
        screen.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

class Checkbox:
    """Toggle switch UI element."""
    def __init__(self, x, y, size, label, initial_val, callback):
        self.rect = pygame.Rect(x, y, size, size)
        self.label = label
        self.val = initial_val
        self.callback = callback
        self.font = pygame.font.SysFont("Arial", 16, bold=True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.val = not self.val
            self.callback(self.val)
            return True
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, (70, 70, 70), self.rect, border_radius=3)
        if self.val:
            pygame.draw.rect(screen, (50, 200, 50), self.rect.inflate(-6, -6), border_radius=2)
        txt = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(txt, (self.rect.right + 10, self.rect.y))

class JudgmentText:
    """Floating accuracy feedback text (e.g., 'GOOD!', 'LATE')."""
    def __init__(self, text, color):
        self.text = text
        self.color = color
        self.start_time = time.perf_counter()
        self.font = pygame.font.SysFont("Arial", 36, bold=True)

    def draw(self, screen, x, y):
        elapsed = time.perf_counter() - self.start_time
        if elapsed > 0.4: return
        alpha = int(255 * (1.0 - elapsed / 0.4))
        # Surface with alpha requires a bit more effort in raw Pygame
        surf = self.font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        screen.blit(surf, (x - surf.get_width()//2, y - 100 - (elapsed * 100)))

import time # Needed for JudgmentText

class Slider:
    """Horizontal slider for numerical value adjustment."""
    def __init__(self, x, y, w, min_val, max_val, initial_val, label, callback):
        self.rect = pygame.Rect(x, y, w, 10)
        self.min_val, self.max_val, self.val = min_val, max_val, initial_val
        self.label, self.callback = label, callback
        self.grabbed = False
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.handle_rect = pygame.Rect(0, 0, 12, 30)
        self.update_handle_pos()

    def update_handle_pos(self):
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.center = (self.rect.x + ratio * self.rect.w, self.rect.y + 5)

    def set_pos(self, x, y):
        self.rect.topleft = (x, y); self.update_handle_pos()

    def draw(self, screen):
        pygame.draw.rect(screen, (80, 80, 80), self.rect, border_radius=5)
        pygame.draw.rect(screen, (200, 200, 200), self.handle_rect, border_radius=3)
        v_str = f"{int(self.val)}" if self.max_val > 1 else f"{round(self.val, 3)}"
        txt = self.font.render(f"{self.label}: {v_str}", True, (255, 255, 255))
        screen.blit(txt, (self.rect.x, self.rect.y - 25))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.handle_rect.collidepoint(event.pos):
            self.grabbed = True; return True
        if event.type == pygame.MOUSEBUTTONUP: self.grabbed = False
        if event.type == pygame.MOUSEMOTION and self.grabbed:
            rel_x = max(0, min(event.pos[0] - self.rect.x, self.rect.w))
            self.val = self.min_val + (rel_x / self.rect.w) * (self.max_val - self.min_val)
            self.update_handle_pos(); self.callback(self.val); return True
        return False

class Dropdown:
    """Collapsible menu for selecting from a list of options."""
    def __init__(self, x, y, w, h, main_text, options, callback):
        self.main_btn = Button(x, y, w, h, main_text, self.toggle)
        self.options, self.callback = options, callback
        self.is_open = False
        self.option_buttons = []
        for i, opt in enumerate(options):
            btn = Button(x, y + (i + 1) * h, w, h, opt["name"], lambda o=opt: self.select(o))
            self.option_buttons.append(btn)

    def toggle(self): self.is_open = not self.is_open
    def select(self, option): self.callback(option); self.is_open = False

    def handle_event(self, event):
        if self.main_btn.handle_event(event): return True
        if self.is_open:
            for btn in self.option_buttons:
                if btn.handle_event(event): return True
            if event.type == pygame.MOUSEBUTTONDOWN: self.is_open = False
        return False

    def draw(self, screen):
        self.main_btn.draw(screen)
        if self.is_open:
            for btn in self.option_buttons: btn.draw(screen)