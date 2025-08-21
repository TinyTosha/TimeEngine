import pygame

class Inventory:
    def __init__(self, slots=10):
        self.slots = [None] * slots
        self.font = pygame.font.Font(None, 24)
    
    def give_item(self, item_name, item_id, slot):
        if 0 <= slot < len(self.slots):
            self.slots[slot] = {
                'name': item_name,
                'id': item_id,
                'count': 1
            }
            return True
        return False
    
    def render(self, screen):
        # Упрощенная отрисовка инвентаря
        for i, item in enumerate(self.slots):
            slot_rect = pygame.Rect(10 + i * 60, 500, 50, 50)
            pygame.draw.rect(screen, (100, 100, 100), slot_rect)
            
            if item:
                item_text = self.font.render(item['name'][:3], True, (255, 255, 255))
                screen.blit(item_text, (slot_rect.x + 5, slot_rect.y + 15))