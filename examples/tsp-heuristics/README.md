# TSP heuristics: an example algorithm race

A template for a Discovery@Home project whose frontier is a **method**, not a record
(spec §5, evaluation suites). The question: which heuristic gives the shortest tours on
60-city Euclidean instances, at a budget of 1,000,000 move evaluations?

- **Formulation `tsp-euclid-60-v1`:** 60 integer points uniform in a 1000 × 1000 square,
  Euclidean distances, closed tours, tour length lower-is-better. Change any of that and
  it's a new formulation, with its own series of results.
- **Budget:** counted in move evaluations (`tsp.Budget`), not seconds, so a run gives the
  same result on any machine.
- **Held-out instances:** drawn from a [drand](https://drand.love) quicknet round later
  than the method's commit, so nobody can tune to them. Instance `i` of a round comes from
  SHA-256 of its randomness and `i`. `draws.json` keeps each round's signature; drand's
  randomness is the SHA-256 of the signature.
- **Baselines:** nearest neighbour (the starter), 2-opt (Croes 1958) and 2-opt with Or-opt
  (Or 1976), both published. There's no mature solver yet; the hub says so beside the claim.

**Contributing.** Develop a method on instances you generate yourself (`tsp.instance`
with any seed). Freeze it in a PR. A maintainer then runs `evaluate.py` for it and for
the current method on the first beacon round after your commit, and it's accepted if it
beats the current method there on a sign test. **Check everything:** `python3 check.py`.

The example's methods and its one round (33241488) were fixed in the same sitting; in a
real project the round comes after the method's commit is merged.
