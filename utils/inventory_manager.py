import json
from datetime import datetime

class InventoryManager:
    def __init__(self, inventory_file):
        self.inventory_file = inventory_file
        self.load_inventory()
    
    def load_inventory(self):
        try:
            with open(self.inventory_file, 'r') as f:
                self.inventory = json.load(f)
            print("✅ Inventory loaded successfully")
        except:
            # Default inventory
            self.inventory = {
                'engine_oil': {'name': 'Engine Oil', 'quantity': 25, 'min_stock': 5, 'unit': 'liters'},
                'oil_filter': {'name': 'Oil Filter', 'quantity': 18, 'min_stock': 4, 'unit': 'pieces'},
                'air_filter': {'name': 'Air Filter', 'quantity': 22, 'min_stock': 4, 'unit': 'pieces'},
                'spark_plugs': {'name': 'Spark Plugs', 'quantity': 35, 'min_stock': 8, 'unit': 'sets'},
                'brake_pads': {'name': 'Brake Pads', 'quantity': 15, 'min_stock': 3, 'unit': 'sets'},
                'brake_fluid': {'name': 'Brake Fluid', 'quantity': 12, 'min_stock': 3, 'unit': 'liters'},
                'ac_gas': {'name': 'AC Refrigerant', 'quantity': 20, 'min_stock': 5, 'unit': 'cans'},
                'ac_cleaner': {'name': 'AC System Cleaner', 'quantity': 15, 'min_stock': 4, 'unit': 'cans'},
                'ac_filter': {'name': 'Cabin Air Filter', 'quantity': 28, 'min_stock': 6, 'unit': 'pieces'},
                'coolant': {'name': 'Engine Coolant', 'quantity': 30, 'min_stock': 8, 'unit': 'liters'},
                'transmission_fluid': {'name': 'Transmission Fluid', 'quantity': 20, 'min_stock': 5, 'unit': 'liters'},
                'power_steering_fluid': {'name': 'Power Steering Fluid', 'quantity': 15, 'min_stock': 4, 'unit': 'liters'}
            }
            self.save_inventory()
    
    def save_inventory(self):
        with open(self.inventory_file, 'w') as f:
            json.dump(self.inventory, f, indent=2)
    
    def check_and_deduct_parts(self, selected_tasks):
        required_parts = {}
        parts_availability = True
        unavailable_parts = []
        
        # Parts required for each task
        task_parts_map = {
            'engine_oil': ['engine_oil', 'oil_filter'],
            'air_filter': ['air_filter'],
            'spark_plugs': ['spark_plugs'],
            'brake_pads': ['brake_pads', 'brake_fluid'],
            'brake_fluid': ['brake_fluid'],
            'ac_service': ['ac_gas', 'ac_cleaner'],
            'ac_filter': ['ac_filter'],
            'wheel_alignment': [],  # No parts needed
            'tire_rotation': []     # No parts needed
        }
        
        # Calculate required parts
        for task in selected_tasks:
            if task in task_parts_map:
                for part in task_parts_map[task]:
                    required_parts[part] = required_parts.get(part, 0) + 1
        
        # Check availability
        for part, quantity in required_parts.items():
            if part in self.inventory:
                if self.inventory[part]['quantity'] < quantity:
                    parts_availability = False
                    unavailable_parts.append({
                        'part': part,
                        'required': quantity,
                        'available': self.inventory[part]['quantity']
                    })
        
        # Deduct parts if available
        if parts_availability:
            for part, quantity in required_parts.items():
                if part in self.inventory:
                    self.inventory[part]['quantity'] -= quantity
                    self.inventory[part]['last_used'] = datetime.now().isoformat()
            self.save_inventory()
        
        return {
            'required_parts': required_parts,
            'available': parts_availability,
            'unavailable_parts': unavailable_parts,
            'inventory_status': self.get_inventory_data()
        }
    
    def check_low_stock(self):
        low_stock = []
        for part_id, part_data in self.inventory.items():
            if part_data['quantity'] <= part_data['min_stock']:
                low_stock.append({
                    'id': part_id,
                    'name': part_data['name'],
                    'quantity': part_data['quantity'],
                    'min_stock': part_data['min_stock'],
                    'unit': part_data.get('unit', 'pieces')
                })
        return low_stock
    
    def restock_part(self, part_name, quantity):
        if part_name in self.inventory:
            self.inventory[part_name]['quantity'] += quantity
            self.inventory[part_name]['last_restocked'] = datetime.now().isoformat()
            self.save_inventory()
            return True
        return False
    
    def get_inventory_data(self):
        return self.inventory
    
    def get_inventory_summary(self):
        total_items = len(self.inventory)
        low_stock_count = len(self.check_low_stock())
        return {
            'total_items': total_items,
            'low_stock_count': low_stock_count
        }
