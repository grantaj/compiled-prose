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

    curl -s "${OLLAMA_HOST}/api/generate" \
      -H 'Content-Type: application/json' \
      -d "$(python - <<PY
import json, os
print(json.dumps({
  "model": os.environ["OLLAMA_MODEL"],
  "prompt": """$PROMPT""",
  "stream": False
}))
PY
)" | python - <<'PY'
import json, sys
data = json.load(sys.stdin)
sys.stdout.write(data.get("response",""))
PY
    ;;
  *)
    echo "Unknown BACKEND=$BACKEND (use openai or ollama)" >&2
    exit 2
    ;;
esac
