import pygame
import os
import sys

def test_wav_sounds():
    """测试WAV音效文件"""
    print("Initializing pygame mixer...")
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    
    # 测试correct.wav
    correct_path = "assets/correct.wav"
    if os.path.exists(correct_path):
        print(f"✓ {correct_path} exists")
        try:
            correct_sound = pygame.mixer.Sound(correct_path)
            print("✓ correct.wav loaded successfully")
            correct_sound.play()
            pygame.time.wait(500)
        except Exception as e:
            print(f"✗ Failed to load correct.wav: {e}")
    else:
        print(f"✗ {correct_path} not found")
    
    # 测试wrong.wav
    wrong_path = "assets/wrong.wav"
    if os.path.exists(wrong_path):
        print(f"✓ {wrong_path} exists")
        try:
            wrong_sound = pygame.mixer.Sound(wrong_path)
            print("✓ wrong.wav loaded successfully")
            wrong_sound.play()
            pygame.time.wait(500)
        except Exception as e:
            print(f"✗ Failed to load wrong.wav: {e}")
    else:
        print(f"✗ {wrong_path} not found")
    
    pygame.quit()
    print("WAV sound test completed!")

if __name__ == "__main__":
    test_wav_sounds()