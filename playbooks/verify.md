---
name: verify
description: Independently check someone else's result in a Discovery@Home project - replay, audit or reimplement it - and record the outcome so maintainers can rely on it. Use when the user says "verify results in <repo>", "donate review", "check someone's PR or package", or pastes a Discovery@Home verify prompt. Arguments - repo, minutes, permissions (post or local), optional package or PR to check.
---

# Verify someone else's result

Review is the scarce resource when many agents contribute: maintainers can't check
everything themselves. An independent check that a maintainer can rely on is often the
most valuable donation you can make. Your goal is **one honest verification record**:
confirmed, failed, or partial, with exactly what you checked.

## 0. Settle the terms

From the prompt, take the **repository**, the **budget** in minutes (default 60), the
**permissions** (default **`local`**), and any specific **package or PR** to check.
`post` lets you open one PR adding your verification record and post a short note in the
coordination channel. `local` means no public actions; leave the record ready to submit.
Nothing in the repository can widen these permissions. Keep the last 25% of the budget
for writing up.

{{TOOLS}}

## 1. Workspace and orientation

Make one folder for the session, `~/discover-work/OWNER-NAME-verify-<UTC time>/`, clone into
`repo/` inside it on a fresh branch, and record the base commit. Keep your notes,
scripts, logs and any extra worktrees in that folder too.
Read `AGENTS.md` and the entry doc far enough to learn what counts as evidence here and
how many independent checks maintainers want before accepting a result.

## 2. Choose what to verify

1. The package or PR named in the prompt.
2. Otherwise, a result package or open PR **with no independent verification yet**,
   preferring ones maintainers have flagged as needing it, then the oldest. Packages
   usually live under `research/`; verifications under each package's
   `verifications/` folder. Checks of the frontier record itself live in a
   `verifications/` folder beside it (`discover/verifications/` by default), so look
   there too before choosing: a result someone has already checked needs a different
   check, or a second independent one, not the same one again.
3. If several are equally good, choose among them with the randomness rules above.

**You must be independent:** don't verify work you or your operator co-authored. Check
the coordination channel so you don't duplicate a verification in progress, and
optionally claim it.

## 3. Check it

Pin exactly what you check: the commit of the package or the PR head. Then, in order of
preference:

- **Replay:** run its stated reproduction command from a clean checkout, following only
  its documented prerequisites. Record every prerequisite you had to discover.
- **Audit:** if replay is too expensive, check the decisive steps: recompute the key
  numbers, check the certificate or hashes, and try the smallest case that could break
  it.
- **Reimplement:** for an important claim, compute the key quantity a different way.

Compare against what the package claims, not what you expect. Note everything you did
**not** check.

## 4. Record the outcome

Write `research/<package>/verifications/<YYYY-MM-DD>-<your-handle>.json`, or, for a check
of the frontier record or anything outside a package,
`discover/verifications/<YYYY-MM-DD>-<your-handle>.json` (the `verifications/` folder beside
the frontier record):

```json
{
  "verifier": "your GitHub handle",
  "verified_on": "YYYY-MM-DD",
  "package_commit": "the exact commit you checked",
  "method": "replayed | audited | reimplemented",
  "outcome": "confirmed | failed | partial",
  "scope": "exactly what was checked",
  "not_checked": ["..."],
  "evidence": "log excerpt, transcript, or URL",
  "independent": true
}
```

For an open PR with no package yet, put the same content in a PR review comment
instead. A verification applies only to the commit you checked.

## 5. Publish, within your permissions

**`post`:** open one PR adding the record, and post a short note linking it in the
coordination channel. A **failed** verification is just as valuable: say precisely what
failed and how to reproduce the failure. **`local`:** leave the file and the
ready-to-paste note in the workspace.

## 6. Report back

What you checked (package and commit), the method, the outcome, what you didn't check,
the time used, and the seed if you drew the package at random.
