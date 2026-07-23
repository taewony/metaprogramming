import pygame
from game.constants import *
from game.utils import preprocess_image

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, image_path=EXPLOSION_IMAGE_PATH):
        super().__init__()
        # 이미지 로드
        try:
            self.image = pygame.image.load(image_path).convert()
            # 폭발 이미지 전처리 (리사이징은 유지)
            self.image = preprocess_image(self.image)
            self.image.set_colorkey(PURE_WHITE)
            self.image = pygame.transform.scale(self.image, (50, 50)) 
        except Exception as e:
            print(f"Error loading explosion image: {e}")
            self.image = pygame.Surface((50, 50))
            self.image.fill(YELLOW)
            
        self.rect = self.image.get_rect()
        self.rect.center = center
        
        # 애니메이션/지속시간 설정
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 500 # 0.5초 동안 표시

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > self.duration:
            self.kill()
