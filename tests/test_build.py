#!/usr/bin/env python3
"""Verification suite for The Clinical Judgment Guide.

Stdlib only. Runs the real build, then checks that:

  1. every expected page exists,
  2. every internal link (file links AND #anchor links) resolves,
  3. no raw markdown leaked into rendered pages,
  4. print support is real (print media block + worksheet marking),
  5. the education-only / no-patient-data framing appears everywhere it must,
  6. LICENSE + README carry the required Asdale Dynamics, LLC credit,
  7. the build is deterministic (rebuild = byte-identical),

Run:

    python3 tests/test_build.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build as build_mod  # noqa: E402

SITE = ROOT / "site"
DOCS_SLUGS = list(build_mod.GUIDE_META)
EXPECTED_FILES = [
    "index.html",
    "styles.css",
    *[f"docs/{s}.html" for s in DOCS_SLUGS],
    *[f"worksheets/{f}" for f in build_mod.WORKSHEETS],
    "worksheets/index.html",
]

COPYRIGHT_LINE = "Copyright (c) 2026 Asdale Dynamics, LLC"
link_href = re.compile(r'<a [^>]*href="([^"]+)"')


def run_build() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build.py")],
        capture_output=True, text=True, cwd=ROOT,
    )
    if result.returncode != 0:
        raise AssertionError(f"build failed:\n{result.stdout}\n{result.stderr}")


def snapshot() -> dict[str, bytes]:
    return {
        str(p.relative_to(SITE)): p.read_bytes()
        for p in sorted(SITE.rglob("*")) if p.is_file()
    }


class TestBuildArtifacts(unittest.TestCase):
    def setUp(self) -> None:
        run_build()

    def test_all_expected_files_exist(self) -> None:
        missing = [f for f in EXPECTED_FILES if not (SITE / f).is_file()]
        self.assertEqual(missing, [], f"missing site files: {missing}")

    def test_no_unexpected_files(self) -> None:
        actual = {str(p.relative_to(SITE)) for p in SITE.rglob("*") if p.is_file()}
        self.assertEqual(actual, set(EXPECTED_FILES))


class TestLinkIntegrity(unittest.TestCase):
    def setUp(self) -> None:
        run_build()

    def test_internal_links_resolve(self) -> None:
        broken: list[str] = []
        for page_path in sorted(SITE.rglob("*.html")):
            text = page_path.read_text()
            page_dir = page_path.parent
            for m in link_href.finditer(text):
                url = m.group(1)
                if url.startswith(("http://", "https://", "mailto:", "//")):
                    continue
                target, _, frag = url.partition("#")
                if target == "":
                    target_file = page_path
                else:
                    target_file = (page_dir / target).resolve()
                    if not target_file.is_file():
                        broken.append(f"{page_path.relative_to(SITE)} -> {url}")
                        continue
                if frag:
                    target_text = target_file.read_text()
                    if f'id="{frag}"' not in target_text:
                        broken.append(f"{page_path.relative_to(SITE)} -> {url} (missing fragment)")
        self.assertEqual(broken, [], "broken internal links")

    def test_no_local_src_assets_missing(self) -> None:
        # the site ships no JavaScript; stylesheet links are verified by the link test
        for page_path in SITE.rglob("*.html"):
            self.assertNotRegex(page_path.read_text(), r"<script")


class TestRenderQuality(unittest.TestCase):
    def setUp(self) -> None:
        run_build()

    RAW_MARKDOWN = (
        r"\n#{1,4} ",      # headings
        r"\n- ",           # bullets
        r"\n\d+\. ",       # ordered
        r"\]\(",           # links
        r"```",            # fences
        r"\n\*\*",
    )

    def test_no_raw_markdown_in_articles(self) -> None:
        for page_path in sorted((SITE / "docs").glob("*.html")):
            text = page_path.read_text()
            for pat in self.RAW_MARKDOWN:
                self.assertNotRegex(
                    text, pat,
                    f"raw markdown {pat!r} leaked in {page_path.name}")

    def test_escapes_angled_brackets(self) -> None:
        # if a doc ever contains angle-bracket text it must come out escaped
        for page_path in (SITE / "docs").glob("*.html"):
            body = page_path.read_text()
            self.assertNotIn("<custom-tag", body)

    def test_every_doc_page_has_heading_ids(self) -> None:
        for slug in DOCS_SLUGS:
            text = (SITE / "docs" / f"{slug}.html").read_text()
            self.assertGreaterEqual(len(re.findall(r'<h[23] id="', text)), 3,
                                    f"{slug} lost heading anchors")


class TestPrintSupport(unittest.TestCase):
    def setUp(self) -> None:
        run_build()

    def test_print_css_rules_exist(self) -> None:
        css = (SITE / "styles.css").read_text()
        self.assertIn("@media print", css)
        self.assertIn("@page", css)
        self.assertIn("page-break-inside", css)

    def test_worksheets_are_marked_fictional_only(self) -> None:
        for fname in build_mod.WORKSHEETS:
            text = (SITE / "worksheets" / fname).read_text()
            self.assertIn("never medical advice", text, fname)
            self.assertIn("Fictional examples only", text, fname)
            self.assertIn("writeline", text, fname)  # ruled writing lines exist


class TestFramingAndCredit(unittest.TestCase):
    def test_license_line_exact(self) -> None:
        lic = (ROOT / "LICENSE").read_text()
        self.assertIn(COPYRIGHT_LINE, lic)
        self.assertIn("MIT License", lic)

    def test_readme_credits_llc(self) -> None:
        readme = (ROOT / "README.md").read_text()
        self.assertIn("Asdale Dynamics, LLC", readme)
        self.assertIn("education only".lower(), readme.lower())
        self.assertIn("never medical advice", readme)

    def test_education_framing_on_site(self) -> None:
        run_build()
        for rel in ["index.html", "docs/01-debrief-scripts.html",
                    "worksheets/index.html"]:
            text = (SITE / rel).read_text()
            self.assertIn("never medical advice", text, rel)

    def test_no_patient_data_fields_in_repo(self) -> None:
        banned = ["MRN:", "SSN:", "date of birth:", "DOB:", "patient name:"]
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path.suffix != ".md":
                continue
            low = path.read_text().lower()
            for b in banned:
                self.assertNotIn(b.lower(), low, f"{path.name} contains {b!r}")


class TestDeterminism(unittest.TestCase):
    def test_rebuild_is_byte_identical(self) -> None:
        run_build()
        snap1 = snapshot()
        run_build()
        snap2 = snapshot()
        self.assertEqual(snap1, snap2)

    def test_rebuild_from_scratch(self) -> None:
        run_build()
        shutil.rmtree(SITE)
        run_build()
        missing = [f for f in EXPECTED_FILES if not (SITE / f).is_file()]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
