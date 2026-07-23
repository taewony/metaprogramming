import pygame
import sys
from game.constants import *
from game.constants import *
from game.explosion import Explosion
from game.score_manager import ScoreManager

class GameManager:
    def __init__(self, player_group, bullet_group, enemy_manager):
        self.player_group = player_group
        self.bullets = bullet_group
        self.enemy_manager = enemy_manager
        self.explosions = pygame.sprite.Group()
        
        self.lives = PLAYER_LIVES
        self.score = 0
        self.game_state = "INTRO" # INTRO, PLAYING, INPUT_NAME, RANKING, WIN
        
        self.score_manager = ScoreManager()
        self.input_name = ""
        
        self.font = pygame.font.SysFont(None, 36)
        self.big_font = pygame.font.SysFont(None, 72)
        
        # 배경 및 인트로 이미지 로드
        try:
            self.intro_image = pygame.image.load(INTRO_IMAGE_PATH).convert()
            self.intro_image = pygame.transform.scale(self.intro_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception as e:
            print(f"Error loading intro image: {e}")
            self.intro_image = None
            
        try:
            self.background_image = pygame.image.load(BACKGROUND_IMAGE_PATH).convert()
            self.background_image = pygame.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.background_image = None

    def update(self):
        if self.game_state == "INTRO":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                self.game_state = "PLAYING"
            # 인트로에서도 종료(QUIT) 이벤트는 main에서 처리됨

        elif self.game_state == "INPUT_NAME":
             # 이름 입력은 handle_event에서 처리
             pass

        elif self.game_state == "RANKING":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                self.reset_game()

        elif self.game_state == "PLAYING":
            self.check_collisions()
            self.check_game_over()
            self.check_win()
            self.explosions.update()

        elif self.game_state in ["GAME_OVER", "WIN"]:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                self.reset_game()

    def handle_event(self, event):
        if self.game_state == "INPUT_NAME":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if len(self.input_name) == 3:
                        self.score_manager.add_score(self.input_name, self.score)
                        self.game_state = "RANKING"
                elif event.key == pygame.K_BACKSPACE:
                    self.input_name = self.input_name[:-1]
                else:
                    if len(self.input_name) < 3 and event.unicode.isalpha():
                        self.input_name += event.unicode.upper()

    def reset_game(self):
        self.score = 0
        self.game_state = "PLAYING"
        self.player_group.sprite.reset_position()
        self.bullets.empty()
        self.explosions.empty()
        self.enemy_manager.reset()
        self.lives = PLAYER_LIVES

    def check_collisions(self):
        # 1. 플레이어 미사일 <-> 적 충돌
        # groupcollide(group1, group2, dokill1, dokill2)
        # bullets are mixed (player and enemy). Wait.
        # I need to distinguish bullets.
        # Option 1: Add 'owner' or 'type' to Bullet.
        # Option 2: Separate groups for player bullets and enemy bullets.
        
        # Currently Main has 'bullets' group which has player bullets.
        # EnemyManager has 'enemy_bullets'.
        
        # Player bullets hitting enemies
        hits = pygame.sprite.groupcollide(self.bullets, self.enemy_manager.enemies, True, True)
        if hits:
            for hit in hits:
                # hit is the bullet, value is list of enemies hit
                self.score += len(hits[hit]) * 10
                for enemy in hits[hit]:
                    explosion = Explosion(enemy.rect.center)
                    self.explosions.add(explosion)
        
        # Enemy bullets hitting player
        if pygame.sprite.spritecollide(self.player_group.sprite, self.enemy_manager.enemy_bullets, True):
            self.lives -= 1
            if self.lives <= 0:
                self.game_state = "INPUT_NAME"
                self.input_name = ""
            
        # Enemies hitting player (body collision)
        if pygame.sprite.spritecollide(self.player_group.sprite, self.enemy_manager.enemies, False):
            self.lives -= 1
            if self.lives <= 0:
                self.game_state = "INPUT_NAME"
                self.input_name = ""

    def check_game_over(self):
        # 플레이어가 죽었거나 적이 너무 내려왔을 때
        # Player death is handled in collision
        
        # Check if any enemy reached bottom
        for enemy in self.enemy_manager.enemies:
            if enemy.rect.bottom >= SCREEN_HEIGHT:
                self.game_state = "INPUT_NAME"
                self.input_name = ""
                break

    def check_win(self):
        if len(self.enemy_manager.enemies) == 0:
            self.game_state = "WIN"

    def draw_ui(self, screen):
        # 점수 표시
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # 생명 표시
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        lives_rect = lives_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
        screen.blit(lives_text, lives_rect)
        
        # 게임 오버 / 승리 메시지
        if self.game_state == "INPUT_NAME":
            text = self.big_font.render("GAME OVER", True, RED)
            rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(text, rect)
            
            name_text = self.font.render(f"Enter Name: {self.input_name}", True, WHITE)
            name_rect = name_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
            screen.blit(name_text, name_rect)
            
            desc_text = self.font.render("Type 3 Letters & Press Enter", True, WHITE)
            desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
            screen.blit(desc_text, desc_rect)

        elif self.game_state == "RANKING":
            title = self.big_font.render("RANKING", True, YELLOW)
            title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
            screen.blit(title, title_rect)
            
            top_scores = self.score_manager.get_top_scores()
            start_y = 180
            for i, entry in enumerate(top_scores):
                score_str = f"{i+1}. {entry['name']}  -  {entry['score']}"
                row_text = self.font.render(score_str, True, WHITE)
                row_rect = row_text.get_rect(center=(SCREEN_WIDTH//2, start_y + i * 40))
                screen.blit(row_text, row_rect)

            restart_text = self.font.render("Press 'R' to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            screen.blit(restart_text, restart_rect)
            
        elif self.game_state == "WIN":
            text = self.big_font.render("YOU WIN", True, GREEN)
            rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(text, rect)
            
            sub_text = self.font.render("Press 'R' to Restart", True, WHITE)
            sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            screen.blit(sub_text, sub_rect)

    def draw_background(self, screen):
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            screen.fill(BLACK)

    def draw_explosions(self, screen):
        self.explosions.draw(screen)

    def draw_intro(self, screen):
        if self.intro_image:
            screen.blit(self.intro_image, (0, 0))
        else:
            screen.fill(BLACK)
            text = self.big_font.render("SPACE DEFENDER", True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(text, rect)
            
            sub_text = self.font.render("Press Space to Start", True, WHITE)
            sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            screen.blit(sub_text, sub_rect)
