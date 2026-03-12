import pygame
from core.asset_loader import load_image_if_exists, project_path


class PlatformTheme:
    BG_TOP = (246, 238, 223)
    BG_BOTTOM = (225, 241, 248)
    GLOW = (255, 214, 153)
    TEXT_PRIMARY = (56, 69, 88)
    TEXT_MUTED = (111, 126, 147)
    CARD = (255, 251, 245)
    CARD_ALT = (244, 249, 252)
    CARD_HOVER = (255, 246, 232)
    BORDER = (214, 201, 183)
    BORDER_HOVER = (235, 169, 108)
    ACCENT = (238, 174, 97)
    ACCENT_DARK = (205, 132, 64)
    ACCENT_SOFT = (252, 231, 199)
    INFO = (139, 176, 199)
    SHADOW = (193, 176, 154)
    CHIP_TEXT = (108, 74, 38)
    CHIP_TEXT_MUTED = (136, 98, 54)


def _load_ui_skin(name, size):
    return load_image_if_exists(project_path("assets", "ui", name), size)


def _load_ui_icon(icon_name, size, light=False):
    suffix = "light" if light else "dark"
    return load_image_if_exists(project_path("assets", "ui", f"{icon_name}_{suffix}.png"), size)


def draw_vertical_gradient(screen, rect, top_color, bottom_color):
    height = max(1, rect.height)
    for offset in range(height):
        ratio = offset / height
        color = tuple(int(top_color[i] + (bottom_color[i] - top_color[i]) * ratio) for i in range(3))
        pygame.draw.line(screen, color, (rect.x, rect.y + offset), (rect.right, rect.y + offset))


def draw_platform_background(screen, width, height):
    draw_vertical_gradient(screen, pygame.Rect(0, 0, width, height), PlatformTheme.BG_TOP, PlatformTheme.BG_BOTTOM)

    glow_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.circle(glow_surface, (*PlatformTheme.GLOW, 42), (width - 90, 110), 120)
    pygame.draw.circle(glow_surface, (255, 255, 255, 28), (110, 90), 88)
    pygame.draw.ellipse(glow_surface, (255, 255, 255, 24), (width // 2 - 180, height - 160, 360, 120))
    screen.blit(glow_surface, (0, 0))


def draw_card(screen, rect, hovered=False, alt=False, radius=16):
    fill = PlatformTheme.CARD_HOVER if hovered else (PlatformTheme.CARD_ALT if alt else PlatformTheme.CARD)
    border = PlatformTheme.BORDER_HOVER if hovered else PlatformTheme.BORDER
    shadow = pygame.Rect(rect.x, rect.y + 4, rect.width, rect.height)
    pygame.draw.rect(screen, PlatformTheme.SHADOW, shadow, border_radius=radius)
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, 2, border_radius=radius)


def draw_chip(screen, rect, hovered=False, radius=12):
    skin_name = "kenney_button_hover.png" if hovered else "kenney_button_flat.png"
    skin = _load_ui_skin(skin_name, (rect.width, rect.height))
    if skin is not None:
        screen.blit(skin, rect)
        return
    fill = PlatformTheme.ACCENT if hovered else PlatformTheme.ACCENT_SOFT
    border = PlatformTheme.ACCENT_DARK if hovered else PlatformTheme.BORDER
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, 2, border_radius=radius)


def draw_chip_label(screen, rect, font, text, hovered=False, icon_name=None, radius=12, text_color=None):
    draw_chip(screen, rect, hovered=hovered, radius=radius)

    label_color = text_color or PlatformTheme.CHIP_TEXT
    text_surface = font.render(text, True, label_color)
    icon_surface = _load_ui_icon(icon_name, (18, 18)) if icon_name else None

    gap = 8 if icon_surface is not None and text else 0
    content_width = text_surface.get_width()
    content_height = text_surface.get_height()
    if icon_surface is not None:
        content_width += icon_surface.get_width() + gap
        content_height = max(content_height, icon_surface.get_height())

    start_x = rect.centerx - content_width // 2
    center_y = rect.centery
    if icon_surface is not None:
        icon_y = center_y - icon_surface.get_height() // 2
        screen.blit(icon_surface, (start_x, icon_y))
        start_x += icon_surface.get_width() + gap

    text_y = center_y - text_surface.get_height() // 2
    screen.blit(text_surface, (start_x, text_y))
