import os

import pygame

from core.app_paths import get_resource_path


class SoundManager:
    """Load and play lightweight application sound effects."""

    def __init__(self):
        self.is_enabled = True
        self.assets_dir = get_resource_path("assets")

        try:
            if pygame.mixer.get_init():
                self.correct_sound = self._load_sound("correct.wav")
                self.wrong_sound = self._load_sound("wrong.wav")
                self.completed_sound = self._load_sound("completed.wav")
            else:
                self.correct_sound = None
                self.wrong_sound = None
                self.completed_sound = None
        except Exception as e:
            print(f"Sound initialization failed: {e}")
            self.correct_sound = None
            self.wrong_sound = None
            self.completed_sound = None

    def _load_sound(self, filename):
        """Load a sound file from the shared assets directory."""
        try:
            filepath = os.path.join(self.assets_dir, filename)
            if os.path.exists(filepath):
                return pygame.mixer.Sound(filepath)
            print(f"Sound file not found: {filepath}")
            return None
        except Exception as e:
            print(f"Failed to load sound file {filename}: {e}")
            return None

    def play_correct(self):
        """Play the positive feedback sound."""
        if self.is_enabled and self.correct_sound:
            try:
                self.correct_sound.play()
            except Exception as e:
                print(f"Failed to play correct sound: {e}")

    def play_wrong(self):
        """Play the negative feedback sound."""
        if self.is_enabled and self.wrong_sound:
            try:
                self.wrong_sound.play()
            except Exception as e:
                print(f"Failed to play wrong sound: {e}")

    def play_completed(self):
        """Play the completion sound and return its duration in seconds."""
        if self.is_enabled and self.completed_sound:
            try:
                self.completed_sound.play()
                return max(0.0, float(self.completed_sound.get_length()))
            except Exception as e:
                print(f"Failed to play completed sound: {e}")
                return 0.0
        return 0.0

    def play_report_ping(self, volume=0.35):
        """Play a lighter report hint sound. Returns True on success."""
        if not self.is_enabled or not self.correct_sound:
            return False
        try:
            channel = self.correct_sound.play()
            if channel:
                channel.set_volume(max(0.0, min(1.0, float(volume))))
            return True
        except Exception as e:
            print(f"Failed to play report ping: {e}")
            return False

    def set_enabled(self, enabled):
        """Enable or disable sound playback."""
        self.is_enabled = enabled
