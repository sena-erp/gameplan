#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="${BENCH_DIR:-/home/arvis/avinash-industries/bench}"
APP_DIR="${APP_DIR:-$BENCH_DIR/apps/gameplan}"
BRANCH="${BRANCH:-main}"
SITES="${SITES:-avinash2.localhost avinash.localhost}"
LOCK_FILE="${LOCK_FILE:-/tmp/sena-gameplan-deploy.lock}"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another Gameplan deployment is already running."
  exit 1
fi

cd "$APP_DIR"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Refusing to deploy with local changes in $APP_DIR"
  git status --short
  exit 1
fi

git fetch origin "$BRANCH"
git switch "$BRANCH"
git reset --hard "origin/$BRANCH"

cd "$APP_DIR/frontend"
yarn install --frozen-lockfile

cd "$BENCH_DIR"
bench build --app gameplan

for site in $SITES; do
  bench --site "$site" migrate
  bench --site "$site" clear-cache
done

bench version --format plain | grep '^gameplan '
