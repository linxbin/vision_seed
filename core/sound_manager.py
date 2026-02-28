import os
import pygame
from core.app_paths import get_resource_path


class SoundManager:
    """音效管理器 - 用于加载和播放答对/答错音效文件"""
    
    def __init__(self):
        self.is_enabled = True  # 音效开关
        
        self.assets_dir = get_resource_path("assets")
        
        # 尝试加载音效文件
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
        """
        从assets目录加载音效文件
        
        Args:
            filename (str): 音效文件名
            
        Returns:
            pygame.mixer.Sound: 音效对象，如果失败则返回None
        """
        try:
            filepath = os.path.join(self.assets_dir, filename)
            if os.path.exists(filepath):
                sound = pygame.mixer.Sound(filepath)
                return sound
            else:
                print(f"Sound file not found: {filepath}")
                return None
        except Exception as e:
            print(f"Failed to load sound file {filename}: {e}")
            return None
    
    def play_correct(self):
        """播放答对音效"""
        if self.is_enabled and self.correct_sound:
            try:
                self.correct_sound.play()
            except Exception as e:
                print(f"Failed to play correct sound: {e}")
                pass  # 忽略播放错误
    
    def play_wrong(self):
        """播放答错音效"""
        if self.is_enabled and self.wrong_sound:
            try:
                self.wrong_sound.play()
            except Exception as e:
                print(f"Failed to play wrong sound: {e}")
                pass  # 忽略播放错误

    def play_completed(self):
        """播放训练完成音效，返回音频时长（秒）。"""
        if self.is_enabled and self.completed_sound:
            try:
                self.completed_sound.play()
                return max(0.0, float(self.completed_sound.get_length()))
            except Exception as e:
                print(f"Failed to play completed sound: {e}")
                return 0.0
        return 0.0

    def play_report_ping(self, volume=0.35):
        """播放报告页提示音（轻量），成功返回 True。"""
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
        """设置音效开关"""
        self.is_enabled = enabled
