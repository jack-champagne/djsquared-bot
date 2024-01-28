import random
import numpy as np
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map

'''
Balthazar Mk 1.

Son of Azazel, but calm and collected.
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


def optimal_tower(tower_tiles):
    tile = np.unravel_index(np.argmax(tower_tiles), tower_tiles.shape)
    return tile


AZ_MINIMUM_HEALTH = 50 # Enough to survive a single gunshot
AZ_GAPFILL = 7
AZ_CLUSTER_SIZE = 20

BOMBER_DPS = 0.4
BOMBER_DAMAGE = 6

class BotPlayer(Player):

    def __init__(self, map: Map):
        self.map = map
        self.gunship_tiles, self.bomber_tiles = num_tiles_in_range(self.map)
        self.enemy_towers = 0
        self.desired_health = AZ_MINIMUM_HEALTH
        self.cluster_size = AZ_CLUSTER_SIZE
        self.sending = 0

        self.offense_mode = False


    def play_turn(self, rc: RobotController):
        if self.offense_mode:
            self.do_offense_strat(rc)
        else:
            self.do_defense_strat(rc)
        self.towers_attack(rc)

    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

    def do_defense_strat(self, rc: RobotController):
        if rc.get_balance(rc.get_ally_team()) >= TowerType.GUNSHIP.cost:
            gunship_x, gunship_y = optimal_tower(self.gunship_tiles)
            gunship_x, gunship_y = int(gunship_x), int(gunship_y)
            if rc.can_build_tower(TowerType.GUNSHIP, gunship_x, gunship_y):
                rc.build_tower(TowerType.GUNSHIP, gunship_x, gunship_y)

                if len(rc.get_towers(rc.get_ally_team())) % 5 == 0:
                    self.offense_mode = True
                # Prevent future placements on this tile
                self.gunship_tiles[gunship_x, gunship_y] = 0
            else:
                print("fail")
                raise Exception

    def do_offense_strat(self, rc: RobotController):
        # Remnants of Azazel
        towers = rc.get_towers(rc.get_enemy_team())
        if len(towers) != self.enemy_towers and self.sending == 0:
            # Recompute health if cached value is incorrect
            tg = 0
            nguns = 0
            tb = 0
            nbombs = 0

            for tower in towers:
                if tower.type == TowerType.GUNSHIP:
                    tg += self.gunship_tiles[tower.x, tower.y]
                    nguns += 1
                elif tower.type == TowerType.BOMBER:
                    tb += self.bomber_tiles[tower.x, tower.y]
                    nbombs += 1

            self.desired_health = max(AZ_MINIMUM_HEALTH,
                                      BOMBER_DAMAGE*np.ceil((BOMBER_DPS * tb)/BOMBER_DAMAGE) + AZ_GAPFILL)
            self.sending = self.cluster_size

        if self.sending > 0:
            if rc.get_balance(rc.get_ally_team()) >= rc.get_debris_cost(1, self.desired_health) * self.sending:
                rc.send_debris(1, self.desired_health)
                self.sending -= 1

            if self.sending == 0:
                self.offense_mode = False

        # otherwise do nothing
