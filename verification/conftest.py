from pathlib import Path

from verification._bootstrap import activate_verification


activate_verification(Path(__file__).resolve().parent)
