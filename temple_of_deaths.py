import random
import sys
import os
import math # Used for distance calculation

# --- Input Handling (Cross-platform attempt) ---
try:
    import getch
    def get_single_char():
        return getch.getch()
except ImportError:
    print("Warning: 'getch' library not found. Falling back to standard input.")
    print("You will need to press ENTER after each command.")
    def get_single_char():
        return input("Enter command: ")

# --- Constants and Configuration ---
MAP_WIDTH = 40
MAP_HEIGHT = 20
MAX_ROOMS = 10
MIN_ROOM_SIZE = 5
MAX_ROOM_SIZE = 10
MAX_MONSTERS_PER_ROOM = 3
MAX_ITEMS_PER_ROOM = 2
MAX_INVENTORY_SIZE = 10 # Reduced from 25 for simplicity
NUM_LEVELS = 5

# Symbols
SYMBOL_WALL = '#'
SYMBOL_FLOOR = '.'
SYMBOL_PLAYER = '@'
SYMBOL_STAIRS_DOWN = '>'
SYMBOL_GOBLIN = 'G'
SYMBOL_DRAGON = 'D'
SYMBOL_WEAPON = '!'
SYMBOL_POTION = '?'
SYMBOL_GOLDEN_IDOL = '$'

# Colors (Optional - may not work on all terminals)
# import colorama
# colorama.init()
# COLOR_RED = "\033[91m"
# COLOR_GREEN = "\033[92m"
# COLOR_YELLOW = "\033[93m"
# COLOR_BLUE = "\033[94m"
# COLOR_MAGENTA = "\033[95m"
# COLOR_CYAN = "\033[96m"
# COLOR_RESET = "\033[0m"

# --- Game Classes ---

class Entity:
    def __init__(self, x, y, char, color="", name="entity"):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.is_alive = True

    def move(self, dx, dy, game):
        new_x = self.x + dx
        new_y = self.y + dy

        if not (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT):
            return False # Out of bounds

        target_tile = game.current_level.game_map[new_y][new_x]

        if target_tile == SYMBOL_WALL:
            return False # Hit a wall

        # Check for other entities at target location
        target_entity = game.current_level.get_entity_at(new_x, new_y, exclude=self)

        if target_entity:
            if isinstance(self, Player) and isinstance(target_entity, Monster):
                game.handle_combat(self, target_entity)
                return False # Player's move was an attack, not a movement into the space
            elif isinstance(self, Monster) and isinstance(target_entity, Player):
                 game.handle_combat(self, target_entity)
                 return True # Monster successfully moved into player's space to attack
            else:
                 return False # Cannot move onto another entity (unless attacking)


        self.x = new_x
        self.y = new_y
        return True

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, SYMBOL_PLAYER, name="Player")
        self.max_health = 100
        self.health = self.max_health
        self.base_strength = 5
        self.base_armor = 2
        self.strength = self.base_strength
        self.armor = self.base_armor
        self.inventory = []
        self.equipped_weapon = None
        self.cheat_mode = False

    def add_item(self, item):
        if len(self.inventory) < MAX_INVENTORY_SIZE:
            self.inventory.append(item)
            return True
        return False

    def equip_weapon(self, weapon):
        if self.equipped_weapon:
            self.inventory.append(self.equipped_weapon) # Put current weapon back
            self.strength -= self.equipped_weapon.damage # Revert strength boost

        self.equipped_weapon = weapon
        self.strength += weapon.damage
        self.inventory.remove(weapon) # Remove new weapon from inventory
        self.game.add_message(f"You equip the {weapon.name}.")


    def use_potion(self, potion):
         heal_amount = random.randint(15, 30) # Random heal amount
         self.health += heal_amount
         if self.health > self.max_health:
             self.health = self.max_health
         self.inventory.remove(potion)
         self.game.add_message(f"You drink the {potion.name} and heal {heal_amount} HP.")


    def take_damage(self, amount):
        if self.cheat_mode:
            self.game.add_message("Cheat mode active! You take no damage.")
            return
        damage_taken = max(0, amount - self.armor)
        self.health -= damage_taken
        self.game.add_message(f"You take {damage_taken} damage.")
        if self.health <= 0:
            self.is_alive = False
            self.game.state = 'lost'


class Monster(Entity):
    def __init__(self, x, y, char, name, health, strength):
        super().__init__(x, y, char, name=name)
        self.max_health = health
        self.health = health
        self.strength = strength
        self.game = None # Will be set by the Game class

    def take_turn(self):
        if not self.is_alive:
            return

        # Simple AI: Move towards the player if within a certain range
        player = self.game.player
        if not player.is_alive:
            return

        dist_x = player.x - self.x
        dist_y = player.y - self.y
        distance = math.sqrt(dist_x**2 + dist_y**2)

        if distance < 10: # Move towards player if within 10 units
            dx, dy = 0, 0
            if abs(dist_x) > abs(dist_y):
                dx = 1 if dist_x > 0 else -1
            else:
                dy = 1 if dist_y > 0 else -1

            # Try moving in the calculated direction
            if not self.move(dx, dy, self.game):
                # If blocked, try moving in the other direction (dy instead of dx, or dx instead of dy)
                if dx != 0 and dy == 0:
                    if self.move(dx, 1, self.game): return
                    if self.move(dx, -1, self.game): return
                elif dy != 0 and dx == 0:
                    if self.move(1, dy, self.game): return
                    if self.move(-1, dy, self.game): return
                # If still blocked, just try a random adjacent move
                else:
                     random_dx = random.choice([-1, 0, 1])
                     random_dy = random.choice([-1, 0, 1])
                     if (random_dx != 0 or random_dy != 0) and (random_dx == 0 or random_dy == 0): # Only cardinal moves
                         self.move(random_dx, random_dy, self.game)


        else: # If player is far away, maybe just random movement
             random_dx = random.choice([-1, 0, 1])
             random_dy = random.choice([-1, 0, 1])
             if (random_dx != 0 or random_dy != 0) and (random_dx == 0 or random_dy == 0): # Only cardinal moves
                 self.move(random_dx, random_dy, self.game)


    def take_damage(self, amount):
        damage_taken = max(0, amount) # No armor for monsters in this simple version
        self.health -= damage_taken
        self.game.add_message(f"The {self.name} takes {damage_taken} damage.")
        if self.health <= 0:
            self.is_alive = False
            self.char = '%' # Symbol for dead monster/corpse
            self.game.add_message(f"The {self.name} dies!")
            # Monsters don't drop items in this simple version

class Goblin(Monster):
    def __init__(self, x, y):
        super().__init__(x, y, SYMBOL_GOBLIN, "Goblin", health=20, strength=5)

class Dragon(Monster):
    def __init__(self, x, y):
        super().__init__(x, y, SYMBOL_DRAGON, "Dragon", health=50, strength=15)
        # Simple Dragon behavior: just stronger stats

class Item(Entity):
    def __init__(self, x, y, char, name, item_type):
        super().__init__(x, y, char, name=name)
        self.item_type = item_type # e.g., 'weapon', 'potion', 'idol'

class Weapon(Item):
    def __init__(self, x, y, name, damage):
        super().__init__(x, y, SYMBOL_WEAPON, name, 'weapon')
        self.damage = damage

class Potion(Item):
    def __init__(self, x, y, name):
        super().__init__(x, y, SYMBOL_POTION, name, 'potion')

class GoldenIdol(Item):
    def __init__(self, x, y):
        super().__init__(x, y, SYMBOL_GOLDEN_IDOL, "Golden Idol", 'idol')


# --- Level Generation ---

class Level:
    def __init__(self, level_number):
        self.level_number = level_number
        self.game_map = [['' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.monsters = []
        self.items = []
        self.player_start = (0, 0)
        self.generate_level()

    def generate_level(self):
        # Fill with walls
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                self.game_map[y][x] = SYMBOL_WALL

        rooms = []
        for _ in range(MAX_ROOMS):
            w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            x = random.randint(1, MAP_WIDTH - w - 1)
            y = random.randint(1, MAP_HEIGHT - h - 1)

            new_room = {'x1': x, 'y1': y, 'x2': x + w -1, 'y2': y + h - 1}

            # Check for intersections (simple overlap check)
            intersect = False
            for room in rooms:
                 if (new_room['x1'] <= room['x2'] and new_room['x2'] >= room['x1'] and
                     new_room['y1'] <= room['y2'] and new_room['y2'] >= room['y1']):
                     intersect = True
                     break

            if not intersect:
                # Carve out the room
                for ry in range(new_room['y1'], new_room['y2'] + 1):
                    for rx in range(new_room['x1'], new_room['x2'] + 1):
                        self.game_map[ry][rx] = SYMBOL_FLOOR
                rooms.append(new_room)

        # Connect rooms with corridors
        for i in range(1, len(rooms)):
            prev_room = rooms[i-1]
            current_room = rooms[i]

            # Center points of rooms
            prev_center_x = random.randint(prev_room['x1'], prev_room['x2'])
            prev_center_y = random.randint(prev_room['y1'], prev_room['y2'])
            current_center_x = random.randint(current_room['x1'], current_room['x2'])
            current_center_y = random.randint(current_room['y1'], current_room['y2'])


            # Dig corridors
            if random.choice([True, False]): # Horizontal first or Vertical first
                self._create_h_corridor(prev_center_x, current_center_x, prev_center_y)
                self._create_v_corridor(prev_center_y, current_center_y, current_center_x)
            else:
                self._create_v_corridor(prev_center_y, current_center_y, prev_center_x)
                self._create_h_corridor(prev_center_x, current_center_x, current_center_y)

        # Place stairs down (if not the last level)
        if self.level_number < NUM_LEVELS:
            stair_placed = False
            while not stair_placed:
                # Place stairs in a random floor tile
                rand_x = random.randint(1, MAP_WIDTH - 2)
                rand_y = random.randint(1, MAP_HEIGHT - 2)
                if self.game_map[rand_y][rand_x] == SYMBOL_FLOOR:
                    self.game_map[rand_y][rand_x] = SYMBOL_STAIRS_DOWN
                    stair_placed = True

        # Place player start (in the center of the first room)
        if rooms:
            first_room = rooms[0]
            self.player_start = (
                random.randint(first_room['x1'] + 1, first_room['x2'] - 1),
                random.randint(first_room['y1'] + 1, first_room['y2'] - 1)
            )
        else: # Should not happen with MAX_ROOMS > 0, but a fallback
             self.player_start = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
             self.game_map[self.player_start[1]][self.player_start[0]] = SYMBOL_FLOOR # Ensure start is floor

        # Place monsters and items in rooms (excluding the first room where the player starts)
        for i, room in enumerate(rooms):
            if i == 0: continue # Don't place enemies/items in the starting room

            # Place Monsters
            num_monsters = random.randint(0, MAX_MONSTERS_PER_ROOM)
            for _ in range(num_monsters):
                placed = False
                while not placed:
                    mx = random.randint(room['x1'] + 1, room['x2'] - 1)
                    my = random.randint(room['y1'] + 1, room['y2'] - 1)
                    if self.game_map[my][mx] == SYMBOL_FLOOR and not self.get_entity_at(mx, my):
                        if random.random() < 0.7: # 70% chance Goblin
                             self.monsters.append(Goblin(mx, my))
                        else: # 30% chance Dragon
                             self.monsters.append(Dragon(mx, my))
                        placed = True

            # Place Items
            num_items = random.randint(0, MAX_ITEMS_PER_ROOM)
            for _ in range(num_items):
                 placed = False
                 while not placed:
                     ix = random.randint(room['x1'] + 1, room['x2'] - 1)
                     iy = random.randint(room['y1'] + 1, room['y2'] - 1)
                     if self.game_map[iy][ix] == SYMBOL_FLOOR and not self.get_entity_at(ix, iy):
                          item_type = random.choice(['weapon', 'potion'])
                          if item_type == 'weapon':
                              self.items.append(Weapon(ix, iy, random.choice(['Sword', 'Axe', 'Club']), random.randint(3, 8)))
                          elif item_type == 'potion':
                              self.items.append(Potion(ix, iy, random.choice(['Healing Potion', 'Red Brew'])))
                          placed = True

        # Place Golden Idol on the last level
        if self.level_number == NUM_LEVELS:
            idol_placed = False
            while not idol_placed:
                # Place idol in a random floor tile (avoiding player start if possible)
                rand_x = random.randint(1, MAP_WIDTH - 2)
                rand_y = random.randint(1, MAP_HEIGHT - 2)
                if self.game_map[rand_y][rand_x] == SYMBOL_FLOOR and (rand_x, rand_y) != self.player_start and not self.get_entity_at(rand_x, rand_y):
                    self.items.append(GoldenIdol(rand_x, rand_y))
                    idol_placed = True


    def _create_h_corridor(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= y < MAP_HEIGHT and 0 <= x < MAP_WIDTH:
                 self.game_map[y][x] = SYMBOL_FLOOR

    def _create_v_corridor(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
             if 0 <= y < MAP_HEIGHT and 0 <= x < MAP_WIDTH:
                self.game_map[y][x] = SYMBOL_FLOOR

    def get_entity_at(self, x, y, exclude=None):
        # Check for player
        if isinstance(exclude, Player):
             pass # Don't check if we are excluding the player
        elif hasattr(self, 'game') and self.game.player and self.game.player.x == x and self.game.player.y == y and self.game.player is not exclude:
             return self.game.player

        # Check for monsters
        for monster in self.monsters:
            if monster.x == x and monster.y == y and monster.is_alive and monster is not exclude:
                return monster

        # Check for items
        for item in self.items:
            if item.x == x and item.y == y and item is not exclude:
                 return item

        return None


# --- Game Management ---

class Game:
    def __init__(self):
        self.current_level_number = 1
        self.player = None
        self.current_level = None
        self.state = 'playing' # 'playing', 'won', 'lost', 'quit'
        self.message_log = []
        self.levels = {} # Cache levels

    def run(self):
        self.generate_level(self.current_level_number)
        self.player = Player(self.current_level.player_start[0], self.current_level.player_start[1])
        self.player.game = self # Give player a reference to the game

        while self.state == 'playing':
            self.render()
            self.process_input()
            if self.state == 'playing': # Only process monster turns if still playing
                 self.process_monster_turns()
                 self.check_win_loss()

        self.render() # Final render for win/loss screen
        self.display_game_over()

    def add_message(self, message):
        self.message_log.append(message)
        # Keep message log relatively short
        if len(self.message_log) > 5:
            self.message_log.pop(0) # Remove the oldest message

    def generate_level(self, level_number):
        self.add_message(f"Generating Level {level_number}...")
        if level_number in self.levels:
            self.current_level = self.levels[level_number]
        else:
            self.current_level = Level(level_number)
            self.levels[level_number] = self.current_level

        # Set game reference for entities in the new level
        self.current_level.game = self
        for monster in self.current_level.monsters:
             monster.game = self


    def render(self):
        # Clear screen (basic attempt, may not work everywhere)
        os.system('cls' if os.name == 'nt' else 'clear')

        # Display Player Stats
        status_line = f"Level: {self.current_level_number} | "
        status_line += f"HP: {self.player.health}/{self.player.max_health} | "
        status_line += f"Str: {self.player.strength} | "
        status_line += f"Arm: {self.player.armor} | "
        status_line += f"Weapon: {self.player.equipped_weapon.name if self.player.equipped_weapon else 'None'}"
        if self.player.cheat_mode:
            status_line += " | CHEAT MODE"
        print(status_line)
        print("-" * MAP_WIDTH)

        # Display the map
        for y in range(MAP_HEIGHT):
            row = ""
            for x in range(MAP_WIDTH):
                # Check for entities at this position
                entity_char = None
                if self.player.x == x and self.player.y == y:
                    entity_char = self.player.char
                else:
                    for monster in self.current_level.monsters:
                        if monster.x == x and monster.y == y and monster.is_alive:
                            entity_char = monster.char
                            break
                    if not entity_char: # Check items only if no monster/player found
                         for item in self.current_level.items:
                             if item.x == x and item.y == y:
                                 entity_char = item.char
                                 break

                # Print the character (entity or map tile)
                if entity_char:
                    row += entity_char # Add entity symbol
                else:
                    row += self.current_level.game_map[y][x] # Add map tile

            print(row)

        print("-" * MAP_WIDTH)

        # Display Messages
        for msg in self.message_log:
            print(msg)
        print("Commands: (w/k)Up (s/j)Down (a/h)Left (d/l)Right (g)Get (u)Use (i)Inv (>)Descend (c)Cheat (q)Quit")


    def process_input(self):
        command = get_single_char().lower()

        if command == 'q':
            self.state = 'quit'
            self.add_message("You quit the game.")
            return

        if command == 'c':
            self.player.cheat_mode = not self.player.cheat_mode
            self.add_message(f"Cheat mode {'ACTIVATED' if self.player.cheat_mode else 'DEACTIVATED'}.")
            return

        moved = False
        if command in ['w', 'k']: moved = self.player.move(0, -1, self)
        elif command in ['s', 'j']: moved = self.player.move(0, 1, self)
        elif command in ['a', 'h']: moved = self.player.move(-1, 0, self)
        elif command in ['d', 'l']: moved = self.player.move(1, 0, self)
        elif command == 'g':
             self.handle_item_pickup()
             moved = True # Picking up item takes a turn
        elif command == 'i':
             self.show_inventory()
             moved = False # Viewing inventory doesn't take a turn
        elif command == 'u':
             self.handle_use_item()
             moved = True # Using item takes a turn
        elif command == '>':
             self.descend_level()
             moved = False # Descending doesn't take a turn yet (turn happens on next level)
        else:
            self.add_message("Invalid command.")
            moved = False # Invalid command doesn't take a turn

        # Acknowledge standard input if using fallback
        if 'getch' not in sys.modules:
             self.add_message("Press ENTER to continue.")
             # In standard input mode, the enter key is already pressed,
             # so we don't need an extra input() here after commands that took input.
             # This message is just informational.

        if moved:
             # Check if player is on stairs/idol after moving
            tile = self.current_level.game_map[self.player.y][self.player.x]
            if tile == SYMBOL_STAIRS_DOWN:
                 self.add_message("You stand on the stairs down. Press '>' to descend.")
            elif tile == SYMBOL_GOLDEN_IDOL and self.current_level_number == NUM_LEVELS:
                # Idol is handled by pickup 'g', but this message confirms position
                 self.add_message("You stand upon the Golden Idol!")


    def handle_item_pickup(self):
        item_at_loc = None
        for item in self.current_level.items:
            if item.x == self.player.x and item.y == self.player.y:
                item_at_loc = item
                break

        if item_at_loc:
            if self.player.add_item(item_at_loc):
                self.current_level.items.remove(item_at_loc)
                self.add_message(f"You pick up the {item_at_loc.name}.")
                if isinstance(item_at_loc, GoldenIdol):
                     self.state = 'won' # Win condition!
            else:
                self.add_message("Your inventory is full!")
        else:
            self.add_message("There is no item here to pick up.")

    def show_inventory(self):
        self.add_message("Inventory:")
        if not self.player.inventory:
            self.add_message("  Empty")
        else:
            for i, item in enumerate(self.player.inventory):
                details = ""
                if isinstance(item, Weapon):
                     details = f" (Damage: {item.damage})"
                self.add_message(f"  {i + 1}: {item.name}{details}")

    def handle_use_item(self):
        self.show_inventory()
        if not self.player.inventory:
            self.add_message("Nothing to use.")
            return

        self.add_message("Enter item number to use:")
        self.render() # Re-render to show messages and inventory prompt

        try:
            if 'getch' in sys.modules:
                # In getch mode, we need a specific input for the number
                choice = input() # Use standard input for number
            else:
                 choice = input() # Standard input is already active

            item_index = int(choice) - 1

            if 0 <= item_index < len(self.player.inventory):
                item = self.player.inventory[item_index]
                if isinstance(item, Weapon):
                    self.player.equip_weapon(item)
                elif isinstance(item, Potion):
                    self.player.use_potion(item)
                elif isinstance(item, GoldenIdol):
                    self.add_message("You can't 'use' the Golden Idol like that! Pick it up to win!")
                else:
                    self.add_message("You can't use this item.")
            else:
                self.add_message("Invalid item number.")
        except ValueError:
            self.add_message("Invalid input. Enter a number.")


    def handle_combat(self, attacker, defender):
        self.add_message(f"{attacker.name} attacks {defender.name}!")
        damage_dealt = random.randint(max(1, attacker.strength // 2), attacker.strength) # Some damage variation
        defender.take_damage(damage_dealt)

        # Check if defender is still alive after taking damage
        if isinstance(defender, Monster) and not defender.is_alive:
            # Remove dead monster (do this after the combat sequence for this turn)
            pass # Handled in take_damage


    def process_monster_turns(self):
        # Need to create a copy of the list because monsters might be removed
        active_monsters = [m for m in self.current_level.monsters if m.is_alive]
        for monster in active_monsters:
            monster.take_turn()
            if self.state != 'playing': # Stop if player died
                break

        # Clean up dead monsters from the level's monster list
        self.current_level.monsters = [m for m in self.current_level.monsters if m.is_alive]


    def descend_level(self):
        if self.current_level.game_map[self.player.y][self.player.x] == SYMBOL_STAIRS_DOWN:
            if self.current_level_number < NUM_LEVELS:
                self.current_level_number += 1
                self.generate_level(self.current_level_number)
                self.player.x, self.player.y = self.current_level.player_start # Place player at new level's start
                self.add_message(f"You descend to Level {self.current_level_number}.")
            else:
                self.add_message("There are no more stairs down on this level.")
        else:
            self.add_message("You need to be on the stairs (>) to descend.")

    def check_win_loss(self):
        if not self.player.is_alive:
            self.state = 'lost'
            self.add_message("You have died...")

    def display_game_over(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        if self.state == 'won':
            print("*************************")
            print("* *")
            print("* YOU FOUND THE      *")
            print(f"* GOLDEN IDOL!       *")
            print("* *")
            print("* YOU WIN!          *")
            print("* *")
            print("*************************")
        elif self.state == 'lost':
            print("*************************")
            print("* *")
            print("* GAME OVER         *")
            print("* *")
            print("* YOU HAVE FALLEN    *")
            print("* IN THE DEPTHS      *")
            print("* *")
            print("*************************")
        elif self.state == 'quit':
             print("*************************")
             print("* *")
             print("* GAME QUIT         *")
             print("* *")
             print("* THANKS FOR PLAYING!*")
             print("* *")
             print("*************************")

        print("\nPress Enter to exit.")
        input() # Wait for user to see the final message


# --- Main Execution ---

if __name__ == "__main__":
    game = Game()
    game.run()