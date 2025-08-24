import os
import yaml

class ValueSystem:
    def __init__(self, cache_manager):
        self.values = {}
        self.cache_manager = cache_manager
        self.load_values()
    
    def load_values(self):
        """Загружает значения из кэша"""
        self.values = self.cache_manager.load_values()
    
    def save_values(self):
        """Сохраняет значения в кэш"""
        self.cache_manager.save_values(self.values)
    
    def get_value(self, value_id):
        """Получает значение по ID"""
        if value_id in self.values:
            return self.values[value_id]['value']
        return 0
    
    def set_value(self, value_id, amount):
        """Устанавливает значение"""
        if value_id in self.values:
            value_data = self.values[value_id]
            value_data['value'] = max(value_data['min'], min(value_data['max'], amount))
            self.save_values()
            return True
        return False
    
    def add_value(self, value_id, amount):
        """Добавляет значение"""
        if value_id in self.values:
            value_data = self.values[value_id]
            new_value = value_data['value'] + amount
            value_data['value'] = max(value_data['min'], min(value_data['max'], new_value))
            self.save_values()
            return True
        return False
    
    def subtract_value(self, value_id, amount):
        """Вычитает значение"""
        return self.add_value(value_id, -amount)
    
    def format_value_text(self, text):
        """Форматирует текст с подстановкой значений %0.v"""
        import re
        pattern = r'%(\d+)\.v'
        
        def replace_match(match):
            value_id = int(match.group(1))
            return str(self.get_value(value_id))
        
        return re.sub(pattern, replace_match, text)