#!/usr/bin/env python3
"""
Print the next free question ID for one or more chapters.

  python3 tools/next_id.py 11-03            -> 11-03-006
  python3 tools/next_id.py 11-03 12-14 5    -> next 5 IDs for each chapter

An ID is "used" if a question file has it now OR ever had it in the git
history (so IDs of deleted questions are never handed out again: old links,
Google results and students' saved progress would otherwise point to a
different question). Gaps left by deleted questions stay empty.
"""
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def used_ids():
    ids = {f.stem for f in (ROOT / "content/questions").glob("*.json")}
    try:
        log = subprocess.run(["git", "log", "--all", "--format=", "--name-only", "--", "content/questions"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
        ids |= set(re.findall(r"content/questions/((?:11|12)-\d{2}-\d{3})\.json", log))
    except (OSError, subprocess.CalledProcessError):
        print("warning: could not read git history; only current files checked", file=sys.stderr)
    return ids


def main():
    args = sys.argv[1:]
    count = int(args.pop()) if args and args[-1].isdigit() else 1
    if not args or not all(re.fullmatch(r"(11|12)-\d{2}", a) for a in args):
        sys.exit(__doc__)
    ids = used_ids()
    for code in args:
        top = max((int(i[6:]) for i in ids if i.startswith(code + "-")), default=0)
        print(" ".join(f"{code}-{top + k:03d}" for k in range(1, count + 1)))


if __name__ == "__main__":
    main()
