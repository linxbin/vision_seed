import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, MIN_SCREEN_WIDTH, MIN_SCREEN_HEIGHT, FPS, TITLE
from core.scene_manager import SceneManager
from core.startup_health import run_startup_health_check, safe_init_audio
from scenes.menu_scene import MenuScene
from scenes.config_scene import ConfigScene
from scenes.training_scene import TrainingScene
from scenes.report_scene import ReportScene
from scenes.history_scene import HistoryScene
from scenes.license_scene import LicenseScene

def main():
    pygame.init()

    run_startup_health_check()
    audio_ok = safe_init_audio()
    
    display_flags = pygame.RESIZABLE

    def clamp_window_size(size):
        return (
            max(MIN_SCREEN_WIDTH, size[0]),
            max(MIN_SCREEN_HEIGHT, size[1]),
        )

    windowed_size = clamp_window_size((SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()

    manager = SceneManager()
    if not audio_ok:
        manager.settings["sound_enabled"] = False
        manager.apply_sound_preference()

    if manager.settings.get("fullscreen"):
        display_flags = pygame.FULLSCREEN
        info = pygame.display.Info()
        screen_size = (info.current_w, info.current_h)
    else:
        screen_size = windowed_size

    screen = pygame.display.set_mode(screen_size, display_flags)
    pygame.display.set_caption(TITLE)
    manager.set_screen_size(*screen.get_size())

    manager.register("menu", MenuScene(manager))
    manager.register("license", LicenseScene(manager))
    manager.register("config", ConfigScene(manager))
    manager.register("training", TrainingScene(manager))
    manager.register("report", ReportScene(manager))
    manager.register("history", HistoryScene(manager))

    has_license, _message = manager.license_manager.check_local_license()
    manager.set_scene("menu" if has_license else "license")

    running = True
    while running:
        clock.tick(FPS)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                if not manager.settings.get("fullscreen", False):
                    windowed_size = clamp_window_size(event.size)
                    display_flags = pygame.RESIZABLE
                    screen = pygame.display.set_mode(windowed_size, display_flags)
                    manager.set_screen_size(*screen.get_size())
                    manager.get_scene().on_resize(*screen.get_size())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)):
                    is_fullscreen = manager.settings.get("fullscreen", False)
                    if is_fullscreen:
                        display_flags = pygame.RESIZABLE
                        screen = pygame.display.set_mode(windowed_size, display_flags)
                    else:
                        display_flags = pygame.FULLSCREEN
                        info = pygame.display.Info()
                        screen = pygame.display.set_mode((info.current_w, info.current_h), display_flags)
                    manager.settings["fullscreen"] = not is_fullscreen
                    manager.save_user_preferences()
                    manager.set_screen_size(*screen.get_size())
                    manager.get_scene().on_resize(*screen.get_size())
                elif event.key == pygame.K_ESCAPE:
                    if manager.settings.get("fullscreen", False):
                        display_flags = pygame.RESIZABLE
                        screen = pygame.display.set_mode(windowed_size, display_flags)
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
