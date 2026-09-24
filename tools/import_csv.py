#!/usr/bin/env python3
"""
Bulk-add questions from a spreadsheet.

1. Fill tools/questions-import-template.csv (Excel or Google Sheets, save as CSV UTF-8).
2. Put diagram files in static/diagrams/ and write just the file name in the diagram column.
3. Run:  python3 tools/import_csv.py my-questions.csv            (adds new questions, skips existing IDs)
         python3 tools/import_csv.py my-questions.csv --update   (also overwrites existing IDs)
"""
import csv, datetime, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
chapters = json.loads((ROOT / "data/chapters.json").read_text(encoding="utf-8"))["chapters"]
by_code = {c["code"]: c for c in chapters}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    update = "--update" in sys.argv
    added = updated = skipped = 0
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
    for n, raw in enumerate(rows, start=2):
        r = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        qid = r.get("id", "")
        if not re.fullmatch(r"(11|12)-\d{2}-\d{3}", qid):
            print(f"Row {n}: ID '{qid}' should look like 11-03-017, skipped"); skipped += 1; continue
        chapter = by_code.get(qid[:5])
        if not chapter:
            print(f"Row {n}: no chapter {qid[:5]}, skipped"); skipped += 1; continue
        path = ROOT / "content/questions" / f"{qid}.json"
        if path.exists() and not update:
            print(f"Row {n}: {qid} already exists, skipped (use --update to overwrite)"); skipped += 1; continue
        qtype = (r.get("type") or "mcq").lower()
        diag = lambda v: ("/diagrams/" + v) if v and not v.startswith(("/", "http")) else v
        q = {
            "id": qid, "chapter": chapter["slug"], "type": qtype,
            "exams": [x.strip() for x in r.get("exams", "").split(",") if x.strip()],
            "difficulty": (r.get("difficulty") or "Medium").capitalize(),
            "important": r.get("top", "").lower() in ("yes", "y", "true", "1"),
            "source": r.get("source") or "PiTheory original",
            "question": r.get("question", ""), "diagram": diag(r.get("diagram", "")), "diagram_alt": r.get("diagram_alt", ""),
            "options": [{"text": r.get(f"option_{k}", ""), "image": diag(r.get(f"option_{k}_image", ""))} for k in "abcd"] if qtype == "mcq" else [],
            "answer": r.get("answer", "").upper() if qtype == "mcq" else "",
            "numerical_answer": r.get("answer", "") if qtype == "numerical" else "",
            "tolerance": r.get("tolerance") or "0",
            "solution": r.get("solution", "").replace("\\n", "\n"),
            "solution_diagram": diag(r.get("solution_diagram", "")),
            "status": (r.get("status") or "draft").lower(),
            "updated": datetime.date.today().isoformat(),
        }
        was = path.exists()
        path.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")
        updated += was; added += not was
    print(f"\nAdded {added}, updated {updated}, skipped {skipped}. Now run: python3 build.py")


if __name__ == "__main__":
    main()
