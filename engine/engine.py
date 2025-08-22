import pygame
import os
import yaml
import re
import shutil
import math
import time
from .item_loader import ItemLoader
from .inventory import Inventory
from .script_runner import ScriptRunner
from .cache_manager import CacheManager
from .entity_manager import EntityManager
from .health_system import HealthSystem
from .quest_system import QuestSystem
from .npc_system import NPCSystem
from .map_system import MapSystem

class Camera:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset_x = 0
        self.offset_y = 0
        self.target_x = 0
        self.target_y = 0
        self.smoothness = 0.1
    
    def update(self, target_x, target_y):
        self.target_x = target_x - self.screen_width // 2
        self.target_y = target_y - self.screen_height // 2
        
        self.offset_x += (self.target_x - self.offset_x) * self.smoothness
        self.offset_y += (self.target_y - self.offset_y) * self.smoothness
    
    def get_offset(self):
        return (int(self.offset_x), int(self.offset_y))

class Localization:
    def __init__(self, lang_code="en"):
        self.lang_code = lang_code
        self.translations = {}
        self.load_config()
        self.load_localization()
    
    def load_config(self):
        config_path = os.path.join("game", "config", "game_config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file)
                    if config and 'language' in config:
                        self.lang_code = config['language']
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def load_localization(self):
        lang_path = os.path.join("engine", "lang", f"{self.lang_code}.yaml")
        if os.path.exists(lang_path):
            try:
                with open(lang_path, 'r', encoding='utf-8') as file:
                    self.translations = yaml.safe_load(file) or {}
            except Exception as e:
                print(f"Error loading localization: {e}")
                self.translations = {}
        else:
            print(f"Localization file not found: {lang_path}")
        
        # Запасные переводы
        defaults = {
            'quest_kill': "Kill",
            'quest_progress': "Progress",
            'active_quests': "Active Quests",
            'cooldown': "Cooldown",
            'health': "Health",
            'max_health': "Max Health",
            'quest_complete': "Complete",
            'quest_cancel': "Cancel",
            'quest_reward': "Reward",
            'quest_task': "Task"
        }
        
        for key, value in defaults.items():
            if key not in self.translations:
                self.translations[key] = value
    
    def get(self, key, default=None):
        return self.translations.get(key, default or key)

class RPGEngine:
    def __init__(self, screen_width=800, screen_height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("TimeEngine v8")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.delta_time = 0
        
        # Локализация
        self.localization = Localization()
        
        # Камера
        self.camera = Camera(screen_width, screen_height)
        
        # Система здоровья
        self.health_system = HealthSystem()
        
        # Менеджер кэша
        self.cache_manager = CacheManager()
        
        # Загрузка ресурсов
        self.item_loader = ItemLoader()
        self.inventory = Inventory(self.cache_manager)
        self.script_runner = ScriptRunner(self.inventory, self.item_loader, self.health_system)
        
        # Менеджер сущностей
        self.entity_manager = EntityManager(self.script_runner)
        self.script_runner.entity_manager = self.entity_manager
        
        # Система квестов
        self.quest_system = QuestSystem(self.entity_manager, self.inventory, self.health_system, self.item_loader, self.localization, self.script_runner)
        self.script_runner.quest_system = self.quest_system
        
        # Система NPC
        self.npc_system = NPCSystem(self.script_runner)
        self.script_runner.npc_system = self.npc_system
        
        # Система карт
        self.map_system = MapSystem()
        self.script_runner.map_system = self.map_system
        
        # Игрок
        self.player = self.create_player()
        self.player_speed = 5
        
        # Выбранный предмет
        self.selected_slot = None
        self.selected_item = None
        self.item_state = "idle"
        self.attack_progress = 0
        self.attack_direction = "down"
        
        # Tooltip
        self.show_tooltip = False
        self.tooltip_item = None
        self.tooltip_mouse_pos = (0, 0)
        
        # Квест UI
        self.show_quest_details = False
        self.selected_quest_id = None
        
        # Кд для клавиш
        self.key_cooldowns = {i: 0 for i in range(1, 10)}
        self.key_cooldown_duration = 10
        
        # Загрузка предметов и скриптов
        self.load_game_data()
        self.cache_manager.load_slot_cooldowns()
        
        # Запускаем только скрипты с callonstart=true
        for script_id, script_data in self.script_runner.scripts.items():
            if script_data['callonstart'] and script_id not in self.script_runner.executed_scripts:
                self.script_runner.execute_script(script_id)
    
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
        if os.path.exists(items_path):
            for item_file in os.listdir(items_path):
                if item_file.endswith(".yaml"):
                    self.item_loader.load_item(os.path.join(items_path, item_file))
        
        # Загрузка и выполнение скриптов
        scripts_path = os.path.join("game", "scripts")
        if os.path.exists(scripts_path):
            for script_file in os.listdir(scripts_path):
                if script_file.endswith(".yaml"):
                    self.script_runner.run_script(os.path.join(scripts_path, script_file))
    
    def format_stat_name(self, stat_name):
        """Форматирует название статы: damage -> Damage, magic_power -> Magic Power"""
        # Специальные случаи
        special_cases = {
            'damage': 'Damage',
            'dmg': 'Damage',
            'atk': 'Attack',
            'def': 'Defense',
            'hp': 'HP',
            'health': 'Health',
            'mp': 'MP',
            'mana': 'Mana',
            'xp': 'XP',
            'exp': 'Experience',
            'str': 'Strength',
            'dex': 'Dexterity',
            'int': 'Intelligence',
            'vit': 'Vitality',
            'agi': 'Agility',
            'luk': 'Luck',
            'crit': 'Critical Chance',
            'crit_dmg': 'Critical Damage',
            'atk_spd': 'Attack Speed',
            'move_spd': 'Movement Speed',
            'cooldown': 'Cooldown',
            'cd': 'Cooldown',
            'res': 'Resistance',
            'elem_res': 'Elemental Resistance',
            'phys_res': 'Physical Resistance',
            'mag_res': 'Magic Resistance'
        }
        
        # Проверяем специальные случаи
        if stat_name in special_cases:
            return special_cases[stat_name]
        
        # Заменяем подчеркивания на пробелы
        words = stat_name.split('_')
        formatted_words = []
        
        for word in words:
            if word:
                # Пропускаем сокращения типа "mp", "hp" и т.д.
                if len(word) <= 2 and word.isalpha():
                    formatted_word = word.upper()
                else:
                    # Делаем первую букву заглавной, остальные строчными
                    formatted_word = word[0].upper() + word[1:].lower()
                formatted_words.append(formatted_word)
        
        return ' '.join(formatted_words)
    
    def get_item_damage(self, item_data):
        """Получает урон предмета из разных возможных мест"""
        # Пробуем получить урон из stats.damage
        damage = item_data.get('stats', {}).get('damage')
        if damage is not None:
            return damage
        
        # Пробуем получить урон из type.damage
        damage = item_data.get('type', {}).get('damage')
        if damage is not None:
            return damage
        
        # Пробуем получить урон из корня предмета
        damage = item_data.get('damage')
        if damage is not None:
            return damage
        
        # Урон по умолчанию
        return 10
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Движение игрока с учетом коллизий
        new_x, new_y = self.player["rect"].x, self.player["rect"].y
        
        if keys[pygame.K_w]:
            new_y -= self.player_speed
        if keys[pygame.K_s]:
            new_y += self.player_speed
        if keys[pygame.K_a]:
            new_x -= self.player_speed
        if keys[pygame.K_d]:
            new_x += self.player_speed
        
        # Применяем движение с проверкой коллизий
        self.map_system.update_player_position(self.player["rect"], new_x, new_y)
        
        # Взаимодействие с NPC по нажатию E
        if keys[pygame.K_e] and not self.npc_system.active_npc:
            self.npc_system.handle_interaction()
        
        # Обновляем кд клавиш
        for key in self.key_cooldowns:
            if self.key_cooldowns[key] > 0:
                self.key_cooldowns[key] -= 1
        
        # Выбор предметов с кд
        if any(self.key_cooldowns[key] <= 0 for key in self.key_cooldowns):
            for i in range(9):
                key = i + 1
                if keys[getattr(pygame, f'K_{key}')] and self.key_cooldowns[key] <= 0:
                    self.toggle_slot(i)
                    self.key_cooldowns[key] = self.key_cooldown_duration
                    break
        
        # Атака ЛКМ
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] and self.selected_item and self.get_current_cooldown() <= 0 and self.item_state == "idle":
            item_data = self.item_loader.get_item(self.selected_item['id'])
            if item_data and item_data.get('type', {}).get('sword'):
                self.start_attack()
        
        # Обновляем кд
        self.cache_manager.update_cooldowns()
        
        # Обновляем сущности
        player_pos = [self.player["rect"].centerx, self.player["rect"].centery]
        self.entity_manager.update(player_pos, self.health_system, self.delta_time)
        
        # Обновляем квесты
        self.quest_system.update_quests()
        
        # Обновляем NPC с позицией игрока
        self.npc_system.update(player_pos)
        
        # Обновляем камеру
        self.camera.update(self.player["rect"].centerx, self.player["rect"].centery)
        
        # Обработка анимации атаки
        if self.item_state == "attacking":
            self.handle_attack_animation()
        
        # Проверка наведения на предметы в инвентаре
        self.check_tooltip()
        
        # Проверка кликов по квестам
        self.check_quest_clicks()
    
    def check_quest_clicks(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        
        if mouse_click[0]:  # ЛКМ
            # Проверяем клик по логу квестов
            quest_log_rect = pygame.Rect(600, 20, 180, 150)
            if quest_log_rect.collidepoint(mouse_pos):
                self.show_quest_details = True
                
                # Определяем какой квест выбран
                y_offset = 40
                for quest_id in self.quest_system.active_quests.keys():
                    quest_rect = pygame.Rect(600, 20 + y_offset, 180, 40)
                    if quest_rect.collidepoint(mouse_pos):
                        self.selected_quest_id = quest_id
                        break
                    y_offset += 60
            
            # Проверяем клик по кнопке отмены квеста
            if self.show_quest_details and self.selected_quest_id:
                cancel_rect = pygame.Rect(200 + 400 - 100, 100 + 300 - 40, 80, 30)
                if cancel_rect.collidepoint(mouse_pos):
                    self.quest_system.cancel_quest(self.selected_quest_id)
                    self.show_quest_details = False
                    self.selected_quest_id = None
    
    def check_tooltip(self):
        mouse_pos = pygame.mouse.get_pos()
        self.show_tooltip = False
        self.tooltip_item = None
        
        # Проверяем, находится ли мышь над инвентарем
        inventory_bg = pygame.Rect(10, 500, 60 * 9 + 20, 80)
        if inventory_bg.collidepoint(mouse_pos):
            # Проверяем конкретные слоты
            for i in range(9):
                slot_rect = pygame.Rect(20 + i * 60, 510, 50, 50)
                if slot_rect.collidepoint(mouse_pos):
                    item = self.inventory.get_item(i)
                    if item:
                        item_data = self.item_loader.get_item(item['id'])
                        if item_data:
                            self.show_tooltip = True
                            self.tooltip_item = item_data
                            self.tooltip_mouse_pos = mouse_pos
                            break
    
    def get_current_cooldown(self):
        if self.selected_slot is not None:
            return self.cache_manager.get_slot_cooldown(self.selected_slot)
        return 0
    
    def toggle_slot(self, slot):
        item = self.inventory.get_item(slot)
        
        if self.selected_slot == slot:
            self.selected_slot = None
            self.selected_item = None
            self.item_state = "idle"
        elif item:
            if self.selected_slot is not None:
                previous_cooldown = self.get_current_cooldown()
                if previous_cooldown > 0:
                    self.cache_manager.save_slot_cooldown(self.selected_slot, previous_cooldown)
            
            self.selected_slot = slot
            self.selected_item = item
            self.item_state = "idle"
    
    def start_attack(self):
        self.item_state = "attacking"
        self.attack_progress = 0
        self.attack_direction = "down"
        
        # Проверяем попадание атаки
        if self.selected_item:
            item_data = self.item_loader.get_item(self.selected_item['id'])
            if item_data and item_data.get('type', {}).get('sword'):
                # ПРАВИЛЬНОЕ ПОЛУЧЕНИЕ УРОНА
                damage = self.get_item_damage(item_data)
                attack_range = 80
                player_center = [self.player["rect"].centerx, self.player["rect"].centery]
                
                # Проверяем попадание по врагам
                hits = self.entity_manager.check_attack_hit(player_center, attack_range, damage)
                if hits:
                    # Обновляем квесты при убийстве врагов
                    for enemy in hits:
                        self.quest_system.register_kill(enemy.id)
    
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
                
                if self.selected_slot is not None:
                    self.cache_manager.save_slot_cooldown(self.selected_slot, cooldown_frames)
    
    def cleanup(self):
        cache_dir = "engine/cache"
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
    
    def render(self):
        self.screen.fill((30, 30, 40))
        
        camera_offset = self.camera.get_offset()
        
        # Отрисовываем карту
        self.map_system.render(self.screen, camera_offset)
        
        # Отрисовка сущностей с учетом камеры
        self.entity_manager.render(self.screen, camera_offset)
        
        # Отрисовка NPC с учетом камеры
        self.npc_system.render(self.screen, camera_offset)
        
        # Отрисовка игрока с учетом камеры
        player_x = self.player["rect"].x - camera_offset[0]
        player_y = self.player["rect"].y - camera_offset[1]
        
        if self.player["texture"]:
            self.screen.blit(self.player["texture"], (player_x, player_y))
        else:
            pygame.draw.rect(self.screen, (0, 0, 255), (player_x, player_y, 50, 50))
        
        # Отрисовка выбранного предмета с учетом камеры
        if self.selected_item:
            self.render_selected_item(camera_offset)
        
        # Отрисовка инвентаря
        self.inventory.render(self.screen, self.item_loader, self.selected_slot)
        
        # Отрисовка UI здоровья
        self.health_system.render(self.screen)
        
        # Отображение имени выбранного предмета
        if self.selected_item:
            self.render_selected_item_name()
        
        # Отображение текущего кд
        cooldown = self.get_current_cooldown()
        if cooldown > 0:
            cooldown_font = pygame.font.Font(None, 24)
            cooldown_text = cooldown_font.render(f"{self.localization.get('cooldown')}: {cooldown/60:.1f}s", True, (255, 0, 0))
            self.screen.blit(cooldown_text, (10, 450))
        
        # Отрисовка тултипа
        if self.show_tooltip and self.tooltip_item:
            self.render_tooltip()
        
        # Отрисовка лога квестов
        self.quest_system.render_quest_log(self.screen)
        
        # Отрисовка деталей квеста если выбрано
        if self.show_quest_details and self.selected_quest_id:
            self.render_quest_details()
        
        # Отрисовка диалога NPC
        self.npc_system.render_dialog(self.screen)
        
        pygame.display.flip()
    
    def render_selected_item_name(self):
        item_data = self.item_loader.get_item(self.selected_item['id'])
        if item_data:
            item_name = item_data.get('name', 'Unknown Item')
            name_font = pygame.font.Font(None, 30)
            name_text = name_font.render(item_name, True, (255, 255, 255))
            self.screen.blit(name_text, (10, 480))
    
    def render_quest_details(self):
        quest = self.quest_system.quests.get(self.selected_quest_id)
        if not quest:
            return
        
        # Позиция и размер деталей квеста
        details_x = 200
        details_y = 100
        details_width = 400
        details_height = 300
        
        # Фон
        details_rect = pygame.Rect(details_x, details_y, details_width, details_height)
        pygame.draw.rect(self.screen, (40, 40, 50), details_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), details_rect, 2)
        
        # Шрифты
        title_font = pygame.font.Font(None, 28)
        desc_font = pygame.font.Font(None, 20)
        section_font = pygame.font.Font(None, 22)
        section_font.set_bold(True)
        
        padding = 20
        y_offset = padding
        
        # Заголовок
        title = quest.get('name', 'Unknown Quest')
        title_surface = title_font.render(title, True, (255, 215, 0))
        self.screen.blit(title_surface, (details_x + padding, details_y + y_offset))
        y_offset += 40
        
        # Описание
        desc_lines = quest.get('desc', [])
        if isinstance(desc_lines, str):
            desc_lines = [desc_lines]
        
        for line in desc_lines:
            desc_surface = desc_font.render(line, True, (200, 200, 200))
            self.screen.blit(desc_surface, (details_x + padding, details_y + y_offset))
            y_offset += 25
        
        y_offset += 10
        
        # Задачи
        task_surface = section_font.render(f"{self.localization.get('quest_task')}:", True, (255, 255, 255))
        self.screen.blit(task_surface, (details_x + padding, details_y + y_offset))
        y_offset += 30
        
        quest_data = self.quest_system.active_quests.get(self.selected_quest_id, {})
        task_progress = quest_data.get('progress', {})
        
        for task_id, task_info in task_progress.items():
            if task_info['type'] == 'kill':
                enemy_id = task_info['enemy_id']
                required_count = task_info['required']
                current_count = task_info['current']
                
                enemy_name = f"Enemy {enemy_id}"
                enemy_template = self.entity_manager.enemy_templates.get(enemy_id)
                if enemy_template:
                    enemy_name = enemy_template.get('name', f"Enemy {enemy_id}")
                
                task_text = f"{self.localization.get('quest_kill')} {enemy_name} ({current_count}/{required_count})"
                task_surface = desc_font.render(task_text, True, (200, 200, 200))
                self.screen.blit(task_surface, (details_x + padding, details_y + y_offset))
                y_offset += 25
        
        y_offset += 10
        
        # Награды
        reward_surface = section_font.render(f"{self.localization.get('quest_reward')}:", True, (255, 255, 255))
        self.screen.blit(reward_surface, (details_x + padding, details_y + y_offset))
        y_offset += 30
        
        rewards = quest.get('quest_reward', [])
        for reward in rewards:
            if reward.startswith('!quest_reward_addmaxhealth('):
                match = re.search(r'!quest_reward_addmaxhealth\((\d+)\)', reward)
                if match:
                    amount = int(match.group(1))
                    reward_text = f"+{amount} {self.localization.get('max_health')}"
                    reward_surface = desc_font.render(reward_text, True, (0, 255, 0))
                    self.screen.blit(reward_surface, (details_x + padding, details_y + y_offset))
                    y_offset += 25
            
            elif reward.startswith('!quest_reward_giveitem('):
                match = re.search(r'!quest_reward_giveitem\((\d+)\)', reward)
                if match:
                    item_id = int(match.group(1))
                    item_data = self.item_loader.get_item(item_id)
                    item_name = item_data.get('name', f"Item {item_id}") if item_data else f"Item {item_id}"
                    reward_text = f"Get {item_name}"
                    reward_surface = desc_font.render(reward_text, True, (0, 255, 0))
                    self.screen.blit(reward_surface, (details_x + padding, details_y + y_offset))
                    y_offset += 25
        
        # Кнопка отмены квеста
        cancel_rect = pygame.Rect(details_x + details_width - 100, details_y + details_height - 40, 80, 30)
        pygame.draw.rect(self.screen, (200, 50, 50), cancel_rect)
        cancel_font = pygame.font.Font(None, 16)
        cancel_text = cancel_font.render("Cancel", True, (255, 255, 255))
        self.screen.blit(cancel_text, (cancel_rect.x + 20, cancel_rect.y + 8))
        
        # Кнопка закрытия
        close_rect = pygame.Rect(details_x + details_width - 40, details_y + 10, 30, 30)
        pygame.draw.rect(self.screen, (255, 0, 0), close_rect)
        close_font = pygame.font.Font(None, 24)
        close_text = close_font.render("X", True, (255, 255, 255))
        self.screen.blit(close_text, (close_rect.x + 10, close_rect.y + 5))
    
    def render_tooltip(self):
        item_data = self.tooltip_item
        if not item_data:
            return
        
        mouse_x, mouse_y = self.tooltip_mouse_pos
        
        # Шрифты
        title_font = pygame.font.Font(None, 24)
        desc_font = pygame.font.Font(None, 18)
        stat_font = pygame.font.Font(None, 18)
        stat_font.set_bold(True)
        
        # Рассчитываем размер тултипа
        padding = 10
        max_width = 250
        line_height = 20
        
        # Заголовок
        title = item_data.get('name', 'Unknown Item')
        title_width = title_font.size(title)[0]
        
        # Описание
        desc_lines = item_data.get('desc', [])
        if isinstance(desc_lines, str):
            desc_lines = [desc_lines]
        
        desc_width = 0
        for line in desc_lines:
            if line.strip():
                line_width = desc_font.size(line)[0]
                desc_width = max(desc_width, line_width)
        
        # Статы - форматируем названия
        stats = item_data.get('stats', {})
        stat_width = 0
        formatted_stats = {}
        
        for stat_name, stat_value in stats.items():
            # Форматируем название статы
            formatted_name = self.format_stat_name(stat_name)
            formatted_stats[formatted_name] = stat_value
            stat_text = f"{formatted_name}: {stat_value}"
            line_width = stat_font.size(stat_text)[0]
            stat_width = max(stat_width, line_width)
        
        # Итоговый размер
        tooltip_width = min(max(title_width, desc_width, stat_width) + padding * 2, max_width)
        tooltip_height = padding * 2 + 30 + len(desc_lines) * line_height + len(formatted_stats) * line_height
        
        # Позиция тултипа
        tooltip_x = mouse_x + 20
        tooltip_y = mouse_y + 20
        
        if tooltip_x + tooltip_width > self.screen.get_width():
            tooltip_x = mouse_x - tooltip_width - 20
        if tooltip_y + tooltip_height > self.screen.get_height():
            tooltip_y = mouse_y - tooltip_height - 20
        
        # Фон тултипа
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(self.screen, (40, 40, 50), tooltip_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), tooltip_rect, 2)
        
        # Заголовок
        title_surface = title_font.render(title, True, (255, 255, 255))
        self.screen.blit(title_surface, (tooltip_x + padding, tooltip_y + padding))
        
        y_offset = padding + 30
        
        # Описание
        for line in desc_lines:
            if line.strip():
                # Перенос строки если нужно
                if desc_font.size(line)[0] > tooltip_width - padding * 2:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        test_line = current_line + word + " "
                        if desc_font.size(test_line)[0] < tooltip_width - padding * 2:
                            current_line = test_line
                        else:
                            if current_line:
                                desc_surface = desc_font.render(current_line, True, (200, 200, 200))
                                self.screen.blit(desc_surface, (tooltip_x + padding, tooltip_y + y_offset))
                                y_offset += line_height
                            current_line = word + " "
                    if current_line:
                        desc_surface = desc_font.render(current_line, True, (200, 200, 200))
                        self.screen.blit(desc_surface, (tooltip_x + padding, tooltip_y + y_offset))
                        y_offset += line_height
                else:
                    desc_surface = desc_font.render(line, True, (200, 200, 200))
                    self.screen.blit(desc_surface, (tooltip_x + padding, tooltip_y + y_offset))
                    y_offset += line_height
        
        # Статы (без звездочек, с форматированными названиями)
        if formatted_stats:
            y_offset += 5
            for stat_name, stat_value in formatted_stats.items():
                stat_text = f"{stat_name}: {stat_value}"
                stat_surface = stat_font.render(stat_text, True, (255, 215, 0))
                self.screen.blit(stat_surface, (tooltip_x + padding, tooltip_y + y_offset))
                y_offset += line_height
    
    def render_selected_item(self, camera_offset):
        item_data = self.item_loader.get_item(self.selected_item['id'])
        if not item_data:
            return
        
        texture_config = item_data.get('texture', {})
        world_size = texture_config.get('world_size', [50, 50])
        if not isinstance(world_size, list) or len(world_size) != 2:
            world_size = [50, 50]
        
        texture_name = texture_config.get('texture')
        if texture_name:
            texture_path = os.path.join("game", "textures", texture_name)
            if os.path.exists(texture_path):
                item_texture = pygame.image.load(texture_path).convert_alpha()
                item_texture = pygame.transform.scale(item_texture, (world_size[0], world_size[1]))
                
                player_center = [
                    self.player["rect"].centerx - camera_offset[0],
                    self.player["rect"].centery - camera_offset[1]
                ]
                
                offset_x, offset_y = self.calculate_item_position(item_data)
                
                item_pos = (player_center[0] - world_size[0]//2 + offset_x, 
                           player_center[1] - world_size[1]//2 + offset_y)
                
                self.screen.blit(item_texture, item_pos)
    
    def calculate_item_position(self, item_data):
        offset_x, offset_y = 40, 0
        
        if self.item_state == "attacking":
            if self.attack_direction == "down":
                offset_y = int(60 * self.attack_progress)
            else:
                offset_y = int(60 * self.attack_progress)
        
        return offset_x, offset_y
    
    def run(self):
        try:
            while self.running:
                self.delta_time = self.clock.tick(60) / 1000.0
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            # Проверяем клик по диалогу NPC
                            if self.npc_system.handle_dialog_click(event.pos):
                                continue
                            
                            # Проверяем клик по кнопке закрытия квеста
                            if self.show_quest_details and self.selected_quest_id:
                                close_rect = pygame.Rect(200 + 400 - 40, 100 + 10, 30, 30)
                                if close_rect.collidepoint(event.pos):
                                    self.show_quest_details = False
                                    self.selected_quest_id = None
                                    continue
                                
                                # Проверяем клик по кнопке отмены квеста
                                cancel_rect = pygame.Rect(200 + 400 - 100, 100 + 300 - 40, 80, 30)
                                if cancel_rect.collidepoint(event.pos):
                                    self.quest_system.cancel_quest(self.selected_quest_id)
                                    self.show_quest_details = False
                                    self.selected_quest_id = None
                                    continue
                            
                            if self.selected_item and self.get_current_cooldown() <= 0 and self.item_state == "idle":
                                item_data = self.item_loader.get_item(self.selected_item['id'])
                                if item_data and item_data.get('type', {}).get('sword'):
                                    self.start_attack()
                
                self.handle_input()
                self.render()
        
        finally:
            self.cleanup()
            pygame.quit()