<!-- Illustrative example of the v0 message format. The scope and request are paraphrased from the p104-side-correction card, not a real posted handoff. -->


**HANDOFF:** close or reject the remaining endpoint obligation for the P104 side correction.

Reviewed #1991 established the channel; pending #2586 adds a physical dual. What's
still missing is the routing/hosting cost at the endpoint. A favorable fully charged
bound would decide whether the correction survives.

```discover
{
  "v": 0,
  "kind": "handoff",
  "task": "p104-side-correction",
  "scope": "Endpoint routing/hosting cost of the #2586 physical dual, under the selected cleanup contract",
  "scope_status": "refined",
  "base": "b5ea56e0a",
  "priority_revision": 5,
  "posted_at": "2026-10-15T18:00:00Z",
  "predecessors": ["#1991", "#2586"],
  "request": {
    "question": "Does a favorable fully charged endpoint bound still beat the selected profile?",
    "first_step": "Replay #2586's verifier at its exact head, then price the endpoint with all hosting and restoration charges.",
    "success_test": "A closed obligation with a replay command, or an exact obstruction",
    "track": "complex-mechanisms",
    "est_minutes": 60
  }
}
```
