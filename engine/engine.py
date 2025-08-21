import pygame
import os
import yaml
import re
from .item_loader import ItemLoader
from .inventory import Inventory
from .script_runner import ScriptRunner

class RPGEngine:
    def __init__(self, screen_width=800, screen_height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("RPG Engine")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Загрузка ресурсов
        self.item_loader = ItemLoader()
        self.inventory = Inventory()
        self.script_runner = ScriptRunner(self.inventory, self.item_loader)
        
        # Игрок
        self.player = self.create_player()
        self.player_speed = 5
        
        # Выбранный предмет
        self.selected_item = None
        self.item_cooldown = 0
        self.item_state = "idle"  # idle, attacking, cooldown
        self.attack_progress = 0
        
        # Загрузка предметов и скриптов
        self.load_game_data()
    
    def create_player(self):
        player_texture = self.load_texture("player.png", (50, 50))
        if player_texture:
            return {"texture": player_texture, "rect": pygame.Rect(400, 300, 50, 50)}
        else:
            return {"texture": None, "rect": pygame.Rect(400, 300, 50, 50)}
    
    def load_texture(self, texture_name, default_size=(50, 50)):
        texture_path = os.path.join("game", "textures", texture_name)
        if os.path.exists(texture_path):
            texture = pygame.image.load(texture_path).convert_alpha()
            texture = pygame.transform.scale(texture, default_size)
            return texture
        return None
    
    def load_game_data(self):
        # Загрузка всех предметов
        items_path = os.path.join("game", "items")
        for item_file in os.listdir(items_path):
            if item_file.endswith(".yaml"):
                self.item_loader.load_item(os.path.join(items_path, item_file))
        
        # Загрузка и выполнение скриптов
        scripts_path = os.path.join("game", "scripts")
        for script_file in os.listdir(scripts_path):
            if script_file.endswith(".yaml"):
                self.script_runner.run_script(os.path.join(scripts_path, script_file))
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Движение игрока
        if keys[pygame.K_w]:
            self.player["rect"].y -= self.player_speed
        if keys[pygame.K_s]:
            self.player["rect"].y += self.player_speed
        if keys[pygame.K_a]:
            self.player["rect"].x -= self.player_speed
        if keys[pygame.K_d]:
            self.player["rect"].x += self.player_speed
        
        # Выбор предметов (1-9)
        for i in range(9):
            if keys[getattr(pygame, f'K_{i+1}')]:
                self.select_item(i)
        
        # Обработка кд предметов
        if self.item_cooldown > 0:
            self.item_cooldown -= 1
        
        # Обработка анимации атаки
        if self.item_state == "attacking":
            self.attack_progress += 0.1
            if self.attack_progress >= 1:
                self.item_state = "cooldown"
                if self.selected_item:
                    item_data = self.item_loader.get_item(self.selected_item['id'])
                    if item_data:
                        cooldown = item_data.get('type', {}).get('cooldown', 1.0)
                        self.item_cooldown = int(cooldown * 60)  # сек в кадры
    
    def select_item(self, slot):
        item = self.inventory.get_item(slot)
        if item and self.item_state == "idle" and self.item_cooldown <= 0:
            self.selected_item = item
            item_data = self.item_loader.get_item(item['id'])
            if item_data and item_data.get('type', {}).get('sword'):
                self.item_state = "attacking"
                self.attack_progress = 0
    
    def render(self):
        self.screen.fill((30, 30, 40))
        
        # Отрисовка игрока
        if self.player["texture"]:
            self.screen.blit(self.player["texture"], self.player["rect"])
        else:
            pygame.draw.rect(self.screen, (0, 0, 255), self.player["rect"])
        
        # Отрисовка выбранного предмета
        if self.selected_item and self.item_state == "attacking":
            self.render_selected_item()
        
        # Отрисовка инвентаря
        self.inventory.render(self.screen, self.item_loader)
        
        # Отрисовка кд
        if self.item_cooldown > 0:
            font = pygame.font.Font(None, 24)
            cooldown_text = font.render(f"Cooldown: {self.item_cooldown//60}.{(self.item_cooldown%60)/10:.1f}s", True, (255, 0, 0))
            self.screen.blit(cooldown_text, (10, 450))
        
        pygame.display.flip()
    
    def render_selected_item(self):
        if not self.selected_item:
            return
        
        item_data = self.item_loader.get_item(self.selected_item['id'])
        if not item_data:
            return
        
        # Получаем размер для мира
        texture_config = item_data.get('texture', {})
        world_size = texture_config.get('world_size', [50, 50])
        if not isinstance(world_size, list) or len(world_size) != 2:
            world_size = [50, 50]
        
        # Загрузка текстуры предмета с правильным размером
        texture_name = texture_config.get('texture')
        if texture_name:
            texture_path = os.path.join("game", "textures", texture_name)
            if os.path.exists(texture_path):
                item_texture = pygame.image.load(texture_path).convert_alpha()
                item_texture = pygame.transform.scale(item_texture, (world_size[0], world_size[1]))
                
                # Позиция предмета относительно игрока (анимация атаки)
                player_center = self.player["rect"].center
                offset_x = 0
                offset_y = 0
                
                if self.attack_progress < 0.5:
                    # Движение вниз
                    offset_y = int(50 * self.attack_progress * 2)
                else:
                    # Движение вверх
                    offset_y = int(50 * (1 - (self.attack_progress - 0.5) * 2))
                
                item_pos = (player_center[0] - world_size[0]//2 + offset_x, 
                           player_center[1] - world_size[1]//2 + offset_y)
                
                self.screen.blit(item_texture, item_pos)
    
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            self.handle_input()
            self.render()
            self.clock.tick(60)
            
            # Сброс состояния атаки
            if self.item_state == "cooldown" and self.item_cooldown <= 0:
                self.item_state = "idle"
                self.selected_item = None
        
        pygame.quit()