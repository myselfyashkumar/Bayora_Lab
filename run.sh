#!/usr/bin/env bash
# One command to run Bayora Lab on your own machine: bash run.sh
set -e
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is needed. Install Docker Desktop: https://docs.docker.com/get-docker/"
  echo "No install? Open this repository in GitHub Codespaces instead (see README)."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker is installed but not running. Start Docker Desktop, then run: bash run.sh"
  exit 1
fi
if ! python3 -c "import nacl" >/dev/null 2>&1; then
  echo "Installing the one Python package the verifier needs (PyNaCl)..."
  python3 -m pip install --user --quiet pynacl 2>/dev/null \
    || python3 -m pip install --user --quiet --break-system-packages pynacl 2>/dev/null \
    || sudo apt-get install -y python3-nacl
fi
exec python3 tools/showcase.py "$@"
