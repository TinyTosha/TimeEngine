import pygame
import os
import yaml
import math
import time

class Entity:
    def __init__(self, data, spawn_x=0, spawn_y=0):
        self.name = data.get('name', 'Unknown')
        self.id = data.get('id', 0)
        self.texture_data = data.get('texture', {})
        self.stats = data.get('stats', {})
        self.behavior = data.get('behavior', {})
        self.texture = None
        
        # Позиция и респавн
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.position = [spawn_x, spawn_y]
        
        # Статы
        self.attack_cooldown = 0
        self.health = self.stats.get('health', 100)
        self.max_health = self.stats.get('max_health', self.health)
        self.show_health_bar = False
        self.alive = True
        
        # Респавн
        self.respawn_time = self.stats.get('respawn_time', 10.0)
        self.respawn_timer = 0
        self.is_respawning = False
        
        self.load_texture()
    
    def load_texture(self):
        texture_name = self.texture_data.get('texture')
        if texture_name:
            texture_path = os.path.join("game", "textures", texture_name)
            if os.path.exists(texture_path):
                self.texture = pygame.image.load(texture_path).convert_alpha()
                world_size = self.texture_data.get('world_size', [50, 50])
                if isinstance(world_size, list) and len(world_size) == 2:
                    self.texture = pygame.transform.scale(self.texture, (world_size[0], world_size[1]))
    
    def update(self, player_position, player_health_system, delta_time):
        # Респавн
        if not self.alive and not self.is_respawning:
            self.start_respawn()
        
        if self.is_respawning:
            self.respawn_timer -= delta_time
            if self.respawn_timer <= 0:
                self.respawn()
            return
        
        if not self.alive:
            return
        
        # Обновление кд атаки
        if self.attack_cooldown > 0:
            self.attack_cooldown -= delta_time
        
        # Проверка аггро и атака
        distance = math.sqrt((self.position[0] - player_position[0])**2 + 
                            (self.position[1] - player_position[1])**2)
        
        if distance <= self.behavior.get('aggro_range', 200):
            self.show_health_bar = True
            
            # Атака игрока
            if distance <= self.stats.get('attack_range', 70) and self.attack_cooldown <= 0:
                self.attack(player_health_system)
        else:
            self.show_health_bar = False
    
    def start_respawn(self):
        self.is_respawning = True
        self.respawn_timer = self.respawn_time
    
    def respawn(self):
        self.is_respawning = False
        self.alive = True
        self.health = self.max_health
        self.position = [self.spawn_x, self.spawn_y]
        self.show_health_bar = False
    
    def attack(self, health_system):
        damage = self.stats.get('damage', 5)
        health_system.damage(damage)
        self.attack_cooldown = self.stats.get('attack_cooldown', 1.0)
    
    def take_damage(self, amount):
        if not self.alive or self.is_respawning:
            return False
            
        self.health = max(0, self.health - amount)
        self.show_health_bar = True
        
        if self.health <= 0:
            self.alive = False
            return True
        
        return False
    
    def render(self, screen, camera_offset):
        if not self.alive or not self.texture or self.is_respawning:
            return
        
        # Применяем смещение камеры
        render_x = self.position[0] - self.texture.get_width()//2 - camera_offset[0]
        render_y = self.position[1] - self.texture.get_height()//2 - camera_offset[1]
        
        screen.blit(self.texture, (render_x, render_y))
        
        # Отрисовка полоски здоровья если нужно
        if self.show_health_bar:
            self.render_health_bar(screen, camera_offset)
    
    def render_health_bar(self, screen, camera_offset):
        bar_width = 60
        bar_height = 6
        x = self.position[0] - bar_width // 2 - camera_offset[0]
        y = self.position[1] - 40 - camera_offset[1]
        
        # Фон
        pygame.draw.rect(screen, (50, 50, 50), (x, y, bar_width, bar_height))
        
        # Здоровье
        health_width = max(0, (self.health / self.max_health) * bar_width)
        pygame.draw.rect(screen, (255, 0, 0), (x, y, health_width, bar_height))
        
        # Обводка
        pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_width, bar_height), 1)

class EntityManager:
    def __init__(self, script_runner):
        self.entities = []
        self.enemy_templates = {}
        self.script_runner = script_runner
        self.load_enemy_templates()
    
    def load_enemy_templates(self):
        enemys_path = os.path.join("game", "enemys")
        if os.path.exists(enemys_path):
            for enemy_file in os.listdir(enemys_path):
                if enemy_file.endswith(".yaml"):
                    file_path = os.path.join(enemys_path, enemy_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            enemy_data = yaml.safe_load(file)
                            enemy_id = enemy_data.get('id')
                            if enemy_id is not None:
                                self.enemy_templates[enemy_id] = enemy_data
                    except Exception as e:
                        print(f"Error loading enemy template {enemy_file}: {e}")
    
    def spawn_enemy(self, enemy_id, x, y, initialize=True):
        if enemy_id not in self.enemy_templates:
            print(f"Enemy template with id {enemy_id} not found!")
            return None
        
        if initialize:
            enemy_data = self.enemy_templates[enemy_id].copy()
            enemy = Entity(enemy_data, x, y)
            self.entities.append(enemy)
            return enemy
        else:
            # Возвращаем пустышку для скриптов
            return {"id": enemy_id, "x": x, "y": y, "initialized": False}
    
    def update(self, player_position, player_health_system, delta_time):
        for entity in self.entities:
            entity.update(player_position, player_health_system, delta_time)
    
    def render(self, screen, camera_offset):
        for entity in self.entities:
            entity.render(screen, camera_offset)
    
    def check_attack_hit(self, attack_position, attack_range, damage):
        """Проверяет попадание атаки игрока по врагам"""
        hits = []
        for entity in self.entities:
            if not entity.alive or entity.is_respawning:
                continue
                
            distance = math.sqrt((entity.position[0] - attack_position[0])**2 + 
                                (entity.position[1] - attack_position[1])**2)
            if distance <= attack_range:
                if entity.take_damage(damage):
                    hits.append(entity)
        return hits