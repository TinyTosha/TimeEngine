import yaml
import os
import re

class ItemLoader:
    def __init__(self):
        self.items = {}
    
    def load_item(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            item_data = yaml.safe_load(file)
            
            # Обработка динамических значений
            self.process_dynamic_values(item_data)
            
            item_id = item_data.get('id')
            if item_id is not None:
                self.items[item_id] = item_data
            
            return item_data
    
    def process_dynamic_values(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self.process_dynamic_values(value)
                elif isinstance(value, str):
                    data[key] = self.parse_dynamic_value(value, data)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self.process_dynamic_values(item)
                elif isinstance(item, str):
                    data[i] = self.parse_dynamic_value(item, data)
    
    def parse_dynamic_value(self, value, context):
        if isinstance(value, str):
            # Обработка $function.nullstroke
            if value == '$function.nullstroke':
                return "\n"
            
            # Обработка $color.цвет
            color_match = re.match(r'\$color\.(\w+)', value)
            if color_match:
                return value  # Возвращаем как есть для скриптов
            
            # Обработка $stats.стат
            stat_match = re.match(r'\$stats\.(\w+)', value)
            if stat_match:
                stat_name = stat_match.group(1)
                return context.get('stats', {}).get(stat_name, value)
            
            # Обработка ссылок на другие предметы $item(id).property
            item_match = re.match(r'\$item\((\d+)\)\.(.+)', value)
            if item_match:
                item_id = int(item_match.group(1))
                property_path = item_match.group(2)
                return self.get_item_property(item_id, property_path)
        
        return value
    
    def get_item_property(self, item_id, property_path):
        item = self.items.get(item_id)
        if not item:
            return f"Item {item_id} not found"
        
        # Рекурсивный поиск свойства
        def get_nested_value(obj, path):
            parts = path.split('.')
            current = obj
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            return current
        
        result = get_nested_value(item, property_path)
        return result if result is not None else f"Property {property_path} not found"
    
    def get_item(self, item_id):
        return self.items.get(item_id)