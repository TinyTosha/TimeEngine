import pygame
import os
import yaml

class HealthSystem:
    def __init__(self, config_path="game/config/game_config.yaml"):
        self.health = 100
        self.max_health = 100
        self.health_texture = None
        self.load_config(config_path)
        self.load_textures()
    
    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                defaults = config.get('default_values', {})
                self.health = defaults.get('health', 100)
                self.max_health = defaults.get('max_health', 100)
    
    def load_textures(self):
        health_ui_path = os.path.join("game", "textures", "health_ui.png")
        if os.path.exists(health_ui_path):
            self.health_texture = pygame.image.load(health_ui_path).convert_alpha()
            self.health_texture = pygame.transform.scale(self.health_texture, (32, 32))
    
    def damage(self, amount):
        self.health = max(0, self.health - amount)
        return self.health <= 0
    
    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
    
    def render(self, screen):
        # Позиция UI здоровья
        ui_x, ui_y = 20, 20
        
        # Отрисовка иконки если есть
        if self.health_texture:
            screen.blit(self.health_texture, (ui_x, ui_y))
            ui_x += 40  # Сдвигаем полоску правее иконки
        
        # Полоска здоровья
        bar_width = 200
        bar_height = 20
        border_width = 2
        
        # Фон полоски
        bg_rect = pygame.Rect(ui_x, ui_y, bar_width, bar_height)
        pygame.draw.rect(screen, (50, 50, 50), bg_rect)
        
        # Заполнение здоровья
        health_width = max(0, (self.health / self.max_health) * bar_width)
        health_rect = pygame.Rect(ui_x, ui_y, health_width, bar_height)
        pygame.draw.rect(screen, (255, 0, 0), health_rect)
        
        # Обводка
        pygame.draw.rect(screen, (100, 100, 120), bg_rect, border_width)
        
        # Текст здоровья
        font = pygame.font.Font(None, 16)
        health_text = font.render(f"{self.health} / {self.max_health}", True, (255, 255, 255))
        text_rect = health_text.get_rect(center=(ui_x + bar_width//2, ui_y + bar_height//2))
        screen.blit(health_text, text_rect)
    
    def get_health_variables(self):
        """Возвращает переменные для использования в скриптах"""
        return {
            'health': self.health,
            'health.max': self.max_health,
            'health.percent': (self.health / self.max_health) * 100
        }