import random
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map

IDEAL_HEALTH = 50
AFFORDABLE_HEALTH = 24

class BotPlayer(Player):

    def __init__(self, map: Map, desired_debris_health=IDEAL_HEALTH):
        self.map = map
        self.desired_debris_health = desired_debris_health

    def play_turn(self, rc: RobotController):
        if rc.can_send_debris(1, self.desired_debris_health):
            rc.send_debris(1, self.desired_debris_health)
        elif rc.can_send_debris(1, AFFORDABLE_HEALTH):
            rc.send_debris(1, AFFORDABLE_HEALTH)
        # otherwise do nothing
