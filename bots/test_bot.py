import random
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map
from bots.helper import num_tiles_in_range, reinf_value

IDEAL_HEALTH = 50
AFFORDABLE_HEALTH = 24
NUM_TOWERS_PER_REINF = 5

class BotPlayer(Player):
    gun_ratio = 0.5

    def __init__(self, map: Map):
        self.map = map
        self.desired_debris_health = IDEAL_HEALTH

    def play_turn(self, rc: RobotController):
        if rc.get_turn() == 1:
            gunship_tiles, bomber_tiles = num_tiles_in_range(self.map)
            print("Gunship:")
            print(gunship_tiles)
            print("Bomber:")
            print(bomber_tiles)
            reinf_gunship_tiles = reinf_value(gunship_tiles, NUM_TOWERS_PER_REINF, self.map)
            reinf_bomber_tiles = reinf_value(bomber_tiles, NUM_TOWERS_PER_REINF, self.map)
            print("Reinforcement at 1-to-1 ratio:")
            print(self.gun_ratio*reinf_gunship_tiles + (1-self.gun_ratio)*reinf_bomber_tiles)

        if rc.can_send_debris(1, self.desired_debris_health):
            rc.send_debris(1, self.desired_debris_health)
        elif rc.can_send_debris(1, AFFORDABLE_HEALTH):
            rc.send_debris(1, AFFORDABLE_HEALTH)
