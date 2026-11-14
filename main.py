#!/usr/bin/env python3
"""Immortal Realms - Offline Cultivation RPG for Android"""
import os
import json
import random
import time
import sqlite3
from pathlib import Path

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.logger import Logger

# Set window properties for landscape mobile
Window.fullscreen = 'auto'
Window.orientation = 'landscape'

# Game configuration
GAME_VERSION = "1.0.0"
DATA_DIR = Path.home() / ".immortal_realms"
SAVE_FILE = DATA_DIR / "savegame.json"
CONFIG_FILE = DATA_DIR / "config.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)


# ============================================================
# DATA DEFINITIONS
# ============================================================

CULTIVATION_RANKS = [
    "Body Tempering",
    "Qi Gathering", 
    "Foundation Establishment",
    "Core Formation",
    "Nascent Soul",
    "Soul Transformation",
    "Void Refinement",
    "Mahayana",
    "Immortal Ascension"
]

CULTIVATION_RANK_SUBREALMS = {
    "Body Tempering": ["1st", "2nd", "3rd", "4th", "5th"],
    "Qi Gathering": ["1st", "2nd", "3rd", "4th", "5th"],
    "Foundation Establishment": ["1st", "2nd", "3rd", "4th", "5th"],
    "Core Formation": ["1st", "2nd", "3rd", "4th", "5th"],
    "Nascent Soul": ["1st", "2nd", "3rd", "4th", "5th"],
    "Soul Transformation": ["1st", "2nd", "3rd", "4th", "5th"],
    "Void Refinement": ["1st", "2nd", "3rd", "4th", "5th"],
    "Mahayana": ["1st", "2nd", "3rd", "4th", "5th"],
    "Immortal Ascension": ["1st", "2nd", "3rd", "4th", "5th"]
}

ELEMENTAL_PATHS = ["Fire", "Water", "Wind", "Earth", "Lightning"]

MONSTER_TYPES = {
    "Spirit Rabbit": {"exp": 10, "gold": 5, "health": 20, "attack": 3, "elements": ["Wind"]},
    "Fire Imp": {"exp": 15, "gold": 8, "health": 25, "attack": 4, "elements": ["Fire"]},
    "Water Serpent": {"exp": 20, "gold": 10, "health": 30, "attack": 3, "elements": ["Water"]},
    "Earth Golem": {"exp": 25, "gold": 12, "health": 50, "attack": 6, "elements": ["Earth"]},
    "Lightning Drake": {"exp": 30, "gold": 15, "health": 35, "attack": 7, "elements": ["Lightning"]},
    "Forest Bandit": {"exp": 15, "gold": 8, "health": 25, "attack": 4, "elements": []},
    "Mountain Troll": {"exp": 40, "gold": 20, "health": 80, "attack": 8, "elements": ["Earth"]},
    "Shadow Assassin": {"exp": 35, "gold": 18, "health": 30, "attack": 9, "elements": ["Dark"]},
}

EQUIPMENT_RARITY = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical", "Immortal"]
EQUIPMENT_SLOTS = ["Sword", "Spear", "Staff", "Armor", "Ring", "Necklace", "Artifact"]

REGIONS = {
    "Mortal Village": {"unlock_level": 1, "monsters": ["Spirit Rabbit", "Forest Bandit"], "treasure_chance": 0.1},
    "Spirit Forest": {"unlock_level": 5, "monsters": ["Fire Imp", "Water Serpent", "Spirit Rabbit"], "treasure_chance": 0.15},
    "Azure Mountain": {"unlock_level": 10, "monsters": ["Earth Golem", "Lightning Drake", "Fire Imp"], "treasure_chance": 0.2},
    "Ancient Ruins": {"unlock_level": 15, "monsters": ["Shadow Assassin", "Earth Golem"], "treasure_chance": 0.25},
    "Demon Territory": {"unlock_level": 20, "monsters": ["Fire Imp", "Shadow Assassin"], "treasure_chance": 0.3},
    "Immortal Mountains": {"unlock_level": 25, "monsters": ["Lightning Drake", "Earth Golem"], "treasure_chance": 0.35},
    "Heavenly Realm": {"unlock_level": 30, "monsters": ["Powerful variants"], "treasure_chance": 0.4},
    "Forbidden Lands": {"unlock_level": 35, "monsters": ["Boss variants"], "treasure_chance": 0.5}
}


# ============================================================
# SAVE SYSTEM
# ============================================================

class SaveSystem:
    """Handles saving and loading game progress locally."""
    
    @staticmethod
    def load_save():
        """Load the saved game from local storage."""
        if SAVE_FILE.exists():
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                Logger.info("Save game loaded successfully")
                return data
            except (json.JSONDecodeError, IOError) as e:
                Logger.error(f"Error loading save: {e}")
        return SaveSystem.get_default_save()
    
    @staticmethod
    def get_default_save():
        """Get a default new game save file."""
        return {
            "player_name": " cultivator",
            "cultivation_rank": "Body Tempering",
            "cultivation_subrealm": "1st",
            "level": 1,
            "exp": 0,
            "exp_to_next": 100,
            "hp": 100,
            "max_hp": 100,
            "qi": 50,
            "max_qi": 50,
            "attack": 10,
            "defense": 5,
            "spiritual_stones": 0,
            "position": {"x": 0, "y": 0, "region": "Mortal Village"},
            "inventory": [],
            "equipment": {slot: None for slot in EQUIPMENT_SLOTS},
            "skills": [],
            "unlocked_regions": ["Mortal Village"],
            "quests": [],
            "world_time": "day",
            "settings": {"touch_sensitivity": "medium", "sound_volume": 0.8, "music_volume": 0.7}
        }
    
    @staticmethod
    def save_game(save_data):
        """Save the game progress to local storage."""
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(save_data, f, indent=2)
            Logger.info("Game saved successfully")
            return True
        except IOError as e:
            Logger.error(f"Error saving game: {e}")
            return False


# ============================================================
# PLAYER CLASS
# ============================================================

class Player:
    """Represents the player character with cultivation and combat stats."""
    
    def __init__(self, data=None):
        if data is None:
            data = SaveSystem.get_default_save()
        
        self.name = data.get("player_name", "Cultivator")
        self.rank = data.get("cultivation_rank", "Body Tempering")
        self.subrealm = data.get("cultivation_subrealm", "1st")
        self.level = data.get("level", 1)
        self.exp = data.get("exp", 0)
        self.exp_to_next = data.get("exp_to_next", 100)
        self.hp = data.get("hp", 100)
        self.max_hp = data.get("max_hp", 100)
        self.qi = data.get("qi", 50)
        self.max_qi = data.get("max_qi", 50)
        self.attack = data.get("attack", 10)
        self.defense = data.get("defense", 5)
        self.spiritual_stones = data.get("spiritual_stones", 0)
        self.position = data.get("position", {"x": 0, "y": 0, "region": "Mortal Village"})
        self.inventory = data.get("inventory", [])
        self.equipment = data.get("equipment", {slot: None for slot in EQUIPMENT_SLOTS})
        self.skills = data.get("skills", [])
        self.unlocked_regions = data.get("unlocked_regions", ["Mortal Village"])
        self.quests = data.get("quests", [])
        self.world_time = data.get("world_time", "day")
        self.settings = data.get("settings", {"touch_sensitivity": "medium", "sound_volume": 0.8, "music_volume": 0.7})
        
        # Calculate derived stats
        self._update_derived_stats()
    
    def _update_derived_stats(self):
        """Update derived stats based on cultivation rank and equipment."""
        # Base stats from rank
        rank_bonus = CULTIVATION_RANKS.index(self.rank) if self.rank in CULTIVATION_RANKS else 0
        self.attack = 10 + rank_bonus * 2 + sum(1 for eq in self.equipment.values() if eq and eq.get("rarity") in ["Rare", "Epic", "Legendary", "Mythical", "Immortal"])
        self.defense = 5 + rank_bonus + sum(1 for eq in self.equipment.values() if eq and eq.get("rarity") in ["Rare", "Epic", "Legendary", "Mythical", "Immortal"])
        self.max_hp = 100 + rank_bonus * 15
        self.max_qi = 50 + rank_bonus * 10
        
        # Clamp current values
        self.hp = min(self.hp, self.max_hp)
        self.qi = min(self.qi, self.max_qi)
    
    def gain_exp(self, amount):
        """Gain experience points."""
        self.exp += amount
        if self.exp >= self.exp_to_next:
            self._check_breakthrough()
        SaveSystem.save_game(self.to_dict())
    
    def _check_breakthrough(self):
        """Check for cultivation breakthrough."""
        # Simple breakthrough chance based on exp
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self._advance_rank()
    
    def _advance_rank(self):
        """Advance to the next cultivation rank."""
        try:
            current_idx = CULTIVATION_RANKS.index(self.rank)
        except ValueError:
            current_idx = len(CULTIVATION_RANKS) - 1
        
        if current_idx < len(CULTIVATION_RANKS) - 1:
            # Check subrealm progression
            subreals = CULTIVATION_RANK_SUBREALMS[self.rank]
            current_subrealm_idx = subreals.index(self.subrealm) if self.subrealm in subreals else 0
            
            if current_subrealm_idx < len(subreals) - 1:
                # Upgrade subrealm
                next_idx = current_subrealm_idx + 1
                self.subrealm = subreals[next_idx]
                Logger.info(f"Advanced to {self.subrealm} subrealm of {self.rank}")
            else:
                # Advance to next rank
                self.rank = CULTIVATION_RANKS[current_idx + 1]
                self.subrealm = CULTIVATION_RANK_SUBREALMS[self.rank][0]
                Logger.info(f"Breakthrough! Advanced to {self.rank} {self.subrealm}")
        else:
            # Already at Immortal Ascension
            Logger.info("Already at maximum cultivation rank!")
    
    def to_dict(self):
        """Convert player data to dictionary for saving."""
        return {
            "player_name": self.name,
            "cultivation_rank": self.rank,
            "cultivation_subrealm": self.subrealm,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "qi": self.qi,
            "max_qi": self.max_qi,
            "attack": self.attack,
            "defense": self.defense,
            "spiritual_stones": self.spiritual_stones,
            "position": self.position,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "skills": self.skills,
            "unlocked_regions": self.unlocked_regions,
            "quests": self.quests,
            "world_time": self.world_time,
            "settings": self.settings
        }


# ============================================================
# MONSTER CLASS
# ============================================================

class Monster:
    """Represents a monster in the world with stats and loot."""
    
    def __init__(self, monster_type, level=None):
        self.type = monster_type
        self.base_data = MONSTER_TYPES.get(monster_type, MONSTER_TYPES["Spirit Rabbit"])
        self.level = level or random.randint(1, 5)
        
        # Scale stats based on level
        level_multiplier = 1 + (self.level - 1) * 0.2
        
        self.name = monster_type
        self.level = self.level
        self.health = int(self.base_data["health"] * level_multiplier)
        self.max_health = self.health
        self.attack = int(self.base_data["attack"] * level_multiplier)
        self.exp_reward = int(self.base_data["exp"] * level_multiplier)
        self.gold_reward = int(self.base_data["gold"] * level_multiplier)
        self.elements = self.base_data.get("elements", [])
        self.is_elite = random.random() < 0.1  # 10% chance to be elite
        self.is_boss = False
    
    def take_damage(self, damage):
        """Apply damage to the monster."""
        actual_damage = max(1, damage - random.randint(0, self.defense if hasattr(self, 'defense') else 0))
        self.health -= actual_damage
        return actual_damage
    
    def is_alive(self):
        """Check if the monster is alive."""
        return self.health > 0


# ============================================================
# EQUIPMENT CLASS
# ============================================================

class Equipment:
    """Represents equipment with rarity and stats."""
    
    def __init__(self, slot, rarity="Common", enhancement_level=0, **stats):
        self.slot = slot
        self.rarity = rarity
        self.enhancement_level = enhancement_level
        self.stats = stats
        self.base_stats = {}
        self._generate_base_stats()
        self._apply_enhancement()
    
    def _generate_base_stats(self):
        """Generate base stats based on rarity."""
        rarity_multipliers = {
            "Common": 1.0,
            "Uncommon": 1.2,
            "Rare": 1.4,
            "Epic": 1.6,
            "Legendary": 1.8,
            "Mythical": 2.0,
            "Immortal": 2.5
        }
        multiplier = rarity_multipliers.get(self.rarity, 1.0)
        
        # Base stats vary by slot
        base_damage = random.uniform(5, 15) * multiplier
        base_defense = random.uniform(2, 8) * multiplier
        
        self.base_stats = {
            "damage": base_damage,
            "defense": base_defense,
            " rarity_bonus": (self.rarity, multiplier)
        }
    
    def _apply_enhancement(self):
        """Apply enhancement level to stats."""
        enhancement_bonus = self.enhancement_level * 0.1
        self.stats = {
            "damage": self.base_stats["damage"] * (1 + enhancement_bonus),
            "defense": self.base_stats["defense"] * (1 + enhancement_bonus),
            "rarity": self.rarity,
            "enhancement_level": self.enhancement_level
        }
    
    def to_dict(self):
        """Convert equipment to dictionary."""
        return {
            "slot": self.slot,
            "rarity": self.rarity,
            "enhancement_level": self.enhancement_level,
            "stats": self.stats
        }
    
    @staticmethod
    def from_dict(data):
        """Create equipment from dictionary."""
        eq = Equipment(data["slot"], data["rarity"], data["enhancement_level"])
        eq.stats = data.get("stats", {})
        return eq


# ============================================================
# QUEST CLASS
# ============================================================

class Quest:
    """Represents a quest with objectives and rewards."""
    
    def __init__(self, quest_id, name, description, objectives, reward_type, reward_value):
        self.id = quest_id
        self.name = name
        self.description = description
        self.objectives = objectives  # List of (objective_type, target, current_count, required_count)
        self.reward_type = reward_type  # "exp", "gold", "item", "realm"
        self.reward_value = reward_value
        self.is_completed = False
        self.is_received = False
    
    def check_progress(self, player, monster_type=None, region=None):
        """Check if objectives are progressing."""
        for i, (obj_type, target, current, required) in enumerate(self.objectives):
            if obj_type == "defeat_monsters":
                # Check if we've defeated enough
                pass
            elif obj_type == "explore_region":
                if region:
                    pass  # Check separately
        
        # Check all objectives completion
        all_complete = all(
            current >= required 
            for obj_type, target, current, required in self.objectives
        )
        return all_complete
    
    def complete(self):
        """Mark quest as completed."""
        self.is_completed = True


# ============================================================
# WORLD / REGION CLASS
# ============================================================

class Region:
    """Represents a explorable region in the game world."""
    
    def __init__(self, name, unlock_level, monsters, treasure_chance):
        self.name = name
        self.unlock_level = unlock_level
        self.monsters = monsters
        self.treasure_chance = treasure_chance
        self.explored = False
    
    def get_random_monster(self, player_level):
        """Get a random monster appropriate for this region and player level."""
        valid_monsters = [m for m in self.monsters if m]  # Filter None values
        if not valid_monsters:
            return None
        monster_type = random.choice(valid_monsters)
        return Monster(monster_type, level=player_level)
    
    def check_unlock(self, player):
        """Check if the player can unlock this region."""
        return player.level >= self.unlock_level and self.name in player.unlocked_regions


# ============================================================
# MAIN GAME SCREENS
# ============================================================

class GameScreenManager(ScreenManager):
    """Manages the different game screens."""
    pass


class MainMenuScreen(Screen):
    """The main menu screen."""
    
    def __init__(self, **kwargs):
        super().__init__(name="main_menu", **kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self._build_ui()
        self.add_widget(self.layout)
    
    def _build_ui(self):
        """Build the main menu interface."""
        title = Label(
            text="Immortal Realms",
            font_size=70,
            center_x="center",
            bold=True,
            color=(1, 0.84, 0, 1)  # Gold color
        )
        self.layout.add_widget(title)
        
        subtitle = Label(
            text="An Offline Cultivation RPG",
            font_size=30,
            center_x="center",
            color=(1, 1, 1, 0.8)
        )
        self.layout.add_widget(subtitle)
        
        buttons = [
            ("New Game", self._start_new_game),
            ("Continue", self._continue_game),
            ("Settings", self._open_settings),
            ("Credits", self._show_credits),
        ]
        
        for text, callback in buttons:
            btn = Button(
                text=text,
                font_size=28,
                size_hint=(1, 0.15),
                background_color=(0.2, 0.5, 0.8, 1),
                bold=True
            )
            btn.bind(on_press=callback)
            self.layout.add_widget(btn)
    
    def _start_new_game(self, instance):
        """Start a new game."""
        App.get_running_app().start_new_game()
    
    def _continue_game(self, instance):
        """Continue the last saved game."""
        App.get_running_app().continue_game()
    
    def _open_settings(self, instance):
        """Open settings screen."""
        App.get_running_app().switch_screen("settings")
    
    def _show_credits(self, instance):
        """Show credits popup."""
        popup = Popup(
            title="Credits",
            content=Label(
                text="Immortal Realms\nCreated with Kivy\nChinese Xianxia Inspired\nOffline Game\nVersion 1.0.0",
                font_size=20
            ),
            size_hint=(0.8, 0.4)
        )
        popup.open()


class GameScreen(Screen):
    """Base game screen with common functionality."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = None
        self.world_regions = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the screen UI layout."""
        self.layout = FloatLayout()
        self.add_widget(self.layout)
    
    def load_game(self):
        """Load the saved game data."""
        save_data = SaveSystem.load_save()
        self.player = Player(save_data)
        self._initialize_world()
        self._update_display()
    
    def _initialize_world(self):
        """Initialize the world regions."""
        self.world_regions = {}
        for region_name, region_data in REGIONS.items():
            region = Region(
                name=region_name,
                unlock_level=region_data["unlock_level"],
                monsters=region_data["monsters"],
                treasure_chance=region_data["treasure_chance"]
            )
            self.world_regions[region_name] = region
        
        # Unlock regions based on player progress
        for region_name, region in self.world_regions.items():
            if region.check_unlock(self.player):
                region.explored = True
    
    def _update_display(self):
        """Update the UI display with player status."""
        if self.player:
            # Update world time
            pass


class WorldMapScreen(GameScreen):
    """The world map exploration screen."""
    
    def _setup_ui(self):
        super()._setup_ui()
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.back_btn = Button(
            text="← Back",
            size_hint=(0.2, 0.1),
            pos_hint={"x": 0.1, "y": 0.9},
            background_color=(0.3, 0.3, 0.3, 1)
        )
        self.back_btn.bind(on_press=self._on_back)
        self.layout.add_widget(self.back_btn)
        
        title = Label(
            text="World Map",
            font_size=36,
            center_x="center",
            size_hint_y=0.1,
            color=(1, 0.84, 0, 1)
        )
        self.layout.add_widget(title)
        
        self.regions_list = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.8),
            pos_hint={"x": 0, "y": 0.1}
        )
        self.layout.add_widget(self.regions_list)
        
        self._refresh_region_list()
    
    def _refresh_region_list(self):
        """Refresh the list of regions."""
        self.regions_list.clear_widgets()
        
        for region_name, region in self.world_regions.items():
            btn = Button(
                text=f"{region_name}\n(Lvl {region.unlock_level}+)",
                font_size=20,
                size_hint_y=None,
                height=50,
                background_color=(
                    (0.2, 0.8, 0.2, 1) if region.explored else (0.5, 0.5, 0.5, 1)
                )
            )
            btn.bind(on_press=lambda instance, r=region_name: self._enter_region(r))
            self.regions_list.add_widget(btn)
    
    def _enter_region(self, region_name):
        """Enter a region."""
        self.manager.current = "exploration"
        exploration_screen = self.manager.get_screen("exploration")
        exploration_screen.enter_region(region_name)
    
    def _on_back(self, instance):
        """Go back to main menu."""
        self.manager.current = "main_menu"


class ExplorationScreen(GameScreen):
    """The main exploration screen for a region."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_region = None
        self.layout = FloatLayout()
        self.add_widget(self.layout)
    
    def enter_region(self, region_name):
        """Enter a specific region."""
        self.current_region = region_name
        region = self.world_regions[region_name]
        
        # Clear existing widgets
        self.layout.clear_widgets()
        
        # Region info
        info = Label(
            text=f"🌿 {region_name}",
            font_size=40,
            center_x="center",
            center_y="0.6",
            bold=True,
            color=(1, 1, 1, 1)
        )
        self.layout.add_widget(info)
        
        # Description
        desc_text = {
            "Mortal Village": "A humble beginning for aspiring cultivators.",
            "Spirit Forest": "A mystical forest filled with nature spirits.",
            "Azure Mountain": "A towering mountain with ancient relics.",
            "Ancient Ruins": "The remnants of a forgotten civilization.",
            "Demon Territory": "A land corrupted by demonic energy.",
            "Immortal Mountains": "Peaks that pierce the clouds.",
            "Heavenly Realm": "The divine realm of immortals.",
            "Forbidden Lands": "A dangerous land where only the strong survive."
        }.get(region_name, "An explorable region.")
        
        desc = Label(
            text=desc_text,
            font_size=20,
            center_x="center",
            center_y="0.45",
            color=(0.8, 0.8, 0.8, 1)
        )
        self.layout.add_widget(desc)
        
        # Player level requirement
        lvl_req = REGIONS[region_name]["unlock_level"]
        lvl_label = Label(
            text=f"Required Cultivation: {lvl_req}+",
            font_size=18,
            center_x="center",
            center_y="0.35",
            color=(1, 0.84, 0, 1)
        )
        self.layout.add_widget(lvl_label)
        
        # Explore button
        if region.check_unlock(self.player):
            explore_btn = Button(
                text="Explore Region",
                font_size=24,
                size_hint=(0.6, 0.1),
                center_x="center",
                center_y="0.2",
                background_color=(0.2, 0.8, 0.2, 1)
            )
            explore_btn.bind(on_press=self._on_explore)
            self.layout.add_widget(explore_btn)
        else:
            locked_label = Label(
                text="Lock: Cultivation Too Low",
                font_size=18,
                center_x="center",
                center_y="0.2",
                color=(1, 0.3, 0.3, 1)
            )
            self.layout.add_widget(locked_label)
        
        # Action buttons
        btn_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.2),
            pos_hint={"x": 0, "y": 0.85}
        )
        
        hunt_btn = Button(
            text="Hunt Monsters",
            font_size=18,
            size_hint=(0.3, 1),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        hunt_btn.bind(on_press=self._on_hunt)
        btn_layout.add_widget(hunt_btn)
        
        meditate_btn = Button(
            text="Meditate",
            font_size=18,
            size_hint=(0.3, 1),
            background_color=(0.3, 0.5, 0.8, 1)
        )
        meditate_btn.bind(on_press=self._on_meditate)
        btn_layout.add_widget(meditate_btn)
        
        inventory_btn = Button(
            text="Inventory",
            font_size=18,
            size_hint=(0.3, 1),
            background_color=(0.5, 0.3, 0.8, 1)
        )
        inventory_btn.bind(on_press=self._on_inventory)
        btn_layout.add_widget(inventory_btn)
        
        self.layout.add_widget(btn_layout)
    
    def _on_explore(self, instance):
        """Handle explore button press."""
        # Mark region as explored
        if self.current_region:
            self.world_regions[self.current_region].explored = True
        self._refresh_region_list()
    
    def _on_hunt(self, instance):
        """Start monster hunting."""
        if self.current_region:
            from screens.combat_screen import CombatScreen
            self.manager.current = "combat"
            combat_screen = self.manager.get_screen("combat")
            combat_screen.start_random_encounter(self.current_region)
    
    def _on_meditate(self, instance):
        """Start meditation for cultivation."""
        if self.player:
            self.player.qi = min(self.player.qi + 20, self.player.max_qi)
            self.player.exp += 5
            SaveSystem.save_game(self.player.to_dict())
            self._update_display()
            self._show_message("Meditated", "Qi restored and minor experience gained.")
    
    def _on_inventory(self, instance):
        """Open inventory screen."""
        self.manager.current = "inventory"
    
    def _update_display(self):
        """Update display with current player status."""
        if self.player:
            hp_label = Label(
                text=f"HP: {self.player.hp}/{self.player.max_hp}",
                font_size=16,
                size_hint=(0.3, 0.1),
                x=10, y=self.layout.top - 30
            )
            self.layout.add_widget(hp_label)
            
            qi_label = Label(
                text=f"Qi: {self.player.qi}/{self.player.max_qi}",
                font_size=16,
                size_hint=(0.3, 0.1),
                x=10, y=self.layout.top - 50
            )
            self.layout.add_widget(qi_label)
    
    def _show_message(self, title, message):
        """Show a popup message."""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.6, 0.3)
        )
        popup.open()
    
    def _on_back(self, instance):
        """Go back to world map."""
        self.manager.current = "world_map"


# ============================================================
# COMBAT SCREEN
# ============================================================

class CombatScreen(GameScreen):
    """Real-time combat screen."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_monster = None
        self.player_action = None
        self.combat_log = []
        self.is_player_turn = True
    
    def start_random_encounter(self, region_name):
        """Start a random encounter in the given region."""
        region = self.world_regions[region_name]
        monster = region.get_random_monster(self.player.level)
        self.current_monster = monster
        
        # Initialize player stats for combat
        self.player_hp = self.player.hp
        self.player_max_hp = self.player.max_hp
        self.player_qi = self.player.qi
        self.player_max_qi = self.player.max_qi
        
        self._setup_combat_ui()
        self._update_combat_display()
        self._start_combat()
    
    def _setup_combat_ui(self):
        """Set up the combat interface."""
        self.layout = FloatLayout()
        self.add_widget(self.layout)
        
        # Monster info
        self.monster_label = Label(
            text=f"Wild {self.current_monster.name} (Lvl {self.current_monster.level})",
            font_size=28,
            center_x="center",
            center_y="0.7",
            bold=True,
            color=(1, 0.3, 0.3, 1)
        )
        self.layout.add_widget(self.monster_label)
        
        self.monster_hp = Label(
            text=f"HP: {self.current_monster.health}/{self.current_monster.max_health}",
            font_size=20,
            center_x="center",
            center_y="0.6",
            color=(1, 0.5, 0.5, 1)
        )
        self.layout.add_widget(self.monster_hp)
        
        # Player info
        self.player_label = Label(
            text=f"You - {self.player.rank} {self.player.subrealm}",
            font_size=20,
            center_x="center",
            center_y="0.4",
            color=(0.8, 0.9, 0.8, 1)
        )
        self.layout.add_widget(self.player_label)
        
        self.player_hp_label = Label(
            text=f"HP: {self.player_hp}/{self.player_max_hp}",
            font_size=18,
            center_x="center",
            center_y="0.3",
            color=(0.8, 0.9, 0.8, 1)
        )
        self.layout.add_widget(self.player_hp_label)
        
        # Action buttons
        btn_height = 0.12
        btn_width = 0.8
        spacing = 0.05
        
        # Attack button
        self.attack_btn = Button(
            text="Basic Attack",
            font_size=20,
            size_hint=(btn_width, btn_height),
            center_x="center",
            center_y="0.15",
            background_color=(0.8, 0.3, 0.3, 1)
        )
        self.attack_btn.bind(on_press=self._on_attack)
        self.layout.add_widget(self.attack_btn)
        
        # Skill button
        self.skill_btn = Button(
            text="Skill",
            font_size=20,
            size_hint=(btn_width, btn_height),
            x=self.layout.width * 0.1,
            center_y="0.15",
            background_color=(0.3, 0.5, 0.8, 1)
        )
        self.skill_btn.bind(on_press=self._on_skill)
        self.layout.add_widget(self.skill_btn)
        
        # Dodge button
        self.dodge_btn = Button(
            text="Dodge",
            font_size=20,
            size_hint=(btn_width, btn_height),
            center_x="center",
            center_y="0.15",
            background_color=(0.3, 0.8, 0.3, 1)
        )
        self.dodge_btn.bind(on_press=self._on_dodge)
        self.layout.add_widget(self.dodge_btn)
        
        # Cultivate button
        self.cultivate_btn = Button(
            text="Cultivate",
            font_size=20,
            size_hint=(btn_width, btn_height),
            x=self.layout.width * 0.9 - self.layout.width * 0.1,
            center_y="0.15",
            background_color=(0.3, 0.8, 0.5, 1)
        )
        self.cultivate_btn.bind(on_press=self._on_cultivate)
        self.layout.add_widget(self.cultivate_btn)
        
        # Log area
        self.log_box = Label(
            text="",
            font_size=14,
            size_hint=(0.9, 0.3),
            center_x="center",
            y=0,
            text_size=(self.layout.width * 0.9, None)
        )
        self.layout.add_widget(self.log_box)
    
    def _update_combat_display(self):
        """Update the combat display."""
        # Update monster HP
        self.monster_hp.text = f"HP: {self.current_monster.health}/{self.current_monster.max_health}"
        
        # Update player HP
        self.player_hp_label.text = f"HP: {self.player_hp}/{self.player_max_hp}"
        
        # Update log
        log_text = "\n".join(self.combat_log[-8:])  # Show last 8 entries
        self.log_box.text = log_text
    
    def _start_combat(self):
        """Start the combat encounter."""
        self.combat_log = []
        self.combat_log.append(f"Encounter: Wild {self.current_monster.name} appeared!")
        self._update_combat_display()
        self.is_player_turn = True
    
    def _on_attack(self, instance):
        """Handle basic attack."""
        if not self.is_player_turn:
            return
        
        # Calculate damage
        base_damage = self.player.attack
        # Add elemental bonus if applicable
        element_bonus = random.uniform(0.8, 1.2) if random.random() > 0.5 else 1.0
        damage = int(base_damage * element_bonus)
        
        # Apply damage to monster
        actual_damage = self.current_monster.take_damage(damage)
        
        # Log action
        self.combat_log.append(f"You attacked {self.current_monster.name} for {actual_damage} damage!")
        
        # Check if monster is dead
        if not self.current_monster.is_alive():
            self.combat_log.append(f"You defeated the {self.current_monster.name}!")
            self._on_victory()
            return
        
        self.combat_log.append(f"{self.current_monster.name} has {self.current_monster.health} HP remaining!")
        
        # Player turn ends, monster attacks
        self.is_player_turn = False
        Clock.schedule_once(self._monster_attack, 1.0)
    
    def _on_skill(self, instance):
        """Handle skill use."""
        if not self.is_player_turn:
            return
        
        if self.player.skills:
            skill = random.choice(self.player.skills)
            damage = int(self.player.attack * 1.5)
            self.combat_log.append(f"You used skill: {skill} for {damage} damage!")
        else:
            self.combat_log.append("You attempt to use a skill but know no skills yet!")
        
        # Monster attacks after
        self.is_player_turn = False
        Clock.schedule_once(self._monster_attack, 1.0)
    
    def _on_dodge(self, instance):
        """Handle dodge action."""
        if not self.is_player_turn:
            return
        
        dodge_chance = 0.6 if not self.player.equipment.get("Necklace") else 0.8
        if random.random() < dodge_chance:
            self.combat_log.append("You successfully dodged the next attack!")
            # Skip monster attack this turn
            self.is_player_turn = False
            Clock.schedule_once(lambda dt: setattr(self, 'is_player_turn', True), 1.0)
        else:
            self.combat_log.append("Your dodge failed!")
            self.is_player_turn = False
            Clock.schedule_once(self._monster_attack, 1.0)
    
    def _on_cultivate(self, instance):
        """Handle cultivation during combat."""
        if not self.is_player_turn:
            return
        
        self.combat_log.append("You meditate to cultivate Qi!")
        self.player_qi = min(self.player_qi + 15, self.player_max_qi)
        self.player.exp += 3
        SaveSystem.save_game(self.player.to_dict())
        self._update_combat_display()
        
        # Monster attacks after
        self.is_player_turn = False
        Clock.schedule_once(self._monster_attack, 1.0)
    
    def _monster_attack(self, dt):
        """Monster's turn to attack."""
        if self.current_monster.is_alive():
            # Calculate monster damage
            monster_damage = self.current_monster.attack
            
            # Check if player dodged
            if self.is_player_turn:  # Player can dodge on their own turn too
                dodge_chance = 0.6
                if random.random() < dodge_chance:
                    self.combat_log.append(f"The {self.current_monster.name}'s attack was dodged!")
                    self.is_player_turn = True
                    self._update_combat_display()
                    return
            
            self.player_hp -= monster_damage
            self.combat_log.append(f"The {self.current_monster.name} attacks you for {monster_damage} damage!")
            
            # Check if player died
            if self.player_hp <= 0:
                self.combat_log.append("You have been defeated...")
                self._on_defeat()
                return
            
            self._update_combat_display()
        
        # Switch back to player turn
        self.is_player_turn = True
    
    def _on_victory(self):
        """Handle victory after defeating a monster."""
        # Gain experience and gold
        exp_gain = self.current_monster.exp_reward
        gold_gain = self.current_monster.gold_reward
        
        self.combat_log.append(f"Gained {exp_gain} EXP and {gold_gain} gold!")
        
        self.player.gain_exp(exp_gain)
        self.player.spiritual_stones += gold_gain
        
        # Loot check
        if random.random() < 0.3:  # 30% chance of loot
            self._roll_loot()
        
        # Unlock regions if needed
        self._check_region_unlock()
        
        self._update_combat_display()
        self._show_victory_popup()
    
    def _roll_loot(self):
        """Roll for equipment loot."""
        # Determine rarity based on monster level and player cultivation
        rarity_roll = random.random()
        if self.player.rank in ["Core Formation", "Nascent Soul"] and rarity_roll < 0.4:
            rarity = "Rare"
        elif self.player.rank in ["Nascent Soul", "Soul Transformation"] and rarity_roll < 0.5:
            rarity = "Epic"
        elif self.player.rank in ["Soul Transformation", "Void Refinement"] and rarity_roll < 0.3:
            rarity = "Legendary"
        else:
            rarity = random.choice(["Common", "Uncommon", "Rare"])
        
        # Choose equipment slot
        slot = random.choice(EQUIPMENT_SLOTS)
        
        # Create equipment
        loot = Equipment(slot=slot, rarity=rarity)
        
        # Add to inventory
        if loot not in self.player.inventory:
            self.player.inventory.append(loot.to_dict())
        
        self.combat_log.append(f"Obtained: {rarity} {slot}")
    
    def _check_region_unlock(self):
        """Check if any new regions should be unlocked."""
        for region_name, region in self.world_regions.items():
            if region.check_unlock(self.player) and region_name not in self.player.unlocked_regions:
                self.player.unlocked_regions.append(region_name)
                SaveSystem.save_game(self.player.to_dict())
                self._show_message("Region Unlocked!", f"You have unlocked {region_name}!")
    
    def _on_defeat(self):
        """Handle player defeat."""
        self.combat_log.append("Game Over - You have been defeated.")
        # Reset to last save or menu
        self.manager.current = "main_menu"
    
    def _show_victory_popup(self):
        """Show victory popup."""
        popup = Popup(
            title="Victory!",
            content=Label(
                text=f"You defeated the {self.current_monster.name}!\n"
                     f"Gained {self.current_monster.exp_reward} EXP and {self.current_monster.gold_reward} gold!",
                font_size=18
            ),
            size_hint=(0.8, 0.4)
        )
        popup.open()


# ============================================================
# ADDITIONAL SCREENS (Quest, Character, etc.)
# ============================================================

class CharacterScreen(GameScreen):
    """Character status and progression screen."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.back_btn = Button(
            text="← Back",
            size_hint=(1, 0.1),
            background_color=(0.3, 0.3, 0.3, 1)
        )
        self.back_btn.bind(on_press=self._on_back)
        self.layout.add_widget(self.back_btn)
        
        title = Label(
            text="Character Status",
            font_size=36,
            center_x="center",
            size_hint_y=0.1,
            color=(1, 0.84, 0, 1)
        )
        self.layout.add_widget(title)
        
        # Cultivation info
        cult_frame = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.2),
            pos_hint={"x": 0, "y": 0.1},
            spacing=5
        )
        
        rank_label = Label(
            text=f"Cultivation: {self.player.rank} {self.player.subrealm}",
            font_size=22,
            bold=True,
            color=(1, 0.84, 0, 1)
        )
        cult_frame.add_widget(rank_label)
        
        lvl_label = Label(
            text=f"Level: {self.player.level} | EXP: {self.player.exp}/{self.player.exp_to_next}",
            font_size=18,
            color=(1, 1, 1, 0.9)
        )
        cult_frame.add_widget(lvl_label)
        
        self.layout.add_widget(cult_frame)
        
        # Stats
        stats_frame = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.3),
            pos_hint={"x": 0, "y": 0.35},
            spacing=10
        )
        
        self.hp_display = Label(
            text=f"HP: {self.player.hp}/{self.player.max_hp}",
            font_size=18,
            color=(1, 0.6, 0.6, 1)
        )
        stats_frame.add_widget(self.hp_display)
        
        self.qi_display = Label(
            text=f"Qi: {self.player.qi}/{self.player.max_qi}",
            font_size=18,
            color=(0.6, 0.8, 1, 1)
        )
        stats_frame.add_widget(self.qi_display)
        
        self.atk_display = Label(
            text=f"Attack: {self.player.attack}",
            font_size=18,
            color=(1, 1, 1, 1)
        )
        stats_frame.add_widget(self.atk_display)
        
        self_def_display = Label(
            text=f"Defense: {self.player.defense}",
            font_size=18,
            color=(1, 1, 1, 1)
        )
        stats_frame.add_widget(self_def_display)
        
        self.layout.add_widget(stats_frame)
        
        # Equipment section
        eq_frame = Label(
            text="Equipment:",
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1)
        )
        self.layout.add_widget(eq_frame)
        
        # Show equipped items
        for slot in EQUIPMENT_SLOTS:
            eq = self.player.equipment.get(slot)
            if eq:
                eq_text = Label(
                    text=f"  {slot}: {eq.rarity} +{eq.enhancement_level}",
                    font_size=16,
                    color=(1, 0.84, 0, 1)
                )
                self.layout.add_widget(eq_text)
            else:
                empty_text = Label(
                    text=f"  {slot}: Empty",
                    font_size=16,
                    color=(0.6, 0.6, 0.6, 1)
                )
                self.layout.add_widget(empty_text)
        
        # Buttons
        btn_frame = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.2),
            pos_hint={"x": 0, "y": 0.7},
            spacing=10
        )
        
        cultivate_btn = Button(
            text="Cultivate",
            font_size=18,
            size_hint=(0.3, 1),
            background_color=(0.3, 0.5, 0.8, 1)
        )
        cultivate_btn.bind(on_press=self._on_cultivate)
        btn_frame.add_widget(cultivate_btn)
        
        inventory_btn = Button(
            text="Inventory",
            font_size=18,
            size_hint=(0.3, 1),
            background_color=(0.5, 0.3, 0.8, 1)
        )
        inventory_btn.bind(on_press=self._on_inventory)
        btn_frame.add_widget(inventory_btn)
        
        quests_btn = Button(
            text="Quests",
            font_size=18,
            size_hint=(0.3, 1),
            background_color=(0.3, 0.8, 0.5, 1)
        )
        quests_btn.bind(on_press=self._on_quests)
        btn_frame.add_widget(quests_btn)
        
        self.layout.add_widget(btn_frame)
    
    def _on_back(self, instance):
        """Go back to world map."""
        self.manager.current = "world_map"
    
    def _on_cultivate(self, instance):
        """Handle cultivation."""
        self.player.qi = min(self.player.qi + 30, self.player.max_qi)
        self.player.exp += 10
        SaveSystem.save_game(self.player.to_dict())
        self._update_displays()
        self._show_message("Cultivation", "Qi restored and experience gained!")
    
    def _on_inventory(self, instance):
        """Go to inventory."""
        self.manager.current = "inventory"
    
    def _on_quests(self, instance):
        """Go to quests."""
        self.manager.current = "quests"
    
    def _update_displays(self):
        """Update the display stats."""
        self.hp_display.text = f"HP: {self.player.hp}/{self.player.max_hp}"
        self.qi_display.text = f"Qi: {self.player.qi}/{self.player.max_qi}"
        self.atk_display.text = f"Attack: {self.player.attack}"
        self_def_display.text = f"Defense: {self.player.defense}"
    
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


class QuestsScreen(GameScreen):
    """Quests and missions screen."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.back_btn = Button(
            text="← Back",
            size_hint=(1, 0.1),
            background_color=(0.3, 0.3, 0.3, 1)
        )
        self.back_btn.bind(on_press=self._on_back)
        self.layout.add_widget(self.back_btn)
        
        title = Label(
            text="Quests & Missions",
            font_size=36,
            center_x="center",
            size_hint_y=0.1,
            color=(1, 0.84, 0, 1)
        )
        self.layout.add_widget(title)
        
        self.quests_list = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.8),
            pos_hint={"x": 0, "y": 0.1},
            spacing=10
        )
        self.layout.add_widget(self.quests_list)
        
        self._refresh_quests()
        
        # Buttons
        btn_frame = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.15),
            pos_hint={"x": 0, "y": 0.9},
            spacing=10
        )
        
        accept_all_btn = Button(
            text="Accept All Available",
            font_size=16,
            size_hint=(0.4, 1),
            background_color=(0.3, 0.5, 0.8, 1)
        )
        btn_frame.add_widget(accept_all_btn)
        
        close_btn = Button(
            text="Close",
            font_size=16,
            size_hint=(0.4, 1),
            background_color=(0.5, 0.3, 0.8, 1)
        )
        close_btn.bind(on_press=self._on_back)
        btn_frame.add_widget(close_btn)
        
        self.layout.add_widget(btn_frame)
    
    def _refresh_quests(self):
        """Refresh the quests list."""
        self.quests_list.clear_widgets()
        
        if not self.player.quests:
            no_quests = Label(
                text="No active quests.\nAccept quests from the village NPCs.",
                font_size=18,
                color=(0.8, 0.8, 0.8, 1),
                size_hint_y=None,
                height=60
            )
            self.quests_list.add_widget(no_quests)
            return
        
        for quest in self.player.quests:
            # Determine status
            status = "Active" if not quest.is_completed else "Completed"
            completed_text = " (Completed)" if quest.is_completed else ""
            
            q_btn = Button(
                text=f"{quest.name}: {status}",
                font_size=16,
                size_hint_y=None,
                height=40,
                background_color=(
                    (0.3, 0.8, 0.3, 1) if not quest.is_completed else (0.5, 0.5, 0.5, 1)
                )
            )
            q_btn.bind(on_press=lambda instance, q=quest: self._on_quest_selected(q))
            self.quests_list.add_widget(q_btn)
    
    def _on_quest_selected(self, quest):
        """Handle quest selection."""
        # Show quest details
        detail_text = f"Quest: {quest.name}\n\n{quest.description}\n\n"
        for obj_type, target, current, required in quest.objectives:
            detail_text += f"• {obj_type}: {current}/{required}\n"
        
        detail_text += f"\nReward: {quest.reward_value} {quest.reward_type}"
        
        detail_label = Label(
            text=detail_text,
            font_size=14,
            size_hint_y=None,
            text_size=(self.layout.width * 0.8, None)
        )
        
        # Simple popup
        from kivy.uix.popup import Popup
        popup = Popup(
            title=f"Quest: {quest.name}",
            content=detail_label,
            size_hint=(0.8, 0.7)
        )
        popup.open()
    
    def _on_back(self, instance):
        """Go back to world map."""
        self.manager.current = "world_map"


# ============================================================
# SETTINGS SCREEN
# ============================================================

class SettingsScreen(Screen):
    """Settings screen for game options."""
    
    def __init__(self, **kwargs):
        super().__init__(name="settings", **kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.back_btn = Button(
            text="← Back",
            size_hint=(1, 0.1),
            background_color=(0.3, 0.3, 0.3, 1)
        )
        self.back_btn.bind(on_press=self._on_back)
        self.layout.add_widget(self.back_btn)
        
        title = Label(
            text="Settings",
            font_size=36,
            center_x="center",
            size_hint_y=0.1,
            color=(1, 0.84, 0, 1)
        )
        self.layout.add_widget(title)
        
        # Touch sensitivity
        touch_frame = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.15),
            spacing=5
        )
        touch_label = Label(
            text="Touch Sensitivity:",
            font_size=18,
            bold=True,
            color=(1, 1, 1, 1)
        )
        touch_frame.add_widget(touch_label)
        
        self.touch_sensitivity = Label(
            text="Medium",
            font_size=18,
            color=(1, 0.84, 0, 1)
        )
        touch_frame.add_widget(self.touch_sensitivity)
        
        self.layout.add_widget(touch_frame)
        
        # Sound volume
        sound_frame = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.15),
            spacing=5
        )
        sound_label = Label(
            text="Sound Volume:",
            font_size=18,
            bold=True,
            color=(1, 1, 1, 1)
        )
        sound_frame.add_widget(sound_label)
        
        self.sound_volume = Label(
            text="80%",
            font_size=18,
            color=(1, 0.84, 0, 1)
        )
        sound_frame.add_widget(self.sound_volume)
        
        self.layout.add_widget(sound_frame)
        
        # Music volume
        music_frame = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.15),
            spacing=5
        )
        music_label = Label(
            text="Music Volume:",
            font_size=18,
            bold=True,
            color=(1, 1, 1, 1)
        )
        music_frame.add_widget(music_label)
        
        self.music_volume = Label(
            text="70%",
            font_size=18,
            color=(1, 0.84, 0, 1)
        )
        music_frame.add_widget(self.music_volume)
        
        self.layout.add_widget(music_frame)
        
        # Buttons
        btn_frame = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.2),
            pos_hint={"x": 0, "y": 0.85},
            spacing=10
        )
        
        save_btn = Button(
            text="Save Settings",
            font_size=18,
            size_hint=(0.4, 1),
            background_color=(0.3, 0.5, 0.8, 1)
        )
        save_btn.bind(on_press=self._on_save_settings)
        btn_frame.add_widget(save_btn)
        
        reset_btn = Button(
            text="Reset to Default",
            font_size=18,
            size_hint=(0.4, 1),
            background_color=(0.7, 0.3, 0.3, 1)
        )
        reset_btn.bind(on_press=self._on_reset_settings)
        btn_frame.add_widget(reset_btn)
        
        self.layout.add_widget(btn_frame)
    
    def _on_back(self, instance):
        self.manager.current = "main_menu"
    
    def _on_save_settings(self, instance):
        """Save the current settings."""
        # Read from UI and save
        settings = {
            "touch_sensitivity": self.touch_sensitivity.text.lower(),
            "sound_volume": float(self.sound_volume.text.replace("%", "")) / 100,
            "music_volume": float(self.music_volume.text.replace("%", "")) / 100
        }
        
        # Update player settings
        if self.player:
            self.player.settings = settings
        
        # Save to file
        SaveSystem.save_game(self.player.to_dict() if self.player else {})
        
        self._show_message("Settings Saved", "All settings have been saved successfully!")
    
    def _on_reset_settings(self, instance):
        """Reset settings to default."""
        self.touch_sensitivity.text = "Medium"
        self.sound_volume.text = "80%"
        self.music_volume.text = "70%"
        self._on_save_settings(instance)
    
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


# ============================================================
# MAIN APPLICATION
# ============================================================

class ImmortalRealmsApp(App):
    """Main application class for Immortal Realms."""
    
    def build(self):
        """Build the Kivy application."""
        self.title = "Immortal Realms"
        self.screen_manager = GameScreenManager(transition=FadeTransition())
        
        # Register screens
        self.screen_manager.add_widget(MainMenuScreen(name="main_menu"))
        self.screen_manager.add_widget(SettingsScreen(name="settings"))
        self.screen_manager.add_widget(WorldMapScreen(name="world_map"))
        
        # Initialize game state
        self._init_game_state()
        
        return self.screen_manager
    
    def _init_game_state(self):
        """Initialize or load game state."""
        save_data = SaveSystem.load_save()
        
        # Check if this is a new game or continue
        if save_data.get("player_name", "") == "" or save_data.get("cultivation_rank") == "Body Tempering" and save_data.get("level", 0) == 1:
            # New game - reset to defaults
            self.player = Player(SaveSystem.get_default_save())
            self._setup_new_game()
        else:
            # Continue existing game
            self.player = Player(save_data)
            self._continue_existing_game()
    
    def _setup_new_game(self):
        """Set up a new game."""
        # Tutorial/introduction
        pass
    
    def _continue_existing_game(self):
        """Continue an existing game."""
        pass
    
    def start_new_game(self):
        """Start a new game from the main menu."""
        # Initialize player with default data
        self.player = Player(SaveSystem.get_default_save())
        # Switch to world map
        self.switch_screen("world_map")
    
    def continue_game(self):
        """Continue the last saved game."""
        save_data = SaveSystem.load_save()
        if save_data.get("player_name", ""):
            self.player = Player(save_data)
            # Need to re-add screens that require player
            self._rebuild_screens_with_player()
        else:
            self.start_new_game()
    
    def _rebuild_screens_with_player(self):
        """Rebuild screens that require player data."""
        # Remove existing screens that need player
        screens_to_remove = [s for s in self.screen_manager.children if s.name not in ["main_menu", "settings"]]
        for screen in screens_to_remove:
            self.screen_manager.remove_widget(screen)
        
        # Re-add screens with player data
        self.screen_manager.add_widget(WorldMapScreen(name="world_map"))
        self.screen_manager.add_widget(CharacterScreen(name="character"))
        self.screen_manager.add_widget(QuestsScreen(name="quests"))
    
    def switch_screen(self, screen_name):
        """Switch to a different screen."""
        # Make sure player is set on the target screen
        target_screen = self.screen_manager.get_screen(screen_name)
        if hasattr(target_screen, 'player'):
            target_screen.player = self.player
        
        # Update player reference on all relevant screens
        for screen in self.screen_manager.children:
            if hasattr(screen, 'player'):
                screen.player = self.player
        
        self.screen_manager.current = screen_name
    
    def build_config(self, config):
        """Build configuration."""
        config.setdefaults('graphics', {
            'touch_sensitivity': 'medium',
            'sound_volume': 0.8,
            'music_volume': 0.7
        })
    
    def build_settings(self, settings):
        """Build settings panel."""
        return settings
    
    def on_pause(self):
        """Handle app pause (save game)."""
        if self.player:
            SaveSystem.save_game(self.player.to_dict())
        return True


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Initialize and run the game
    try:
        app = ImmortalRealmsApp()
        app.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Game error: {e}")