# Bayora Lab

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/myselfyashkumar/Bayora_Lab)

Red team, blue team and an AI model under test run side by side in isolated containers.
Every isolation claim is checked by attacking the platform itself: **35 of 35 attacks stopped**.

**Project page:** https://myselfyashkumar.github.io/Bayora_Lab/

## Run it in your browser (nothing to install)

1. Click **Open in GitHub Codespaces** above and sign in to GitHub.
2. Click **Create codespace** and wait about 2 minutes.
3. In the terminal, type `make showcase`. At the end, the visual report opens in a new tab.

## Run it on your computer

Install and start [Docker Desktop](https://docs.docker.com/get-docker/), then:

```bash
git clone https://github.com/myselfyashkumar/Bayora_Lab
cd Bayora_Lab
bash run.sh
```

`run.sh` checks Docker, installs the one Python package it needs, and starts the guided demo.
On Windows, run it inside WSL (Ubuntu).

## All commands

```bash
make showcase # guided demo, module by module, then opens the visual report
make demo     # new experiment keys + build + start all containers
make test     # 35 attacks on our own system; saves evidence/<exp_id>/ and report.html
make serve    # view reports at http://localhost:8080/latest_report.html
make publish  # copy the latest report to docs/ for the project page
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
