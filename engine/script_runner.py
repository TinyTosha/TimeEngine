import yaml
import re

class ScriptRunner:
    def __init__(self, inventory):
        self.inventory = inventory
    
    def run_script(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            script_data = yaml.safe_load(file)
        
        script_content = script_data.get('script', '')
        if isinstance(script_content, list):
            script_content = '\n'.join(script_content)
        
        # Выполнение команд скрипта
        self.execute_commands(script_content)
    
    def execute_commands(self, script):
        lines = script.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('$inventory.GiveItem'):
                self.execute_give_item(line)
            elif line.startswith('$log.'):
                self.execute_log(line)
    
    def execute_give_item(self, command):
        # Парсинг команды: $inventory.GiveItem(Blade, 0, 1)
        match = re.search(r'\$inventory\.GiveItem\(([^,]+),\s*([^,]+),\s*([^)]+)\)', command)
        if match:
            item_name = match.group(1).strip()
            item_id = int(match.group(2).strip())
            slot = int(match.group(3).strip())
            
            self.inventory.give_item(item_name, item_id, slot)
    
    def execute_log(self, command):
        # Парсинг команды: $log.green("Blade with id 0 gived to player in slot 1")
        match = re.search(r'\$log\.(\w+)\(["\']([^"\']+)["\']\)', command)
        if match:
            color = match.group(1)
            message = match.group(2)
            print(f"[{color.upper()}] {message}")