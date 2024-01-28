# Execute the actual game, starts the game and keep tracks of everything
# Import all other classes

import copy
import importlib.util
import random
import sys
import os
from src.game import Game
from src.game_state import GameState
from src.robot_controller import RobotController
from src.game_constants import Team, GameConstants, TowerType, get_debris_schedule
from src.player import Player
from src.map import Map
from src.replay import Replay
from threading import Thread
import time

class GameExt(Game):
    def __init__(self, blue_player_name: str, blue_player: Player, red_player_name: str, red_player: Player, map_inst: Map, output_replay=False, render=False):
        self.output_replay = output_replay
        self.render = render

        # initialize map
        self.map = map_inst

        # initialize game_state
        self.gs = GameState(self.map)

        self.blue_failed_init = False
        self.red_failed_init = False

        self.blue_player: Player = blue_player
        self.red_player: Player = red_player

        # initialize replay
        self.game_name = f"{blue_player_name}-{red_player_name}-{self.map.name}"
        self.replay = Replay(
            self.game_name,
            self.map,
            red_player_name,
            blue_player_name
        )

        # initialize controllers
        self.blue_controller = RobotController(Team.BLUE, self.gs)
        self.red_controller = RobotController(Team.RED, self.gs)
