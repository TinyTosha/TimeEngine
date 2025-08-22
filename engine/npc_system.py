import pygame
import os
import yaml
import time
import math

class NPC:
    def __init__(self, data, spawn_x=0, spawn_y=0):
        self.name = data.get('name', 'Unknown NPC')
        self.id = data.get('id', 0)
        self.texture_name = data.get('texture')
        self.npc_data = data.get('npc', {})
        self.texture = None
        self.position = [spawn_x, spawn_y]
        
        # World size для масштабирования текстуры
        self.world_size = data.get('world_size', [64, 64])
        if not isinstance(self.world_size, list) or len(self.world_size) != 2:
            self.world_size = [64, 64]
            
        self.interaction_range = data.get('interaction_range', 100)
        self.can_interact = False
        self.show_interact_prompt = False
        
        self.load_texture()
        
        # Диалог
        self.current_dialog = None
        self.dialog_index = 0
        self.char_index = 0
        self.last_char_time = 0
        self.base_char_delay = 0.05  # Базовая задержка
        self.char_delay = self.base_char_delay  # Текущая задержка
        self.show_buttons = False
        
    def load_texture(self):
        if self.texture_name:
            texture_path = os.path.join("game", "textures", self.texture_name)
            if os.path.exists(texture_path):
                self.texture = pygame.image.load(texture_path).convert_alpha()
                self.texture = pygame.transform.scale(self.texture, 
                                                    (self.world_size[0], self.world_size[1]))
    
    def check_interaction(self, player_position):
        """Проверяет, может ли игрок взаимодействовать с NPC"""
        distance = math.sqrt((self.position[0] - player_position[0])**2 + 
                           (self.position[1] - player_position[1])**2)
        self.can_interact = distance <= self.interaction_range
        return self.can_interact
    
    def start_dialog(self):
        """Начинает диалог с NPC"""
        self.current_dialog = self.npc_data.get('dialog')
        self.dialog_index = 0
        self.char_index = 0
        self.last_char_time = time.time()
        self.show_buttons = False
        self.show_interact_prompt = False
        
        # Устанавливаем скорость диалога из настроек
        dialog_speed = self.current_dialog.get('speed', 1) if self.current_dialog else 1
        self.set_dialog_speed(dialog_speed)
        
        if self.current_dialog:
            return True
        return False
    
    def set_dialog_speed(self, speed_level):
        """Устанавливает скорость диалога из настроек (1-4)"""
        speed_level = max(1, min(4, speed_level))  # Ограничиваем от 1 до 4
        
        if speed_level == 1:
            self.char_delay = self.base_char_delay  # Обычная
        elif speed_level == 2:
            self.char_delay = self.base_char_delay / 2  # 2x
        elif speed_level == 3:
            self.char_delay = self.base_char_delay / 3.5  # 3.5x
        elif speed_level == 4:
            self.char_delay = 0  # Моментальная
    
    def update_dialog(self):
        """Обновляет анимацию текста диалога"""
        if not self.current_dialog or self.show_buttons:
            return
        
        # Если скорость моментальная - сразу показываем весь текст
        if self.char_delay == 0:
            messages = self.current_dialog.get('message', [])
            if self.dialog_index < len(messages):
                current_message = messages[self.dialog_index]
                if isinstance(current_message, list):
                    current_message = "\n".join(current_message)
                self.char_index = len(current_message)
                self.show_buttons = True
            return
        
        current_time = time.time()
        if current_time - self.last_char_time >= self.char_delay:
            messages = self.current_dialog.get('message', [])
            if self.dialog_index < len(messages):
                current_message = messages[self.dialog_index]
                if isinstance(current_message, list):
                    current_message = "\n".join(current_message)
                
                if self.char_index < len(current_message):
                    self.char_index += 1
                    self.last_char_time = current_time
                else:
                    self.show_buttons = True
    
    def get_current_text(self):
        """Возвращает текущий текст с анимацией"""
        if not self.current_dialog:
            return ""
        
        messages = self.current_dialog.get('message', [])
        if self.dialog_index < len(messages):
            current_message = messages[self.dialog_index]
            
            # Если сообщение - список строк (многострочный диалог)
            if isinstance(current_message, list):
                # Объединяем строки с переносами
                return "\n".join(current_message)[:self.char_index]
            else:
                # Обычная строка
                return current_message[:self.char_index]
        return ""
    
    def handle_button_click(self, button_key, script_runner):
        """Обрабатывает клик по кнопке диалога"""
        if not self.current_dialog:
            return False
        
        buttons = self.current_dialog.get('button', {})
        if button_key in buttons:
            button_data = buttons[button_key]
            
            # Выполняем скрипт кнопки
            script = button_data.get('script', [])
            for command in script:
                if command == "@close":
                    return False
                else:
                    script_runner.execute_command(command)
            
            if button_data.get('nextdialog', False):
                next_dialog = button_data.get('dialog')
                if next_dialog:
                    self.current_dialog = next_dialog
                    self.dialog_index = 0
                    self.char_index = 0
                    self.show_buttons = False
                    
                    # Устанавливаем скорость для следующего диалога
                    next_speed = next_dialog.get('speed', 1)
                    self.set_dialog_speed(next_speed)
                    
                    return True
            
            return False
        return True
    
    def render(self, screen, camera_offset):
        """Отрисовывает NPC"""
        if not self.texture:
            return
        
        render_x = self.position[0] - self.texture.get_width()//2 - camera_offset[0]
        render_y = self.position[1] - self.texture.get_height()//2 - camera_offset[1]
        
        screen.blit(self.texture, (render_x, render_y))
        
        # Имя NPC
        font = pygame.font.Font(None, 16)
        name_text = font.render(self.name, True, (255, 255, 255))
        name_x = self.position[0] - name_text.get_width()//2 - camera_offset[0]
        name_y = self.position[1] - self.world_size[1]//2 - 20 - camera_offset[1]
        screen.blit(name_text, (name_x, name_y))
        
        # Подсказка взаимодействия
        if self.show_interact_prompt:
            prompt_font = pygame.font.Font(None, 20)
            prompt_text = prompt_font.render("Press E to talk", True, (255, 255, 0))
            prompt_x = self.position[0] - prompt_text.get_width()//2 - camera_offset[0]
            prompt_y = name_y - 20
            screen.blit(prompt_text, (prompt_x, prompt_y))

class NPCSystem:
    def __init__(self, script_runner):
        self.npcs = []
        self.npc_templates = {}
        self.script_runner = script_runner
        self.active_npc = None
        self.load_npc_templates()
    
    def load_npc_templates(self):
        npcs_path = os.path.join("game", "npcs")
        if os.path.exists(npcs_path):
            for npc_file in os.listdir(npcs_path):
                if npc_file.endswith(".yaml"):
                    file_path = os.path.join(npcs_path, npc_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            npc_data = yaml.safe_load(file)
                            npc_id = npc_data.get('id')
                            if npc_id is not None:
                                self.npc_templates[npc_id] = npc_data
                    except Exception as e:
                        print(f"Error loading NPC template {npc_file}: {e}")
    
    def spawn_npc(self, npc_id, x, y, initialize=True):
        if npc_id not in self.npc_templates:
            print(f"NPC template with id {npc_id} not found!")
            return None
        
        if initialize:
            npc_data = self.npc_templates[npc_id].copy()
            npc = NPC(npc_data, x, y)
            self.npcs.append(npc)
            return npc
        else:
            return {"id": npc_id, "x": x, "y": y, "initialized": False}
    
    def update(self, player_position):
        """Обновляет взаимодействие и анимацию диалога"""
        # Проверяем взаимодействие со всеми NPC
        for npc in self.npcs:
            npc.show_interact_prompt = npc.check_interaction(player_position)
        
        # Обновляем анимацию диалога активного NPC
        if self.active_npc:
            self.active_npc.update_dialog()
    
    def handle_interaction(self):
        """Обрабатывает нажатие E для взаимодействия"""
        for npc in self.npcs:
            if npc.can_interact and not self.active_npc:
                if npc.start_dialog():
                    self.active_npc = npc
                    return True
        return False
    
    def start_dialog(self, npc_id):
        """Начинает диалог с NPC по ID"""
        for npc in self.npcs:
            if npc.id == npc_id:
                if npc.start_dialog():
                    self.active_npc = npc
                    return True
        return False
    
    def handle_dialog_click(self, mouse_pos):
        """Обрабатывает клики в диалоге"""
        if not self.active_npc or not self.active_npc.show_buttons:
            return False
        
        buttons = self.active_npc.current_dialog.get('button', {})
        button_height = 30
        button_width = 120
        button_spacing = 10
        
        # Позиционируем кнопки справа от текста (как в рендере)
        dialog_width = 500
        dialog_height = 180
        dialog_x = 150
        dialog_y = 280
        
        buttons_x = dialog_x + dialog_width - button_width - 20
        buttons_y = dialog_y + dialog_height - (len(buttons) * (button_height + button_spacing)) - 10
        
        for i, (button_key, button_data) in enumerate(buttons.items()):
            button_rect = pygame.Rect(
                buttons_x,
                buttons_y + i * (button_height + button_spacing),
                button_width,
                button_height
            )
            
            if button_rect.collidepoint(mouse_pos):
                continue_dialog = self.active_npc.handle_button_click(button_key, self.script_runner)
                if not continue_dialog:
                    self.active_npc = None
                return True
        
        return False
    
    def render(self, screen, camera_offset):
        """Отрисовывает всех NPC"""
        for npc in self.npcs:
            npc.render(screen, camera_offset)
    
    def render_dialog(self, screen):
        """Отрисовывает диалог активного NPC"""
        if not self.active_npc:
            return
        
        # Увеличиваем ширину диалога
        dialog_width = 500
        dialog_height = 180
        dialog_x = 150
        dialog_y = 280
        
        # Фон диалога
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(screen, (40, 40, 50), dialog_rect)
        pygame.draw.rect(screen, (100, 100, 120), dialog_rect, 2)
        
        # Имя NPC
        title_font = pygame.font.Font(None, 24)
        title_text = title_font.render(self.active_npc.name, True, (255, 215, 0))
        screen.blit(title_text, (dialog_x + 10, dialog_y + 10))
        
        # Текст диалога
        text_font = pygame.font.Font(None, 20)
        dialog_text = self.active_npc.get_current_text()
        
        # Разделяем на строки (учитываем \n и многострочные списки)
        lines = []
        if isinstance(dialog_text, str):
            lines = dialog_text.split('\n')
        
        # Отрисовка строк текста
        text_x = dialog_x + 10
        text_y = dialog_y + 40
        
        for i, line in enumerate(lines):
            if line.strip():  # Пропускаем пустые строки
                text_surface = text_font.render(line, True, (255, 255, 255))
                screen.blit(text_surface, (text_x, text_y + i * 25))
        
        # Кнопки справа от текста
        if self.active_npc.show_buttons:
            buttons = self.active_npc.current_dialog.get('button', {})
            button_height = 30
            button_width = 120
            button_spacing = 10
            
            # Позиционируем кнопки справа от текста
            buttons_x = dialog_x + dialog_width - button_width - 20
            buttons_y = dialog_y + dialog_height - (len(buttons) * (button_height + button_spacing)) - 10
            
            for i, (button_key, button_data) in enumerate(buttons.items()):
                button_rect = pygame.Rect(
                    buttons_x,
                    buttons_y + i * (button_height + button_spacing),
                    button_width,
                    button_height
                )
                
                # Фон кнопки
                pygame.draw.rect(screen, (80, 80, 100), button_rect)
                pygame.draw.rect(screen, (120, 120, 140), button_rect, 2)
                
                # Текст кнопки
                button_text = button_data.get('text', 'Button')
                text_surface = text_font.render(button_text, True, (255, 255, 255))
                text_x = button_rect.x + (button_width - text_surface.get_width()) // 2
                text_y = button_rect.y + (button_height - text_surface.get_height()) // 2
                screen.blit(text_surface, (text_x, text_y))