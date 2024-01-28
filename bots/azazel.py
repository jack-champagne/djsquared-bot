import random
import numpy as np
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map

'''
Azazel Mk. 3

Sends a doom-wave of scrap
'''

def num_tiles_in_range(map: Map):
    # Upper bounds on bounding square
    GUNX = GUNY = int(np.sqrt(TowerType.GUNSHIP.range))
    BOMBX = BOMBY = int(np.sqrt(TowerType.BOMBER.range))

    gunship_tiles = np.zeros(shape=(map.width, map.height), dtype=int)
    bomber_tiles = np.zeros(shape=(map.width, map.height), dtype=int)
    for tile in map.path:
        x, y = tile
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

MINIMUM_HEALTH = 24
GAPFILL = 5

class BotPlayer(Player):

    def __init__(self, map: Map):
        self.map = map
        self.gunship_tiles, self.bomber_tiles = num_tiles_in_range(self.map)
        self.enemy_towers = 0
        self.desired_health = MINIMUM_HEALTH

    def play_turn(self, rc: RobotController):
        towers = rc.get_towers(rc.get_enemy_team())
        if len(towers) != self.enemy_towers:
            # Recompute health if cached value is incorrect
            tg = 0
            tb = 0

            for tower in towers:
                if tower.type == TowerType.GUNSHIP:
                    tg += self.gunship_tiles[tower.x, tower.y]
                elif tower.type == TowerType.BOMBER:
                    tg += self.bomber_tiles[tower.x, tower.y]

            self.desired_health = min(MINIMUM_HEALTH, 1.25 * tg + 0.4 * tb + GAPFILL)
        
        if rc.can_send_debris(1, self.desired_health):
            rc.send_debris(1, self.desired_health)
        # otherwise do nothing
