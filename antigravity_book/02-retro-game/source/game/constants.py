import pygame

# 화면 설정
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Space Defender MVP"
FPS = 60
PLAYER_LIVES = 3

# 디자인 테마: Deep Space Neon
# 눈이 편안한 Dark Navy 배경에 Neon Pastel 톤으로 포인트를 주어 세련된 느낌을 제공합니다.

# 1. Color Palette (R, G, B)
# Backgrounds
COLOR_DEEP_NAVY = (15, 23, 42)    # Slate 900: 우주 배경
# Accents
COLOR_NEON_CYAN = (34, 211, 238)  # Cyan 400: 플레이어 (청량감, 히어로)
COLOR_SOFT_CORAL = (251, 113, 133)# Rose 400: 적 (공격적이지만 눈이 아프지 않은 톤)
COLOR_WARM_AMBER = (251, 191, 36) # Amber 400: 미사일, 효과
COLOR_OFF_WHITE = (248, 250, 252) # Slate 50: 텍스트 (순백색보다 부드러움)

# 2. Semantic Colors (Legacy Support)
PURE_WHITE = (255, 255, 255)
WHITE = COLOR_OFF_WHITE
BLACK = COLOR_DEEP_NAVY
GREEN = COLOR_NEON_CYAN
RED = COLOR_SOFT_CORAL
YELLOW = COLOR_WARM_AMBER

# 플레이어 설정
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 40
PLAYER_SPEED = 5
PLAYER_COLOR = GREEN
PLAYER_START_X = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
PLAYER_START_Y = SCREEN_HEIGHT - PLAYER_HEIGHT - 20

# 적 설정
ENEMY_WIDTH = 40
ENEMY_HEIGHT = 30
ENEMY_COLOR = RED
ENEMY_SPEED_X = 20
ENEMY_DROP_SPEED = 20

# 미사일 설정
BULLET_WIDTH = 5
BULLET_HEIGHT = 10
BULLET_COLOR = YELLOW
BULLET_SPEED = 7
FIRE_COOLDOWN = 500  # ms

# Asset Paths
import sys
import os

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

BACKGROUND_DIR = os.path.join(ASSETS_DIR, "background")
INTRO_IMAGE_PATH = os.path.join(BACKGROUND_DIR, "intro_screen.png")
BACKGROUND_IMAGE_PATH = os.path.join(BACKGROUND_DIR, "space_background.png")

PLAYER_DIR = os.path.join(ASSETS_DIR, "player")
PLAYER_IMAGE_PATH = os.path.join(PLAYER_DIR, "player_ship.png")
PLAYER_BULLET_PATH = os.path.join(PLAYER_DIR, "player_bullet.png")

ENEMY_DIR = os.path.join(ASSETS_DIR, "enemy")
ENEMY_IMAGE_PATH = os.path.join(ENEMY_DIR, "enemy_ship.png")
ENEMY_BULLET_PATH = os.path.join(ENEMY_DIR, "enemy_bullet.png")

EXPLOSION_IMAGE_PATH = os.path.join(ASSETS_DIR, "explosion_fx.png")

SOUND_DIR = os.path.join(ASSETS_DIR, "sounds")
SHOOT_SOUND_PATH = os.path.join(SOUND_DIR, "shoot.wav")
EXPLOSION_SOUND_PATH = os.path.join(SOUND_DIR, "explosion.wav")

