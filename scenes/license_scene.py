import pygame
import time

from core.base_scene import BaseScene
from config import SCREEN_WIDTH, SCREEN_HEIGHT


class LicenseScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self._refresh_fonts()

        self.input_active = False
        self.input_text = ""
        self.message = ""
        self.message_color = (220, 180, 120)
        self._backspace_held = False
        self._backspace_next_repeat_at = 0.0
        self.copy_flash_frames = 0

        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
        except Exception:
            # 剪贴板初始化失败时仍允许手动输入
            pass

        self._reflow_layout()

    def _refresh_fonts(self):
        self.title_font = self.create_font(46)
        self.subtitle_font = self.create_font(24)
        self.text_font = self.create_font(22)
        self.small_font = self.create_font(18)
        self.hash_font = self.create_font(14)

    def _reflow_layout(self):
        panel_w = min(860, self.width - 80)
        panel_h = 380
        self.panel_rect = pygame.Rect(
            self.width // 2 - panel_w // 2,
            self.height // 2 - panel_h // 2,
            panel_w,
            panel_h,
        )
        # 单行哈希展示区 + 右侧紧凑复制按钮
        self.hash_value_rect = pygame.Rect(self.panel_rect.x + 30, self.panel_rect.y + 146, panel_w - 176, 34)
        self.copy_hash_button_rect = pygame.Rect(self.hash_value_rect.right + 10, self.hash_value_rect.y, 106, 34)
        self.input_rect = pygame.Rect(self.panel_rect.x + 30, self.panel_rect.y + 196, panel_w - 60, 46)
        self.paste_button_rect = pygame.Rect(self.input_rect.right - 96, self.input_rect.y + 6, 86, self.input_rect.height - 12)
        self.activate_button_rect = pygame.Rect(self.panel_rect.x + 30, self.panel_rect.y + 250, 180, 44)
        self.exit_button_rect = pygame.Rect(self.panel_rect.right - 210, self.panel_rect.y + 250, 180, 44)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._reflow_layout()

    def _activate(self):
        token = self.input_text.strip()
        if not token:
            self._paste_token(silent=True)
            token = self.input_text.strip()
            if not token:
                self.message = self.manager.t("license.error_empty")
                self.message_color = (240, 150, 150)
                return

        ok, code = self.manager.license_manager.activate_with_token(token)
        if ok:
            self.message = self.manager.t("license.success")
            self.message_color = (145, 225, 165)
            self.manager.set_scene("menu")
        else:
            self.message = self.manager.t("license.error_invalid") + f" [{code}] " + self.manager.t(f"license.err.{code}")
            self.message_color = (240, 150, 150)

    def _copy_device_hash(self):
        device_hash = self.manager.license_manager.get_device_hash()
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, device_hash.encode("utf-8") + b"\x00")
            self.message = self.manager.t("license.copy_success")
            self.message_color = (145, 225, 165)
            self.copy_flash_frames = 20
        except Exception:
            self.message = self.manager.t("license.copy_failed")
            self.message_color = (240, 150, 150)

    def _paste_token(self, silent=False):
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            raw = pygame.scrap.get(pygame.SCRAP_TEXT)
            if not raw:
                if not silent:
                    self.message = self.manager.t("license.paste_failed")
                    self.message_color = (240, 150, 150)
                return
            text = raw.decode("utf-8", errors="ignore").replace("\x00", "").strip()
            if not text:
                if not silent:
                    self.message = self.manager.t("license.paste_failed")
                    self.message_color = (240, 150, 150)
                return
            self.input_text = text
            self.input_active = True
            if not silent:
                self.message = self.manager.t("license.paste_success")
                self.message_color = (145, 225, 165)
        except Exception:
            if not silent:
                self.message = self.manager.t("license.paste_failed")
                self.message_color = (240, 150, 150)

    def _delete_one_char(self):
        if self.input_text:
            self.input_text = self.input_text[:-1]

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.input_active:
                    ctrl_pressed = bool(event.mod & pygame.KMOD_CTRL)
                    shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)
                    if (ctrl_pressed and event.key == pygame.K_v) or (shift_pressed and event.key == pygame.K_INSERT):
                        self._paste_token()
                        continue
                    if event.key == pygame.K_RETURN:
                        self._activate()
                        continue
                    if event.key == pygame.K_BACKSPACE:
                        self._delete_one_char()
                        self._backspace_held = True
                        self._backspace_next_repeat_at = time.time() + 0.35
                        continue
                    if event.unicode and event.unicode.isprintable():
                        if len(self.input_text) < 1024:
                            self.input_text += event.unicode
                    continue

                if event.key == pygame.K_RETURN:
                    self._activate()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    raise SystemExit
                elif event.key == pygame.K_c:
                    self._copy_device_hash()
                elif (event.mod & pygame.KMOD_CTRL) and event.key == pygame.K_v:
                    self._paste_token()
                elif event.unicode and event.unicode.isprintable():
                    # 未聚焦时，直接输入字符也能开始录入
                    self.input_active = True
                    if len(self.input_text) < 1024:
                        self.input_text += event.unicode
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_BACKSPACE:
                    self._backspace_held = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.input_active = self.input_rect.collidepoint(mouse_pos)
                if self.copy_hash_button_rect.collidepoint(mouse_pos):
                    self._copy_device_hash()
                elif self.paste_button_rect.collidepoint(mouse_pos):
                    self._paste_token()
                elif self.activate_button_rect.collidepoint(mouse_pos):
                    self._activate()
                elif self.exit_button_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    raise SystemExit
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.input_rect.collidepoint(mouse_pos):
                    self.input_active = True
                    self._paste_token()

    def _draw_button(self, screen, rect, text, mouse_pos, base_color, flash=False):
        hovered = rect.collidepoint(mouse_pos)
        fill = tuple(min(c + 20, 255) for c in base_color) if hovered else base_color
        if flash:
            fill = (96, 166, 228)
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, (195, 212, 238), rect, 2, border_radius=8)
        font = self.small_font if rect.height <= 36 else self.text_font
        label = font.render(text, True, (255, 255, 255))
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        screen.fill((21, 30, 48))
        mouse_pos = pygame.mouse.get_pos()

        pygame.draw.rect(screen, (33, 47, 75), self.panel_rect, border_radius=12)
        pygame.draw.rect(screen, (92, 128, 186), self.panel_rect, 2, border_radius=12)

        title = self.title_font.render(self.manager.t("license.title"), True, (255, 255, 255))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, self.panel_rect.y + 28))

        subtitle = self.small_font.render(self.manager.t("license.subtitle"), True, (186, 202, 230))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, self.panel_rect.y + 88))

        device_hash = self.manager.license_manager.get_device_hash()
        device_title = self.small_font.render(self.manager.t("license.device_hash"), True, (206, 220, 244))
        screen.blit(device_title, (self.panel_rect.x + 30, self.panel_rect.y + 128))

        pygame.draw.rect(screen, (27, 40, 64), self.hash_value_rect, border_radius=8)
        pygame.draw.rect(screen, (96, 130, 188), self.hash_value_rect, 2, border_radius=8)
        # 设计规范：哈希单行显示，不换行
        device_surface = self.hash_font.render(device_hash, True, (151, 206, 255))
        previous_clip = screen.get_clip()
        screen.set_clip(self.hash_value_rect.inflate(-8, -2))
        screen.blit(
            device_surface,
            (
                self.hash_value_rect.x + 8,
                self.hash_value_rect.centery - device_surface.get_height() // 2,
            ),
        )
        screen.set_clip(previous_clip)

        self._draw_button(
            screen,
            self.copy_hash_button_rect,
            self.manager.t("license.copy_hash"),
            mouse_pos,
            (73, 118, 175),
            flash=self.copy_flash_frames > 0,
        )

        input_bg = (211, 227, 246) if self.input_active else (184, 202, 230)
        input_border = (115, 161, 227) if self.input_active else (94, 128, 182)
        pygame.draw.rect(screen, input_bg, self.input_rect, border_radius=8)
        pygame.draw.rect(screen, input_border, self.input_rect, 2, border_radius=8)

        display_text = self.input_text if self.input_text else self.manager.t("license.input_placeholder")
        text_color = (18, 26, 40) if self.input_text else (92, 112, 144)
        render_text = display_text
        text_surface = self.small_font.render(render_text, True, text_color)
        while text_surface.get_width() > self.input_rect.width - 20 and len(render_text) > 1:
            render_text = render_text[1:]
            text_surface = self.small_font.render(render_text, True, text_color)
        screen.blit(text_surface, (self.input_rect.x + 10, self.input_rect.centery - text_surface.get_height() // 2))
        self._draw_button(
            screen,
            self.paste_button_rect,
            self.manager.t("license.paste"),
            mouse_pos,
            (80, 114, 168),
        )

        self._draw_button(
            screen,
            self.activate_button_rect,
            self.manager.t("license.activate"),
            mouse_pos,
            (60, 150, 92),
        )
        self._draw_button(
            screen,
            self.exit_button_rect,
            self.manager.t("license.exit"),
            mouse_pos,
            (92, 106, 144),
        )

        hint = self.small_font.render(self.manager.t("license.hint"), True, (176, 194, 222))
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.panel_rect.y + 312))
        paste_tip = self.small_font.render(self.manager.t("license.paste_tip"), True, (158, 186, 220))
        screen.blit(paste_tip, (self.panel_rect.x + 30, self.input_rect.y - 24))

        if self.message:
            msg = self.small_font.render(self.message, True, self.message_color)
            screen.blit(msg, (self.width // 2 - msg.get_width() // 2, self.panel_rect.y + 342))

    def update(self):
        if self.input_active and self._backspace_held:
            now = time.time()
            if now >= self._backspace_next_repeat_at:
                self._delete_one_char()
                self._backspace_next_repeat_at = now + 0.045
        if self.copy_flash_frames > 0:
            self.copy_flash_frames -= 1
