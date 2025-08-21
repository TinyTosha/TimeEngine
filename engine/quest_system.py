import pygame
import os
import yaml
import re

class QuestSystem:
    def __init__(self, entity_manager, inventory, health_system, item_loader, localization, script_runner):
        self.entity_manager = entity_manager
        self.inventory = inventory
        self.health_system = health_system
        self.item_loader = item_loader
        self.localization = localization
        self.script_runner = script_runner
        self.quests = {}
        self.active_quests = {}
        self.completed_quests = set()
        self.kill_counter = {}  # Счетчик убийств по ID врагов
        self.load_quests()
    
    def load_quests(self):
        quests_path = os.path.join("game", "quests")
        if os.path.exists(quests_path):
            for quest_file in os.listdir(quests_path):
                if quest_file.endswith(".yaml"):
                    file_path = os.path.join(quests_path, quest_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            quest_data = yaml.safe_load(file)
                            quest_id = quest_data.get('id')
                            if quest_id is not None:
                                self.quests[quest_id] = quest_data
                    except Exception as e:
                        print(f"Error loading quest {quest_file}: {e}")
    
    def give_quest(self, quest_id):
        if quest_id in self.quests and quest_id not in self.active_quests and quest_id not in self.completed_quests:
            # Инициализируем прогресс для всех задач квеста
            quest = self.quests[quest_id]
            tasks = quest.get('quest_task', [])
            task_progress = {}
            
            for i, task in enumerate(tasks):
                if task.startswith('!quest_kill('):
                    match = re.search(r'!quest_kill\((\d+),\s*(\d+)\)', task)
                    if match:
                        enemy_id = int(match.group(1))
                        task_progress[i] = {
                            'type': 'kill',
                            'enemy_id': enemy_id,
                            'required': int(match.group(2)),
                            'current': 0
                        }
            
            self.active_quests[quest_id] = {
                'progress': task_progress,
                'completed': False
            }
            print(f"\033[34m[i] Quest '{self.quests[quest_id].get('name')}' started!\033[0m")
            return True
        return False
    
    def cancel_quest(self, quest_id):
        if quest_id in self.active_quests:
            quest_name = self.quests[quest_id].get('name', 'Unknown Quest')
            del self.active_quests[quest_id]
            print(f"\033[34m[i] Quest '{quest_name}' canceled!\033[0m")
            return True
        return False
    
    def register_kill(self, enemy_id):
        """Регистрирует убийство врага и обновляет прогресс квестов"""
        if enemy_id not in self.kill_counter:
            self.kill_counter[enemy_id] = 0
        self.kill_counter[enemy_id] += 1
        
        # Обновляем прогресс всех активных квестов
        for quest_id, quest_data in self.active_quests.items():
            if not quest_data['completed']:
                self.update_quest_progress(quest_id, enemy_id)
    
    def update_quest_progress(self, quest_id, enemy_id):
        quest_data = self.active_quests[quest_id]
        
        for task_id, task_info in quest_data['progress'].items():
            if task_info['type'] == 'kill' and task_info['enemy_id'] == enemy_id:
                current_kills = self.kill_counter.get(enemy_id, 0)
                task_info['current'] = min(current_kills, task_info['required'])
                
                # Логируем прогресс
                enemy_name = f"Enemy {enemy_id}"
                enemy_template = self.entity_manager.enemy_templates.get(enemy_id)
                if enemy_template:
                    enemy_name = enemy_template.get('name', f"Enemy {enemy_id}")
                
                print(f"\033[34m[i] Quest progress: {enemy_name} ({task_info['current']}/{task_info['required']})\033[0m")
    
    def update_quests(self):
        for quest_id in list(self.active_quests.keys()):
            quest_data = self.active_quests[quest_id]
            if not quest_data['completed'] and self.check_quest_completion(quest_id):
                self.complete_quest(quest_id)
    
    def check_quest_completion(self, quest_id):
        quest_data = self.active_quests[quest_id]
        
        # Проверяем completion всех задач
        all_tasks_completed = True
        for task_info in quest_data['progress'].values():
            if task_info['current'] < task_info['required']:
                all_tasks_completed = False
                break
        
        return all_tasks_completed
    
    def complete_quest(self, quest_id):
        quest = self.quests.get(quest_id)
        if not quest:
            return
        
        # Выдаем награды
        rewards = quest.get('quest_reward', [])
        for reward in rewards:
            self.process_reward(reward)
        
        # Помечаем как завершенный
        self.completed_quests.add(quest_id)
        if quest_id in self.active_quests:
            del self.active_quests[quest_id]
        
        print(f"\033[34m[i] Quest '{quest.get('name')}' completed! Rewards given.\033[0m")
    
    def process_reward(self, reward):
        if reward.startswith('!quest_reward_addmaxhealth('):
            match = re.search(r'!quest_reward_addmaxhealth\((\d+)\)', reward)
            if match:
                amount = int(match.group(1))
                self.health_system.max_health += amount
                self.health_system.heal(amount)
        
        elif reward.startswith('!quest_reward_giveitem('):
            match = re.search(r'!quest_reward_giveitem\((\d+)\)', reward)
            if match:
                item_id = int(match.group(1))
                # Находим свободный слот
                for slot in range(9):
                    if not self.inventory.get_item(slot):
                        self.inventory.give_item(item_id, slot)
                        break
    
    def render_quest_log(self, screen):
        if not self.active_quests:
            return
        
        quest_log_x = 600
        quest_log_y = 20
        quest_log_width = 180
        line_height = 20
        
        # Фон лога квестов
        log_bg = pygame.Rect(quest_log_x, quest_log_y, quest_log_width, 150)
        pygame.draw.rect(screen, (40, 40, 50), log_bg)
        pygame.draw.rect(screen, (100, 100, 120), log_bg, 2)
        
        # Заголовок
        font = pygame.font.Font(None, 20)
        title = font.render(f"{self.localization.get('active_quests')}:", True, (255, 255, 255))
        screen.blit(title, (quest_log_x + 10, quest_log_y + 10))
        
        y_offset = 40
        
        for quest_id, quest_data in self.active_quests.items():
            quest = self.quests.get(quest_id)
            if quest:
                # Название квеста
                name_font = pygame.font.Font(None, 16)
                name_text = name_font.render(quest['name'], True, (255, 215, 0))
                screen.blit(name_text, (quest_log_x + 10, quest_log_y + y_offset))
                y_offset += line_height
                
                # Прогресс квеста
                for task_info in quest_data['progress'].values():
                    if task_info['type'] == 'kill':
                        enemy_id = task_info['enemy_id']
                        enemy_name = f"Enemy {enemy_id}"
                        enemy_template = self.entity_manager.enemy_templates.get(enemy_id)
                        if enemy_template:
                            enemy_name = enemy_template.get('name', f"Enemy {enemy_id}")
                        
                        progress_text = name_font.render(
                            f"{self.localization.get('quest_kill')} {enemy_name} ({task_info['current']}/{task_info['required']})", 
                            True, (200, 200, 200)
                        )
                        screen.blit(progress_text, (quest_log_x + 10, quest_log_y + y_offset))
                        y_offset += line_height
                
                y_offset += 5