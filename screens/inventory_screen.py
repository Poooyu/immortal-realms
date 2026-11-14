#!/usr/bin/env python3
"""Inventory Screen - Manage equipment and items"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from immortal_realms.main import Player, EQUIPMENT_SLOTS, Equipment, SaveSystem


class InventoryScreen(Screen):
    """Inventory and equipment management screen."""
    
    def __init__(self, **kwargs):
        super().__init__(name="inventory", **kwargs)
        self.layout = FloatLayout()
        self.add_widget(self.layout)
        
        # Back button
        self.back_btn = Button(
            text="← Back",
            font_size=24,
            size_hint=(0.2, 0.1),
            pos_hint={"x": 0.1, "y": 0.9},
            background_color=(0.3, 0.3, 0.3, 1)
        )
        self.back_btn.bind(on_press=self._on_back)
        self.layout.add_widget(self.back_btn)
        
        # Title
        self.title_label = Label(
            text="Inventory",
            font_size=36,
            center_x="center",
            center_y="0.1",
            color=(1, 0.84, 0, 1),
            bold=True
        )
        self.layout.add_widget(self.title_label)
        
        # Currency display
        self.currency_label = Label(
            text=f"Spiritual Stones: {self.player.spiritual_stones}",
            font_size=20,
            center_x="center",
            center_y="0.15",
            color=(1, 1, 1, 1)
        )
        self.layout.add_widget(self.currency_label)
        
        # Equipment section
        eq_title = Label(
            text="Equipment",
            font_size=24,
            center_x="center",
            center_y="0.25",
            color=(1, 0.84, 0, 1),
            bold=True
        )
        self.layout.add_widget(eq_title)
        
        # Equipment slots
        self.equipment_display = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.5),
            pos_hint={"x": 0, "y": 0.3},
            spacing=8
        )
        self.layout.add_widget(self.equipment_display)
        
        # Refresh equipment display
        self._refresh_equipment()
        
        # Inventory section
        inv_title = Label(
            text="Inventory",
            font_size=24,
            center_x="center",
            center_y="0.8",
            color=(1, 0.84, 0, 1),
            bold=True
        )
        self.layout.add_widget(inv_title)
        
        # Scrollable inventory area (simplified - fixed grid)
        self.inventory_display = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.45),
            pos_hint={"x": 0, "y": 0.55},
            spacing=5
        )
        self.layout.add_widget(self.inventory_display)
        
        # Refresh inventory
        self._refresh_inventory()
    
    def _refresh_equipment(self):
        """Refresh the equipment display."""
        self.equipment_display.clear_widgets()
        
        for slot in EQUIPMENT_SLOTS:
            eq = self.player.equipment.get(slot)
            if eq:
                # Create equipment from dict
                from immortal_realms.main import Equipment
                equipment = Equipment.from_dict(eq)
                eq_text = Label(
                    text=f"  {slot}:\n{equipment.rarity} +{equipment.enhancement_level}\n"
                         f"Atk:+{int(equipment.stats.get('damage', 0))} Def:+{int(equipment.stats.get('defense', 0))}",
                    font_size=14,
                    color=(1, 0.84, 0, 1),
                    size_hint_y=None,
                    height=60,
                    text_size=(Window.width * 0.4, None)
                )
                self.equipment_display.add_widget(eq_text)
                
                # Equip/unequip button
                if equipment.rarity in ["Common", "Uncommon"]:
                    btn_text = "Unequip"
                    btn_color = (0.8, 0.3, 0.3, 1)
                else:
                    btn_text = "Keep"
                    btn_color = (0.3, 0.5, 0.8, 1)
                
                btn = Button(
                    text=btn_text,
                    font_size=12,
                    size_hint=(1, 0.1),
                    background_color=btn_color
                )
                btn.tag = slot  # Store the slot tag
                btn.bind(on_press=self._on_equipment_toggle)
                self.equipment_display.add_widget(btn)
            else:
                # Empty slot
                empty_text = Label(
                    text=f"  {slot}: Empty",
                    font_size=14,
                    color=(0.6, 0.6, 0.6, 1),
                    size_hint_y=None,
                    height=40,
                    text_size=(Window.width * 0.4, None)
                )
                self.equipment_display.add_widget(empty_text)
                
                # Equip button
                btn = Button(
                    text="Equip",
                    font_size=12,
                    size_hint=(1, 0.1),
                    background_color=(0.3, 0.5, 0.8, 1)
                )
                btn.tag = slot
                btn.bind(on_press=self._on_equipment_toggle)
                self.equipment_display.add_widget(btn)
    
    def _refresh_inventory(self):
        """Refresh the inventory display."""
        self.inventory_display.clear_widgets()
        
        inventory = self.player.inventory
        
        if not inventory:
            no_items = Label(
                text="No items in inventory.",
                font_size=18,
                color=(0.8, 0.8, 0.8, 1),
                size_hint_y=None,
                height=40
            )
            self.inventory_display.add_widget(no_items)
            return
        
        for i, item_dict in enumerate(inventory):
            from immortal_realms.main import Equipment
            equipment = Equipment.from_dict(item_dict)
            
            item_text = Label(
                text=f"[{equipment.rarity}] {equipment.slot}\n"
                     f"Atk:+{int(equipment.stats.get('damage', 0))} "
                     f"Def:+{int(equipment.stats.get('defense', 0))}",
                font_size=14,
                color=(1, 0.84, 0, 1),
                size_hint_y=None,
                height=50,
                text_size=(Window.width * 0.6, None)
            )
            self.inventory_display.add_widget(item_text)
    
    def _on_back(self, instance):
        """Go back to world map."""
        self.manager.current = "world_map"
    
    def _on_equipment_toggle(self, instance):
        """Handle equipment toggle (equip/unequip)."""
        slot = instance.tag
        current_eq = self.player.equipment.get(slot)
        
        if current_eq:
            # Unequip - remove equipment
            self.player.equipment[slot] = None
            # Remove from inventory (find first matching item)
            for i, item in enumerate(self.player.inventory):
                from immortal_realms.main import Equipment
                eq = Equipment.from_dict(item)
                if eq.slot == slot and eq.rarity == current_eq.rarity:
                    self.player.inventory.pop(i)
                    break
        else:
            # Try to equip - find in inventory
            for i, item in enumerate(self.player.inventory):
                from immortal_realms.main import Equipment
                eq = Equipment.from_dict(item)
                if eq.slot == slot:
                    # Equip it
                    self.player.equipment[slot] = item
                    self.player.inventory.pop(i)
                    break
        
        # Save and refresh
        SaveSystem.save_game(self.player.to_dict())
        self._refresh_equipment()
        self._refresh_inventory()
        
        self._show_message("Equipment", f"Slot {slot} {'unequipped' if not current_eq else 'equipped'} successfully!")
    
    def _show_message(self, title, message):
        """Show popup message."""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.6, 0.3)
        )
        popup.open()


# Helper imports at the bottom
from immortal_realms.main import Equipment