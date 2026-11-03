#!/usr/bin/env python3
"""Build the static site from docs/ markdown + worksheet data.

Stdlib only — no pip installs, no network. Run:

    python3 tools/build.py

Outputs a self-contained static site in site/.
"""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE = ROOT / "site"

SUBTITLE = "A manual for clinical educators turning wrong answers into learning"
TAGLINE = ("Plain-English debrief scripts, judgment-ladder questions, handoff "
           "teaching, and peer micro-lessons — human-first, education only, "
           "never medical advice.")

# slug -> (number label, short title, card blurb)
GUIDE_META = {
    "01-debrief-scripts": ("Guide 1", "Post-Clinical Debrief Scripts",
                           "Word-for-word scripts for 5-, 15-, and 30-minute "
                           "debriefs, a phrase bank, and what to do with wrong answers."),
    "02-judgment-ladder": ("Guide 2", "The Judgment Ladder",
                           "Climbable questions that move a student from "
                           "noticing to reflecting — with five ready-made chains."),
    "03-family-to-nurse-handoff-teaching": ("Guide 3", "Family-to-Nurse Handoff Teaching",
                                            "Teach students to receive information from "
                                            "families: the doorway script, fiction-kit role cards, teach-back."),
    "04-handoff-rubric-builder": ("Guide 4", "Handoff Rubric Builder",
                                  "Build a fair, observable scoring rubric for any "
                                  "handoff skill in about 20 minutes."),
    "05-peer-led-micro-lessons": ("Guide 5", "Peer-Led Micro-Lessons",
                                  "The 10-minute student-taught lesson: skeleton, "
                                  "rotation plan, prep worksheet, and a three-item peer rubric."),
}

WORKSHEET_FOR = {
    "01-debrief-scripts": "worksheet-debrief.html",
    "02-judgment-ladder": "worksheet-judgment-ladder.html",
    "03-family-to-nurse-handoff-teaching": "worksheet-family-handoff.html",
    "04-handoff-rubric-builder": "worksheet-rubric-builder.html",
    "05-peer-led-micro-lessons": "worksheet-micro-lesson.html",
}

WORKSHEETS = {
    "worksheet-debrief.html": {
        "guide": "Guide 1", "doc": "01-debrief-scripts.html",
        "title": "Debrief Planner",
        "subtitle": "Plan your next post-clinical debrief",
        "blurb": ("Fill this in before your circle opens. Five minutes of "
                  "planning saves twenty of wandering."),
        "sections": [
            ("Clock", [
                ("prompt", "Debrief length ( 5 / 15 / 30 min ): ______________________"),
                ("prompt", "Where: ______________________   How many students: ______"),
            ]),
            ("The one case", [
                ("prompt", "The case I'll pull (FICTIONAL details only — no names, rooms, or chart numbers):"),
                ("lines", 3),
                ("prompt", "The decision fork — the moment it split:"),
                ("lines", 3),
            ]),
            ("My ladder chain", [
                ("prompt", "Rung 1 · What did you see? (my opening question):"),
                ("lines", 2),
                ("prompt", "Rung 2 · What might it mean? (my second question):"),
                ("lines", 2),
                ("prompt", "Rung 3 · What would you do? (my choice moment):"),
                ("lines", 2),
                ("prompt", "Rung 4 · What changed for you? (my closing question):"),
                ("lines", 2),
            ]),
            ("Commitments to bring back", [
                ("check", "I will return each person's commitment card next clinical."),
                ("check", "I will say \"Tell me more\" at least once — and wait three seconds."),
                ("check", "No real patient data anywhere on this sheet."),
            ]),
        ],
    },
    "worksheet-judgment-ladder.html": {
        "guide": "Guide 2", "doc": "02-judgment-ladder.html",
        "title": "Judgment Ladder Practice Sheet",
        "subtitle": "Track where each student stands on the ladder",
        "blurb": ("One page per student. Check the rung they reached today; "
                  "the climb across the semester is the grade."),
        "sections": [
            ("Student + scene (fictional only)", [
                ("prompt", "Student: ______________________   Date: ______________"),
                ("prompt", "Scene — what happened, in plain words, no identifiers:"),
                ("lines", 2),
            ]),
            ("Rungs reached today", [
                ("check", "Rung 0 · Data floor — gave actual numbers / words / sounds"),
                ("check", "Rung 1 · Noticing — described what they saw"),
                ("check", "Rung 2 · Interpreting — offered explanations with options"),
                ("check", "Rung 3 · Responding — said what they'd do, in order"),
                ("check", "Rung 4 · Reflecting — named what they'd change"),
                ("check", "Rung 5 · Transfer — found the pattern somewhere else"),
            ]),
            ("The rung I asked for next", [
                ("prompt", "One step above their weakest link, not three. My question:"),
                ("lines", 2),
            ]),
            ("Springboard from today", [
                ("prompt", "Question hook for next session (one sentence):"),
                ("lines", 2),
            ]),
        ],
    },
    "worksheet-family-handoff.html": {
        "guide": "Guide 3", "doc": "03-family-to-nurse-handoff-teaching.html",
        "title": "Family Handoff Role-Play Kit",
        "subtitle": "Observer checklist + doorway-script practice",
        "blurb": ("Print one per triad. All scenarios are fictional — role cards "
                  "come from the guide's fiction kit."),
        "sections": [
            ("Triad setup", [
                ("prompt", "Receiver: ______________   Family member: ______________   Observer: ______________"),
                ("prompt", "Fictional scenario card (A · Chronic Expert / B · Guilty Reporter / C · Onset Story): ______"),
            ]),
            ("Doorway script — Receiver self-check", [
                ("check", "1. Named myself and my role"),
                ("check", "2. Asked for the pattern, not the plot (\"compared with yesterday?\")"),
                ("check", "3. Mined the everyday three (appetite, sleep, mood)"),
                ("check", "4. Wrote something down in view of the family"),
            ]),
            ("Observer checklist", [
                ("check", "Asked at least one comparative question"),
                ("check", "Anchored at least one untimed event (\"before or after lunch?\")"),
                ("check", "Ran a teach-back ending with \"What did I miss?\""),
                ("check", "Never said a single word that sounded like medical advice"),
                ("check", "Treated caregiver guesses as data, not verdicts"),
            ]),
            ("Bridge to the record", [
                ("prompt", "\"Where does what they just told you GO?\" — the Receiver answered:"),
                ("lines", 2),
            ]),
            ("Observer feedback (positive first, then one growth edge)", [
                ("lines", 3),
            ]),
        ],
    },
    "worksheet-rubric-builder.html": {
        "guide": "Guide 4", "doc": "04-handoff-rubric-builder.html",
        "title": "Rubric Builder Worksheet",
        "subtitle": "Draft criteria that two graders would score the same",
        "blurb": ("Work top to bottom. If a row can't be filled in at level 1, "
                  "your criterion is too vague."),
        "sections": [
            ("Scene choice", [
                ("prompt", "One scene only (shift handoff / doorway / report-off call): ______________________"),
                ("prompt", "Anchor example — a well-run version, fictional:"),
                ("lines", 2),
                ("prompt", "Counter-example — a poorly-run version, fictional:"),
                ("lines", 2),
            ]),
            ("Criteria pass — level 2 must be observable", [
                ("table", None),
                ("note", "Rules: 4–6 rows · observable verbs only · whole numbers · each row stands alone."),
            ]),
            ("Reliability check", [
                ("check", "A colleague scored a fictional handoff without knowing who wrote what"),
                ("prompt", "Their total: ______   My total: ______   Gap over 2? Circle the row we fought about."),
                ("prompt", "Level-1 language I sharpened: ______________________"),
            ]),
        ],
    },
    "worksheet-micro-lesson.html": {
        "guide": "Guide 5", "doc": "05-peer-led-micro-lessons.html",
        "title": "Micro-Lesson Prep Sheet",
        "subtitle": "Plan your 10-minute lesson with the class skeleton",
        "blurb": ("Presenters submit this 48 hours early. Asking early is the "
                  "clinical-judgment behavior we're training."),
        "sections": [
            ("Topic", [
                ("prompt", "Topic (narrow — one rule, one tool, one doorway moment): ______________________"),
                ("prompt", "The one sentence my audience must remember:"),
                ("lines", 2),
                ("prompt", "My three facts:  1) ______________   2) ______________   3) ______________"),
            ]),
            ("The skeleton", [
                ("prompt", "Hook (minute 0–1) — a question or fictional scenario:"),
                ("lines", 2),
                ("prompt", "Teach (minute 1–4) — three facts max. Which one is non-negotiable?"),
                ("lines", 2),
                ("prompt", "Show (minute 4–7) — something the class can SEE:"),
                ("lines", 2),
                ("prompt", "Try (minute 7–9) — what everyone WILL DO:"),
                ("lines", 2),
                ("prompt", "Exit check (minute 9–10) — one question, one-sentence answer:"),
                ("lines", 2),
            ]),
            ("Before submitting", [
                ("check", "Anything I'm unsure about is written down — asking early is the skill"),
                ("check", "Topic passes the 10-minute test (three facts + one demonstrable move)"),
            ]),
        ],
    },
}

CODE_SPAN = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITAL = re.compile(r"\*([^*\n]+)\*")
HEADING = re.compile(r"^(#{1,4})\s+(.*)$")
OL_ITEM = re.compile(r"^(\d+)[.)]\s+(.*)$")
UL_ITEM = re.compile(r"^[-*]\s+(.*)$")
FENCE = re.compile(r"^```(.*)$")


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text).strip("-") or "section"


def inline(text: str, content_dir: str = "") -> str:
    """Inline markdown to HTML. Escape first; then code spans, links, bold, italic."""
    text = html.escape(text, quote=True)
    saved: list[str] = []

    def stash(m: re.Match) -> str:
        saved.append(html.escape(m.group(1), quote=True))
        return f"\x00{len(saved)}\x00"

    text = CODE_SPAN.sub(stash, text)

    def linksub(m: re.Match) -> str:
        label, url = m.group(1), m.group(2)
        if not url.startswith(("#", "http://", "https://", "mailto:")):
            if url.endswith(".md"):
                url = url[:-3] + ".html"
            if content_dir and url.startswith("../site/"):
                url = "../" + url[len("../site/"):]
            elif content_dir and url.startswith("site/"):
                url = url[len("site/"):]
        return f'<a href="{url}">{label}</a>'

    text = LINK.sub(linksub, text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = ITAL.sub(r"<em>\1</em>", text)

    for n, code in enumerate(saved, 1):
        text = text.replace(f"\x00{n}\x00", f"<code>{code}</code>")
    return text


def list_items(items: list[str], content_dir: str, ordered: bool) -> str:
    tag = "ol" if ordered else "ul"
    lis = []
    for it in items:
        content = inline(it, content_dir)
        if content.startswith("[ ]"):
            content = '<span class="cb">☐</span>' + content[3:]
        lis.append(f"<li>{content}</li>")
    return f"<{tag}>" + "".join(lis) + f"</{tag}>"


def render_markdown(text: str, content_dir: str = "") -> tuple[str, list[str]]:
    """Tiny markdown-subset renderer. Returns (html body, heading ids)."""
    lines = text.splitlines()
    out: list[str] = []
    ids: list[str] = []
    i, n = 0, len(lines)
    par: list[str] = []

    def flush() -> None:
        nonlocal par
        if par:
            out.append(f"<p>{inline(' '.join(par), content_dir)}</p>")
            par = []

    while i < n:
        line = lines[i]

        fm = FENCE.match(line)
        if fm:
            flush()
            i += 1
            block: list[str] = []
            while i < n and not FENCE.match(lines[i]):
                block.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(block)) + "</code></pre>")
            continue

        hm = HEADING.match(line)
        if hm:
            flush()
            level, content = len(hm.group(1)), hm.group(2).strip()
            content = re.sub(r"\s*#+\s*$", "", content)
            sid = slugify(content)
            ids.append(sid)
            out.append(f'<h{level} id="{sid}">{inline(content, content_dir)}</h{level}>')
            i += 1
            continue

        if re.match(r"^-{3,}\s*$", line):
            flush()
            out.append("<hr>")
            i += 1
            continue

        # table: header row followed by a --- separator row
        if line.lstrip().startswith("|") and i + 1 < n:
            sep = lines[i + 1].strip()
            if sep.startswith("|") and set(sep.replace("|", "").replace(" ", "")) <= set(":-") and sep.count("-") >= 3:
                flush()
                header = [c.strip() for c in line.strip().strip("|").split("|")]
                i += 2
                rows: list[list[str]] = []
                while i < n and lines[i].lstrip().startswith("|"):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                    i += 1
                out.append('<div class="tablewrap"><table>' + "<thead><tr>" + "".join(
                    f"<th>{inline(c, content_dir)}</th>" for c in header)
                    + "</tr></thead><tbody>")
                for r in rows:
                    out.append("<tr>" + "".join(
                        f"<td>{inline(c, content_dir)}</td>" for c in r) + "</tr>")
                out.append("</tbody></table></div>")
                continue

        if line.lstrip().startswith(">"):
            flush()
            quote: list[str] = []
            while i < n and lines[i].lstrip().startswith(">"):
                quote.append(lines[i].lstrip()[1:].lstrip())
                i += 1
            out.append("<blockquote><p>" + inline(" ".join(quote), content_dir)
                       + "</p></blockquote>")
            continue

        if OL_ITEM.match(line):
            flush()
            items: list[str] = []
            while i < n and OL_ITEM.match(lines[i]):
                items.append(OL_ITEM.match(lines[i]).group(2))
                i += 1
            out.append(list_items(items, content_dir, ordered=True))
            continue

        if UL_ITEM.match(line):
            flush()
            items = []
            while i < n and UL_ITEM.match(lines[i]):
                items.append(UL_ITEM.match(lines[i]).group(1))
                i += 1
            out.append(list_items(items, content_dir, ordered=False))
            continue

        if line.strip() == "":
            flush()
            i += 1
            continue

        par.append(line.strip())
        i += 1

    flush()
    return "\n".join(out), ids


def page(title: str, subtitle: str, body: str, content_dir: str = "") -> str:
    """Full HTML page. content_dir is "../" for pages under site/worksheets/."""
    nav = "".join(
        f'<a href="{content_dir}docs/{slug}.html">{num}</a>'
        for slug, (num, _short, _b) in GUIDE_META.items()
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · The Clinical Judgment Guide</title>
<meta name="description" content="{html.escape(subtitle)}">
<link rel="stylesheet" href="{content_dir}styles.css">
</head>
<body>
<header class="sitehead no-print">
  <p class="brand"><a href="{content_dir}index.html">The Clinical Judgment Guide</a></p>
  <p class="sub">{SUBTITLE}</p>
  <nav class="guidenav">{nav}
  <a href="{content_dir}worksheets/index.html">Worksheets</a></nav>
</header>
<main class="wrap">
<article>
{body}
</article>
<footer class="foot">
  <p>Education only · never medical advice · zero patient data — every example is fictional.</p>
  <p class="tiny">MIT licensed · Copyright (c) 2026 Asdale Dynamics, LLC ·
  <a href="https://dylanasdale.github.io">Asdale Dynamics, LLC</a></p>
</footer>
</main>
</body>
</html>
"""


def build() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "docs").mkdir(parents=True)
    (SITE / "worksheets").mkdir(parents=True)

    # Guide pages
    for slug, (_num, short, _blurb) in GUIDE_META.items():
        raw = (DOCS / f"{slug}.md").read_text()
        body, _ids = render_markdown(raw, content_dir="site/docs")
        pm = re.search(r"<h1[^>]*>.*?</h1>", body)
        if pm:
            body = body.replace(pm.group(0), "", 1)
        back = '<p class="backlink"><a href="../index.html">← All guides &amp; worksheets</a></p>'
        (SITE / "docs" / f"{slug}.html").write_text(
            page(short, SUBTITLE, back + body, content_dir="../"))

    # Worksheets
    for fname, ws in WORKSHEETS.items():
        (SITE / "worksheets" / fname).write_text(worksheet_html(ws))
    (SITE / "worksheets" / "index.html").write_text(worksheet_index())

    # Stylesheet
    (SITE / "styles.css").write_text(STYLES_CSS)

    # Index
    cards = []
    for slug, (num, short, blurb) in GUIDE_META.items():
        cards.append(f"""  <section class="card">
    <p class="kicker">{num}</p>
    <h2><a href="docs/{slug}.html">{html.escape(short)}</a></h2>
    <p>{blurb}</p>
    <p class="wslink"><a href="worksheets/{WORKSHEET_FOR[slug]}">Print the worksheet →</a>
      <a class="doclink" href="docs/{slug}.html">Read the guide →</a></p>
  </section>""")

    body = f"""<section class="hero">
  <h1>The Clinical Judgment Guide</h1>
  <p class="tag">{SUBTITLE}</p>
  <p class="tag2">{TAGLINE}</p>
  <div class="pillrow"><span class="pill">Education only</span><span class="pill">Never medical advice</span><span class="pill">Zero patient data</span><span class="pill">Free forever · MIT</span></div>
</section>
<section class="start">
  <h2>Start here: wrong answers are data</h2>
  <p>A student who picked the wrong answer did you a favor — they showed you exactly
  where their thinking broke, before a real patient paid for it. The five guides below
  give you scripts, question ladders, rubrics, and peer-teaching formats built on one
  idea: <strong>critique decisions, never people.</strong></p>
</section>
<div class="grid">
{chr(10).join(cards)}
</div>
<section class="about">
  <h2>About</h2>
  <p>Made by <a href="https://dylanasdale.github.io">Asdale Dynamics, LLC</a> —
  Dylan Asdale's shop for beginner-friendly AI education, books and guides, and open
  tools. This manual is the human-first companion to the AI-focused
  <em>ai-for-nurse-educators-guide</em>.</p>
  <p class="tiny">MIT licensed · Copyright (c) 2026 Asdale Dynamics, LLC ·
  No JavaScript frameworks, no cookies, no tracking. Print the worksheets as many
  times as you like.</p>
</section>"""

    (SITE / "index.html").write_text(page("The Clinical Judgment Guide", SUBTITLE, body))

    print(f"Built {SITE}")
    print(f"  {len(GUIDE_META)} guide pages, {len(WORKSHEETS)} worksheets + worksheet index")


def worksheet_html(ws: dict) -> str:
    blocks: list[str] = []
    for sec_title, items in ws["sections"]:
        rows: list[str] = []
        for item in items:
            assert isinstance(item, tuple), f"bad worksheet item {item!r}"
            kind, payload = item
            if kind == "check" and payload is not None:
                rows.append(f'<p class="cbitem"><span class="cb">☐</span> {html.escape(payload)}</p>')
            elif kind == "note":
                rows.append(f'<p class="note">{html.escape(payload)}</p>')
            elif kind == "table":
                rows.append(RUBRIC_TABLE_HTML)
            elif kind == "lines":
                rows.append('<div class="writeline"></div>' * payload)
            elif kind == "prompt":
                rows.append(f'<p class="prompt">{html.escape(payload)}</p>')
            else:
                raise ValueError(f"Unknown worksheet item kind: {kind!r}")
        blocks.append(f'<section class="wblock"><h2>{html.escape(sec_title)}</h2>'
                      + "".join(rows) + "</section>")

    body = f"""<p class="backlink"><a href="index.html">← All worksheets</a></p>
<header class="wshead">
  <p class="kicker">{ws['guide']} worksheet · <a href="../docs/{ws['doc']}">read the guide</a></p>
  <h1>{html.escape(ws['title'])}</h1>
  <p class="sub">{html.escape(ws['subtitle'])}</p>
  <p class="blurb">{html.escape(ws['blurb'])}</p>
</header>
<div class="no-print printbar"><button type="button" onclick="window.print()">Print this worksheet</button></div>
{''.join(blocks)}
<section class="wblock ethics">
  <h2>Education-only reminder</h2>
  <p>This worksheet is teaching material — never medical advice, never a clinical
  protocol. <strong>Do not write real patient information here</strong>: no names,
  rooms, medical record numbers, or chart details. Fictional examples only.</p>
</section>
<footer class="foot"><p>MIT licensed · Copyright (c) 2026 Asdale Dynamics, LLC ·
<a href="https://dylanasdale.github.io">Asdale Dynamics, LLC</a></p></footer>"""
    return page(ws["title"], ws["subtitle"], f'<div class="wshead-wrap">{body}</div>',
                content_dir="../")


def worksheet_index() -> str:
    cards = []
    for fname, ws in WORKSHEETS.items():
        cards.append(f"""  <section class="card">
    <p class="kicker">{ws['guide']} worksheet</p>
    <h2><a href="{fname}">{html.escape(ws['title'])}</a></h2>
    <p>{html.escape(ws['blurb'])}</p>
    <p class="wslink"><a href="{fname}">Open &amp; print →</a>
      <a class="doclink" href="../docs/{ws['doc']}">Read the guide →</a></p>
  </section>""")
    body = f"""<section class="hero">
  <h1>Print Worksheets</h1>
  <p class="tag">Five one-page tools, ready for the printer.</p>
  <p class="tag2">Each pairs with a guide. Nothing here is ever medical advice, and
  no real patient data belongs on a printed page — every worksheet is fictional-only.</p>
</section>
<div class="grid">
{chr(10).join(cards)}
</div>"""
    return page("Worksheets · The Clinical Judgment Guide", SUBTITLE, body,
                content_dir="../")


RUBRIC_TABLE_HTML = """<table class="rtable">
<thead><tr><th>#</th><th>Criterion (observable verb + object)</th><th>0 — absent</th><th>1 — fuzzy</th><th>2 — present &amp; complete</th></tr></thead>
<tbody>
<tr><td>1</td><td><div class="writeline"></div></td><td>☐</td><td>☐</td><td>☐</td></tr>
<tr><td>2</td><td><div class="writeline"></div></td><td>☐</td><td>☐</td><td>☐</td></tr>
<tr><td>3</td><td><div class="writeline"></div></td><td>☐</td><td>☐</td><td>☐</td></tr>
<tr><td>4</td><td><div class="writeline"></div></td><td>☐</td><td>☐</td><td>☐</td></tr>
<tr><td>5</td><td><div class="writeline"></div></td><td>☐</td><td>☐</td><td>☐</td></tr>
<tr><td>6</td><td><div class="writeline"></div></td><td>☐</td><td>☐</td><td>☐</td></tr>
</tbody></table>"""

STYLES_CSS = """:root {
  --bg: #faf6f0;
  --panel: #ffffff;
  --ink: #2c2620;
  --muted: #6b6259;
  --accent: #0f766e;
  --accent-ink: #0b514c;
  --warm: #c2410c;
  --line: #e5ddd2;
  --bad: #b91c1c;
}
* { box-sizing: border-box; }
html { font-size: 16px; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Georgia, "Iowan Old Style", "Times New Roman", serif;
  line-height: 1.65;
}
.wrap { max-width: 46rem; margin: 0 auto; padding: 2rem 1.25rem 3rem; }
a { color: var(--accent-ink); }
a:hover { color: var(--accent); }

/* header */
.sitehead { border-bottom: 3px solid var(--accent); background: var(--panel); padding: 1.25rem; }
.brand { margin: 0; font-size: 1.15rem; font-weight: bold; }
.brand a { color: var(--ink); text-decoration: none; }
.sub { margin: 0.15rem 0 0.75rem; color: var(--muted); font-size: 0.95rem; font-style: italic; }
.guidenav { display: flex; flex-wrap: wrap; gap: 0.35rem 1.1rem; font-size: 0.9rem; }
.guidenav a { text-decoration: none; color: var(--accent-ink); }

/* index */
.hero { padding: 1.5rem 0 0.5rem; }
.hero h1 { font-size: 2.2rem; margin: 0 0 0.4rem; line-height: 1.15; }
.tag { margin: 0; font-size: 1.15rem; color: var(--muted); font-style: italic; }
.tag2 { margin: 0.75rem 0 1rem; }
.pillrow { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.5rem 0 1rem; }
.pill { display: inline-block; background: var(--accent); color: #fff; border-radius: 999px;
  padding: 0.15rem 0.8rem; font-size: 0.8rem; font-weight: bold; letter-spacing: 0.02em; }
.start, .about { background: var(--panel); border: 1px solid var(--line);
  border-radius: 10px; padding: 1rem 1.25rem; margin: 1.5rem 0; }
.start p, .about p { margin: 0.5rem 0; }
.grid { display: grid; grid-template-columns: 1fr; gap: 1rem; margin: 1.5rem 0; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 1rem 1.25rem 0.75rem; }
.card h2 { margin: 0.1rem 0 0.4rem; font-size: 1.25rem; }
.card h2 a { text-decoration: none; color: var(--ink); }
.card h2 a:hover { color: var(--accent); }
.kicker { margin: 0; color: var(--warm); font-size: 0.8rem; font-weight: bold;
  text-transform: uppercase; letter-spacing: 0.08em; }
.fonttag { font-style: italic; }
.wslink { font-size: 0.92rem; margin: 0.5rem 0 0; }
.wslink .doclink { margin-left: 0.75rem; }

/* guide article */
article { background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 0.75rem 1.75rem 2rem; margin-top: 1rem; }
body.worksheet article { border: none; background: #fff; padding: 0; }
article h1 { font-size: 1.8rem; line-height: 1.2; margin: 0.5rem 0 0.4rem; }
article h2 { margin-top: 2.25rem; padding-top: 0.4rem; border-top: 2px solid var(--line); }
article h3 { margin-top: 1.75rem; }
article h4 { margin-top: 1.5rem; }
article blockquote { margin: 1rem 0; padding: 0.6rem 1.1rem; border-left: 4px solid var(--accent);
  background: #f0faf8; border-radius: 0 8px 8px 0; font-style: italic; }
table { border-collapse: collapse; width: 100%; font-size: 0.93rem; margin: 1rem 0; }
.tablewrap { overflow-x: auto; }
th, td { border: 1px solid var(--line); padding: 0.45rem 0.6rem; vertical-align: top; text-align: left; }
th { background: #f3ede4; font-size: 0.85rem; }
tr:nth-child(even) td { background: #fbf8f3; }
pre { background: #2c2620; color: #f5efe6; padding: 1rem; border-radius: 8px;
  overflow-x: auto; font-size: 0.88rem; line-height: 1.5; }
code { background: #efe8dd; border-radius: 4px; padding: 0.08rem 0.3rem; font-size: 0.9em; }
pre code { background: none; padding: 0; }
.cb { color: var(--accent-ink); font-weight: bold; margin-right: 0.25rem; }
.backlink { margin-top: 0.5rem; font-size: 0.92rem; }

.foot { margin-top: 2.5rem; padding-top: 1rem; border-top: 2px solid var(--line);
  color: var(--muted); font-size: 0.9rem; }
.tiny { font-size: 0.82rem; color: var(--muted); }

/* worksheets */
body.worksheet { background: #fff; }
.wshead { border-bottom: 3px solid var(--accent); padding: 0.25rem 0 0.8rem; margin-bottom: 1rem; }
.wshead h1 { margin: 0.2rem 0 0.3rem; font-size: 1.7rem; }
.wshead .blurb { color: var(--muted); font-size: 0.95rem; margin: 0.4rem 0 0; }
.wblock { margin: 1.25rem 0; }
.wblock h2 { font-size: 1.05rem; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--accent-ink); border-bottom: 1px solid var(--line); padding-bottom: 0.3rem; }
.prompt { margin: 0.8rem 0 0.15rem; }
.writeline { border-bottom: 1.5px solid var(--ink); height: 1.9rem; }
.cbitem { margin: 0.45rem 0; }
.note { color: var(--muted); font-size: 0.88rem; font-style: italic; }
.rtable { font-size: 0.85rem; }
.rtable th, .rtable td { text-align: center; }
.rtable td:nth-child(2), .rtable th:nth-child(2) { text-align: left; }
.rtable .writeline { border-bottom: 1px solid var(--ink); height: 1.6rem; }
.ethics { border: 2px solid var(--bad); border-radius: 8px; padding: 0.75rem 1rem; }
.ethics h2 { color: var(--bad); border-bottom: none; margin-top: 0; }
.printbar { margin: 0.5rem 0 1rem; }
.printbar button { font: inherit; background: var(--accent); color: #fff; border: 0;
  padding: 0.5rem 1.2rem; border-radius: 999px; cursor: pointer; }
.printbar button:hover { background: var(--accent-ink); }

/* print */
@media print {
  :root { --line: #999; }
  body { background: #fff; color: #000; font-size: 12.5pt; }
  .no-print, .printbar, .guidenav, .backlink { display: none !important; }
  .sitehead { background: #fff; }
  main.wrap { max-width: none; padding: 0; margin: 0; }
  article { border: none; padding: 0; }
  .wblock { page-break-inside: avoid; }
  .writeline { height: 2.2rem; border-color: #333; }
  a { color: #000; text-decoration: none; }
  .rtable { page-break-inside: avoid; }
  @page { margin: 1.6cm; }
}
@media (min-width: 900px) {
  .grid { grid-template-columns: 1fr 1fr; }
  .hero h1 { font-size: 2.6rem; }
}
"""


if __name__ == "__main__":
    build()
