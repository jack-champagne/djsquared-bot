import subprocess

out = subprocess.run(["python", "run_game.py", "-b", "bots/azazel.py", "-r", "bots/random_bot.py", "-m", "maps/biki_bott.awap24m"])
print(out, type(out))
