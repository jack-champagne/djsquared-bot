import numpy as np
from src.map import Map
from src.game_constants import TowerType

def num_tiles_in_range(map: Map):
    # Upper bounds on bounding square
    GUNX = GUNY = int(np.sqrt(TowerType.GUNSHIP.range))
    BOMBX = BOMBY = int(np.sqrt(TowerType.BOMBER.range))

    gunship_tiles = np.zeros(shape=(map.width, map.height), dtype=int)
    bomber_tiles = np.zeros(shape=(map.width, map.height), dtype=int)
    for tile in map.path:
        x, y = tile
        print(tile)
        for tower_x in range(x - GUNX, x + GUNX + 1):
            for tower_y in range(y - GUNY, y + GUNY + 1):
                if not map.is_space(tower_x, tower_y):
                    continue
                if (x - tower_x)**2 + (y - tower_y)**2 <= TowerType.GUNSHIP.range:
                    gunship_tiles[tower_x, tower_y] += 1
        
        for tower_x in range(x - BOMBX, x + BOMBX + 1):
            for tower_y in range(y - BOMBY, y + BOMBY + 1):
                if not map.is_space(tower_x, tower_y):
                    continue
                if (x - tower_x)**2 + (y - tower_y)**2 <= TowerType.BOMBER.range:
                    bomber_tiles[tower_x, tower_y] += 1
    
    return (gunship_tiles, bomber_tiles)

def reinf_value(tower_tiles, num_towers, map):
    """
    Returns the best sport to place a reinforcement,
    assuming you can only place a given number of towers
    Very inefficient function...
    """
    REINFX = REINFY = int(np.sqrt(TowerType.REINFORCER.range))
    reinf_val = np.zeros(shape=(map.width, map.height), dtype=int)
    for x in range(map.width):
        for y in range(map.height):
            if not map.is_space(x, y):
                continue
            value_in_range = []
            for tower_x in range(x - REINFX, x + REINFX + 1):
                for tower_y in range(y - REINFY, y + REINFY + 1):
                    if not(map.is_space(tower_x, tower_y)) or (tower_x == x and tower_y == y):
                        continue
                    if (x - tower_x)**2 + (y - tower_y)**2 <= TowerType.REINFORCER.range:
                        value_in_range.append(tower_tiles[tower_x, tower_y])

            value_in_range.sort()
            for i in range(min(num_towers, len(value_in_range))):
                reinf_val[x, y] += value_in_range[len(value_in_range)-1-i]

    return reinf_val


# Gunship DPS: 25/20 = 1.25 per tick
# Bomber DPS: 6/15   = 0.40 per tick
# Breakeven point is at 3 (simultaneous debris / num tiles in range ratio).
# a.k.a. 8 tiles for gunship, 4 tiles for bomber, means 6 simultaneous debris