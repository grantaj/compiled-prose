#!/usr/bin/env bash
set -euo pipefail

BACKEND="${BACKEND:-ollama}"

case "$BACKEND" in
  openai)
    python tools/openai_responses.py
    ;;
  ollama)
    PROMPT="$(cat)"
    : "${OLLAMA_HOST:=http://localhost:11434}"
    : "${OLLAMA_MODEL:=llama3.1}"

    if ! RESP="$(curl -sS -w '\n__HTTP_STATUS__%{http_code}' "${OLLAMA_HOST}/api/generate" \
      -H 'Content-Type: application/json' \
      -d "$(PROMPT="$PROMPT" python - <<'PY'
import json, os
print(json.dumps({
  "model": os.environ["OLLAMA_MODEL"],
  "prompt": os.environ["PROMPT"],
  "stream": False
}))
PY
)" )"; then
      echo "Ollama request failed to connect to ${OLLAMA_HOST}/api/generate" >&2
      exit 1
    fi

    BODY="${RESP%$'\n__HTTP_STATUS__'*}"
    STATUS="${RESP##*$'\n__HTTP_STATUS__'}"
    if [ -z "$BODY" ] || [ -z "$(printf '%s' "$BODY" | tr -d '[:space:]')" ]; then
      echo "Ollama returned empty response (HTTP $STATUS) from /api/generate" >&2
      exit 1
    fi
    if [ "$STATUS" != "200" ]; then
      echo "Ollama /api/generate failed (HTTP $STATUS):" >&2
      echo "$BODY" >&2
      exit 1
    fi

    OLLAMA_HTTP_STATUS="$STATUS" printf '%s' "$BODY" | python -c 'import json, os, sys
body = sys.stdin.read()
try:
    data = json.loads(body)
except json.JSONDecodeError as exc:
    snippet = body[:200].replace("\\n", "\\\\n")
    sys.stderr.write(f"Ollama returned invalid JSON: {exc}\\n")
    sys.stderr.write(f"HTTP status: {os.environ.get('OLLAMA_HTTP_STATUS', '')}\\n")
    sys.stderr.write(f"Raw response (first 200 chars): {snippet}\\n")
    sys.stderr.write(f"Raw response length: {len(body)}\\n")
    sys.exit(1)
sys.stdout.write(data.get("response",""))'
    ;;
  *)
    echo "Unknown BACKEND=$BACKEND (use openai or ollama)" >&2
    exit 2
    ;;
esac
