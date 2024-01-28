#!/usr/bin/env python3

from src.player import Player
from src.game import Game
from src.game_ext import GameExt
from src.map import Map
import importlib.util
import argparse
import json
import sys
import copy
import os
import itertools

def import_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module

def make_player(fpath: str, map_path: Map) -> (str, Player):
    player_name = os.path.basename(fpath).split(".")[0]
    return (player_name, import_file(player_name, fpath).BotPlayer(copy.deepcopy(map_path)))

def arena_builder():
    map_paths: list[str] = ["maps/biki_bott.awap24m", "maps/line.awap24m", "maps/three_disjoint_paths.awap24m"]
    
    maps = [Map(mpath)for mpath in map_paths]

    player_paths = ["bots/azazel.py", "bots/random_bot.py"]
    
    player_combinations = [
        (make_player(ppath1, map_inst), make_player(ppath2, map_inst), map_inst) for ((ppath1, ppath2), map_inst) in itertools.product(itertools.combinations_with_replacement(player_paths, 2), maps) ]
    print(len(player_combinations))

    games = [ 
        (p1_name, p2_name, GameExt(p1_name, p1, p2_name, p2, map_inst)) 
        for ((p1_name, p1), (p2_name, p2), map_inst) 
        in player_combinations
    ]

    results = []
    for (i ,(p1_name, p2_name, game)) in enumerate(games):
        print(f"Match {i+1}: {p1_name} vs. {p2_name}")
        winner = game.run_game()
        results.append({"player1": p1_name, "player2": p2_name, "winner": winner, "turns": game.gs.turn })
        del(game)
    return results

def main():
    print(f"arena result {arena_builder()}")

if __name__ == "__main__":
    main()