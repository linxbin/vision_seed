import pygame
import random
import time
from datetime import datetime
from core.base_scene import BaseScene
from core.e_generator import EGenerator
from config import E_SIZE_LEVELS, SCREEN_WIDTH, SCREEN_HEIGHT


class Particle:
    """粒子效果类 - 支持火花与扩散环两种反馈。"""

    def __init__(self, x, y, vx, vy, color, lifetime, size, kind="spark"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = max(1, lifetime)
        self.size = float(size)
        self.kind = kind
        self.gravity = 0.16 if kind == "spark" else 0.0
        self.drag = 0.96 if kind == "spark" else 1.0

    def update(self):
        self.lifetime -= 1
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= self.drag
        self.vy *= self.drag
        if self.kind == "ring":
            self.size += 0.9
        else:
            self.size = max(1.0, self.size * 0.985)

    def draw(self, screen, offset=(0, 0)):
        if self.lifetime <= 0:
            return

        fade = max(0.0, min(1.0, self.lifetime / self.max_lifetime))
        color = (
            int(self.color[0] * fade),
            int(self.color[1] * fade),
            int(self.color[2] * fade),
        )
        radius = max(1, int(self.size))
        center = (int(self.x + offset[0]), int(self.y + offset[1]))
        if self.kind == "ring":
            width = 2 if radius > 4 else 1
            pygame.draw.circle(screen, color, center, radius, width)
        else:
            pygame.draw.circle(screen, color, center, radius)

    def is_alive(self):
        return self.lifetime > 0


class TrainingScene(BaseScene):
    FINISH_TRANSITION_SECONDS = 1
    FINISH_TRANSITION_AUDIO_PADDING_SECONDS = 0.05
    FINISH_TRANSITION_MIN_SECONDS = 0.35
    FINISH_TRANSITION_MAX_SECONDS = 1.2
    MAX_PARTICLES = 120

    KEY_DIRECTION = {
        pygame.K_UP: "UP",
        pygame.K_DOWN: "DOWN",
        pygame.K_LEFT: "LEFT",
        pygame.K_RIGHT: "RIGHT"
    }

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()

        # 自适应布局参数（基于屏幕尺寸）
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self._reflow_layout()

        # 运行态字段（进入训练时由 reset 正式赋值）
        self.total = 0
        self.current = 0
        self.correct = 0
        self.combo = 0
        self.max_combo = 0
        self.base_size = E_SIZE_LEVELS[0]
        self.target_direction = "RIGHT"
        self.surface = EGenerator.create_e_surface(self.base_size, self.target_direction)
        self.rect = self.surface.get_rect(center=self.center_pos)
        self.is_waiting_for_delay = False
        self.answer_delay_end_time = 0
        self.combo_display_frames = 0
        self.finish_transition_active = False
        self.finish_transition_ends_at = 0.0
        self.finish_transition_committed = False
        self.completed_sound_played = False
        self.shake_frames = 0
        self.shake_intensity = 0
        self.shake_offset = (0, 0)

        # 粒子效果列表
        self.particles = []

        # 保持现有行为：构造后即可进入可用状态
        self.reset()

    def _refresh_fonts(self):
        self.small_font = self.create_font(40)
        self.back_button_font = self.create_font(24)

    def _reflow_layout(self):
        self.center_pos = (self.width // 2, self.height // 2 - 50)
        self.progress_pos = (self.width // 2, self.height - 70)
        self.status_pos = (self.width // 2, self.height - 36)
        self.back_button_rect = pygame.Rect(self.width - 90, 15, 80, 30)
        self.pause_button_rect = pygame.Rect(self.width - 180, 15, 80, 30)
        if getattr(self, "rect", None):
            self.rect.center = self.center_pos

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._reflow_layout()

    def reset(self):
        self.total = self.manager.settings["total_questions"]
        self.current = 0
        self.correct = 0
        self.combo = 0
        self.max_combo = 0
        self.combo_display_frames = 0
        self.start_time = time.time()
        self.paused_duration_seconds = 0.0
        self.pause_started_at = 0.0
        self.is_paused = False
        self.previous_direction = None

        # 每次开训时应用最新音效偏好
        self.manager.apply_sound_preference()
        
        # 根据设置的难度等级获取对应的E字大小（动态等级）
        level_index = self.manager.settings["start_level"] - 1
        self.base_size = E_SIZE_LEVELS[level_index]
        
        # 时间控制相关属性
        self.last_change_time = time.time()  # 上次变换时间
        self.answer_delay_end_time = 0  # 用户回答后的延迟结束时间
        self.is_waiting_for_delay = False  # 是否在等待回答后的延迟
        self.finish_transition_active = False
        self.finish_transition_ends_at = 0.0
        self.finish_transition_committed = False
        self.completed_sound_played = False
        self.shake_frames = 0
        self.shake_intensity = 0
        self.shake_offset = (0, 0)

        # 0题模式：直接结束并生成报告，避免进入无意义训练循环
        if self.total <= 0:
            self._finalize_finish_transition()
            return

        self.new_question()

    def _pause_training(self):
        if self.is_paused:
            return
        self.is_paused = True
        self.pause_started_at = time.time()

    def _resume_training(self):
        if not self.is_paused:
            return
        now = time.time()
        paused_span = max(0.0, now - self.pause_started_at)
        self.paused_duration_seconds += paused_span
        if self.is_waiting_for_delay:
            self.answer_delay_end_time += paused_span
        self.pause_started_at = 0.0
        self.is_paused = False

    def _toggle_pause(self):
        if self.is_paused:
            self._resume_training()
        else:
            self._pause_training()

    def _active_elapsed_seconds(self) -> float:
        now = time.time()
        paused_now = max(0.0, now - self.pause_started_at) if self.is_paused else 0.0
        elapsed = now - self.start_time - self.paused_duration_seconds - paused_now
        return max(0.0, elapsed)

    def _add_particle(self, particle):
        self.particles.append(particle)
        if len(self.particles) > self.MAX_PARTICLES:
            overflow = len(self.particles) - self.MAX_PARTICLES
            del self.particles[:overflow]

    def _start_screen_shake(self, frames, intensity):
        self.shake_frames = max(self.shake_frames, frames)
        self.shake_intensity = max(self.shake_intensity, intensity)

    def _spawn_feedback_particles(self, is_correct, x, y):
        if is_correct:
            base_color = (78, 232, 132)
            accent_color = (250, 212, 104)
            count = 9 if self.combo < 3 else 13
            speed = 2.5 if self.combo < 3 else 3.2
            self._start_screen_shake(4 if self.combo < 3 else 7, 2 if self.combo < 3 else 4)
        else:
            base_color = (242, 102, 102)
            accent_color = (255, 158, 118)
            count = 10
            speed = 3.0
            self._start_screen_shake(6, 3)

        for _ in range(count):
            vx = random.uniform(-speed, speed)
            vy = random.uniform(-speed - 1.0, -0.4)
            size = random.uniform(2.0, 4.6)
            life = random.randint(18, 34)
            color = base_color if random.random() < 0.7 else accent_color
            self._add_particle(Particle(x, y, vx, vy, color, life, size, kind="spark"))

        if is_correct and self.combo >= 3:
            ring_color = (250, 220, 130) if self.combo < 6 else (255, 182, 108)
            self._add_particle(Particle(x, y, 0.0, 0.0, ring_color, 18, 10.0, kind="ring"))

    def new_question(self):
        directions = ["UP", "DOWN", "LEFT", "RIGHT"]

        if self.previous_direction in directions:
            directions.remove(self.previous_direction)

        self.target_direction = random.choice(directions)
        self.previous_direction = self.target_direction

        self.surface = EGenerator.create_e_surface(self.base_size, self.target_direction)
        self.rect = self.surface.get_rect(center=self.center_pos)

    def _save_training_record(self, duration: float, wrong: int):
        """保存训练记录到数据管理器"""
        try:
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "difficulty_level": self.manager.settings["start_level"],
                "e_size_px": self.base_size,
                "total_questions": self.total,
                "correct_count": self.correct,
                "wrong_count": wrong,
                "duration_seconds": duration,
                "accuracy_rate": round((self.correct / self.total) * 100, 1) if self.total > 0 else 0.0
            }
            
            success = self.manager.data_manager.save_training_session(session_data)
            if success:
                print(f"Training record saved successfully: {session_data['timestamp']}")
            else:
                print("Failed to save training record")
                
        except Exception as e:
            print(f"Error saving training record: {e}")

    def _finalize_finish_transition(self):
        """统一训练结束逻辑，确保边界值安全。"""
        if self.finish_transition_committed:
            return
        self.finish_transition_committed = True
        self.finish_transition_active = False

        duration = round(self._active_elapsed_seconds(), 2)
        wrong = max(0, self.total - self.correct)

        self.manager.current_result["correct"] = self.correct
        self.manager.current_result["wrong"] = wrong
        self.manager.current_result["total"] = self.total
        self.manager.current_result["duration"] = duration
        self.manager.current_result["max_combo"] = self.max_combo

        # 保存训练记录
        self._save_training_record(duration, wrong)

        # 防止在场景尚未完整注册时切换导致异常
        scenes = getattr(self.manager, "scenes", None)
        if isinstance(scenes, dict) and len(scenes) > 0 and "report" not in scenes:
            self.manager.set_scene("menu")
        else:
            self.manager.set_scene("report")

    def _begin_finish_transition(self):
        if self.finish_transition_active or self.finish_transition_committed:
            return
        self.finish_transition_active = True
        transition_seconds = self.FINISH_TRANSITION_SECONDS
        if not self.completed_sound_played and self.manager.sound_manager:
            played_seconds = float(self.manager.sound_manager.play_completed() or 0.0)
            if played_seconds > 0:
                transition_seconds = played_seconds + self.FINISH_TRANSITION_AUDIO_PADDING_SECONDS
            self.completed_sound_played = True
        transition_seconds = max(
            self.FINISH_TRANSITION_MIN_SECONDS,
            min(self.FINISH_TRANSITION_MAX_SECONDS, transition_seconds),
        )
        self.finish_transition_ends_at = time.time() + transition_seconds

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        focus_lost_event = getattr(pygame, "WINDOWFOCUSLOST", None)
        
        for event in events:
            if focus_lost_event is not None and event.type == focus_lost_event:
                self._pause_training()
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    if getattr(event, "repeat", 0):
                        continue
                    self._toggle_pause()
                    continue

                if event.key == pygame.K_ESCAPE:
                    self.manager.set_scene("menu")
                    continue

                if self.finish_transition_active:
                    if event.key == pygame.K_RETURN:
                        self._finalize_finish_transition()
                    continue

                if self.is_paused:
                    continue

                if event.key in self.KEY_DIRECTION:
                    # 检查是否在等待延迟期间，如果是则忽略输入
                    if self.is_waiting_for_delay:
                        continue

                    self.current += 1
                    is_correct = (self.KEY_DIRECTION[event.key] == self.target_direction)

                    # 播放音效反馈
                    if self.manager.sound_manager:
                        if is_correct:
                            self.manager.sound_manager.play_correct()
                        else:
                            self.manager.sound_manager.play_wrong()

                    if is_correct:
                        self.correct += 1
                        self.combo += 1
                        self.max_combo = max(self.max_combo, self.combo)
                        self.combo_display_frames = 45
                    else:
                        self.combo = 0

                    # 视觉反馈粒子在计分后生成，可根据连击强度变化
                    particle_x = self.rect.centerx
                    particle_y = self.rect.centery - max(30, self.base_size // 2 + 10)
                    self._spawn_feedback_particles(is_correct, particle_x, particle_y)

                    if self.current >= self.total:
                        self._begin_finish_transition()
                    else:
                        # 设置回答后的延迟标志和结束时间（1秒延迟）
                        self.is_waiting_for_delay = True
                        self.answer_delay_end_time = time.time() + 1.0

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    if self.finish_transition_active:
                        continue
                    if self.back_button_rect.collidepoint(mouse_pos):
                        self.manager.set_scene("menu")
                    elif self.pause_button_rect.collidepoint(mouse_pos):
                        self._toggle_pause()

    def update(self):
        """更新训练场景的时间逻辑"""
        if self.is_paused:
            return

        current_time = time.time()
        
        # 更新粒子效果
        for particle in self.particles[:]:
            particle.update()
            if not particle.is_alive():
                self.particles.remove(particle)

        if self.combo_display_frames > 0:
            self.combo_display_frames -= 1

        if self.shake_frames > 0:
            self.shake_frames -= 1
            jitter = self.shake_intensity
            self.shake_offset = (
                random.randint(-jitter, jitter),
                random.randint(-jitter, jitter),
            )
            if self.shake_frames == 0:
                self.shake_intensity = 0
                self.shake_offset = (0, 0)

        if self.finish_transition_active:
            if current_time >= self.finish_transition_ends_at:
                self._finalize_finish_transition()
            return
        
        # 处理回答后的延迟逻辑
        if self.is_waiting_for_delay:
            if current_time >= self.answer_delay_end_time:
                # 延迟结束，生成新问题
                self.is_waiting_for_delay = False
                self.new_question()
                self.last_change_time = current_time
        else:
            # 检查是否需要自动变换（每2秒变换一次）
            # 注意：这里保持原有逻辑，即只有用户回答后才会变换
            # 自动变换逻辑可能不需要，因为用户需要时间来回答
            # 如果需要自动变换，可以在这里添加逻辑
            pass

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        screen.fill((0, 0, 0))
        ox, oy = self.shake_offset
        screen.blit(self.surface, self.rect.move(ox, oy))

        progress = f"{self.current}/{self.total}"
        progress_surface = self.small_font.render(progress, True, (200, 200, 200))
        screen.blit(
            progress_surface,
            (self.progress_pos[0] - progress_surface.get_width() // 2, self.progress_pos[1]),
        )

        # 轻量训练状态信息：等级/尺寸/正确率
        accuracy = round((self.correct / self.current) * 100, 1) if self.current > 0 else 0.0
        level = self.manager.settings.get("start_level", 1)
        status_text = f"L{level} | {self.base_size}px | {accuracy:.1f}%"
        status_surface = self.back_button_font.render(status_text, True, (160, 180, 210))
        screen.blit(
            status_surface,
            (self.status_pos[0] - status_surface.get_width() // 2, self.status_pos[1]),
        )

        pause_hint = self.back_button_font.render(self.manager.t("training.pause_hint"), True, (135, 155, 185))
        screen.blit(pause_hint, (22, self.height - 34))

        if self.combo >= 2 and self.combo_display_frames > 0:
            combo_color = (245, 210, 110) if self.combo < 5 else (255, 170, 95)
            combo_text = self.small_font.render(self.manager.t("training.combo", combo=self.combo), True, combo_color)
            screen.blit(combo_text, (self.center_pos[0] - combo_text.get_width() // 2, 36))
        
        # 绘制粒子效果（已经在update中处理了）
        for particle in self.particles:
            particle.draw(screen, self.shake_offset)
        
        # 绘制返回按钮（右上角，强迫症级别的精确位置）
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.back_button_rect.collidepoint(mouse_pos)
        
        # 按钮背景色
        button_color = (80, 120, 200) if is_hovered else (60, 90, 150)
        border_color = (150, 180, 255) if is_hovered else (100, 130, 200)
        
        pygame.draw.rect(screen, button_color, self.back_button_rect, border_radius=6)
        pygame.draw.rect(screen, border_color, self.back_button_rect, 2, border_radius=6)
        
        # 按钮文字（多语言）
        back_text = self.back_button_font.render(self.manager.t("training.back"), True, (255, 255, 255))
        text_x = self.back_button_rect.centerx - back_text.get_width() // 2
        text_y = self.back_button_rect.centery - back_text.get_height() // 2
        screen.blit(back_text, (text_x, text_y))

        pause_hovered = self.pause_button_rect.collidepoint(mouse_pos)
        pause_color = (80, 152, 109) if pause_hovered else (62, 124, 90)
        pause_border = (154, 221, 184) if pause_hovered else (112, 182, 146)
        pygame.draw.rect(screen, pause_color, self.pause_button_rect, border_radius=6)
        pygame.draw.rect(screen, pause_border, self.pause_button_rect, 2, border_radius=6)
        pause_key = "training.resume" if self.is_paused else "training.pause"
        pause_text = self.back_button_font.render(self.manager.t(pause_key), True, (255, 255, 255))
        pause_x = self.pause_button_rect.centerx - pause_text.get_width() // 2
        pause_y = self.pause_button_rect.centery - pause_text.get_height() // 2
        screen.blit(pause_text, (pause_x, pause_y))

        if self.is_paused:
            # 暂停态视觉反馈：不遮挡 E 字，使用外圈描边高亮
            focus_rect = self.rect.inflate(26, 26).move(ox, oy)
            pygame.draw.rect(screen, (112, 172, 242), focus_rect, 3, border_radius=10)
            pygame.draw.rect(screen, (62, 104, 162), focus_rect.inflate(10, 10), 2, border_radius=12)

            paused_rect = pygame.Rect(self.width // 2 - 120, 18, 240, 38)
            pygame.draw.rect(screen, (42, 66, 102), paused_rect, border_radius=9)
            pygame.draw.rect(screen, (150, 182, 232), paused_rect, 2, border_radius=9)
            paused_text = self.back_button_font.render(self.manager.t("training.paused"), True, (240, 245, 255))
            paused_x = paused_rect.centerx - paused_text.get_width() // 2
            paused_y = paused_rect.centery - paused_text.get_height() // 2
            screen.blit(paused_text, (paused_x, paused_y))

        if self.finish_transition_active:
            done_rect = pygame.Rect(self.width // 2 - 230, self.height // 2 - 34, 460, 78)
            pygame.draw.rect(screen, (30, 48, 78), done_rect, border_radius=10)
            pygame.draw.rect(screen, (132, 174, 232), done_rect, 2, border_radius=10)
            done_text = self.back_button_font.render(self.manager.t("training.completed"), True, (236, 244, 255))
            hint_text = self.back_button_font.render(self.manager.t("training.skip_hint"), True, (180, 206, 238))
            screen.blit(done_text, (done_rect.centerx - done_text.get_width() // 2, done_rect.y + 13))
            screen.blit(hint_text, (done_rect.centerx - hint_text.get_width() // 2, done_rect.y + 42))
