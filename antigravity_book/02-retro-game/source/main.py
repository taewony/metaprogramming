import pygame
import sys
from game.constants import *
from game.player import Player
from game.enemy import EnemyManager
from game.game_manager import GameManager

def main():
    # Pygame 초기화
    pygame.init()
    
    # 화면 설정
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(SCREEN_TITLE)
    clock = pygame.time.Clock()
    
    # 게임 객체 생성
    player_sprite = Player()
    player = pygame.sprite.GroupSingle(player_sprite)
    bullets = pygame.sprite.Group()
    
    # 소리 로드
    try:
        shoot_sound = pygame.mixer.Sound(SHOOT_SOUND_PATH)
        shoot_sound.set_volume(0.3)
    except Exception as e:
        print(f"Error loading sound: {e}")
        shoot_sound = None

    enemy_manager = EnemyManager()
    
    # 게임 매니저 생성
    game_manager = GameManager(player, bullets, enemy_manager)
    
    running = True
    while running:
        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # 게임 매니저에게 이벤트 전달 (텍스트 입력 등을 위해)
            game_manager.handle_event(event)
        
        # 입력 처리
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            # 게임 중일 때만 발사 가능
            if game_manager.game_state == "PLAYING":
                bullet = player_sprite.shoot(pygame.time.get_ticks())
                if bullet:
                    bullets.add(bullet)
                    if shoot_sound:
                        shoot_sound.play()
        
        # 게임 상태 업데이트
        game_manager.update()
        
        # 렌더링 시작
        if game_manager.game_state == "INTRO":
            game_manager.draw_intro(screen)
        else:
            # 배경 그리기
            game_manager.draw_background(screen)
            
            # 게임 객체 업데이트 (PLAYING 상태일 때만)
            if game_manager.game_state == "PLAYING":
                player.update()
                bullets.update()
                enemy_manager.update()

            # 게임 객체 그리기
            player.draw(screen)
            bullets.draw(screen)
            enemy_manager.draw(screen)
            game_manager.draw_explosions(screen)
            
            # UI 그리기
            game_manager.draw_ui(screen)
        
        # 화면 갱신
        pygame.display.flip()
        
        # FPS 제한
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
