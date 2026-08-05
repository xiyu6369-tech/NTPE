# NTPE batch translation compatibility wrapper
from ntpe_production_translate import main

if __name__ == "__main__":
    import sys
    raise SystemExit(main(["batch", *sys.argv[1:]]))
