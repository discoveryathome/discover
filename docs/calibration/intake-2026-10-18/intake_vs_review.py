#!/usr/bin/env python3
"""Join integer-mult-bounds' PR ledger dispositions with GitHub PR data (from the round-2 fetch).
usage: intake_vs_review.py PR_LEDGER.json FETCHED_PRS.json WINDOW_START WINDOW_END"""
import collections, json, sys
ledger = {r['number']: r for r in json.load(open(sys.argv[1]))['pull_requests']}
prs = json.load(open(sys.argv[2]))['prs']
start, end = sys.argv[3], sys.argv[4]
win = [p for p in prs if start <= p['created_at'] < end]
covered = [p for p in win if p['number'] in ledger]
state = lambda p: 'MERGED' if p['merged_at'] else ('CLOSED' if p['closed_at'] else 'OPEN')
tab = collections.Counter((state(p), ledger[p['number']]['disposition']) for p in covered)
merged = [p for p in covered if p['merged_at']]
out = {'window': [start, end], 'window_prs': len(win), 'in_ledger': len(covered),
       'ledger_max_pr': max(ledger), 'by_state_and_disposition': {f'{a}/{b}': n for (a, b), n in sorted(tab.items())},
       'merged': len(merged),
       'merged_partially_reviewed_share': round(sum(ledger[p['number']]['disposition'] == 'partially_reviewed' for p in merged) / len(merged), 4) if merged else None,
       'not_in_ledger_yet': len(win) - len(covered)}
print(json.dumps(out, indent=1))
