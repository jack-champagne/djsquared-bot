import random
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map

class BotPlayer(Player):
    IDEAL_HEALTH = 30

    def __init__(self, map: Map):
        self.map = map

    def play_turn(self, rc: RobotController):
        if rc.can_send_debris(1, self.IDEAL_HEALTH):
            rc.send_debris(1, self.IDEAL_HEALTH)
        else:
            rc.send_debris(1, 9)
