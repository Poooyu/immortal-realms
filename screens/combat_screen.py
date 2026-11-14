#!/usr/bin/env python3
"""Combat Screen - Real-time combat system for Immortal Realms"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from immortal_realms.main import Player, MONSTER_TYPES, SaveSystem, EQUIPMENT_SLOTS, Window


class CombatScreen(Screen):
    """Real-time combat screen with touch controls."""
    
    def __init__(self, **kwargs):
        super().__init__(name="combat", **kwargs)
        self.current_monster = None
        self.player_hp = 0
        self.player_max_hp = 0
        self.player_qi = 0
        self.player_max_qi = 0
        self.is_player_turn = True
        self.combat_log = []
        self.dodge_pending = False
        
        # Auto-attack timer for continuous combat
        self.attack_timer = None
        self.combat_speed = 1.0  # seconds between auto-attacks
        
    def on_enter(self, *args):
        """Called when the screen is entered."""
        self._initialize_combat()
    
    def _initialize_combat(self):
        """Initialize a new combat encounter."""
        # Get the player from the app
        app = App.get_running_app()
        player = app.player if app.player else Player()
        
        # Get region from world map
        world_screen = self.manager.get_screen("world_map")
        region_name = getattr(world_screen, 'current_region', 'Mortal Village')
        region = world_screen.world_regions.get(region_name)
        
        if region:
            # Get random monster based on player level and region
            monster_type = random.choice(region.monsters) if region.monsters else "Spirit Rabbit"
            self.current_monster = Monster(monster_type, level=player.level)
        else:
            self.current_monster = Monster("Spirit Rabbit", level=player.level)
        
        # Set player combat stats
        self.player_hp = player.hp
        self.player_max_hp = player.max_hp
        self.player_qi = player.qi
        self.player_max_qi = player.max_qi
        
        self.combat_log = []
        self.is_player_turn = True
        self.dodge_pending = False
        
        # Start combat UI
        self._build_combat_ui()
        self._update_combat_display()
        
        # Start auto-attack if no player action
        if not self.attack_timer:
            self.attack_timer = Clock.schedule_interval(self._auto_attack, self.combat_speed)
    
    def _build_combat_ui(self):
        """Build the combat interface."""
        self.layout = FloatLayout()
        self.add_widget(self.layout)
        
        # Monster info panel
        with self.layout.canvas:
            Color(0.2, 0.1, 0.1, 0.8)
            Rectangle(pos=(Window.width * 0.1, Window.height * 0.6), 
                     size=(Window.width * 0.3, Window.height * 0.3))
        
        self.monster_name = Label(
            text=f"Wild {self.current_monster.name} (Lvl {self.current_monster.level})",
            font_size=24,
            center_x="center",
            center_y="0.7",
            bold=True,
            color=(1, 0.3, 0.3, 1)
        )
        self.layout.add_widget(self.monster_name)
        
        self.monster_hp_bar = Label(
            text=f"HP: {self.current_monster.health}/{self.current_monster.max_health}",
            font_size=18,
            center_x="center",
            center_y="0.55",
            color=(1, 0.5, 0.5, 1)
        )
        self.layout.add_widget(self.monster_hp_bar)
        
        # Player info panel
        with self.layout.canvas:
            Color(0.1, 0.2, 0.1, 0.8)
            Rectangle(pos=(Window.width * 0.7, Window.height * 0.6), 
                     size=(Window.width * 0.3, Window.height * 0.3))
        
        self.player_name = Label(
            text=f"Cultivator - {player.rank} {player.subrealm}",
            font_size=20,
            center_x="center",
            center_y="0.4",
            color=(0.8, 0.9, 0.8, 1)
        )
        self.layout.add_widget(self.player_name)
        
        self.player_hp_bar = Label(
            text=f"HP: {self.player_hp}/{self.player_max_hp}",
            font_size=18,
            center_x="center",
            center_y="0.25",
            color=(0.8, 0.9, 0.8, 1)
        )
        self.layout.add_widget(self.player_hp_bar)
        
        self.player_qi_bar = Label(
            text=f"Qi: {int(self.player_qi)}/{self.player_max_qi}",
            font_size=16,
            center_x="center",
            center_y="0.15",
            color=(1, 0.8, 0.3, 1)
        )
        self.layout.add_widget(self.player_qi_bar)
        
        # Action buttons panel
        btn_height = Window.height * 0.08
        btn_width = Window.width * 0.35
        btn_y = Window.height * 0.85
        btn_x_start = Window.width * 0.05
        spacing = Window.width * 0.04
        
        # Basic Attack
        self.attack_btn = Button(
            text="Basic Attack",
            font_size=20,
            size_hint=(btn_width, btn_height),
            pos_hint={"x": 0.05, "y": 0.85},
            background_color=(0.8, 0.3, 0.3, 1),
            bold=True
        )
        self.attack_btn.bind(on_press=self._on_basic_attack)
        self.layout.add_widget(self.attack_btn)
        
        # Skill
        self.skill_btn = Button(
            text="Skill",
            font_size=20,
            size_hint=(btn_width, btn_height),
            pos_hint={"x": 0.05, "y": 0.72},
            background_color=(0.3, 0.5, 0.8, 1),
            bold=True
        )
        self.skill_btn.bind(on_press=self._on_skill)
        self.layout.add_widget(self.skill_btn)
        
        # Elemental Ability
        self.ability_btn = Button(
            text="Elemental Ability",
            font_size=20,
            size_hint=(btn_width, btn_height),
            pos_hint={"x": 0.05, "y": 0.59},
            background_color=(0.3, 0.8, 0.5, 1),
            bold=True
        )
        self.ability_btn.bind(on_press=self._on_elemental_ability)
        self.layout.add_widget(self.ability_btn)
        
        # Flying Sword
        self.flying_sword_btn = Button(
            text="Flying Sword",
            font_size=20,
            size_hint=(btn_width, btn_height),
            pos_hint={"x": 0.05, "y": 0.46},
            background_color=(0.5, 0.5, 0.8, 1),
            bold=True
        )
        self.flying_sword_btn.bind(on_press=self._on_flying_sword)
        self.layout.add_widget(self.flying_sword_btn)
        
        # Dash/Dodge
        self.dodge_btn = Button(
            text="Dash/Dodge",
            font_size=20,
            size_hint=(btn_width, btn_height),
            pos_hint={"x": 0.05, "y": 0.33},
            background_color=(0.3, 0.8, 0.3, 1),
            bold=True
        )
        self.dodge_btn.bind(on_press=self._on_dodge)
        self.layout.add_widget(self.dodge_btn)
        
        # Ultimate
        self.ultimate_btn = Button(
            text="Ultimate Ability",
            font_size=20,
            size_hint=(btn_width, btn_height),
            pos_hint={"x": 0.05, "y": 0.2},
            background_color=(0.8, 0.5, 0.2, 1),
            bold=True
        )
        self.ultimate_btn.bind(on_press=self._on_ultimate)
        self.layout.add_widget(self.ultimate_btn)
        
        # Combat log
        self.combat_log_label = Label(
            text="",
            font_size=14,
            size_hint=(0.9, 0.3),
            center_x="center",
            y=Window.height * 0.05,
            text_size=(Window.width * 0.9, None)
        )
        self.layout.add_widget(self.combat_log_label)
        
        # Update log
        self._update_log_display()
    
    def _update_log_display(self):
        """Update the combat log display."""
        log_text = "\n".join(self.combat_log[-10:])  # Show last 10 entries
        self.combat_log_label.text = log_text
    
    def _add_log(self, message):
        """Add a message to the combat log."""
        self.combat_log.append(message)
        self._update_log_display()
    
    def _update_combat_display(self):
        """Update the combat display with current stats."""
        self.monster_hp_bar.text = f"HP: {self.current_monster.health}/{self.current_monster.max_health}"
        self.player_hp_bar.text = f"HP: {self.player_hp}/{self.player_max_hp}"
        self.player_qi_bar.text = f"Qi: {int(self.player_qi)}/{self.player_max_qi}"
    
    def _start_monster_turn(self, dt):
        """Start the monster's turn in the combat loop."""
        if not self.current_monster.is_alive():
            return
        
        # Monster attacks
        if self.is_player_turn:  # Player may have dodged
            # Check dodge
            dodge_chance = 0.6
            if random.random() < dodge_chance and not self.dodge_pending:
                self._add_log(f"The {self.current_monster.name}'s attack was dodged!")
                self.is_player_turn = True
                self._update_combat_display()
                self.dodge_pending = False
                return
        
        # Calculate damage
        damage = self.current_monster.attack
        self.player_hp -= damage
        
        self._add_log(f"The {self.current_monster.name} attacks you for {damage} damage!")
        self._update_combat_display()
        
        # Check player death
        if self.player_hp <= 0:
            self._add_log("You have been defeated...")
            self._on_player_defeated()
            return
        
        # Switch to player turn
        self.is_player_turn = True
        self.dodge_pending = False
        
        # Stop monster turn timer
        if self.attack_timer:
            self.attack_timer.cancel()
            self.attack_timer = None
    
    def _auto_attack(self, dt):
        """Auto-attack when player doesn't act."""
        if not self.is_player_turn or not self.current_monster.is_alive():
            return
        
        # Player basic attack
        damage = self.player.attack
        actual_damage = self.current_monster.take_damage(damage)
        
        self._add_log(f"You attack {self.current_monster.name} for {actual_damage} damage!")
        self._update_combat_display()
        
        if not self.current_monster.is_alive():
            self._add_log(f"You defeated the {self.current_monster.name}!")
            self._on_victory()
            # Cancel auto-attack timer
            if self.attack_timer:
                self.attack_timer.cancel()
                self.attack_timer = None
        else:
            # Monster's turn after player attack
            self.is_player_turn = False
            Clock.schedule_once(self._start_monster_turn, 1.0)
    
    def _on_basic_attack(self, instance):
        """Handle basic attack button press."""
        if not self.is_player_turn:
            return
        
        damage = self.player.attack
        actual_damage = self.current_monster.take_damage(damage)
        
        self._add_log(f"You attack {self.current_monster.name} for {actual_damage} damage!")
        self._update_combat_display()
        
        if not self.current_monster.is_alive():
            self._add_log(f"You defeated the {self.current_monster.name}!")
            self._on_victory()
            if self.attack_timer:
                self.attack_timer.cancel()
                self.attack_timer = None
        else:
            # Monster's turn
            self.is_player_turn = False
            Clock.schedule_once(self._start_monster_turn, 1.0)
    
    def _on_skill(self, instance):
        """Handle skill button press."""
        if not self.is_player_turn:
            return
        
        # Check if player has skills
        if self.player.skills:
            skill_name = self.player.skills[0]  # Use first skill
            damage = int(self.player.attack * 1.5)
            self._add_log(f"You use skill: {skill_name} for {damage} damage!")
        else:
            self._add_log("You attempt to use a skill but know no skills yet!")
            damage = 0
        
        # Monster attacks after
        self.is_player_turn = False
        Clock.schedule_once(self._start_monster_turn, 1.0)
    
    def _on_elemental_ability(self, instance):
        """Handle elemental ability button press."""
        if not self.is_player_turn:
            return
        
        # Determine elemental path based on cultivation
        element = self._determine_elemental_path()
        if element:
            damage = int(self.player.attack * 2.0)
            self._add_log(f"You unleash {element} elemental power for {damage} damage!")
        else:
            self._add_log("You concentrate your energy but find no elemental path attuned!")
            damage = 0
        
        self.player_qi = max(0, self.player.qi - 20)  # Qi cost
        self._update_combat_display()
        
        # Monster's turn
        self.is_player_turn = False
        Clock.schedule_once(self._start_monster_turn, 1.0)
    
    def _determine_elemental_path(self):
        """Determine the player's elemental cultivation path."""
        # Based on cultivation rank and skills
        rank_idx = min(len(ELEMENTAL_PATHS) - 1, CULTIVATION_RANKS.index(self.player.rank) 
                       if self.player.rank in CULTIVATION_RANKS else 0)
        return ELEMENTAL_PATHS[rank_idx] if ELEMENTAL_PATHS else None
    
    def _on_flying_sword(self, instance):
        """Handle flying sword attack."""
        if not self.is_player_turn:
            return
        
        # Flying sword deals weapon-based damage
        equip = self.player.equipment.get("Sword")
        if equip:
            damage = int(equip.stats.get("damage", self.player.attack) * 1.5)
            self._add_log(f"You summon your flying sword for {damage} damage!")
        else:
            damage = int(self.player.attack * 1.2)
            self._add_log(f"You summon a flying sword for {damage} damage!")
        
        self.player_qi = max(0, self.player.qi - 15)  # Qi cost for flying sword
        self._update_combat_display()
        
        # Monster's turn
        self.is_player_turn = False
        Clock.schedule_once(self._start_monster_turn, 1.0)
    
    def _on_dodge(self, instance):
        """Handle dodge/dash button press."""
        if not self.is_player_turn:
            return
        
        self.dodge_pending = True
        self._add_log("You prepare to dodge the next attack!")
        
        # Immediately end player turn, monster will check dodge
        self.is_player_turn = False
        Clock.schedule_once(self._start_monster_turn, 0.5)
    
    def _on_ultimate(self, instance):
        """Handle ultimate ability button press."""
        if not self.is_player_turn:
            return
        
        # Ultimate ability - powerful attack with high Qi cost
        if self.player_qi >= 50:
            damage = int(self.player.attack * 3.5)
            self.player_qi -= 50
            self._add_log(f"You unleash your ultimate ability for {damage} damage!")
            self._update_combat_display()
        else:
            self._add_log("Not enough Qi for ultimate ability! Build up Qi first.")
        
        # Monster's turn after ultimate
        self.is_player_turn = False
        Clock.schedule_once(self._start_monster_turn, 1.0)
    
    def _on_victory(self):
        """Handle victory after defeating the monster."""
        # Gain experience
        exp_gain = self.current_monster.exp_reward
        gold_gain = self.current_monster.gold_reward
        
        self._add_log(f"Gained {exp_gain} EXP and {gold_gain} gold!")
        
        self.player.gain_exp(exp_gain)
        self.player.spiritual_stones += gold_gain
        
        # Loot check
        if random.random() < 0.3:  # 30% chance of equipment drop
            self._roll_loot()
        
        # Check for region unlock
        self._check_region_unlock()
        
        self._update_combat_display()
        self._show_victory()
        
        # Clean up
        if self.attack_timer:
            self.attack_timer.cancel()
            self.attack_timer = None
    
    def _roll_loot(self):
        """Roll for equipment loot."""
        # Determine rarity based on monster level and player cultivation
        rarity_roll = random.random()
        rank_bonus = min(len(EQUIPMENT_RARITY) - 1, 
                        max(0, CULTIVATION_RANKS.index(self.player.rank) - 2)
                        if self.player.rank in CULTIVATION_RANKS else 0)
        
        # Base rarity Common, adjust based on rank
        if rank_bonus >= 4 and rarity_roll < 0.4:
            rarity = "Rare"
        elif rank_bonus >= 5 and rarity_roll < 0.5:
            rarity = "Epic"
        elif rank_bonus >= 6 and rarity_roll < 0.3:
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
        
        self._add_log(f"Obtained: {rarity} {slot}")
    
    def _check_region_unlock(self):
        """Check if any new regions should be unlocked."""
        for region_name, region in world_screen.world_regions.items():
            if region.check_unlock(self.player) and region_name not in self.player.unlocked_regions:
                self.player.unlocked_regions.append(region_name)
                SaveSystem.save_game(self.player.to_dict())
                self._add_log(f"Region unlocked: {region_name}!")
    
    def _on_player_defeated(self):
        """Handle player defeat."""
        self._add_log("You have been defeated in combat...")
        # Return to world map or heal at cost
        self.player.hp = self.player.max_hp  # Partial recovery
        SaveSystem.save_game(self.player.to_dict())
        self._switch_to_world_map()
    
    def _switch_to_world_map(self):
        """Switch back to world map."""
        self.manager.current = "world_map"
    
    def _show_victory(self):
        """Show victory popup."""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        
        victory_text = (f"Victory!\n\n"
                       f"You defeated the {self.current_monster.name}!\n"
                       f"Gained {self.current_monster.exp_reward} EXP and "
                       f"{self.current_monster.gold_reward} gold!\n")
        
        if self.player.inventory:
            last_loot = self.player.inventory[-1]
            victory_text += f"Obtained: {last_loot.get('rarity', 'Common')} equipment!\n"
        
        popup = Popup(
            title="Combat Victory",
            content=Label(text=victory_text),
            size_hint=(0.8, 0.6)
        )
        popup.open()


# Helper function for random monster selection
import random
from immortal_realms.main import Monster, CULTIVATION_RANKS, EQUIPMENT_RARITY, EQUIPMENT_SLOTS, REGIONS, SaveSystem, Player


def get_random_monster(region_name, player_level):
    """Get a random monster for the given region and player level."""
    from immortal_realms.main import REGIONS
    region = REGIONS.get(region_name)
    if region:
        valid_monsters = [m for m in region.monsters if m]
        if valid_monsters:
            monster_type = random.choice(valid_monsters)
            return Monster(monster_type, level=player_level)
    return Monster("Spirit Rabbit", level=player_level)