# Welcome to the DUNGEON

Please have fun playing this python CLI based game I coded out of pure boredom as a second semester senior in high school.

## Gameplay Instructions:

The game is turn-based. You make a move, then monsters make their moves.
Your goal is to reach Level 5 and pick up the Golden Idol.
Your stats (Health, Strength, Armor, Weapon) are displayed at the top.
Messages about events (combat, item pickup) appear below the map.
Controls:

## Movement:
 - w or k : Move Up
 - s or j : Move Down
 - a or h : Move Left
 - d or l : Move Right
 - Attack: Move into an adjacent square occupied by a monster.
 - Pick Up Item: Stand on an item (!, ?) and press g.
 - Use Item (from Inventory):
 - u : Use an item. You will be prompted to enter the inventory slot number (1-based).
 - Inventory: Press i to view your current items.
 - Descend Levels: Stand on the stairs down (>) and press >. Stairs only appear on levels 1-4.
 - Quit Game: Press q.
 - Cheat Mode (Invincibility): Press c to toggle cheat mode. When active, you take no damage.

## Map Symbols:

 - **#**: Wall
 - **.**: Floor
 - **@**: You (The Player)
 - **G**: Goblin (Basic Monster)
 - **D**: Dragon (Stronger Monster - doesn't heal in this simple version)
 - **!**: Weapon (Increases Strength/Damage)
 - **?**: Potion (Heals Health)
 - **>**: Stairs Down
 - **$**: Golden Idol (Win Condition - only on Level 5)
