#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <user@host> [remote-path]" >&2
  echo "example: $0 root@187.77.229.82" >&2
  exit 1
fi

HOST="$1"
REMOTE_PATH="${2:-~/server-kneresz}"

echo "==> deploying to $HOST:$REMOTE_PATH"

ssh "$HOST" bash -se <<EOF
set -euo pipefail
cd $REMOTE_PATH
echo "==> git pull"
git pull --ff-only
echo "==> docker compose up --build -d"
docker compose up --build -d
echo "==> waiting for api to become healthy"
for i in \$(seq 1 30); do
  if docker compose exec -T api curl -fs http://localhost:8000/health >/dev/null 2>&1; then
    echo "==> api is healthy"
    exit 0
  fi
  sleep 1
done
echo "!! api did not become healthy within 30s" >&2
docker compose logs --tail=50 api >&2
exit 1
EOF

echo "==> deploy complete"
