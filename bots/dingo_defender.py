import random
from enum import Enum
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map
import numpy as np

NUM_TOWERS_PER_REINF = 5

MINIMUM_HEALTH = 51 # Enough to survive a 2 gunshots
GAPFILL = 7
CLUSTER_SIZE = 60

BOMBER_DPS = 0.4
BOMBER_DAMAGE = 6
GUNSHIP_DPS = 1.25
GUNSHIP_DAMAGE = 25

class BotMode(Enum):
    STARTING = 0
    DEFENDING = 1
    FARMING = 2
    ATTACKING = 3

def max_cluster(reinf_tiles):
    tile = np.unravel_index(np.argmax(reinf_tiles), reinf_tiles.shape)
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

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map

        gunship_tiles, bomber_tiles = num_tiles_in_range(self.map)
        self.base_gunship_tiles = gunship_tiles.copy()
        self.base_bomber_tiles = bomber_tiles.copy()
        self.gunship_tiles = gunship_tiles
        self.bomber_tiles = bomber_tiles

        self.cur_reinfs = set()
        self.cur_farm_reinf = None
        self.farm_reinf_boundary = set()
        # Tentative farm tiles
        self.farm_tiles = set()

        # STARTING metrics
        self.num_towers = 0

        self.gun_rate = 2
        self.bomb_rate = 2
        self.ratio_sum = self.gun_rate + self.bomb_rate

        # Current mode
        self.mode = BotMode.STARTING

    def set_farm_cluster(self, corner, rc):
        self.cur_farm_reinf = corner
        self.cur_reinfs.add(corner)
        x, y = corner
        for new_corner in [(x-2,y-2),(x-2,y+2),(x+2,y-2),(x+2,y+2)]:
            if (new_corner not in self.cur_reinfs) and rc.is_placeable(rc.get_ally_team(), new_corner[0], new_corner[1]):
                self.farm_reinf_boundary.add(new_corner)

    def next_farm_reinf(self, rc: RobotController):
        """
        XOOOXOOOX
        OOOOOOOOO
        OOXOOOXOO <- relatively good layout of farms and reinforcer
        OOOOOOOOO
        XOOOXOOOX
        """
        min_val = 10000
        min_corner = None
        for corner in self.farm_reinf_boundary:
            if self.reinf_tiles[corner[0], corner[1]] < min_val:
                min_corner = corner
                min_val = self.reinf_tiles[corner[0], corner[1]]
        self.cur_farm_reinf = min_corner
        if min_corner is None:
            return
        
        self.farm_reinf_boundary.remove(min_corner)
        self.set_farm_cluster(min_corner, rc)
        self.get_new_farm_locs(min_corner, rc)

    def init_farm_cluster(self, rc):
        min_reinf = 1000
        tile = None
        for x in range(self.map.width):
            for y in range(self.map.height):
                if self.map.is_space(x, y):
                    if self.reinf_tiles[x, y] < min_reinf:
                        min_reinf = self.reinf_tiles[x, y]
                        tile = (x, y)
        self.set_farm_cluster(tile, rc)
        if tile:
            self.next_farm_reinf(rc)
        
    def get_new_farm_locs(self, next_reinf, rc):
        """
        Adds new farm locations
        """
        x, y = next_reinf
        for new_corner in [(x-2,y-2),(x-2,y+2),(x+2,y-2),(x+2,y+2)]:
            if new_corner not in self.cur_reinfs:
                continue
            minx, maxx = min(x, new_corner[0]), max(x, new_corner[0])
            miny, maxy = min(y, new_corner[1]), max(y, new_corner[1])
            for tower_x in range(minx, maxx+1):
                for tower_y in range(miny, maxy+1):
                    if (tower_x == x and tower_y == y) or (tower_x == new_corner[0] and tower_y == new_corner[1]):
                        continue
                    if rc.is_placeable(rc.get_ally_team(), tower_x, tower_y):
                        self.farm_tiles.add((tower_x, tower_y))
    
    def fallback_farm_loc(self, rc: RobotController):
        min_reinf = 1000
        tile = None
        for x in range(self.map.width):
            for y in range(self.map.height):
                if rc.is_placeable(rc.get_ally_team(), x, y):
                    if self.gunship_tiles[x, y] < min_reinf:
                        min_reinf = self.gunship_tiles[x, y]
                        tile = (x, y)
        if rc.get_balance(rc.get_ally_team()) >= TowerType.SOLAR_FARM.cost:
            tower_x, tower_y = tile
            if rc.can_build_tower(TowerType.SOLAR_FARM, tower_x, tower_y):
                rc.build_tower(TowerType.SOLAR_FARM, tower_x, tower_y)

    def fill_farm_tile(self, rc):
        if rc.get_balance(rc.get_ally_team()) >= TowerType.SOLAR_FARM.cost:
            tower_x, tower_y = self.farm_tiles.pop()
            # print("attempting farm tile", tower_x, tower_y)
            if rc.can_build_tower(TowerType.SOLAR_FARM, tower_x, tower_y):
                rc.build_tower(TowerType.SOLAR_FARM, tower_x, tower_y)

    def build_farm(self, rc: RobotController):
        if len(self.farm_tiles) == 0:
            # print("out of farm tiles")
            if len(self.farm_reinf_boundary) == 0:
                self.fallback_farm_loc(rc)
            elif not self.cur_farm_reinf:
                self.next_farm_reinf(rc)
                if len(self.farm_tiles) > 0:
                    self.fill_farm_tile(rc)
                else:
                    self.fallback_farm_loc(rc)
            else:
                tower_x, tower_y = self.cur_farm_reinf
                if rc.can_build_tower(TowerType.REINFORCER, tower_x, tower_y):
                    rc.build_tower(TowerType.REINFORCER, tower_x, tower_y)
                    self.cur_farm_reinf = None
        else:
            self.fill_farm_tile(rc)        


    def optimal_tower(self, tower_tiles, rc):
        while True:
            tile = np.unravel_index(np.argmax(tower_tiles), tower_tiles.shape)
            x, y = int(tile[0]), int(tile[1])
            if tower_tiles[x, y] == 0:
                return tile
            # Prevent future placements on this tile
            tower_tiles[x, y] = 0
            if rc.is_placeable(rc.get_ally_team(), x, y):
                return tile
    
    def get_num_farms(self, rc):
        num_farms = 0
        for tower in rc.get_towers(rc.get_ally_team()):
            if tower.type == TowerType.SOLAR_FARM:
                num_farms += 1
        return num_farms

    def sell_farms(self, target, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        num_towers = 0
        for tower in towers:
            if tower.type == TowerType.SOLAR_FARM:
                num_towers += 1

        for tower in towers:
            if tower.type == TowerType.SOLAR_FARM:
                # Add farm spot into farm_tiles
                self.farm_tiles.add((tower.x, tower.y))
                rc.sell_tower(tower.id)
                num_towers -= 1
                if num_towers <= target:
                    break

    def check_offense_power(self, num_farms, num_enemy_farms, rc):
        towers = rc.get_towers(rc.get_enemy_team())
        # Recompute health if cached value is incorrect
        tg = 0
        nguns = 0
        tb = 0
        nbombs = 0
        # for tower in towers:
            # if tower.type == TowerType.REINFORCER:

        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                tg += self.base_gunship_tiles[tower.x, tower.y]
                nguns += 1
            elif tower.type == TowerType.BOMBER:
                tb += self.base_bomber_tiles[tower.x, tower.y]
                nbombs += 1

        self.desired_health = max(MINIMUM_HEALTH,
                                    BOMBER_DAMAGE*np.ceil((BOMBER_DPS * tb)/BOMBER_DAMAGE * 1.1) + GAPFILL)
        self.single_health = max(MINIMUM_HEALTH,
                                    (BOMBER_DAMAGE*np.ceil((BOMBER_DPS * tb)/BOMBER_DAMAGE * 1.1) + 
                                    GUNSHIP_DAMAGE*np.ceil((GUNSHIP_DPS * tg)/GUNSHIP_DAMAGE * 1.2)) + GAPFILL)

        # Calculate the cheaper option
        cluster_cost = rc.get_debris_cost(1, self.desired_health) * CLUSTER_SIZE
        single_cost = rc.get_debris_cost(1, self.single_health)
        # How many farms are we willing to sell? Up to enemy farms? Unless hail mary...
        total_value = rc.get_balance(rc.get_ally_team())
        if num_farms > num_enemy_farms:
            total_value += (num_farms - num_enemy_farms) * 0.8 * TowerType.SOLAR_FARM.cost

        if total_value >= single_cost and (single_cost / self.single_health < cluster_cost / (0.5* CLUSTER_SIZE * self.desired_health)):
            # Assumes about 50% get through
            self.sending_health = self.single_health
            self.sending = 1
            if num_farms > num_enemy_farms:
                self.sell_farms(num_enemy_farms, rc)
            self.mode = BotMode.ATTACKING
        elif total_value >= cluster_cost:
            self.sending_health = self.desired_health
            self.sending = CLUSTER_SIZE
            if num_farms > num_enemy_farms:
                self.sell_farms(num_enemy_farms, rc)
            self.mode = BotMode.ATTACKING
        
    
    def get_defense_power(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        tg = 0
        nguns = 0
        tb = 0
        nbombs = 0
        # for tower in towers:
            # if tower.type == TowerType.REINFORCER:
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                tg += self.base_gunship_tiles[tower.x, tower.y]
                nguns += 1
            elif tower.type == TowerType.BOMBER:
                tb += self.base_bomber_tiles[tower.x, tower.y]
                nbombs += 1
        cluster_health = BOMBER_DAMAGE*np.ceil((BOMBER_DPS * tb)/BOMBER_DAMAGE)
        single_health = (BOMBER_DAMAGE*np.ceil((BOMBER_DPS * tb)/BOMBER_DAMAGE) +
                          GUNSHIP_DAMAGE*np.ceil((GUNSHIP_DPS * tg)/GUNSHIP_DAMAGE))
        
        all_debris = rc.get_debris(rc.get_ally_team())
        debris_life = 0
        for debris in all_debris:
            # Sample stuff in front
            if debris.progress <= 15:
                # Remove 50% bomber damage from health
                debris_life += max(0, (debris.health / debris.total_cooldown) - cluster_health * 0.9)
        debris_life *= self.map.path_length / 15

        return (cluster_health, single_health, debris_life)
        

    # Strategies
    def do_offense_strat(self, rc: RobotController):
        if self.sending > 0:
            if rc.get_balance(rc.get_ally_team()) >= rc.get_debris_cost(1, self.sending_health) * self.sending:
                rc.send_debris(1, self.sending_health)
                self.sending -= 1
        if self.sending == 0:
            # self.offense_mode = False
            self.mode = BotMode.FARMING

    def do_defense_strat(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        nguns = 0
        nbombs = 0
        # for tower in towers:
            # if tower.type == TowerType.REINFORCER:
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                nguns += 1
            elif tower.type == TowerType.BOMBER:
                nbombs += 1
        
        if nbombs / nguns < self.bomb_rate / self.gun_rate:
            if rc.get_balance(rc.get_ally_team()) >= TowerType.BOMBER.cost:
                bomber_x, bomber_y = self.optimal_tower(self.bomber_tiles, rc)
                bomber_x, bomber_y = int(bomber_x), int(bomber_y)
                if rc.can_build_tower(TowerType.BOMBER, bomber_x, bomber_y):
                    rc.build_tower(TowerType.BOMBER, bomber_x, bomber_y)
        else:
            if rc.get_balance(rc.get_ally_team()) >= TowerType.GUNSHIP.cost:
                gunship_x, gunship_y = self.optimal_tower(self.gunship_tiles, rc)
                gunship_x, gunship_y = int(gunship_x), int(gunship_y)
                if rc.can_build_tower(TowerType.GUNSHIP, gunship_x, gunship_y):
                    rc.build_tower(TowerType.GUNSHIP, gunship_x, gunship_y)


    def do_farming_strat(self, rc: RobotController):
        if rc.get_balance(rc.get_ally_team()) >= TowerType.SOLAR_FARM.cost:
            self.build_farm(rc)
            
        towers = rc.get_towers(rc.get_enemy_team())
        enemy_value = 0
        num_enemy_farms = 0
        for tower in towers:
            if tower.type == TowerType.SOLAR_FARM:
                num_enemy_farms += 1
            enemy_value += tower.type.cost
        num_farms = self.get_num_farms(rc)


        # Don't farm more than their tower count (TODO: change to value count) (TODO: check debris danger)
        # Need more defense if enemy has more farms, or if it's later in the round
        if rc.get_turn() % 5 == 0:
            # Debris analysis
            cluster_health, single_health, debris_life = self.get_defense_power(rc)
            if debris_life > single_health:
                self.mode = BotMode.DEFENDING
            if num_farms * TowerType.SOLAR_FARM.cost >= enemy_value and cluster_health < 30 * np.sqrt(1 + 0.2*num_enemy_farms):
                # Source is that I made it up 
                self.mode = BotMode.DEFENDING        
            if self.mode == BotMode.FARMING:
                self.check_offense_power(num_farms, num_enemy_farms, rc)
        # Defend if we have more farm than enemies (more farm should mean less defense)
        # if num_farms >= num_enemy_farms + 1:
            # Rush if enemies have low defense/we have enough money
            # Sell farms if needed. TODO: How many farms?


    def play_turn(self, rc: RobotController):
        if rc.get_turn() == 1:
            gunship_tiles, bomber_tiles = num_tiles_in_range(self.map)
            
            reinf_gunship_tiles = reinf_value(gunship_tiles, NUM_TOWERS_PER_REINF, self.map)
            reinf_bomber_tiles = reinf_value(bomber_tiles, NUM_TOWERS_PER_REINF, self.map)
            self.reinf_tiles = (self.gun_rate*reinf_gunship_tiles + self.bomb_rate*reinf_bomber_tiles) / self.ratio_sum


            # Init the starting farm location
            self.init_farm_cluster(rc)

        if self.mode == BotMode.STARTING:
            if rc.get_balance(rc.get_ally_team()) >= TowerType.GUNSHIP.cost:
                gunship_x, gunship_y = self.optimal_tower(self.gunship_tiles, rc)
                gunship_x, gunship_y = int(gunship_x), int(gunship_y)
                if rc.can_build_tower(TowerType.GUNSHIP, gunship_x, gunship_y):
                    rc.build_tower(TowerType.GUNSHIP, gunship_x, gunship_y)
                    self.num_towers += 1
            
                    if self.num_towers >= 5:
                        self.mode = BotMode.FARMING
            
        # When to build farms?
        if self.mode == BotMode.FARMING:
            self.do_farming_strat(rc)

        if self.mode == BotMode.DEFENDING:
            self.do_defense_strat(rc)
            
            enemy_value = 0
            num_enemy_farms = 0
            towers = rc.get_towers(rc.get_enemy_team())    
            for tower in towers:
                if tower.type == TowerType.SOLAR_FARM:
                    num_enemy_farms += 1
                enemy_value += tower.type.cost
            num_farms = self.get_num_farms(rc)
            if rc.get_turn() % 5 == 0: # mod 5 for less computation
                cluster_health, single_health, debris_life = self.get_defense_power(rc)
                if debris_life <= single_health:
                    if num_farms * TowerType.SOLAR_FARM.cost < enemy_value and cluster_health >= 30 * np.sqrt(1 + 0.2*num_enemy_farms):
                        self.mode = BotMode.FARMING
                else:
                    self.sell_farms(num_enemy_farms + 1, rc)
        
        if self.mode == BotMode.ATTACKING:
            self.do_offense_strat(rc)

        self.towers_attack(rc)
        
        
    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST) # TODO: target enemy with highest current hp
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)
