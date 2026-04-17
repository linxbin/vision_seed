from typing import Optional, Tuple


STARTUP_WINDOW_MARGIN = (48, 96)
STARTUP_FALLBACK_MIN_SIZE = (640, 480)


def detect_desktop_size(display) -> Optional[Tuple[int, int]]:
    """Return the current desktop size if SDL can provide it."""
    try:
        info = display.Info()
    except Exception:
        return None

    width = int(getattr(info, "current_w", 0) or 0)
    height = int(getattr(info, "current_h", 0) or 0)
    if width <= 0 or height <= 0:
        return None
    return (width, height)


def fit_startup_window_size(
    default_size: Tuple[int, int],
    desktop_size: Optional[Tuple[int, int]],
) -> Tuple[int, int]:
    """Fit the first window inside smaller laptop displays."""
    if not desktop_size:
        return default_size

    max_width = desktop_size[0]
    max_height = desktop_size[1]
    if max_width > 960:
        max_width -= STARTUP_WINDOW_MARGIN[0]
    if max_height > 720:
        max_height -= STARTUP_WINDOW_MARGIN[1]

    max_width = max(STARTUP_FALLBACK_MIN_SIZE[0], max_width)
    max_height = max(STARTUP_FALLBACK_MIN_SIZE[1], max_height)
    return (
        min(int(default_size[0]), int(max_width)),
        min(int(default_size[1]), int(max_height)),
    )


def clamp_window_size(
    size: Tuple[int, int],
    minimum_size: Tuple[int, int],
    desktop_size: Optional[Tuple[int, int]],
) -> Tuple[int, int]:
    """Clamp a resizable window while still allowing smaller displays."""
    width = int(size[0])
    height = int(size[1])
    min_width = int(minimum_size[0])
    min_height = int(minimum_size[1])

    if desktop_size:
        min_width = min(min_width, int(desktop_size[0]))
        min_height = min(min_height, int(desktop_size[1]))

    width = max(min_width, width)
    height = max(min_height, height)

    if desktop_size:
        width = min(width, int(desktop_size[0]))
        height = min(height, int(desktop_size[1]))

    return (width, height)


def set_compatible_display_mode(display, pygame_module, prefer_fullscreen: bool, windowed_size: Tuple[int, int]):
    """Open a display mode that is safer on laptop hardware."""
    desktop_size = detect_desktop_size(display)

    if prefer_fullscreen and desktop_size:
        try:
            surface = display.set_mode(desktop_size, pygame_module.NOFRAME)
            return surface, True, None
        except Exception as exc:
            fallback = display.set_mode(windowed_size, pygame_module.RESIZABLE)
            return fallback, False, str(exc)

    if prefer_fullscreen and not desktop_size:
        fallback = display.set_mode(windowed_size, pygame_module.RESIZABLE)
        return fallback, False, "desktop size unavailable"

    surface = display.set_mode(windowed_size, pygame_module.RESIZABLE)
    return surface, False, None
