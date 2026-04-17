import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, MIN_SCREEN_WIDTH, MIN_SCREEN_HEIGHT, FPS, TITLE
from core.app_paths import get_resource_path
from core.display_bootstrap import clamp_window_size, detect_desktop_size, fit_startup_window_size, set_compatible_display_mode
from core.scene_manager import SceneManager
from core.startup_health import run_startup_health_check, safe_init_audio
from scenes.menu_scene import MenuScene
from scenes.license_scene import LicenseScene
from scenes.onboarding_scene import OnboardingScene
from scenes.category_scene import CategoryScene
from scenes.game_host_scene import GameHostScene
from scenes.system_settings_scene import SystemSettingsScene


def main():
    pygame.init()

    icon_path = get_resource_path("assets", "branding", "shiya_app_icon_256.png")
    try:
        window_icon = pygame.image.load(icon_path)
        if pygame.display.get_surface() is not None:
            window_icon = window_icon.convert_alpha()
        pygame.display.set_icon(window_icon)
    except (pygame.error, FileNotFoundError):
        pass

    run_startup_health_check()
    audio_ok = safe_init_audio()
    desktop_size = detect_desktop_size(pygame.display)
    windowed_size = fit_startup_window_size((SCREEN_WIDTH, SCREEN_HEIGHT), desktop_size)

    clock = pygame.time.Clock()

    manager = SceneManager()
    if not audio_ok:
        manager.settings["sound_enabled"] = False
        manager.apply_sound_preference()

    pygame.display.set_caption(TITLE)
    screen, is_fullscreen, mode_error = set_compatible_display_mode(
        pygame.display,
        pygame,
        bool(manager.settings.get("fullscreen")),
        windowed_size,
    )
    if mode_error:
        print(f"[display] Fullscreen startup fallback: {mode_error}")
    if is_fullscreen != bool(manager.settings.get("fullscreen")):
        manager.settings["fullscreen"] = is_fullscreen
        manager.save_user_preferences()
    manager.set_screen_size(*screen.get_size())

    manager.register("menu", MenuScene(manager))
    manager.register("license", LicenseScene(manager))
    manager.register("onboarding", OnboardingScene(manager))
    manager.register("category", CategoryScene(manager))
    manager.register("game_host", GameHostScene(manager))
    manager.register("system_settings", SystemSettingsScene(manager))

    has_license, _message = manager.license_manager.check_local_license()
    initial_scene = manager.decide_initial_scene(
        has_license=has_license,
        onboarding_completed=bool(manager.settings.get("onboarding_completed", False)),
    )
    manager.set_scene(initial_scene)

    running = True
    while running:
        manager.update_frame_timing(clock.tick(FPS))

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                if not manager.settings.get("fullscreen", False):
                    desktop_size = detect_desktop_size(pygame.display)
                    windowed_size = clamp_window_size(
                        event.size,
                        (MIN_SCREEN_WIDTH, MIN_SCREEN_HEIGHT),
                        desktop_size,
                    )
                    screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                    manager.set_screen_size(*screen.get_size())
                    manager.get_scene().on_resize(*screen.get_size())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)):
                    is_fullscreen = manager.settings.get("fullscreen", False)
                    if is_fullscreen:
                        desktop_size = detect_desktop_size(pygame.display)
                        windowed_size = fit_startup_window_size(
                            windowed_size,
                            desktop_size,
                        )
                        screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                        next_fullscreen = False
                    else:
                        screen, next_fullscreen, mode_error = set_compatible_display_mode(
                            pygame.display,
                            pygame,
                            True,
                            windowed_size,
                        )
                        if mode_error:
                            print(f"[display] Fullscreen toggle fallback: {mode_error}")
                    manager.settings["fullscreen"] = next_fullscreen
                    manager.save_user_preferences()
                    manager.set_screen_size(*screen.get_size())
                    manager.get_scene().on_resize(*screen.get_size())
                elif event.key == pygame.K_ESCAPE:
                    if manager.settings.get("fullscreen", False):
                        desktop_size = detect_desktop_size(pygame.display)
                        windowed_size = fit_startup_window_size(
                            windowed_size,
                            desktop_size,
                        )
                        screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                        manager.settings["fullscreen"] = False
                        manager.save_user_preferences()
                        manager.set_screen_size(*screen.get_size())
                        manager.get_scene().on_resize(*screen.get_size())

        manager.get_scene().handle_events(events)
        manager.get_scene().update()
        manager.get_scene().draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
