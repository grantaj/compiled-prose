#!/usr/bin/env python3
import os, sys
from openai import OpenAI

def main():
    prompt = sys.stdin.read()

    model = os.environ.get("OPENAI_MODEL", "gpt-5")
    temperature = float(os.environ.get("OPENAI_TEMPERATURE", "0.2"))
    seed = os.environ.get("OPENAI_SEED")
    seed = int(seed) if seed is not None else None

    client = OpenAI()

    kwargs = {"model": model, "input": prompt, "temperature": temperature}
    if seed is not None:
        kwargs["seed"] = seed

    resp = client.responses.create(**kwargs)
    sys.stdout.write(resp.output_text)

if __name__ == "__main__":
    main()
