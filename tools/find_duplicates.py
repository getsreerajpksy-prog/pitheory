#!/usr/bin/env python3
"""
Find questions that look like duplicates, and delete the ones you don't want.

  python3 tools/find_duplicates.py                  list pairs that are 80% or more alike
  python3 tools/find_duplicates.py --min 70         use a lower threshold (catches reworded copies)
  python3 tools/find_duplicates.py --delete 11-03-017
                                                    delete that question, plus its diagram files
                                                    if no other question uses them

The check compares question text and option text, ignoring maths formatting,
so the same question typed from two sources is still caught. Two questions
that only share a template ("the output Y of the given logic gate is...")
can also score high: read both before deleting.
"""
import difflib, itertools, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QDIR = ROOT / "content/questions"


def load():
    qs = []
    for f in sorted(QDIR.glob("*.json")):
        q = json.loads(f.read_text(encoding="utf-8"))
        text = q.get("question", "") + " " + " ".join(o.get("text", "") for o in q.get("options") or [])
        text = re.sub(r"\\[a-zA-Z]+|[^a-z0-9 ]", " ", text.lower())
        q["_norm"] = " ".join(text.split())
        q["_file"] = f
        qs.append(q)
    return qs


def images(q):
    paths = [q.get("diagram"), q.get("solution_diagram")] + [o.get("image") for o in q.get("options") or []]
    return {p for p in paths if p}


def find(threshold):
    qs = load()
    pairs = []
    for q in qs:
        q["_words"] = set(q["_norm"].split())
    for a, b in itertools.combinations(qs, 2):
        # cheap pre-filter: very alike texts must share most of their words
        wa, wb = a["_words"], b["_words"]
        if len(wa & wb) < threshold * 0.6 * max(len(wa), len(wb)):
            continue
        m = difflib.SequenceMatcher(None, a["_norm"], b["_norm"])
        if m.quick_ratio() < threshold:
            continue
        r = m.ratio()
        if r >= threshold:
            pairs.append((r, a, b))
    print(f"Checked {len(qs)} questions.")
    if not pairs:
        print(f"No pairs {threshold:.0%} or more alike.")
        return
    for r, a, b in sorted(pairs, key=lambda p: -p[0]):
        print(f"\n{r:.0%} alike")
        for q in (a, b):
            print(f"  {q['id']}  [{q.get('status', '')}]  {q.get('source', '')}  answer {q.get('answer') or q.get('numerical_answer')}")
            print(f"      {q.get('question', '')[:110].replace(chr(10), ' ')}")
    print(f"\n{len(pairs)} pair(s). To remove one: python3 tools/find_duplicates.py --delete <ID>")


def delete(qid):
    target = QDIR / f"{qid}.json"
    if not target.exists():
        sys.exit(f"No question {qid}")
    q = json.loads(target.read_text(encoding="utf-8"))
    others = set().union(*(images(o) for o in load() if o["id"] != qid))
    target.unlink()
    print(f"Deleted {target.relative_to(ROOT)}")
    for p in images(q) - others:
        f = ROOT / "static" / p.lstrip("/")
        if f.exists():
            f.unlink()
            print(f"Deleted {f.relative_to(ROOT)}")
    if q.get("status") == "published":
        print("Note: this question was published, so its page will disappear from the site on the next deploy.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--delete" in args:
        delete(args[args.index("--delete") + 1])
    else:
        find(float(args[args.index("--min") + 1]) / 100 if "--min" in args else 0.80)
