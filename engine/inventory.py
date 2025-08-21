import pygame
import os

class Inventory:
    def __init__(self, cache_manager, slots=9):
        self.slots = [None] * slots
        self.cache_manager = cache_manager
        self.font = pygame.font.Font(None, 24)
        self.cooldown_font = pygame.font.Font(None, 18)
        self.slot_size = 60
        self.inventory_textures = {}
    
    def give_item(self, item_id, slot):
        if 0 <= slot < len(self.slots):
            self.slots[slot] = {
                'id': item_id,
                'count': 1
            }
            return True
        return False
    
    def get_item(self, slot):
        if 0 <= slot < len(self.slots):
            return self.slots[slot]
        return None
    
    def render(self, screen, item_loader, selected_slot=None):
        # Отрисовка фона инвентаря
        inventory_bg = pygame.Rect(10, 500, self.slot_size * len(self.slots) + 20, self.slot_size + 20)
        pygame.draw.rect(screen, (50, 50, 60), inventory_bg)
        pygame.draw.rect(screen, (100, 100, 120), inventory_bg, 2)
        
        # Отрисовка слотов и предметов
        for i, item in enumerate(self.slots):
            slot_rect = pygame.Rect(20 + i * self.slot_size, 510, self.slot_size - 10, self.slot_size - 10)
            
            # Фон слота (выделение выбранного)
            if i == selected_slot:
                pygame.draw.rect(screen, (100, 100, 200), slot_rect)
            else:
                pygame.draw.rect(screen, (80, 80, 90), slot_rect)
            
            pygame.draw.rect(screen, (120, 120, 140), slot_rect, 2)
            
            # Номер слота
            slot_text = self.font.render(str(i+1), True, (200, 200, 200))
            screen.blit(slot_text, (slot_rect.x + 5, slot_rect.y + 5))
            
            # Предмет (только текстура, без имени)
            if item:
                item_data = item_loader.get_item(item['id'])
                if item_data:
                    self.render_item(screen, slot_rect, item_data, item_loader)
            
            # Отображение кд для слота
            slot_cooldown = self.cache_manager.get_slot_cooldown(i)
            if slot_cooldown > 0:
                self.render_cooldown(screen, slot_rect, slot_cooldown)
    
    def render_item(self, screen, slot_rect, item_data, item_loader):
        texture_config = item_data.get('texture', {})
        texture_name = texture_config.get('texture')
        
        if texture_name:
            if texture_name not in self.inventory_textures:
                texture_path = os.path.join("game", "textures", texture_name)
                if os.path.exists(texture_path):
                    texture = pygame.image.load(texture_path).convert_alpha()
                    
                    inventory_size = texture_config.get('inventory_size', [self.slot_size - 20, self.slot_size - 20])
                    if isinstance(inventory_size, list) and len(inventory_size) == 2:
                        texture = pygame.transform.scale(texture, (inventory_size[0], inventory_size[1]))
                    else:
                        texture = pygame.transform.scale(texture, (self.slot_size - 20, self.slot_size - 20))
                    
                    self.inventory_textures[texture_name] = texture
            
            if texture_name in self.inventory_textures:
                texture = self.inventory_textures[texture_name]
                texture_rect = texture.get_rect(center=slot_rect.center)
                screen.blit(texture, texture_rect)
    
    def render_cooldown(self, screen, slot_rect, cooldown):
        overlay = pygame.Surface((slot_rect.width, slot_rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, slot_rect)
        
        seconds = cooldown / 60
        cooldown_text = self.cooldown_font.render(f"{seconds:.1f}", True, (255, 0, 0))
        text_rect = cooldown_text.get_rect(center=slot_rect.center)
        screen.blit(cooldown_text, text_rect)