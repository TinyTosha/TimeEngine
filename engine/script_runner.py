import yaml
import re
import time

class ScriptRunner:
    def __init__(self, inventory, item_loader, health_system=None, entity_manager=None, quest_system=None):
        self.inventory = inventory
        self.item_loader = item_loader
        self.health_system = health_system
        self.entity_manager = entity_manager
        self.quest_system = quest_system
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
        lines = script_content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                self.execute_command(line)
    
    def execute_command(self, command):
        try:
            if command.startswith('$log.') and '(' in command and ')' in command:
                self.execute_simple_log(command)
            elif command.startswith('$inventory.GiveItem'):
                self.execute_give_item(command)
            elif command.startswith('$function.'):
                self.execute_function(command)
            elif command.startswith('$enemy.spawn'):
                self.execute_enemy_spawn(command)
            elif command.startswith('$npc.spawn'):
                self.execute_npc_spawn(command)
            elif command.startswith('$call.script'):
                self.execute_call_script(command)
            elif command.startswith('$recall.script'):
                self.execute_recall_script(command)
            elif command.startswith('$quest.Give'):
                self.execute_give_quest(command)
            elif command.startswith('$quest.Cancel'):
                self.execute_cancel_quest(command)
            elif command.startswith('$npc.dialog'):
                self.execute_npc_dialog(command)
        except Exception as e:
            if not self.silent_mode:
                print(f"{self.colors['red']}Error executing command: {command}{self.colors['reset']}")
    
    def execute_npc_spawn(self, command):
        match = re.search(r'\$npc\.spawn\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', command)
        if match and hasattr(self, 'npc_system'):
            npc_id = int(match.group(1).strip())
            x = int(match.group(2).strip())
            y = int(match.group(3).strip())
            initialize = match.group(4).strip().lower() == 'true'
        
            result = self.npc_system.spawn_npc(npc_id, x, y, initialize)
            if result and initialize and not self.silent_mode:
                print(f"{self.colors['green']}✓ Spawned NPC {npc_id} at ({x}, {y}){self.colors['reset']}")

    def execute_npc_dialog(self, command):
        match = re.search(r'\$npc\.dialog\(([^)]+)\)', command)
        if match and hasattr(self, 'npc_system'):
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
        if match and self.quest_system:
            quest_id = int(match.group(1).strip())
            success = self.quest_system.give_quest(quest_id)
            if success and not self.silent_mode:
                print(f"{self.colors['green']}✓ Quest {quest_id} given{self.colors['reset']}")
    
    def execute_cancel_quest(self, command):
        match = re.search(r'\$quest\.Cancel\(([^)]+)\)', command)
        if match and self.quest_system:
            quest_id = int(match.group(1).strip())
            success = self.quest_system.cancel_quest(quest_id)
            if success and not self.silent_mode:
                print(f"{self.colors['yellow']}✓ Quest {quest_id} canceled{self.colors['reset']}")
    
    def execute_enemy_spawn(self, command):
        match = re.search(r'\$enemy\.spawn\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', command)
        if match and self.entity_manager:
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
            slot = int(match.group(2).strip())
            
            success = self.inventory.give_item(item_id, slot)
            if success and not self.silent_mode:
                item_data = self.item_loader.get_item(item_id)
                if item_data:
                    print(f"{self.colors['green']}✓ Item '{item_data.get('name')}' added to slot {slot}{self.colors['reset']}")
    
    def execute_function(self, command):
        if command == '$function.nullstroke':
            if not self.silent_mode:
                print()
        elif command.startswith('$function.delay'):
            match = re.search(r'\$function\.delay\((\d+)\)', command)
            if match:
                delay_ms = int(match.group(1))
                time.sleep(delay_ms / 1000)