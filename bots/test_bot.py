import random
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map
from bots.helper import num_tiles_in_range, reinf_value

class BotPlayer(Player):
    IDEAL_HEALTH = 30

    def __init__(self, map: Map):
        self.map = map

    def play_turn(self, rc: RobotController):
        if rc.get_turn() == 1:
            gunship_tiles, bomber_tiles = num_tiles_in_range(self.map)
            print("Gunship:")
            print(gunship_tiles)
            print("Bomber:")
            print(bomber_tiles)
            reinf_tiles = reinf_value(gunship_tiles, 4, self.map)
            print("Reinforcement:")
            print(reinf_tiles)

        if rc.can_send_debris(1, self.IDEAL_HEALTH):
            rc.send_debris(1, self.IDEAL_HEALTH)
        else:
            rc.send_debris(1, 9)
