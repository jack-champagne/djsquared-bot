#!/usr/bin/env python3

from src.game_constants import Team
from src.player import Player
from src.game import Game
from src.game_ext import GameExt
from src.map import Map
from multiprocessing import Pool
import importlib.util
import argparse
import json
import sys
import copy
import os
import itertools
import numpy as np
from tabulate import tabulate

def import_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module

def make_player(fpath: str, map_inst: Map) -> (str, Player):
    player_name = os.path.basename(fpath).split(".")[0]
    return import_file(player_name, fpath).BotPlayer(copy.deepcopy(map_inst))

def get_player_name_and_path(fstr):
    return (os.path.basename(fstr).split(".")[0], fstr)

def arena_builder(player_paths):
    map_paths: list[str] = ["maps/three_disjoint_paths.awap24m"]
    map_paths += ["maps/spiral.awap24m"]
    map_paths += ["maps/line.awap24m"]
    map_paths += ["maps/temple.awap24m"]
    map_paths += ["maps/hilbert.awap24m"]
    map_paths += [ "maps/squig.awap24m" ]
    map_paths += [ "maps/biki_bott.awap24m" ]
    map_paths += [ "maps/simple_map1.awap24m" ]

    maps = [Map(mpath)for mpath in map_paths]
    player_combinations = [
        (get_player_name_and_path(ppath1), get_player_name_and_path(ppath2), map_inst) for ((ppath1, ppath2), map_inst) in itertools.product(itertools.combinations_with_replacement(player_paths, 2), maps) ]

    working_opps = [] #["defense_farmer", "cane_farmer", "balthazar_farmer", "defense_bot", "dingo_farmer"]
    filtered_player_combos = list(filter(lambda e: True, enumerate(player_combinations)))
    filtered_opponents_that_work = list(filter(lambda x: True, filtered_player_combos))
    no_against_self = list(filter(lambda x: x[1][0][0] != x[1][1][0], filtered_opponents_that_work))
    print(len(no_against_self))
    with Pool(12) as p:
        return p.map(execute_game_and_output, no_against_self)


def execute_game_and_output(player_combination):
    (i, ((p1_name, p1_path), (p2_name, p2_path), map_inst)) = player_combination
    p1 = make_player(p1_path, map_inst)
    p2 = make_player(p2_path, map_inst)
    game = GameExt(p1_name, p1, p2_name, p2, map_inst)

    winner = game.run_game()
    row = [p1_name, p2_name, game.map.name, winner, game.gs.turn]
    print('| {:^20} | {:^20} | {:^20} | {:10} | {:<5} |'.format(*row)) 
    return {"player1": p1_name, "player2": p2_name, "winner": winner, "turns": game.gs.turn }

def main():
    player_paths = ["bots/azazel.py", "bots/azazel_farmer.py", "bots/balthazar_farmer.py", "bots/defense_bot.py", "bots/defense_bomb.py", "bots/dingo_farmer_fixhp.py", "bots/defense_farmer.py", "bots/dingo_defender.py", "bots/exodius_overload.py", "bots/exodius_horizon.py", "bots/exodius_fortress.py"]
    results = arena_builder(player_paths)

    player_names = [os.path.basename(p_path).split(".")[0] for p_path in player_paths]

    print(f"ordering: {[ e for e in enumerate(player_names)]})")

    victory_matrix = np.zeros([len(player_names), len(player_names)])
    for result in results:
        if result["winner"] == Team.BLUE:
            victory_matrix[player_names.index(result["player1"]),player_names.index(result["player2"])] += 1
        else:
            victory_matrix[player_names.index(result["player2"]),player_names.index(result["player1"])] += 1

    table = tabulate(list(map(lambda x: [player_names[x[0]]] + list(x[1]), enumerate(victory_matrix))))

    print(f"arena result {result}")
    print(table)

if __name__ == "__main__":
    main()
