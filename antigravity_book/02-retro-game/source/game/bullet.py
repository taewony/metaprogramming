import pygame
from game.constants import *

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed_y, image=None):
        super().__init__()
        # 이미지 설정
        if image:
            self.image = image
        else:
            self.image = pygame.Surface((BULLET_WIDTH, BULLET_HEIGHT))
            self.image.fill(BULLET_COLOR)
            
        self.rect = self.image.get_rect()
        
        # 미사일 위치 설정
        self.rect.centerx = x
        
        # 속도 설정 (음수면 위로, 양수면 아래로)
        self.speed_y = speed_y
        
        if speed_y < 0:
            self.rect.bottom = y
        else:
            self.rect.top = y
        
    def update(self):
        """미사일 이동"""
        self.rect.y += self.speed_y
        
        # 화면 밖으로 나가면 제거
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()
