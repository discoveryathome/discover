"""Check rows of rulers.csv: each ruler has n marks, starts at 0, ends at its length, and
every pair of marks is a different distance apart (a Golomb ruler).

    python3 check.py --n 11     one row
    python3 check.py --all      every row
"""

import argparse
import csv
import sys
from itertools import combinations
from pathlib import Path

TABLE = Path(__file__).with_name("rulers.csv")


def problems(row):
    marks = [int(x) for x in row["marks"].split()]
    n, length = int(row["n"]), int(row["length"])
    out = []
    if len(marks) != n:
        out.append(f"{len(marks)} marks, not {n}")
    if marks != sorted(set(marks)) or not marks or marks[0] != 0:
        out.append("marks must start at 0 and strictly increase")
    elif marks[-1] != length:
        out.append(f"last mark is {marks[-1]}, not the stated length {length}")
    diffs = [b - a for a, b in combinations(marks, 2)]
    if len(diffs) != len(set(diffs)):
        out.append("two pairs of marks are the same distance apart")
    if row.get("optimum") and length < int(row["optimum"]):
        out.append(f"length {length} is below the proven optimum {row['optimum']}")
    return out


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--n")
    g.add_argument("--all", action="store_true")
    a = ap.parse_args()
    rows = list(csv.DictReader(TABLE.open()))
    if a.n:
        rows = [r for r in rows if r["n"] == a.n]
        if not rows:
            sys.exit(f"no row with n = {a.n}")
    bad = 0
    for r in rows:
        p = problems(r)
        bad += bool(p)
        print(f"n={r['n']} length={r['length']}: {'ok' if not p else '; '.join(p)}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
