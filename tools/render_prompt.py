#!/usr/bin/env python3
import argparse
from pathlib import Path

def read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8").rstrip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--review", required=False)
    args = ap.parse_args()

    print(read(args.system))
    print("\n\n# Target\n")
    print(read(args.target))
    print("\n\n# Stage\n")
    print(read(args.stage))
    print("\n\n# Input (Markdown)\n")
    print(read(args.inp))

    if args.review:
        print("\n\n# Peer Review (Markdown, Diagnostic Only)\n")
        print(read(args.review))

    print("\n\n# Output\n")
    print("Return only the LaTeX output. Do not repeat or summarize the prompt.")

if __name__ == "__main__":
    main()
