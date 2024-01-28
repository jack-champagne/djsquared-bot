import random
import numpy as np
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map

'''
Dingo Mk. 2

Both Balthazar and Cane, but not dumb enough to stand there and die
'''

def optimal_tower(tower_tiles):
    tile = np.unravel_index(np.argmax(tower_tiles), tower_tiles.shape)
    return tile

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

MINIMUM_HEALTH = 51 # Enough to survive a 2 gunshots
GAPFILL = 7
CLUSTER_SIZE = 60

BOMBER_DPS = 0.4
BOMBER_DAMAGE = 6

class BotPlayer(Player):

    def __init__(self, map: Map, gun_rate=2, bomb_rate=2):
        self.map = map
        self.gunship_tiles, self.bomber_tiles = num_tiles_in_range(self.map)
        self.enemy_towers = 0
        self.desired_health = MINIMUM_HEALTH
        self.cluster_size = CLUSTER_SIZE
        self.sending = 0

        self.farm = (0, 0)
        self.num_farms = 0

        self.gun_rate = gun_rate
        self.bomb_rate = bomb_rate
        self.ratio_sum = gun_rate + bomb_rate

        self.offense_mode = False
        self.tip_scale = 0

    def get_next_farm(self, rc: RobotController):
        x, y = self.farm
        x += 1
        if x >= self.map.width:
            y += 1
            x = 0
        while not(self.map.is_space(x, y)):
            x += 1
            if x >= self.map.width:
                y += 1
                x = 0
        self.farm = (x, y)

    def sell_farms(self, rc: RobotController):
        farms = rc.get_towers(rc.get_ally_team())
        for farm in farms:
            if farm.type == TowerType.SOLAR_FARM:
                rc.sell_tower(farm.id)
        self.num_farms = 0
        self.farm = (0, 0)
        self.get_next_farm(rc)

    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.STRONG)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

    def play_turn(self, rc: RobotController):
        # If opponent is trying to rush, just sit and turtle

        if self.offense_mode:
            if len(rc.get_towers(rc.get_enemy_team())) == 0:
                self.offense_mode = False
                self.do_defense_strat(rc)
            else:
                self.do_offense_strat(rc)
        else:
            self.do_defense_strat(rc)
        self.towers_attack(rc)

    def do_defense_strat(self, rc: RobotController):
        num_towers = len(rc.get_towers(rc.get_ally_team()))
        if num_towers < self.tip_scale or num_towers % self.ratio_sum < self.gun_rate:
            if rc.get_balance(rc.get_ally_team()) >= TowerType.GUNSHIP.cost:
                gunship_x, gunship_y = optimal_tower(self.gunship_tiles)
                gunship_x, gunship_y = int(gunship_x), int(gunship_y)
                if rc.can_build_tower(TowerType.GUNSHIP, gunship_x, gunship_y):
                    rc.build_tower(TowerType.GUNSHIP, gunship_x, gunship_y)

                    # Prevent future placements on this tile
                    self.bomber_tiles[gunship_x, gunship_y] = 0
                    self.gunship_tiles[gunship_x, gunship_y] = 0

                    if num_towers > 0 and (num_towers+1) % self.ratio_sum == 0:
                        self.offense_mode = True

        else:
            if rc.get_balance(rc.get_ally_team()) >= TowerType.BOMBER.cost:
                bomber_x, bomber_y = optimal_tower(self.bomber_tiles)
                bomber_x, bomber_y = int(bomber_x), int(bomber_y)
                if rc.can_build_tower(TowerType.BOMBER, bomber_x, bomber_y):
                    rc.build_tower(TowerType.BOMBER, bomber_x, bomber_y)

                    # Prevent future placements on this tile
                    self.bomber_tiles[bomber_x, bomber_y] = 0
                    self.gunship_tiles[bomber_x, bomber_y] = 0

                    if num_towers > 0 and (num_towers+1) % self.ratio_sum == 0:
                        self.offense_mode = True

        if rc.get_turn() >= 50 and rc.get_turn() % 50 == 0 and len(rc.get_towers(rc.get_enemy_team())) == 0:
            self.tip_scale += 10


    def do_offense_strat(self, rc: RobotController):
        if rc.get_turn() == 0:
            self.get_next_farm(rc)

        towers = rc.get_towers(rc.get_enemy_team())
        if self.sending == 0:
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

            self.desired_health = int(max(MINIMUM_HEALTH,
                                      BOMBER_DAMAGE*np.ceil((BOMBER_DPS * tb)/BOMBER_DAMAGE) + GAPFILL))
            self.sending = self.cluster_size

        if self.sending > 0:
            total_val = rc.get_balance(rc.get_ally_team()) + self.num_farms * 0.8 * TowerType.SOLAR_FARM.cost
            if total_val >= rc.get_debris_cost(1, self.desired_health) * self.sending:
                self.sell_farms(rc)
                rc.send_debris(1, self.desired_health)
                self.sending -= 1

                if self.sending == 0:
                    self.offense_mode = False
            else:
                if rc.can_build_tower(TowerType.SOLAR_FARM, self.farm[0], self.farm[1]):
                    rc.build_tower(TowerType.SOLAR_FARM, self.farm[0], self.farm[1])
                    self.get_next_farm(rc)
                    self.num_farms += 1
        # otherwise do nothing
