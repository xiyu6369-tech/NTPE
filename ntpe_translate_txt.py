# NTPE TXT translation compatibility wrapper
from ntpe_production_translate import main

if __name__ == "__main__":
    import sys
    raise SystemExit(main(["txt", *sys.argv[1:]]))
