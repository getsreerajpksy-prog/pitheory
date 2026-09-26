# PiTheory website: instructions for Claude

This repository is the pitheory.in NEET/JEE physics question bank. `build.py` turns the files below into the website; GitHub Actions publishes it on every push to `main`.

## Adding questions from screenshots
- One file per question: `content/questions/<ID>.json`. Copy the exact structure of an existing file (for example `content/questions/12-03-002.json`).
- ID = `class-chapter-number`, e.g. `11-03-017`. Chapter codes and slugs are in `data/chapters.json`. Get the number from `python3 tools/next_id.py <chapter code> [count]`, which also counts IDs of deleted questions from the git history. Never reuse or change an ID, including the ID of a deleted question; gaps left by deletions stay empty.
- `chapter` = the chapter's `slug` from `data/chapters.json`.
- `type`: `mcq` (exactly 4 options, `answer` A/B/C/D, `numerical_answer` "") or `numerical` (JEE only, `options` [], `answer` "", `numerical_answer` a number, `tolerance` "0" unless stated).
- `exams`: any of `NEET`, `JEE Main`, `JEE Advanced`.
- `source`: exam and date for previous year questions, e.g. `JEE Main 2024 (27 Jan, Shift 1)`, only if the user states it; otherwise `PiTheory original`.
- Maths in KaTeX: inline `$...$`, display `$$...$$`. Blank line between paragraphs.
- Only previous year exam questions (NEET, JEE Main/Advanced, AIEEE, AIPMT, EAMCET, KCET and similar entrance exams, with the exam and year known) may be transcribed exactly. Never copy questions from coaching modules, textbooks or other websites, even if they are widely shared; for those, write a genuinely new question on the same concept and level (new situation, numbers and wording), with source `PiTheory original`.
- Write a clear step-by-step solution in your own words and double-check the answer yourself; if your answer disagrees with an answer key the user gives, tell the user instead of guessing.
- New questions always get `"status": "draft"` and `"updated"` = today's date (YYYY-MM-DD). The user publishes them after checking.

## Diagrams
- Save in `static/diagrams/<ID>.svg` (or `.png`) and set `"diagram": "/diagrams/<ID>.svg"` plus a one-line `diagram_alt`.
- Redraw simple diagrams (circuits, inclines, pulleys, rays, graphs) as clean SVG: white background, black 2.5px strokes, Arial labels, like `static/diagrams/12-03-002.svg`. Crop complex ones from the screenshot as PNG instead.
- The diagram always renders after the question text, before the options.

## Before finishing
1. Run `python3 build.py` and confirm it reports no skipped questions.
   Run `python3 tools/find_duplicates.py` and tell the user about any pair that involves a new question. Never delete a duplicate yourself; list both IDs and let the user choose which to keep, then remove the other with `python3 tools/find_duplicates.py --delete <ID>`.
2. Commit with a message like `Add 11-01-003 to 11-01-012 (drafts)` and push to `main`.
3. Tell the user which IDs were added, and any question where you were unsure of the transcription or answer.

Do not change `build.py`, `assets/`, `admin/` or `data/` unless the user asks.
