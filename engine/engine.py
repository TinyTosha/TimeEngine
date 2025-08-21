import pygame
import os
import yaml
import re
import shutil
from .item_loader import ItemLoader
from .inventory import Inventory
from .script_runner import ScriptRunner
from .cache_manager import CacheManager

class RPGEngine:
    def __init__(self, screen_width=800, screen_height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("RPG Engine")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Менеджер кэша
        self.cache_manager = CacheManager()
        
        # Загрузка ресурсов
        self.item_loader = ItemLoader()
        self.inventory = Inventory(self.cache_manager)
        self.script_runner = ScriptRunner(self.inventory, self.item_loader)
        
        # Игрок
        self.player = self.create_player()
        self.player_speed = 5
        
        # Выбранный предмет
        self.selected_slot = None
        self.selected_item = None
        self.item_state = "idle"  # idle, attacking
        self.attack_progress = 0
        self.attack_direction = "down"  # down, up
        
        # Кд для клавиш выбора слотов (1-9)
        self.key_cooldowns = {i: 0 for i in range(1, 10)}  # Кд для клавиш 1-9
        self.key_cooldown_duration = 10  # ~0.17 секунды (10 кадров при 60 FPS)
        
        # Загрузка предметов и скриптов
        self.load_game_data()
        
        # Загружаем кд слотов из кэша
        self.cache_manager.load_slot_cooldowns()
    
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
        
        # Обновляем кд клавиш
        for key in self.key_cooldowns:
            if self.key_cooldowns[key] > 0:
                self.key_cooldowns[key] -= 1
        
        # Выбор предметов (1-9) с кд для клавиш
        for i in range(9):
            key = i + 1
            if keys[getattr(pygame, f'K_{key}')] and self.key_cooldowns[key] <= 0:
                self.toggle_slot(i)
                self.key_cooldowns[key] = self.key_cooldown_duration
                break  # Обрабатываем только одно нажатие за кадр
        
        # Обработка ЛКМ для атаки
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] and self.selected_item and self.get_current_cooldown() <= 0 and self.item_state == "idle":
            item_data = self.item_loader.get_item(self.selected_item['id'])
            if item_data and item_data.get('type', {}).get('sword'):
                self.start_attack()
        
        # Обновляем кд предметов
        self.cache_manager.update_cooldowns()
        
        # Обработка анимации атаки
        if self.item_state == "attacking":
            self.handle_attack_animation()
    
    def get_current_cooldown(self):
        """Получает кд для текущего выбранного слота"""
        if self.selected_slot is not None:
            return self.cache_manager.get_slot_cooldown(self.selected_slot)
        return 0
    
    def toggle_slot(self, slot):
        item = self.inventory.get_item(slot)
        
        if self.selected_slot == slot:
            # Снимаем предмет при повторном нажатии
            self.selected_slot = None
            self.selected_item = None
            self.item_state = "idle"
        elif item:
            # Сохраняем кд предыдущего слота (если был выбран)
            if self.selected_slot is not None:
                previous_cooldown = self.get_current_cooldown()
                if previous_cooldown > 0:
                    self.cache_manager.save_slot_cooldown(self.selected_slot, previous_cooldown)
            
            # Выбираем новый слот и загружаем его кд из кэша
            self.selected_slot = slot
            self.selected_item = item
            self.item_state = "idle"
    
    def start_attack(self):
        self.item_state = "attacking"
        self.attack_progress = 0
        self.attack_direction = "down"
    
    def handle_attack_animation(self):
        if self.attack_direction == "down":
            self.attack_progress += 0.15
            if self.attack_progress >= 1:
                self.attack_direction = "up"
                self.attack_progress = 1
        else:
            self.attack_progress -= 0.15
            if self.attack_progress <= 0:
                self.complete_attack()
    
    def complete_attack(self):
        self.item_state = "idle"
        if self.selected_item:
            item_data = self.item_loader.get_item(self.selected_item['id'])
            if item_data:
                cooldown = item_data.get('type', {}).get('cooldown', 1.0)
                cooldown_frames = int(cooldown * 60)
                
                # Сохраняем кд для текущего слота
                if self.selected_slot is not None:
                    self.cache_manager.save_slot_cooldown(self.selected_slot, cooldown_frames)
    
    def cleanup(self):
        """Очистка при выходе из игры"""
        cache_dir = "engine/cache"
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print("Cache folder cleaned up")
    
    def render(self):
        self.screen.fill((30, 30, 40))
        
        # Отрисовка игрока
        if self.player["texture"]:
            self.screen.blit(self.player["texture"], self.player["rect"])
        else:
            pygame.draw.rect(self.screen, (0, 0, 255), self.player["rect"])
        
        # Отрисовка выбранного предмета
        if self.selected_item:
            self.render_selected_item()
        
        # Отрисовка инвентаря
        self.inventory.render(self.screen, self.item_loader, self.selected_slot)
        
        # Отображение состояния
        state_font = pygame.font.Font(None, 20)
        state_text = state_font.render(f"State: {self.item_state}", True, (255, 255, 255))
        self.screen.blit(state_text, (10, 480))
        
        # Отображение текущего кд
        cooldown = self.get_current_cooldown()
        if cooldown > 0:
            cooldown_font = pygame.font.Font(None, 24)
            cooldown_text = cooldown_font.render(f"Cooldown: {cooldown/60:.1f}s", True, (255, 0, 0))
            self.screen.blit(cooldown_text, (10, 450))
        
        pygame.display.flip()
    
    def render_selected_item(self):
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
                
                # Позиция предмета относительно игрока
                player_center = self.player["rect"].center
                offset_x, offset_y = self.calculate_item_position(item_data)
                
                item_pos = (player_center[0] - world_size[0]//2 + offset_x, 
                           player_center[1] - world_size[1]//2 + offset_y)
                
                self.screen.blit(item_texture, item_pos)
    
    def calculate_item_position(self, item_data):
        offset_x, offset_y = 40, 0  # Предмет справа от игрока
        
        if self.item_state == "attacking":
            # Анимация атаки: вниз-вверх
            if self.attack_direction == "down":
                offset_y = int(60 * self.attack_progress)
            else:
                offset_y = int(60 * self.attack_progress)
        
        return offset_x, offset_y
    
    def run(self):
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # ЛКМ
                            if self.selected_item and self.get_current_cooldown() <= 0 and self.item_state == "idle":
                                item_data = self.item_loader.get_item(self.selected_item['id'])
                                if item_data and item_data.get('type', {}).get('sword'):
                                    self.start_attack()
                
                self.handle_input()
                self.render()
                self.clock.tick(60)
        
        finally:
            # Всегда выполняем очистку при выходе
            self.cleanup()
            pygame.quit()