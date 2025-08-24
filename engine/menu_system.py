import pygame
import os
import yaml
import re
import time

class MenuSystem:
    def __init__(self, script_runner, value_system):
        self.script_runner = script_runner
        self.value_system = value_system
        self.menus = {}
        self.active_menu = None
        self.button_cooldowns = {}  # Кд для кнопок меню
        self.button_cooldown_duration = 10  # Кд в кадрах
        self.load_menus()
    
    def load_menus(self):
        """Загружает все меню из папки menus"""
        menus_path = os.path.join("game", "menus")
        if os.path.exists(menus_path):
            for menu_file in os.listdir(menus_path):
                if menu_file.endswith(".yaml"):
                    file_path = os.path.join(menus_path, menu_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            menu_data = yaml.safe_load(file)
                            menu_id = menu_data.get('id')
                            if menu_id is not None:
                                self.menus[menu_id] = menu_data
                    except Exception as e:
                        print(f"Error loading menu {menu_file}: {e}")
    
    def open_menu(self, menu_id):
        """Открывает меню по ID"""
        if menu_id in self.menus:
            self.active_menu = self.menus[menu_id]
            return True
        return False
    
    def close_menu(self):
        """Закрывает текущее меню"""
        self.active_menu = None
    
    def update_cooldowns(self):
        """Обновляет кд кнопок"""
        for button_name in list(self.button_cooldowns.keys()):
            if self.button_cooldowns[button_name] > 0:
                self.button_cooldowns[button_name] -= 1
                if self.button_cooldowns[button_name] <= 0:
                    del self.button_cooldowns[button_name]
    
    def handle_click(self, mouse_pos):
        """Обрабатывает клики в меню"""
        if not self.active_menu:
            return False
        
        # Обновляем кд
        self.update_cooldowns()
        
        ui_elements = self.active_menu.get('menu', {}).get('ui', {})
        
        for element_name, element_data in ui_elements.items():
            if element_data.get('type') == 'button':
                pos = element_data.get('pos', [0, 0])
                size = element_data.get('size', [100, 30])
                
                button_rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
                if button_rect.collidepoint(mouse_pos):
                    # Проверяем кд кнопки
                    if element_name in self.button_cooldowns:
                        return True
                    
                    # Устанавливаем кд
                    self.button_cooldowns[element_name] = self.button_cooldown_duration
                    
                    script = element_data.get('script', [])
                    self.execute_menu_script(script)
                    return True
        
        # Проверяем клик по кнопке закрытия
        if self.active_menu.get('menu', {}).get('config', {}).get('show_cross', True):
            menu_config = self.active_menu.get('menu', {}).get('config', {})
            menu_width = menu_config.get('width', 600)
            menu_height = menu_config.get('height', 400)
            menu_x = menu_config.get('pos', [100, 100])[0]
            menu_y = menu_config.get('pos', [100, 100])[1]
            
            cross_rect = pygame.Rect(menu_x + menu_width - 30, menu_y + 10, 20, 20)
            if cross_rect.collidepoint(mouse_pos):
                self.close_menu()
                return True
        
        return False
    
    def execute_menu_script(self, script_lines):
        """Выполняет скрипт меню"""
        for line in script_lines:
            if line.strip() and not line.strip().startswith('#'):
                self.script_runner.execute_command(line.strip())
    
    def render(self, screen):
        """Отрисовывает активное меню"""
        if not self.active_menu:
            return
        
        menu_config = self.active_menu.get('menu', {}).get('config', {})
        ui_elements = self.active_menu.get('menu', {}).get('ui', {})
        
        # Получаем размеры и позицию меню
        menu_width = menu_config.get('width', 600)
        menu_height = menu_config.get('height', 400)
        menu_x = menu_config.get('pos', [100, 100])[0]
        menu_y = menu_config.get('pos', [100, 100])[1]
        
        # Фон меню
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(screen, (40, 40, 50), menu_rect)
        pygame.draw.rect(screen, (100, 100, 120), menu_rect, 2)
        
        # Заголовок
        title_font = pygame.font.Font(None, 32)
        title_text = title_font.render(menu_config.get('title', 'Menu'), True, (255, 215, 0))
        screen.blit(title_text, (menu_x + 20, menu_y + 20))
        
        # Кнопка закрытия (рисуется поверх всего)
        if menu_config.get('show_cross', True):
            cross_rect = pygame.Rect(menu_x + menu_width - 30, menu_y + 10, 20, 20)
            # Рисуем кнопку как обычную, но с красным крестиком
            pygame.draw.rect(screen, (80, 80, 100), cross_rect)
            pygame.draw.rect(screen, (120, 120, 140), cross_rect, 2)
            
            cross_font = pygame.font.Font(None, 20)
            cross_text = cross_font.render("X", True, (255, 0, 0))  # Красный крестик
            screen.blit(cross_text, (cross_rect.x + 6, cross_rect.y + 2))
        
        # Отрисовка UI элементов
        for element_name, element_data in ui_elements.items():
            self.render_ui_element(screen, element_data)
    
    def render_ui_element(self, screen, element_data):
        """Отрисовывает UI элемент"""
        element_type = element_data.get('type')
        pos = element_data.get('pos', [0, 0])
        
        if element_type == 'button':
            text = element_data.get('text', 'Button')
            # Форматируем текст с значениями
            if '%' in text:
                text = self.value_system.format_value_text(text)
            
            size = element_data.get('size', [100, 30])
            
            button_rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
            pygame.draw.rect(screen, (80, 80, 100), button_rect)
            
            if element_data.get('frame', True):
                pygame.draw.rect(screen, (120, 120, 140), button_rect, 2)
            
            font = pygame.font.Font(None, 20)
            text_surface = font.render(text, True, (255, 255, 255))
            text_x = pos[0] + (size[0] - text_surface.get_width()) // 2
            text_y = pos[1] + (size[1] - text_surface.get_height()) // 2
            screen.blit(text_surface, (text_x, text_y))
        
        elif element_type == 'text':
            text = element_data.get('text', '')
            # Форматируем текст с значениями
            if '%' in text:
                text = self.value_system.format_value_text(text)
            
            text_size = element_data.get('text_size', 20)
            
            font = pygame.font.Font(None, text_size)
            text_surface = font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (pos[0], pos[1]))
        
        elif element_type == 'icon':
            texture_name = element_data.get('texture')
            icon_size = element_data.get('icon_size', [64, 64])
            
            if texture_name:
                texture_path = os.path.join("game", "textures", texture_name)
                if os.path.exists(texture_path):
                    texture = pygame.image.load(texture_path).convert_alpha()
                    texture = pygame.transform.scale(texture, (icon_size[0], icon_size[1]))
                    screen.blit(texture, (pos[0], pos[1]))
            
            if element_data.get('frame', True):
                frame_size = element_data.get('frame_size', icon_size)
                frame_rect = pygame.Rect(pos[0], pos[1], frame_size[0], frame_size[1])
                pygame.draw.rect(screen, (120, 120, 140), frame_rect, 2)