"""Rerun every method on every draw in results.jsonl and confirm each row exactly.

    python3 check.py                      # everything (a few minutes)
    python3 check.py --method kicked-ils  # one method
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method")
    a = ap.parse_args()
    rows = [json.loads(line) for line in (HERE / "results.jsonl").read_text().splitlines() if line.strip()]
    runs = sorted({(r["method"], r["draw"]) for r in rows if not a.method or r["method"] == a.method})
    bad = 0
    for method, draw in runs:
        want = [r for r in rows if (r["method"], r["draw"]) == (method, draw)]
        count = len({r["instance"] for r in want})
        out = subprocess.run([sys.executable, str(HERE / "evaluate.py"), "--method", method, "--draw", draw,
                              "--count", str(count)], capture_output=True, text=True, check=True).stdout
        got = [json.loads(line) for line in out.splitlines() if line.strip()]
        key = lambda r: (r["instance"], r["seed"])
        if sorted(got, key=key) != sorted(want, key=key):
            bad += 1
            print(f"MISMATCH {method} on draw {draw}")
        else:
            print(f"ok {method} on draw {draw}: {len(want)} runs")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
