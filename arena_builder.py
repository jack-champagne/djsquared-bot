#!/usr/bin/env python3

from src.game import Game
import importlib.util
import argparse
import json
import sys
import copy

def import_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module



def arena_builder():
    parser = argparse.ArgumentParser(description="Run the game")
    parser.add_argument("-m", "--map_path", type=str, required=False)
    parser.add_argument("-c", "--config_file", type=str, required=False)
    parser.add_argument("--render", action="store_true", help="Whether or not to display the game while it is running")
    args = parser.parse_args()

    blue_path = "bots/nothing_bot.py"
    red_path = "bots/nothing_bot.py"

    if args.config_file:
        configs = json.load(open(args.config_file))
        map_path = configs["map"]
    else:
        if not args.map_path:
            raise Exception("Must provide --map_path if not using --config_file")
        map_path = args.map_path

    game = Game(
        blue_path=blue_path,
        red_path=red_path,
        map_path=map_path,
        render=args.render
    )

    game.blue_player = import_file("azazel", "bots/azazel.py").BotPlayer(copy.deepcopy(game.map))

    winner = game.run_game()

    print(f"Winner: {winner}")
    print(f"Turns: {game.gs.turn}")

    return { "winner": winner, "turns": game.gs.turn }


def main():
    print(f"arena result {arena_builder()}")

if __name__ == "__main__":
    main()