import unittest

from core.display_bootstrap import clamp_window_size, detect_desktop_size, fit_startup_window_size, set_compatible_display_mode


class _Info:
    def __init__(self, width, height):
        self.current_w = width
        self.current_h = height


class _DisplayStub:
    def __init__(self, desktop_size=(1920, 1080), fail_fullscreen=False):
        self.desktop_size = desktop_size
        self.fail_fullscreen = fail_fullscreen
        self.calls = []

    def Info(self):
        return _Info(*self.desktop_size)

    def set_mode(self, size, flags):
        self.calls.append((size, flags))
        if self.fail_fullscreen and flags == _PygameStub.NOFRAME:
            raise RuntimeError("exclusive fullscreen failed")
        return {"size": size, "flags": flags}


class _BrokenDisplayStub:
    def Info(self):
        raise RuntimeError("display info unavailable")


class _PygameStub:
    NOFRAME = 10
    RESIZABLE = 20


class DisplayBootstrapTests(unittest.TestCase):
    def test_detect_desktop_size_ignores_invalid_info(self):
        self.assertIsNone(detect_desktop_size(_BrokenDisplayStub()))

    def test_fit_startup_window_size_shrinks_for_laptop_screens(self):
        size = fit_startup_window_size((1000, 800), (1366, 768))
        self.assertEqual(size, (1000, 672))

    def test_clamp_window_size_allows_small_desktops(self):
        size = clamp_window_size((1000, 800), (1000, 800), (1366, 768))
        self.assertEqual(size, (1000, 768))

    def test_set_compatible_display_mode_falls_back_to_windowed(self):
        display = _DisplayStub(desktop_size=(1366, 768), fail_fullscreen=True)
        surface, is_fullscreen, error = set_compatible_display_mode(
            display,
            _PygameStub,
            True,
            (1000, 672),
        )

        self.assertEqual(surface["flags"], _PygameStub.RESIZABLE)
        self.assertFalse(is_fullscreen)
        self.assertIn("fullscreen failed", error)
        self.assertEqual(display.calls, [((1366, 768), _PygameStub.NOFRAME), ((1000, 672), _PygameStub.RESIZABLE)])

    def test_set_compatible_display_mode_uses_borderless_desktop_for_fullscreen(self):
        display = _DisplayStub(desktop_size=(1600, 900))
        surface, is_fullscreen, error = set_compatible_display_mode(
            display,
            _PygameStub,
            True,
            (1000, 704),
        )

        self.assertEqual(surface["size"], (1600, 900))
        self.assertEqual(surface["flags"], _PygameStub.NOFRAME)
        self.assertTrue(is_fullscreen)
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
