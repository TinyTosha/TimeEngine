import yaml
import re
import time
import pygame

class ScriptRunner:
    def __init__(self, inventory, item_loader, health_system=None, value_system=None):
        self.inventory = inventory
        self.item_loader = item_loader
        self.health_system = health_system
        self.value_system = value_system
        self.entity_manager = None
        self.quest_system = None
        self.npc_system = None
        self.map_system = None
        self.menu_system = None
        self.colors = {
            'green': '\033[32m',
            'red': '\033[31m',
            'yellow': '\033[33m',
            'purple': '\033[35m',
            'magenta': '\033[35m',
            'blue': '\033[34m',
            'cyan': '\033[36m',
            'reset': '\033[0m'
        }
        self.silent_mode = False
        self.scripts = {}
        self.executed_scripts = set()
        
        # Для неблокирующих задержек
        self.delay_active = False
        self.delay_end_time = 0
        self.delay_commands = []
        self.current_delay_index = 0
        
        # Для условных операторов
        self.if_condition = False
        self.if_skip = False
        self.if_level = 0
    
    def update(self, delta_time):
        """Обновляет состояние скриптов"""
        if self.delay_active:
            current_time = time.time()
            if current_time >= self.delay_end_time:
                self.delay_active = False
                self.continue_script_execution()
    
    def run_script(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                script_data = yaml.safe_load(file)
            
            script_id = script_data.get('id')
            script_name = script_data.get('name', 'Unknown')
            call_on_start = script_data.get('callonstart', False)
            script_content = script_data.get('script', '')
            
            if isinstance(script_content, list):
                script_content = '\n'.join(script_content)
            
            # Сохраняем скрипт
            if script_id is not None:
                self.scripts[script_id] = {
                    'name': script_name,
                    'content': script_content,
                    'callonstart': call_on_start
                }
            
            # Запускаем только если callonstart=true
            if call_on_start and script_id is not None:
                self.execute_script_content(script_content)
                self.executed_scripts.add(script_id)
            
        except Exception as e:
            if not self.silent_mode:
                print(f"{self.colors['red']}Error loading script {file_path}: {e}{self.colors['reset']}")
    
    def execute_script(self, script_id):
        """Запускает скрипт по ID"""
        if script_id in self.scripts:
            script = self.scripts[script_id]
            self.execute_script_content(script['content'])
            self.executed_scripts.add(script_id)
            return True
        return False
    
    def recall_script(self, script_id):
        """Перезапускает скрипт по ID"""
        if script_id in self.scripts:
            script = self.scripts[script_id]
            self.execute_script_content(script['content'])
            return True
        return False
    
    def execute_script_content(self, script_content):
        """Выполняет содержимое скрипта"""
        lines = script_content.split('\n')
        self.delay_commands = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        self.current_delay_index = 0
        self.execute_next_command()
    
    def execute_next_command(self):
        """Выполняет следующую команду в скрипте"""
        if self.current_delay_index < len(self.delay_commands):
            command = self.delay_commands[self.current_delay_index]
            self.current_delay_index += 1
            self.execute_command(command)
    
    def continue_script_execution(self):
        """Продолжает выполнение скрипта после задержки"""
        self.execute_next_command()
    
    def execute_command(self, command):
        try:
            # Обработка условных операторов
            if command.startswith('&'):
                self.handle_conditional(command)
                return
            
            # Если мы в режиме пропуска (условие false)
            if self.if_skip and self.if_level > 0:
                return
            
            # Обработка значений
            if command.startswith('%'):
                self.handle_value_command(command)
                return
            
            # Обработка специальных команд
            if command.startswith('@'):
                self.handle_special_command(command)
                return
            
            # Обработка обычных команд
            if command.startswith('$log.') and '(' in command and ')' in command:
                self.execute_simple_log(command)
                self.execute_next_command()
            elif command.startswith('$inventory.GiveItem'):
                self.execute_give_item(command)
                self.execute_next_command()
            elif command.startswith('$enemy.spawn'):
                self.execute_enemy_spawn(command)
                self.execute_next_command()
            elif command.startswith('$npc.spawn'):
                self.execute_npc_spawn(command)
                self.execute_next_command()
            elif command.startswith('$call.script'):
                self.execute_call_script(command)
                self.execute_next_command()
            elif command.startswith('$recall.script'):
                self.execute_recall_script(command)
                self.execute_next_command()
            elif command.startswith('$quest.Give'):
                self.execute_give_quest(command)
                self.execute_next_command()
            elif command.startswith('$quest.Cancel'):
                self.execute_cancel_quest(command)
                self.execute_next_command()
            elif command.startswith('$npc.dialog'):
                self.execute_npc_dialog(command)
                self.execute_next_command()
            elif command.startswith('$map.set'):
                self.execute_set_map(command)
                self.execute_next_command()
            elif command.startswith('!delay'):
                self.execute_delay(command)
            else:
                self.execute_next_command()
                
        except Exception as e:
            if not self.silent_mode:
                print(f"{self.colors['red']}Error executing command: {command}{self.colors['reset']}")
                print(f"Error details: {e}")
            self.execute_next_command()
    
    def handle_conditional(self, command):
        """Обрабатывает условные операторы"""
        if command == '&end':
            self.if_level = max(0, self.if_level - 1)
            if self.if_level == 0:
                self.if_skip = False
            self.execute_next_command()
            return
        
        if command.startswith('&') and ':' in command:
            self.if_level += 1
            condition = command[1:].split(':')[0].strip()
            
            # Проверяем условие с значениями
            if '>' in condition:
                parts = condition.split('>')
                left = parts[0].strip()
                right = parts[1].strip()
                
                if left.startswith('%') and '.' in left:
                    # Обработка значений %0.v
                    value_parts = left[1:].split('.')
                    value_id = int(value_parts[0])
                    left_value = self.value_system.get_value(value_id) if self.value_system else 0
                    right_value = float(right)
                    self.if_skip = not (left_value > right_value)
            
            self.execute_next_command()
    
    def handle_value_command(self, command):
        """Обрабатывает команды с значениями"""
        if '-=' in command:
            parts = command.split('-=')
            left = parts[0].strip()
            right = parts[1].strip()
            
            if left.startswith('%') and '.' in left:
                value_parts = left[1:].split('.')
                value_id = int(value_parts[0])
                amount = float(right)
                if self.value_system:
                    self.value_system.subtract_value(value_id, amount)
        
        self.execute_next_command()
    
    def handle_special_command(self, command):
        """Обрабатывает специальные команды"""
        if command == '@close.menu' and self.menu_system:
            self.menu_system.close_menu()
        elif command.startswith('@open.menu') and self.menu_system:
            match = re.search(r'@open\.menu\(([^)]+)\)', command)
            if match:
                menu_id = int(match.group(1))
                self.menu_system.open_menu(menu_id)
        elif command == '@close' and self.npc_system:
            self.npc_system.active_npc = None
        
        self.execute_next_command()
    
    def execute_delay(self, command):
        """Обрабатывает команду !delay с секундами (неблокирующая)"""
        match = re.search(r'!delay\(([\d.]+)\)', command)
        if match:
            seconds = float(match.group(1).strip())
            self.delay_active = True
            self.delay_end_time = time.time() + seconds
            
            if not self.silent_mode:
                print(f"{self.colors['blue']}⏳ Delay: {seconds}s{self.colors['reset']}")
        else:
            # Если команда не распознана, продолжаем выполнение
            self.execute_next_command()
    
    def execute_set_map(self, command):
        match = re.search(r'\$map\.set\(([^)]+)\)', command)
        if match and hasattr(self, 'map_system') and self.map_system:
            map_id = int(match.group(1).strip())
            success = self.map_system.set_map(map_id)
            if success and not self.silent_mode:
                print(f"{self.colors['green']}✓ Map {map_id} loaded{self.colors['reset']}")
    
    def execute_npc_spawn(self, command):
        match = re.search(r'\$npc\.spawn\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', command)
        if match and hasattr(self, 'npc_system') and self.npc_system:
            npc_id = int(match.group(1).strip())
            x = int(match.group(2).strip())
            y = int(match.group(3).strip())
            initialize = match.group(4).strip().lower() == 'true'
        
            result = self.npc_system.spawn_npc(npc_id, x, y, initialize)
            if result and initialize and not self.silent_mode:
                print(f"{self.colors['green']}✓ Spawned NPC {npc_id} at ({x}, {y}){self.colors['reset']}")

    def execute_npc_dialog(self, command):
        match = re.search(r'\$npc\.dialog\(([^)]+)\)', command)
        if match and hasattr(self, 'npc_system') and self.npc_system:
            npc_id = int(match.group(1).strip())
            success = self.npc_system.start_dialog(npc_id)
            if success and not self.silent_mode:
                print(f"{self.colors['blue']}✓ Started dialog with NPC {npc_id}{self.colors['reset']}")
    
    def execute_simple_log(self, command):
        match = re.search(r'\$log\.(\w+)\(["\']([^"\']+)["\']\)', command)
        if match:
            color_name = match.group(1).lower()
            message = match.group(2)
            
            color_code = self.colors.get(color_name, self.colors['reset'])
            print(f"{color_code}{message}{self.colors['reset']}")
    
    def execute_call_script(self, command):
        match = re.search(r'\$call\.script\(([^)]+)\)', command)
        if match:
            script_id = int(match.group(1).strip())
            success = self.execute_script(script_id)
            if success and not self.silent_mode:
                print(f"{self.colors['blue']}✓ Called script {script_id}{self.colors['reset']}")
    
    def execute_recall_script(self, command):
        match = re.search(r'\$recall\.script\(([^)]+)\)', command)
        if match:
            script_id = int(match.group(1).strip())
            success = self.recall_script(script_id)
            if success and not self.silent_mode:
                print(f"{self.colors['cyan']}✓ Recalled script {script_id}{self.colors['reset']}")
    
    def execute_give_quest(self, command):
        match = re.search(r'\$quest\.Give\(([^)]+)\)', command)
        if match and hasattr(self, 'quest_system') and self.quest_system:
            quest_id = int(match.group(1).strip())
            success = self.quest_system.give_quest(quest_id)
            if success and not self.silent_mode:
                print(f"{self.colors['green']}✓ Quest {quest_id} given{self.colors['reset']}")
    
    def execute_cancel_quest(self, command):
        match = re.search(r'\$quest\.Cancel\(([^)]+)\)', command)
        if match and hasattr(self, 'quest_system') and self.quest_system:
            quest_id = int(match.group(1).strip())
            success = self.quest_system.cancel_quest(quest_id)
            if success and not self.silent_mode:
                print(f"{self.colors['yellow']}✓ Quest {quest_id} canceled{self.colors['reset']}")
    
    def execute_enemy_spawn(self, command):
        match = re.search(r'\$enemy\.spawn\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', command)
        if match and hasattr(self, 'entity_manager') and self.entity_manager:
            enemy_id = int(match.group(1).strip())
            x = int(match.group(2).strip())
            y = int(match.group(3).strip())
            initialize = match.group(4).strip().lower() == 'true'
            
            result = self.entity_manager.spawn_enemy(enemy_id, x, y, initialize)
            if result and initialize and not self.silent_mode:
                print(f"{self.colors['green']}✓ Spawned enemy {enemy_id} at ({x}, {y}){self.colors['reset']}")
    
    def execute_give_item(self, command):
        match = re.search(r'\$inventory\.GiveItem\(([^,]+),\s*([^)]+)\)', command)
        if match:
            item_id = int(match.group(1).strip())
            slot_str = match.group(2).strip().lower()
            
            if slot_str == 'false':
                # Ищем свободный слот
                for slot in range(9):
                    if not self.inventory.get_item(slot):
                        success = self.inventory.give_item(item_id, slot)
                        if success and not self.silent_mode:
                            item_data = self.item_loader.get_item(item_id)
                            if item_data:
                                print(f"{self.colors['green']}✓ Item '{item_data.get('name')}' added to free slot {slot}{self.colors['reset']}")
                        return
            else:
                try:
                    slot = int(slot_str)
                    success = self.inventory.give_item(item_id, slot)
                    if success and not self.silent_mode:
                        item_data = self.item_loader.get_item(item_id)
                        if item_data:
                            print(f"{self.colors['green']}✓ Item '{item_data.get('name')}' added to slot {slot}{self.colors['reset']}")
                except ValueError:
                    if not self.silent_mode:
                        print(f"{self.colors['red']}Error: Invalid slot '{slot_str}'{self.colors['reset']}")
        
        self.execute_next_command()