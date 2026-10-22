"""Run one method on a draw and print result rows (JSON Lines).

    python3 evaluate.py --method kicked-ils --draw 33241428 >> results.jsonl

The draw is a drand quicknet round listed in draws.json; its randomness is checked
against its signature (drand's randomness is the SHA-256 of the signature).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import tsp

HERE = Path(__file__).resolve().parent


def randomness(draw):
    rec = json.loads((HERE / "draws.json").read_text())[str(draw)]
    if hashlib.sha256(bytes.fromhex(rec["signature"])).hexdigest() != rec["randomness"]:
        sys.exit(f"draw {draw}: randomness isn't the SHA-256 of its signature")
    return rec["randomness"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True, choices=sorted(tsp.METHODS))
    ap.add_argument("--draw", required=True)
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=3)
    a = ap.parse_args()
    rand = randomness(a.draw)
    seeds = range(a.seeds) if a.method == "kicked-ils" else range(1)  # the others are deterministic
    for i in range(a.count):
        pts = tsp.instance(rand, i)
        for s in seeds:
            tour = tsp.METHODS[a.method](pts, seed=s, budget=tsp.Budget(tsp.BUDGET))
            assert sorted(tour) == list(range(len(pts))), "not a tour"
            print(json.dumps({"method": a.method, "instance": f"{a.draw}/{i}", "seed": s,
                              "value": f"{tsp.length(tour, pts):.3f}", "draw": str(a.draw)}))


if __name__ == "__main__":
    main()
