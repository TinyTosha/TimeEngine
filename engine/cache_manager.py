import os
import yaml

class CacheManager:
    def __init__(self, cache_dir="engine/cache"):
        self.cache_dir = cache_dir
        self.slot_cooldowns = {}
        self.values_cache = {}
    
    def save_slot_cooldown(self, slot, cooldown):
        """Сохраняет кд для слота"""
        self.slot_cooldowns[slot] = cooldown
        
        # Сохраняем в файл
        cooldown_data = {
            'slot': slot,
            'cooldown': cooldown
        }
        
        # Создаем папку если не существует
        os.makedirs(self.cache_dir, exist_ok=True)
        
        file_path = os.path.join(self.cache_dir, f"slot_{slot}_cooldown.yaml")
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(cooldown_data, file)
    
    def load_slot_cooldowns(self):
        """Загружает все кд слотов из cache"""
        self.slot_cooldowns = {}
        
        if os.path.exists(self.cache_dir):
            for file_name in os.listdir(self.cache_dir):
                if file_name.startswith('slot_') and file_name.endswith('_cooldown.yaml'):
                    file_path = os.path.join(self.cache_dir, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            cooldown_data = yaml.safe_load(file)
                            slot = cooldown_data.get('slot')
                            cooldown = cooldown_data.get('cooldown', 0)
                            if slot is not None:
                                self.slot_cooldowns[slot] = cooldown
                    except:
                        continue
    
    def get_slot_cooldown(self, slot):
        """Получает кд для слота"""
        return self.slot_cooldowns.get(slot, 0)
    
    def clear_slot_cooldown(self, slot):
        """Очищает кд для слота"""
        if slot in self.slot_cooldowns:
            del self.slot_cooldowns[slot]
        
        # Удаляем файл
        file_path = os.path.join(self.cache_dir, f"slot_{slot}_cooldown.yaml")
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def update_cooldowns(self):
        """Обновляет все кд (уменьшает на 1 кадр)"""
        slots_to_remove = []
        
        for slot in list(self.slot_cooldowns.keys()):
            if self.slot_cooldowns[slot] > 0:
                self.slot_cooldowns[slot] -= 1
                if self.slot_cooldowns[slot] <= 0:
                    slots_to_remove.append(slot)
                else:
                    self.save_slot_cooldown(slot, self.slot_cooldowns[slot])
        
        # Удаляем завершенные кд
        for slot in slots_to_remove:
            self.clear_slot_cooldown(slot)
    
    def save_values(self, values):
        """Сохраняет значения в кэш"""
        values_data = {}
        for value_id, value_data in values.items():
            values_data[f"value_{value_id}"] = value_data
        
        file_path = os.path.join(self.cache_dir, "values.yaml")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(values_data, file)
    
    def load_values(self):
        """Загружает значения из кэша"""
        values = {}
        file_path = os.path.join(self.cache_dir, "values.yaml")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    values_data = yaml.safe_load(file) or {}
                
                for key, value_data in values_data.items():
                    if isinstance(value_data, dict):
                        values[value_data.get('id')] = {
                            'name': value_data.get('name', f'Value {value_data.get("id")}'),
                            'value': value_data.get('value', 0),
                            'min': value_data.get('min', 0),
                            'max': value_data.get('max', float('inf'))
                        }
            except Exception as e:
                print(f"Error loading values from cache: {e}")
        
        # Если нет кэша, загружаем из конфига
        if not values:
            values = self.load_values_from_config()
            self.save_values(values)
        
        return values
    
    def load_values_from_config(self):
        """Загружает значения из конфига (резервный вариант)"""
        values = {}
        config_path = os.path.join("game", "config", "values.yaml")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    values_data = yaml.safe_load(file) or {}
                
                for value_id, value_data in values_data.items():
                    if isinstance(value_data, dict):
                        values[value_data.get('id')] = {
                            'name': value_data.get('name', f'Value {value_data.get("id")}'),
                            'value': value_data.get('start_value', 0),
                            'min': value_data.get('min', 0),
                            'max': value_data.get('max', float('inf'))
                        }
            except Exception as e:
                print(f"Error loading values from config: {e}")
        
        return values