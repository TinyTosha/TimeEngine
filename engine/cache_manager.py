import os
import yaml

class CacheManager:
    def __init__(self, cache_dir="engine/cache"):
        self.cache_dir = cache_dir
        self.slot_cooldowns = {}
    
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