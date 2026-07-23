import pygame
from game.constants import *
from game.bullet import Bullet
from game.utils import preprocess_image

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 플레이어 이미지 로드
        try:
            self.original_image = pygame.image.load(PLAYER_IMAGE_PATH).convert()
            # 이미지 전처리 (리사이징 및 흰색 정규화)
            self.original_image = preprocess_image(self.original_image)
            self.original_image.set_colorkey(PURE_WHITE)
            self.image = pygame.transform.scale(self.original_image, (PLAYER_WIDTH, PLAYER_HEIGHT))
        except Exception as e:
            print(f"Error loading player image: {e}")
            self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
            self.image.fill(PLAYER_COLOR)
            
        self.rect = self.image.get_rect()
        
        # 미사일 이미지 로드
        try:
            self.bullet_img = pygame.image.load(PLAYER_BULLET_PATH).convert()
            # 미사일 이미지도 전처리 및 투명화 적용
            self.bullet_img = preprocess_image(self.bullet_img)
            self.bullet_img.set_colorkey(PURE_WHITE)
            self.bullet_img = pygame.transform.scale(self.bullet_img, (BULLET_WIDTH, BULLET_HEIGHT))
        except Exception as e:
            print(f"Error loading player bullet image: {e}")
            self.bullet_img = None

        # 초기 위치 설정
        self.rect.x = PLAYER_START_X
        self.rect.y = PLAYER_START_Y
        
        # 마지막 발사 시간 (쿨타임 체크용)
        self.last_shot_time = 0

    def update(self):
        """플레이어 키 입력 처리 및 이동"""
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED
            
        # 화면 밖으로 나가지 않도록 제한
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def shoot(self, current_time):
        """
        미사일 발사 메서드
        쿨타임을 체크하여 발사 가능 여부를 반환합니다.
        실제 미사일 객체 생성은 메인/게임매니저에서 처리하거나 여기서 처리 후 반환할 수 있습니다.
        """
        if current_time - self.last_shot_time >= FIRE_COOLDOWN:
            self.last_shot_time = current_time
            # 위로 발사하므로 속도는 음수
            return Bullet(self.rect.centerx, self.rect.top, -BULLET_SPEED, self.bullet_img)
    def reset_position(self):
        self.rect.x = PLAYER_START_X
        self.rect.y = PLAYER_START_Y
        self.last_shot_time = 0
