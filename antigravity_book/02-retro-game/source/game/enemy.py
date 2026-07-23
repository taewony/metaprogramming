import pygame
import random
import os
from game.constants import *
from game.bullet import Bullet
from game.utils import preprocess_image

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image=None):
        super().__init__()
        if image:
            self.image = image
        else:
            self.image = pygame.Surface((ENEMY_WIDTH, ENEMY_HEIGHT))
            self.image.fill(ENEMY_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, direction_x):
        self.rect.x += direction_x * ENEMY_SPEED_X

    def drop(self):
        self.rect.y += ENEMY_DROP_SPEED

class EnemyManager:
    def __init__(self):
        self.enemies = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.direction = 1  # 1: right, -1: left
        
        # 이미지 로드
        self.enemy_images = {}
        try:
            # 기본 적
            img = pygame.image.load(os.path.join(ENEMY_DIR, "enemy_ship.png")).convert()
            img = preprocess_image(img)
            img.set_colorkey(PURE_WHITE)
            self.enemy_images['ship'] = pygame.transform.scale(img, (ENEMY_WIDTH, ENEMY_HEIGHT))
            
            # 스카우트 (앞열)
            img = pygame.image.load(os.path.join(ENEMY_DIR, "enemy_scout.png")).convert()
            img = preprocess_image(img)
            img.set_colorkey(PURE_WHITE)
            self.enemy_images['scout'] = pygame.transform.scale(img, (ENEMY_WIDTH, ENEMY_HEIGHT))
            
            # 헤비 (뒷열)
            img = pygame.image.load(os.path.join(ENEMY_DIR, "enemy_heavy.png")).convert()
            img = preprocess_image(img)
            img.set_colorkey(PURE_WHITE)
            self.enemy_images['heavy'] = pygame.transform.scale(img, (ENEMY_WIDTH, ENEMY_HEIGHT))
        except Exception as e:
            print(f"Error loading enemy images: {e}")
            self.enemy_images = None
            
        try:
            self.bullet_img = pygame.image.load(ENEMY_BULLET_PATH).convert()
            # 적 미사일 이미지도 전처리 및 투명화 적용
            self.bullet_img = preprocess_image(self.bullet_img)
            self.bullet_img.set_colorkey(PURE_WHITE)
            self.bullet_img = pygame.transform.scale(self.bullet_img, (BULLET_WIDTH, BULLET_HEIGHT))
        except Exception as e:
            print(f"Error loading enemy bullet image: {e}")
            self.bullet_img = None

        self.setup_enemies()

    def setup_enemies(self):
        # 3행 8열 배치
        start_x = 50
        start_y = 50
        gap_x = 20
        gap_y = 20
        
        for row in range(3):
            # 행별로 다른 이미지 적용
            if self.enemy_images:
                if row == 0:
                    image = self.enemy_images.get('heavy') # 맨 윗줄
                elif row == 1:
                    image = self.enemy_images.get('ship')  # 중간
                else:
                    image = self.enemy_images.get('scout') # 맨 앞줄
            else:
                image = None

            for col in range(8):
                x = start_x + col * (ENEMY_WIDTH + gap_x)
                y = start_y + row * (ENEMY_HEIGHT + gap_y)
                enemy = Enemy(x, y, image)
                self.enemies.add(enemy)

    def update(self):
        self.enemies.update(self.direction)
        self.check_wall_collision()
        self.enemy_shoot()
        self.enemy_bullets.update()
        
        # 미사일 화면 밖 처리 logic is in Bullet.update(), but enemy bullets go down.
        # Wait, the current Bullet class moves UP by default.
        # I need to modify Bullet class to support direction or speed vector.
        
    def check_wall_collision(self):
        collision = False
        for enemy in self.enemies:
            if enemy.rect.right >= SCREEN_WIDTH or enemy.rect.left <= 0:
                collision = True
                break
        
        if collision:
            self.direction *= -1
            for enemy in self.enemies:
                enemy.drop()
                
    def enemy_shoot(self):
        # 일정 확률로 미사일 발사
        if random.randint(1, 100) < 2:  # 1% 확률 (프레임당) - 조절 필요
            if self.enemies:
                shooter = random.choice(self.enemies.sprites())
                # 적 미사일은 아래로 내려가야 함. 속도는 양수.
                bullet = Bullet(shooter.rect.centerx, shooter.rect.bottom, BULLET_SPEED, self.bullet_img)
                self.enemy_bullets.add(bullet) 

    def reset(self):
        self.enemies.empty()
        self.enemy_bullets.empty()
        self.direction = 1
        self.setup_enemies()

    def draw(self, screen):
        self.enemies.draw(screen)
        self.enemy_bullets.draw(screen)
