#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-/opt/bp-cms-scraper}"
cd "$ROOT_DIR"

git pull --rebase
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Upgrade completed. Please restart managed services (bot/cron workers) as needed."

