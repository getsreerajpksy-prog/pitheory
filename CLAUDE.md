# PiTheory website: instructions for Claude

This repository is the pitheory.in NEET/JEE physics question bank. `build.py` turns the files below into the website; GitHub Actions publishes it on every push to `main`.

## Adding questions from screenshots
- One file per question: `content/questions/<ID>.json`. Copy the exact structure of an existing file (for example `content/questions/12-03-002.json`).
- ID = `class-chapter-number`, e.g. `11-03-017`. Chapter codes and slugs are in `data/chapters.json`. Before choosing a number, list the existing files for that chapter and use the next free number. Never reuse or change an existing ID.
- `chapter` = the chapter's `slug` from `data/chapters.json`.
- `type`: `mcq` (exactly 4 options, `answer` A/B/C/D, `numerical_answer` "") or `numerical` (JEE only, `options` [], `answer` "", `numerical_answer` a number, `tolerance` "0" unless stated).
- `exams`: any of `NEET`, `JEE Main`, `JEE Advanced`.
- `source`: exam and date for previous year questions, e.g. `JEE Main 2024 (27 Jan, Shift 1)`, only if the user states it; otherwise `PiTheory original`.
- Maths in KaTeX: inline `$...$`, display `$$...$$`. Blank line between paragraphs.
- Transcribe the question and options exactly. Write a clear step-by-step solution and double-check the answer; if your answer disagrees with an answer key the user gives, tell the user instead of guessing.
- New questions always get `"status": "draft"` and `"updated"` = today's date (YYYY-MM-DD). The user publishes them after checking.

## Diagrams
- Save in `static/diagrams/<ID>.svg` (or `.png`) and set `"diagram": "/diagrams/<ID>.svg"` plus a one-line `diagram_alt`.
- Redraw simple diagrams (circuits, inclines, pulleys, rays, graphs) as clean SVG: white background, black 2.5px strokes, Arial labels, like `static/diagrams/12-03-002.svg`. Crop complex ones from the screenshot as PNG instead.
- The diagram always renders after the question text, before the options.

## Before finishing
1. Run `python3 build.py` and confirm it reports no skipped questions.
2. Commit with a message like `Add 11-01-003 to 11-01-012 (drafts)` and push to `main`.
3. Tell the user which IDs were added, and any question where you were unsure of the transcription or answer.

Do not change `build.py`, `assets/`, `admin/` or `data/` unless the user asks.
