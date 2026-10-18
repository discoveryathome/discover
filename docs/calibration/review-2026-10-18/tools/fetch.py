#!/usr/bin/env python3
"""Read-only fetch of PRs and comments for review/duplicate measurements (GitHub REST via `gh api`).
usage: fetch.py OWNER/NAME SINCE_ISO OUTDIR [--reviews]
Writes OUTDIR/<owner>__<name>.json with PRs created since SINCE (and still-open older PRs),
repo-wide issue and review comments updated since SINCE, and (optionally) per-PR reviews."""
import json, subprocess, sys
from pathlib import Path

repo, since, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]); reviews = '--reviews' in sys.argv
def get(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))
keep = lambda p: {k: p.get(k) for k in ['number', 'title', 'state', 'created_at', 'closed_at', 'merged_at', 'author_association', 'draft']} | {'user': (p.get('user') or {}).get('login'), 'body': (p.get('body') or '')[:4000], 'head': (p.get('head') or {}).get('ref')}
prs = []; page = 1
while True:
    batch = get(f'repos/{repo}/pulls?state=all&sort=created&direction=desc&per_page=100&page={page}')
    if not batch: break
    prs += [keep(p) for p in batch]
    if batch[-1]['created_at'] < since: break
    page += 1
older_open = []; page = 1
while True:  # open PRs created before SINCE (context for backlog)
    batch = get(f'repos/{repo}/pulls?state=open&sort=created&direction=asc&per_page=100&page={page}')
    if not batch: break
    older_open += [keep(p) for p in batch if p['created_at'] < since]
    if batch[-1]['created_at'] >= since: break
    page += 1
def comments(kind):
    res = []; page = 1
    while True:
        batch = get(f'repos/{repo}/{kind}/comments?since={since}&per_page=100&page={page}&sort=created&direction=asc')
        if not batch: break
        for c in batch:
            url = c.get('issue_url') or c.get('pull_request_url') or ''
            res.append({'n': int(url.rsplit('/', 1)[1]) if url else None, 'user': (c.get('user') or {}).get('login'),
                        'assoc': c.get('author_association'), 'created_at': c['created_at']})
        page += 1
    return res
data = {'repo': repo, 'since': since, 'prs': [p for p in prs if p['created_at'] >= since], 'older_open': older_open,
        'issue_comments': comments('issues'), 'review_comments': comments('pulls')}
if reviews:
    data['reviews'] = {}
    for p in data['prs']:
        rv = get(f"repos/{repo}/pulls/{p['number']}/reviews?per_page=100")
        data['reviews'][p['number']] = [{'user': (r.get('user') or {}).get('login'), 'assoc': r.get('author_association'), 'submitted_at': r.get('submitted_at'), 'state': r.get('state')} for r in rv]
out.mkdir(parents=True, exist_ok=True)
(out / (repo.replace('/', '__') + '.json')).write_text(json.dumps(data))
print(repo, 'prs', len(data['prs']), 'older_open', len(older_open), 'issue_comments', len(data['issue_comments']), 'review_comments', len(data['review_comments']))
