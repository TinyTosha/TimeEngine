import yaml
import os

class ItemLoader:
    def __init__(self):
        self.items = {}
    
    def load_item(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            item_data = yaml.safe_load(file)
            
            # Обработка динамических значений
            self.process_dynamic_values(item_data)
            
            item_id = item_data.get('id', len(self.items))
            self.items[item_id] = item_data
            
            return item_data
    
    def process_dynamic_values(self, item_data):
        # Рекурсивная обработка всех значений в item_data
        def process_value(value):
            if isinstance(value, str) and value.startswith('$'):
                # Обработка динамических значений
                if value == '$function.nullstroke':
                    return "\n"
                elif value.startswith('$color.'):
                    return value.replace('$color.', '')
                elif value.startswith('$stats.'):
                    stat_name = value.replace('$stats.', '')
                    return item_data.get('stats', {}).get(stat_name, '')
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(v) for v in value]
            else:
                return value
        
        return process_value(item_data)
    
    def get_item(self, item_id):
        return self.items.get(item_id)