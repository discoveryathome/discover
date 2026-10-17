# Agents

This repository is the canonical Discovery@Home hub: the spec, the `discover` plugin and
CLI, the project registry, and the explore site.

- **Contributing hub work** (assessing projects, verifying assessments, improving the
  rubric, tooling or gallery): read [`DISCOVERY.md`](DISCOVERY.md). The hub is listed on
  itself as a Discovery@Home project.
- **Developing the code:** see the Development section of [`README.md`](README.md).
  Run `make test` before proposing changes. `spec/schemas/` is canonical; `make sync`
  copies it into the plugin.

Don't contact maintainers of other projects on the hub's behalf. Outreach follows the
first-contact rule in `spec/v0.md` §11.4 and is done by hub maintainers.
