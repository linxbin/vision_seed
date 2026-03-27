import pygame


def draw_button(*, screen, rect, text, color, font, mouse_pos, text_color=(255, 255, 255), icon=None, selected=False):
    hovered = rect.collidepoint(mouse_pos)
    fill = tuple(min(255, c + 16) for c in color) if hovered or selected else color
    border_color = (255, 250, 212) if selected else (255, 255, 255)
    if selected:
        glow = rect.inflate(10, 10)
        pygame.draw.rect(screen, (255, 236, 176), glow, border_radius=16)
    pygame.draw.rect(screen, fill, rect, border_radius=12)
    pygame.draw.rect(screen, border_color, rect, 3 if selected else 2, border_radius=12)
    label = font.render(text, True, text_color)
    gap = 8 if icon is not None else 0
    content_width = label.get_width() + (icon.get_width() + gap if icon is not None else 0)
    start_x = rect.centerx - content_width // 2
    if icon is not None:
        screen.blit(icon, (start_x, rect.centery - icon.get_height() // 2))
        start_x += icon.get_width() + gap
    screen.blit(label, (start_x, rect.centery - label.get_height() // 2))


def draw_top_stat_text(*, screen, font, text, pos, color=(56, 82, 118)):
    surface = font.render(text, True, color)
    screen.blit(surface, pos)
    return surface
