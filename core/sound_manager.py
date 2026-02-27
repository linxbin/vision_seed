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
            else:
                self.correct_sound = None
                self.wrong_sound = None
        except Exception as e:
            print(f"Sound initialization failed: {e}")
            self.correct_sound = None
            self.wrong_sound = None
    
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
    
    def set_enabled(self, enabled):
        """设置音效开关"""
        self.is_enabled = enabled
