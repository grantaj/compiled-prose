#!/usr/bin/env python3
import json
import os
import sys
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


def main() -> int:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "llama3.1")
    url = f"{host.rstrip('/')}/api/tags"

    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
    except (URLError, HTTPError) as exc:
        print(f"Ollama not reachable at {host}: {exc}", file=sys.stderr)
        return 1

    try:
        tags = json.loads(body)
    except json.JSONDecodeError:
        print("Ollama returned invalid JSON from /api/tags", file=sys.stderr)
        return 1

    names = [m.get("name", "") for m in tags.get("models", [])]
    if model in names or f"{model}:latest" in names:
        resolved = model if model in names else f"{model}:latest"
        print(f"Ollama OK: {resolved}")
        return 0

    print(f"Ollama model not found: {model}", file=sys.stderr)
    print("Available models:", ", ".join(names), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
