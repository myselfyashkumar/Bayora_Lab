# Bayora Lab (MVP)

Red team, blue team and a model under test run side by side. Every isolation
claim is checked by `make test`, which attacks the platform itself.

## Run it

Requirements: Docker with Compose v2, Python 3.10+, `pip install pynacl`, `make`, `curl`.

```bash
make demo     # new experiment keys + build + start all containers
make test     # prints the pass/fail table, saves evidence/<exp_id>/
make down     # remove containers, networks and volumes
```

## Layout

| Path | What it is |
| --- | --- |
| `docker-compose.yml` | Five internal networks, hardened containers, secrets |
| `services/gateway/` | The only bridge: auth, attack flow, uniform replies, audit log |
| `services/notary/` | Signs audit checkpoints with its own key |
| `services/defense_runner/` | Sealed Blue defense (regex policy uploaded by Blue) |
| `services/model_stub/` | Stub model; deliberately leaks its system prompt if asked |
| `services/clients/` | Red and Blue toolboxes: attack client, policy upload, probes |
| `tools/` | Experiment setup, audit verifier, tamper tool, canary scanner |
| `tests/run_tests.sh` | The test suite |

## What the MVP does not cover yet

Custom seccomp profile, a real model, the side-channel study, a fresh model per
experiment, the prefix-cache probe, decoy listeners and a dashboard. The gateway
also sits on a non-internal `edge` network so the host can reach its admin
endpoints; Phase 2 moves admin to a separate listener.
