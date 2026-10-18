#!/usr/bin/env python3
"""Spec §3.2 Review measurements on fetched data, under explicit variants.
usage: analyze.py DATADIR END_ISO OUT_JSON
First maintainer response to a PR = earliest of: an issue/review comment or review by a maintainer
(author_association OWNER/MEMBER/COLLABORATOR) who is not the PR author; merge; close (the closer is not
in the data, so a close counts as a response, as in the integer-mult-bounds record). Bots are excluded."""
import json, random, statistics, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

MAINT = {'OWNER', 'MEMBER', 'COLLABORATOR'}
T = lambda s: datetime.fromisoformat(s.replace('Z', '+00:00'))
DAY = 86400.0
datadir, END, outp = Path(sys.argv[1]), T(sys.argv[2]), Path(sys.argv[3])


def load(path):
    d = json.loads(path.read_text())
    prs = [p for p in d['prs'] if not (p['user'] or '').endswith('[bot]') and p['user'] not in ('sympy-bot',)]
    ev = {}
    for c in d['issue_comments'] + d['review_comments']:
        if c['assoc'] in MAINT: ev.setdefault(c['n'], []).append((T(c['created_at']), c['user']))
    for n, rv in d.get('reviews', {}).items():
        for r in rv:
            if r['assoc'] in MAINT and r['submitted_at']: ev.setdefault(int(n), []).append((T(r['submitted_at']), r['user']))
    for p in prs:
        times = [t for t, u in ev.get(p['number'], []) if u != p['user']]
        for k in ('merged_at', 'closed_at'):
            if p[k]: times.append(T(p[k]))
        p['_created'] = T(p['created_at']); p['_resp'] = min(times) if times else None
        p['_outside'] = p['author_association'] not in MAINT
    return d['repo'], prs  # PRs created before the fetch start (older_open) are excluded: their earlier comments are not in the data


def grade(ts, n_await_start, n_await_end, minimum=20, denominator='all'):
    """ts: list of (response_days or None if censored, age_days at window end)."""
    if len(ts) < minimum: return {'n': len(ts), 'grade': 'unknown'}
    vals = [r if r is not None else float('inf') for r, a in ts]
    med = statistics.median(vals)
    late = [1 for r, a in ts if (r is not None and r > 7) or (r is None and a > 7)]
    denom = len(ts) if denominator == 'all' else sum(1 for r, a in ts if a >= 7)
    share = len(late) / denom if denom else float('nan')
    growing = n_await_end > n_await_start
    g = 'strong' if med < 3 and share < .10 and not growing else 'adequate' if med < 14 and share < .30 else 'weak'
    return {'n': len(ts), 'denominator': denom, 'median_days': round(med, 3) if med != float('inf') else 'inf',
            'share_over_7d': round(share, 4), 'await_start': n_await_start, 'await_end': n_await_end, 'grade': g}


def window(prs, end, outside_only, **kw):
    start = end - timedelta(days=14)
    pop = [p for p in prs if (p['_outside'] or not outside_only)]
    def awaiting(t): return sum(1 for p in pop if p['_created'] < t and (p['_resp'] is None or p['_resp'] > t))
    ts = []
    for p in pop:
        if start <= p['_created'] < end:
            r = p['_resp'] if p['_resp'] is not None and p['_resp'] <= end else None
            ts.append(((r - p['_created']).total_seconds() / DAY if r else None, (end - p['_created']).total_seconds() / DAY))
    return ts, grade(ts, awaiting(start), awaiting(end), **kw)


report = {'end': sys.argv[2], 'repos': {}}
rng = random.Random(20261018)
for f in sorted(datadir.glob('*.json')):
    repo, prs = load(f); R = report['repos'][repo] = {}
    for pop in ('all', 'outside'):
        o = pop == 'outside'
        ts, g = window(prs, END, o); R[pop] = g
        R[pop + '_denominator_eligible'] = window(prs, END, o, denominator='eligible')[1]
        R[pop + '_no_minimum'] = window(prs, END, o, minimum=1)[1]
        R[pop + '_rolling'] = {}
        for k in range(0, 15):
            e = END - timedelta(days=k)
            R[pop + '_rolling'][e.date().isoformat()] = window(prs, e, o)[1]
        # subsampling: how often does a random n-sample of this window's PRs give the full-window grade?
        if len(ts) >= 40:
            full = grade(ts, 0, 0, minimum=1)['grade']  # backlog term held fixed (not growing) for this test
            R[pop + '_subsample'] = {'full_grade_backlog_fixed': full}
            for n in (5, 10, 20, 40):
                agree = sum(grade(rng.sample(ts, n), 0, 0, minimum=1)['grade'] == full for _ in range(2000))
                R[pop + '_subsample'][str(n)] = round(agree / 2000, 3)
    pop = [p for p in prs if p['_outside']]
    R['outside_backlog_daily'] = {}
    for k in range(0, 15):
        t = END - timedelta(days=k)
        aw = [p for p in pop if p['_created'] < t and (p['_resp'] is None or p['_resp'] > t)]
        R['outside_backlog_daily'][t.date().isoformat()] = {'awaiting': len(aw), 'awaiting_over_1d': sum((t - p['_created']).total_seconds() > DAY for p in aw), 'awaiting_over_7d': sum((t - p['_created']).total_seconds() > 7 * DAY for p in aw)}
    # self-response: maintainer-authored PRs whose first "response" is the author's own merge/close
    mine = [p for p in prs if not p['_outside'] and END - timedelta(days=14) <= p['_created'] < END]
    R['maintainer_authored_in_window'] = len(mine)
    R['maintainer_authored_median_days'] = round(statistics.median([(p['_resp'] - p['_created']).total_seconds() / DAY if p['_resp'] and p['_resp'] <= END else float('inf') for p in mine]), 3) if mine else None
outp.write_text(json.dumps(report, indent=1) + '\n')
for repo, R in report['repos'].items():
    print(repo); print('  all     ', R['all']); print('  outside ', R['outside']); print('  outside, eligible denom', R['outside_denominator_eligible'])
    print('  outside, no minimum', R['outside_no_minimum']); print('  maintainer-authored', R['maintainer_authored_in_window'], 'median days', R['maintainer_authored_median_days'])
    print('  rolling outside grades', ' '.join(f"{k[5:]}:{v['grade'][0]}{v['n']}" for k, v in sorted(R['outside_rolling'].items())))
    print('  backlog (awaiting / >1d / >7d)', ' '.join(f"{k[5:]}:{v['awaiting']}/{v['awaiting_over_1d']}/{v['awaiting_over_7d']}" for k, v in sorted(R['outside_backlog_daily'].items())))
    for pop in ('all', 'outside'):
        if pop + '_subsample' in R: print('  subsample', pop, R[pop + '_subsample'])


def proposed(prs, end):
    """Proposed §3.2 Review reading: outside contributions only; share over 7 days among contributions
    opened >= 7 days before the window end; backlog = outside PRs awaiting a first response for more than
    1 day, compared at the window end and at its midpoint (7 days earlier); growing = up by more than
    max(3, 10%). Fewer than 20 contributions >= 7 days old: share unknown, grade at most adequate."""
    pop = [p for p in prs if p['_outside']]
    def backlog(t): return sum(1 for p in pop if p['_created'] < t - timedelta(days=1) and (p['_resp'] is None or p['_resp'] > t))
    ts = window(prs, end, True, minimum=1)[0]
    if len(ts) < 20: return {'n': len(ts), 'grade': 'unknown'}
    vals = [r if r is not None else float('inf') for r, a in ts]; med = statistics.median(vals)
    elig = [(r, a) for r, a in ts if a >= 7]
    share = sum(1 for r, a in elig if r is None or r > 7) / len(elig) if elig else float('nan')
    b0, b1 = backlog(end - timedelta(days=7)), backlog(end)
    growing = b1 - b0 > max(3, 0.1 * b0)
    if len(elig) < 20:  # share unknown: grade on the median alone, at most adequate
        share = float('nan'); g = 'adequate' if med < 14 else 'weak'
    else:
        g = 'strong' if med < 3 and share < .10 and not growing else 'adequate' if med < 14 and share < .30 else 'weak'
    return {'n': len(ts), 'eligible': len(elig), 'median_days': round(med, 3) if med != float('inf') else 'inf', 'share_over_7d_eligible': round(share, 4),
            'backlog_mid': b0, 'backlog_end': b1, 'growing': growing, 'grade': g}


for f in sorted(datadir.glob('*.json')):
    repo, prs = load(f)
    report['repos'][repo]['proposed'] = proposed(prs, END)
    report['repos'][repo]['proposed_rolling'] = {(END - timedelta(days=k)).date().isoformat(): proposed(prs, END - timedelta(days=k))['grade'] for k in range(15)}
    print('PROPOSED', repo, report['repos'][repo]['proposed'], ' '.join(f"{k[5:]}:{v[0]}" for k, v in sorted(report['repos'][repo]['proposed_rolling'].items())))
outp.write_text(json.dumps(report, indent=1) + '\n')
