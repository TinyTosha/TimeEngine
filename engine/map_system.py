import pygame
import os
import yaml

class MapObject:
    def __init__(self, object_data):
        self.layer = object_data.get('layer', 0)  # 0 - фон, 1+ - объекты
        self.collision = object_data.get('collision', False)
        self.world_size = object_data.get('world_size', [64, 64])
        self.world_pos = object_data.get('world_pos', [0, 0])
        self.texture_config = object_data.get('texture', {})
        self.texture = None
        self.rect = pygame.Rect(self.world_pos[0], self.world_pos[1], 
                               self.world_size[0], self.world_size[1])
        
        self.load_texture()
    
    def load_texture(self):
        texture_name = self.texture_config.get('texture')
        use_texture = self.texture_config.get('use_texture', False)
        color = self.texture_config.get('color')
        
        if use_texture and texture_name:
            texture_path = os.path.join("game", "textures", texture_name)
            if os.path.exists(texture_path):
                self.texture = pygame.image.load(texture_path).convert_alpha()
                self.texture = pygame.transform.scale(self.texture, 
                                                    (self.world_size[0], self.world_size[1]))
        elif color:
            if isinstance(color, list) and len(color) == 3:
                self.texture = pygame.Surface((self.world_size[0], self.world_size[1]))
                self.texture.fill(color)
    
    def check_collision(self, player_rect):
        """Проверяет коллизию с игроком"""
        if not self.collision:
            return False
        return self.rect.colliderect(player_rect)
    
    def render(self, screen, camera_offset):
        """Отрисовывает объект карты"""
        if not self.texture:
            return
        
        render_x = self.world_pos[0] - camera_offset[0]
        render_y = self.world_pos[1] - camera_offset[1]
        
        screen.blit(self.texture, (render_x, render_y))

class MapSystem:
    def __init__(self):
        self.maps = {}
        self.current_map = None
        self.map_objects = []
        self.load_maps()
    
    def load_maps(self):
        """Загружает все карты из папки maps"""
        maps_path = os.path.join("game", "maps")
        if os.path.exists(maps_path):
            for map_file in os.listdir(maps_path):
                if map_file.endswith(".yaml"):
                    file_path = os.path.join(maps_path, map_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            map_data = yaml.safe_load(file)
                            map_id = map_data.get('id')
                            if map_id is not None:
                                self.maps[map_id] = map_data
                    except Exception as e:
                        print(f"Error loading map {map_file}: {e}")
    
    def set_map(self, map_id):
        """Устанавливает текущую карту"""
        if map_id in self.maps:
            map_data = self.maps[map_id]
            self.current_map = map_data
            self.map_objects = []
            
            # Создаем объекты карты
            map_objects = map_data.get('map', {})
            for obj_name, obj_data in map_objects.items():
                map_object = MapObject(obj_data)
                self.map_objects.append(map_object)
            
            # Сортируем объекты по слоям
            self.map_objects.sort(key=lambda x: x.layer)
            
            print(f"Map '{map_data.get('name')}' loaded successfully!")
            return True
        else:
            print(f"Map with id {map_id} not found!")
            return False
    
    def check_collisions(self, player_rect):
        """Проверяет коллизии игрока с объектами карты"""
        collisions = []
        for obj in self.map_objects:
            if obj.check_collision(player_rect):
                collisions.append(obj)
        return collisions
    
    def update_player_position(self, player_rect, new_x, new_y):
        """Обновляет позицию игрока с учетом коллизий"""
        temp_rect = player_rect.copy()
        temp_rect.x = new_x
        temp_rect.y = new_y
        
        # Проверяем коллизии
        collisions = self.check_collisions(temp_rect)
        
        if collisions:
            return False
        else:
            player_rect.x = new_x
            player_rect.y = new_y
            return True
    
    def render(self, screen, camera_offset):
        """Отрисовывает все объекты карты"""
        for obj in self.map_objects:
            obj.render(screen, camera_offset)