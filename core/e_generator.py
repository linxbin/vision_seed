import pygame


class EGenerator:
    """E字生成器，用于创建不同方向和大小的E字"""
    
    @staticmethod
    def create_e_surface(size, direction):
        """
        创建指定大小和方向的E字表面
        
        Args:
            size (int): E字的尺寸
            direction (str): 方向 ("UP", "DOWN", "LEFT", "RIGHT")
            
        Returns:
            pygame.Surface: E字表面
        """
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        thickness = size // 5
        bar = size

        if direction == "RIGHT":
            pygame.draw.rect(surface, (255, 255, 255), (0, 0, thickness, size))
            pygame.draw.rect(surface, (255, 255, 255), (0, 0, bar, thickness))
            pygame.draw.rect(surface, (255, 255, 255), (0, size//2 - thickness//2, bar, thickness))
            pygame.draw.rect(surface, (255, 255, 255), (0, size - thickness, bar, thickness))

        elif direction == "LEFT":
            pygame.draw.rect(surface, (255, 255, 255), (size - thickness, 0, thickness, size))
            pygame.draw.rect(surface, (255, 255, 255), (0, 0, bar, thickness))
            pygame.draw.rect(surface, (255, 255, 255), (0, size//2 - thickness//2, bar, thickness))
            pygame.draw.rect(surface, (255, 255, 255), (0, size - thickness, bar, thickness))

        elif direction == "UP":
            pygame.draw.rect(surface, (255, 255, 255), (0, size - thickness, size, thickness))
            pygame.draw.rect(surface, (255, 255, 255), (0, 0, thickness, bar))
            pygame.draw.rect(surface, (255, 255, 255), (size//2 - thickness//2, 0, thickness, bar))
            pygame.draw.rect(surface, (255, 255, 255), (size - thickness, 0, thickness, bar))

        elif direction == "DOWN":
            pygame.draw.rect(surface, (255, 255, 255), (0, 0, size, thickness))
            pygame.draw.rect(surface, (255, 255, 255), (0, 0, thickness, bar))
            pygame.draw.rect(surface, (255, 255, 255), (size//2 - thickness//2, 0, thickness, bar))
            pygame.draw.rect(surface, (255, 255, 255), (size - thickness, 0, thickness, bar))

        return surface
    
    @staticmethod
    def draw_e(screen, center_pos, size, direction="RIGHT"):
        """
        直接在屏幕上绘制E字
        
        Args:
            screen (pygame.Surface): 目标屏幕表面
            center_pos (tuple): 中心位置 (x, y)
            size (int): E字尺寸
            direction (str): 方向，默认为"RIGHT"
        """
        e_surface = EGenerator.create_e_surface(size, direction)
        rect = e_surface.get_rect(center=center_pos)
        screen.blit(e_surface, rect)