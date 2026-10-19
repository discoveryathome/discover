#!/usr/bin/env python3
"""Seeded sample of closed-unmerged PRs in the window: who closed them? usage: closer_sample.py DATA.json N SEED"""
import json, random, subprocess, sys
d = json.load(open(sys.argv[1])); n = int(sys.argv[2]); rng = random.Random(sys.argv[3])
pool = [p for p in d['prs'] if p['closed_at'] and not p['merged_at'] and p['created_at'] >= '2026-10-04T16:00:00Z' and not (p['user'] or '').endswith('[bot]')]
rows = []
for p in rng.sample(pool, min(n, len(pool))):
    ev = json.loads(subprocess.check_output(['gh', 'api', f"repos/{d['repo']}/issues/{p['number']}/events?per_page=100"], text=True))
    closers = [(e.get('actor') or {}).get('login') for e in ev if e['event'] == 'closed']
    rows.append({'n': p['number'], 'author': p['user'], 'closer': closers[-1] if closers else None})
self_closed = sum(r['closer'] == r['author'] for r in rows)
print(json.dumps({'repo': d['repo'], 'closed_unmerged_in_window': len(pool), 'sampled': len(rows), 'closed_by_author': self_closed,
                  'closers': sorted({r['closer'] for r in rows} - {None}, key=str)[:10], 'rows': rows}))
