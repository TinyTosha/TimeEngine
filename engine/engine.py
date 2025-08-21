import pygame
import os
import yaml
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
        self.script_runner = ScriptRunner(self.inventory)
        
        # Игрок
        self.player = self.create_player()
        self.player_speed = 5
        
        # Загрузка предметов и скриптов
        self.load_game_data()
    
    def create_player(self):
        player_texture = self.load_texture("player.png")
        if player_texture:
            return {"texture": player_texture, "rect": pygame.Rect(400, 300, 50, 50)}
        else:
            return {"texture": None, "rect": pygame.Rect(400, 300, 50, 50)}
    
    def load_texture(self, texture_name):
        texture_path = os.path.join("game", "textures", texture_name)
        if os.path.exists(texture_path):
            return pygame.image.load(texture_path).convert_alpha()
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
        
        if keys[pygame.K_w]:
            self.player["rect"].y -= self.player_speed
        if keys[pygame.K_s]:
            self.player["rect"].y += self.player_speed
        if keys[pygame.K_a]:
            self.player["rect"].x -= self.player_speed
        if keys[pygame.K_d]:
            self.player["rect"].x += self.player_speed
    
    def render(self):
        self.screen.fill((0, 0, 0))
        
        # Отрисовка игрока
        if self.player["texture"]:
            self.screen.blit(self.player["texture"], self.player["rect"])
        else:
            pygame.draw.rect(self.screen, (255, 0, 0), self.player["rect"])
        
        # Отрисовка инвентаря (упрощенная версия)
        self.inventory.render(self.screen)
        
        pygame.display.flip()
    w
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            self.handle_input()
            self.render()
            self.clock.tick(60)
        
        pygame.quit()