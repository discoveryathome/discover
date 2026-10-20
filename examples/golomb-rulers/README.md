# Golomb rulers: an example record-table project

A template for a Discovery@Home project whose frontier is a table of independent cases
(spec §5, record tables). Each row of `rulers.csv` is one case: the shortest ruler known
with `n` marks on which every pair of marks is a different distance apart, and the proven
optimum where one is known. A row is open until its length meets the optimum.

- **Check one row:** `python3 check.py --n 11`. **Check them all:** `python3 check.py --all`.
- **Contribute:** change one open row to a shorter ruler, run its check, open a PR. A
  workflow that runs the check and merges on success would make review mechanical, as
  `discover.json` declares; this example doesn't ship one.
- **Pick a row:** `discover pick` draws one open row for the `shorten-open-row` card.

The data is illustrative: rows 2–10 hold known optimal rulers and rows 11–14 deliberately
hold greedy ones, so the example has open cases.
