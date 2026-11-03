# The Clinical Judgment Guide

**A manual for nursing faculty and clinical educators who want to turn wrong answers into learning.**

Written in the plain, friendly style of Dylan Asdale's *The Massive AI Manual* — step by step, never condescending — but with a **human-first lens**: no AI needed, just you, your students, and better questions.

---

## What's inside

Five practice guides in `docs/`, each paired with a printable worksheet:

| Guide | What it helps you do | Worksheet |
| --- | --- | --- |
| [Post-Clinical Debrief Scripts](docs/01-debrief-scripts.md) | Run 5-, 15-, and 30-minute debriefs that treat wrong answers as data, not shame | `site/worksheets/worksheet-debrief.html` |
| [The Judgment Ladder](docs/02-judgment-ladder.md) | Ask climbing questions that move students from noticing to reflecting | `site/worksheets/worksheet-judgment-ladder.html` |
| [Family-to-Nurse Handoff Teaching](docs/03-family-to-nurse-handoff-teaching.md) | Teach students to *receive* clinical information from families — a skill almost never practiced | `site/worksheets/worksheet-family-handoff.html` |
| [Handoff Rubric Builder](docs/04-handoff-rubric-builder.md) | Build a fair, observable scoring rubric for any handoff skill in about 20 minutes | `site/worksheets/worksheet-rubric-builder.html` |
| [Peer-Led Micro-Lessons](docs/05-peer-led-micro-lessons.md) | Let students teach 10-minute lessons that stick better than a lecture | `site/worksheets/worksheet-micro-lesson.html` |

## The static site

`site/` is a self-contained, offline-friendly HTML version of the whole manual, with print-optimized worksheets (`Ctrl/Cmd-P` → save as PDF or print directly). No JavaScript frameworks, no cookies, no tracking, no network calls.

## Build and test

Everything runs on stock Python 3 — no pip installs, no internet.

```bash
# Rebuild the site from docs/
python3 tools/build.py

# Run the verification suite (builds, then checks pages, links, and print support)
python3 tests/test_build.py
```

Open `site/index.html` in any browser to read the site.

## Ground rules of this guide

- **Education only.** This is teaching material for faculty and students. It is never medical advice, never a clinical protocol, and never a substitute for your program's policies, your state's practice act, or your institution's procedures.
- **Zero patient data.** Every scenario and script in these guides uses clearly fictional examples (names like "Sample" and "Practice"). Do not paste real patient information into any worksheet, debrief note, or rubric.
- **Free forever.** MIT licensed. Copy it, adapt it for your program, print the worksheets as many times as you like.

## About

Created by **Asdale Dynamics, LLC** — Dylan Asdale's shop for beginner-friendly AI education, practical books and guides, and open tools. Learn more at [dylanasdale.github.io](https://dylanasdale.github.io).

**Companion guide:** this project pairs with *ai-for-nurse-educators-guide* (the AI-focused sibling). Start there if you want AI in the loop; start here if you want the human-first version.

## License

[MIT](LICENSE) — Copyright (c) 2026 Asdale Dynamics, LLC
