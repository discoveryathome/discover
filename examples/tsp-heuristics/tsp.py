"""Euclidean TSP heuristics, a toy evaluation suite (spec §5, Evaluation suites).

Instances are drawn from a public randomness beacon round, so nobody can tune a method to
them before they exist. Every method gets the same budget, counted in move evaluations
rather than seconds, so results don't depend on the machine.
"""

import hashlib
import math
import random

N_POINTS = 60
BUDGET = 1_000_000  # move evaluations per run


def instance(randomness, i, n=N_POINTS):
    """Instance i of a draw: n integer points in a 1000 x 1000 square."""
    rng = random.Random(hashlib.sha256(f"{randomness}:{i}".encode()).digest())
    return [(rng.randrange(1000), rng.randrange(1000)) for _ in range(n)]


def length(tour, pts):
    return sum(math.dist(pts[tour[k - 1]], pts[tour[k]]) for k in range(len(tour)))


class Budget:
    def __init__(self, amount):
        self.left = amount

    def spend(self):
        self.left -= 1
        return self.left >= 0


def nearest_neighbour(pts, seed=0, budget=None):
    left, tour = set(range(1, len(pts))), [0]
    while left:
        here = pts[tour[-1]]
        nxt = min(left, key=lambda j: (math.dist(here, pts[j]), j))
        tour.append(nxt)
        left.remove(nxt)
    return tour


def two_opt(pts, tour, budget):
    """First-improvement 2-opt until no move helps or the budget runs out."""
    n, d = len(tour), math.dist
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n if i else n - 1):
                if not budget.spend():
                    return tour
                a, b, c, e = pts[tour[i]], pts[tour[i + 1]], pts[tour[j]], pts[tour[(j + 1) % n]]
                if d(a, c) + d(b, e) < d(a, b) + d(c, e) - 1e-9:
                    tour[i + 1:j + 1] = reversed(tour[i + 1:j + 1])
                    improved = True
    return tour


def or_opt(pts, tour, budget):
    """Move segments of 1-3 cities elsewhere in the tour while that shortens it."""
    n, d = len(tour), math.dist
    improved = True
    while improved:
        improved = False
        for seg in (1, 2, 3):
            for i in range(n):
                if i + seg >= n:
                    break
                p, s0, s1, q = tour[i - 1], tour[i], tour[i + seg - 1], tour[(i + seg) % n]
                gain_out = d(pts[p], pts[s0]) + d(pts[s1], pts[q]) - d(pts[p], pts[q])
                rest = tour[:i] + tour[i + seg:]
                for k in range(len(rest)):
                    if not budget.spend():
                        return tour
                    u, v = rest[k - 1], rest[k]
                    for a, b in ((s0, s1), (s1, s0)):
                        add = d(pts[u], pts[a]) + d(pts[b], pts[v]) - d(pts[u], pts[v])
                        if add < gain_out - 1e-9:
                            piece = tour[i:i + seg] if a == s0 else tour[i:i + seg][::-1]
                            tour[:] = rest[:k] + piece + rest[k:]
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break
    return tour


def croes(pts, seed=0, budget=None):
    """2-opt from the nearest-neighbour tour (Croes 1958)."""
    return two_opt(pts, nearest_neighbour(pts), budget or Budget(BUDGET))


def two_opt_or_opt(pts, seed=0, budget=None):
    """2-opt and Or-opt alternated to a joint local optimum (Or 1976)."""
    budget = budget or Budget(BUDGET)
    tour, best = nearest_neighbour(pts), None
    while budget.left > 0 and best != length(tour, pts):
        best = length(tour, pts)
        tour = or_opt(pts, two_opt(pts, tour, budget), budget)
    return tour


def kicked(pts, seed=0, budget=None):
    """The candidate: iterated local search. 2-opt to a local optimum, then random
    double-bridge kicks, each followed by 2-opt, keeping the better tour; the last quarter
    of the budget polishes the best tour with 2-opt and Or-opt."""
    budget, rng = budget or Budget(BUDGET), random.Random(seed)
    reserve = budget.left // 4
    best = two_opt(pts, nearest_neighbour(pts), budget)
    best_len = length(best, pts)
    while budget.left > reserve:
        n = len(best)
        a, b, c = sorted(rng.sample(range(1, n), 3))
        tour = two_opt(pts, best[:a] + best[b:c] + best[a:b] + best[c:], budget)
        if length(tour, pts) < best_len - 1e-9:
            best, best_len = tour, length(tour, pts)
    prev = None
    while budget.left > 0 and prev != best_len:
        prev = best_len
        best = or_opt(pts, two_opt(pts, best, budget), budget)
        best_len = length(best, pts)
    return best


METHODS = {"nearest-neighbour": nearest_neighbour, "2-opt": croes, "2-opt+or-opt": two_opt_or_opt,
           "kicked-ils": kicked}
