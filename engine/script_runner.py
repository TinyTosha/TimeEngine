import yaml
import re
import pygame
import time

class ScriptRunner:
    def __init__(self, inventory, item_loader):
        self.inventory = inventory
        self.item_loader = item_loader
        self.colors = {
            'black': '\033[30m', 'red': '\033[31m', 'green': '\033[32m',
            'yellow': '\033[33m', 'blue': '\033[34m', 'magenta': '\033[35m',
            'cyan': '\033[36m', 'white': '\033[37m', 'gray': '\033[90m',
            'reset': '\033[0m'
        }
    
    def run_script(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            script_data = yaml.safe_load(file)
        
        script_content = script_data.get('script', '')
        if isinstance(script_content, list):
            script_content = '\n'.join(script_content)
        
        self.execute_commands(script_content)
    
    def execute_commands(self, script):
        lines = script.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):  # Пропускаем комментарии и пустые строки
                self.execute_command(line)
    
    def execute_command(self, command):
        try:
            if command.startswith('$inventory.GiveItem'):
                self.execute_give_item(command)
            elif command.startswith('$log.'):
                self.execute_log(command)
            elif command.startswith('$function.'):
                self.execute_function(command)
        except Exception as e:
            print(f"{self.colors['red']}Error executing command: {command}{self.colors['reset']}")
            print(f"{self.colors['red']}Error: {e}{self.colors['reset']}")
    
    def execute_give_item(self, command):
        # Новый формат: $inventory.GiveItem(item_id, slot)
        match = re.search(r'\$inventory\.GiveItem\(([^,]+),\s*([^)]+)\)', command)
        if match:
            item_id = int(match.group(1).strip())
            slot = int(match.group(2).strip())
            
            self.inventory.give_item(item_id, slot)
            item_data = self.item_loader.get_item(item_id)
            if item_data:
                print(f"{self.colors['green']}Item '{item_data.get('name')}' added to slot {slot}!{self.colors['reset']}")
    
    def execute_log(self, command):
        match = re.search(r'\$log\.(\w+)\(["\']([^"\']+)["\']\)', command)
        if match:
            color_name = match.group(1).lower()
            message = match.group(2)
            
            color_code = self.colors.get(color_name, self.colors['white'])
            print(f"{color_code}{message}{self.colors['reset']}")
    
    def execute_function(self, command):
        if command == '$function.nullstroke':
            print()  # Пустая строка
        elif command.startswith('$function.delay'):
            match = re.search(r'\$function\.delay\((\d+)\)', command)
            if match:
                delay_ms = int(match.group(1))
                time.sleep(delay_ms / 1000)