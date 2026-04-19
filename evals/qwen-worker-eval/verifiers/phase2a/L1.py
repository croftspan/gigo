#!/usr/bin/env python3
"""L1 verifier - god-class split: ReportReader / ReportComputer / ReportFormatter / ReportGenerator facade."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract import extract_fenced, fail, ok, read_stdin


# Expected output of the ORIGINAL ReportGenerator (before the refactor) on the
# canonical payload — the refactored facade must produce identical strings.
PAYLOAD = {
    "rows": [
        {"category": "Books", "amount": 12.5, "count": 2},
        {"category": "  books ", "amount": 7.5, "count": 1},
        {"category": "music", "amount": 20.0, "count": 4},
    ]
}

EXPECTED_MD = (
    "# Report\n"
    "\n"
    "Rows: 3\n"
    "Total amount: 40.00\n"
    "Total count: 7\n"
    "\n"
    "## By category\n"
    "- books: amount=20.00 count=3\n"
    "- music: amount=20.00 count=4"
)

EXPECTED_HTML = (
    "<h1>Report</h1>\n"
    "<p>Rows: 3</p>\n"
    "<p>Total amount: 40.00</p>\n"
    "<p>Total count: 7</p>\n"
    "<h2>By category</h2>\n"
    "<ul>\n"
    "<li>books: amount=20.00 count=3</li>\n"
    "<li>music: amount=20.00 count=4</li>\n"
    "</ul>"
)


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        fail(f"syntax error: {e}")

    classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    required = {"ReportReader", "ReportComputer", "ReportFormatter", "ReportGenerator"}
    missing = required - set(classes)
    if missing:
        fail(f"missing classes: {sorted(missing)}")

    # No class inherits from any other of the four.
    for cls_name in required:
        cls = classes[cls_name]
        for base in cls.bases:
            base_id = _name_of(base)
            if base_id in required:
                fail(f"class {cls_name} inherits from {base_id} — refactor should use composition")

    # Exec and check behaviour.
    ns: dict = {}
    runner = getattr(__builtins__, "exec", None) or __builtins__["exec"]
    try:
        runner(code, ns)
    except Exception as e:
        fail(f"exec raised: {type(e).__name__}: {e}")

    RG = ns["ReportGenerator"]

    # Constructor must take no required args.
    try:
        gen = RG()
    except Exception as e:
        fail(f"ReportGenerator() raised: {type(e).__name__}: {e}")

    try:
        md = gen.generate(PAYLOAD, "markdown")
    except Exception as e:
        fail(f"generate(payload, 'markdown') raised: {type(e).__name__}: {e}")
    if md.rstrip() != EXPECTED_MD.rstrip():
        fail(f"markdown output mismatch.\n--- got ---\n{md}\n--- expected ---\n{EXPECTED_MD}")

    try:
        html = gen.generate(PAYLOAD, "html")
    except Exception as e:
        fail(f"generate(payload, 'html') raised: {type(e).__name__}: {e}")
    if html.rstrip() != EXPECTED_HTML.rstrip():
        fail(f"html output mismatch.\n--- got ---\n{html}\n--- expected ---\n{EXPECTED_HTML}")

    # Unknown fmt must raise ValueError.
    try:
        gen.generate(PAYLOAD, "xml")
        fail("generate(payload, 'xml') should have raised ValueError")
    except ValueError:
        pass
    except Exception as e:
        fail(f"generate(payload, 'xml') raised {type(e).__name__} instead of ValueError")

    ok("facade preserves markdown+html output exactly; composition OK; no inheritance")


def _name_of(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


if __name__ == "__main__":
    main()
