#!/usr/bin/env python3
"""XL1 verifier - cross-file rename Order -> Purchase across 3 files."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract import extract_named_fences, fail, ok, read_stdin


EXPECTED_FILES = ["models.py", "purchase_service.py", "test_purchase_service.py"]
FORBIDDEN_TOKENS = {"Order", "Orders", "order", "orders"}


def main() -> None:
    content = read_stdin()
    files = extract_named_fences(content, EXPECTED_FILES)

    missing = [fn for fn in EXPECTED_FILES if fn not in files]
    if missing:
        fail(f"missing file fence(s): {missing}; found headings for: {list(files)}")

    # Forbidden original-file fences (the rename must drop the old names).
    stale = extract_named_fences(content, ["order_service.py", "test_order_service.py"])
    if stale:
        fail(f"output still contains original filename fence(s): {sorted(stale)}")

    # For each file, parse as Python and check no forbidden identifiers remain.
    for fn, code in files.items():
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            fail(f"{fn}: syntax error: {e}")
        hits = _find_forbidden(tree)
        if hits:
            fail(f"{fn}: still contains forbidden identifier(s) {hits!r} after rename")

    # Per-file structural assertions.
    models_tree = ast.parse(files["models.py"])
    class_names = {n.name for n in ast.walk(models_tree) if isinstance(n, ast.ClassDef)}
    if "Purchase" not in class_names:
        fail(f"models.py: no class `Purchase` defined; got classes: {sorted(class_names)}")

    svc_tree = ast.parse(files["purchase_service.py"])
    svc_funcs = {n.name for n in ast.walk(svc_tree) if isinstance(n, ast.FunctionDef)}
    required_funcs = {
        "create_purchase",
        "get_purchase",
        "list_open_purchases",
        "ship_purchase",
        "reset_purchases",
    }
    missing_funcs = required_funcs - svc_funcs
    if missing_funcs:
        fail(f"purchase_service.py: missing functions {sorted(missing_funcs)}")

    # purchase_service must import Purchase from models (not Order).
    svc_from_imports = [
        n for n in ast.walk(svc_tree) if isinstance(n, ast.ImportFrom)
    ]
    imports_purchase = any(
        (imp.module == "models")
        and any(a.name == "Purchase" for a in imp.names)
        for imp in svc_from_imports
    )
    if not imports_purchase:
        fail("purchase_service.py: does not `from models import Purchase`")

    test_tree = ast.parse(files["test_purchase_service.py"])
    test_imports = [
        imp for imp in ast.walk(test_tree) if isinstance(imp, ast.ImportFrom)
    ]
    imports_from_new_service = any(
        imp.module == "purchase_service" for imp in test_imports
    )
    if not imports_from_new_service:
        fail("test_purchase_service.py: does not import from `purchase_service`")
    imports_from_old_service = any(
        imp.module == "order_service" for imp in test_imports
    )
    if imports_from_old_service:
        fail("test_purchase_service.py: still imports from `order_service`")

    ok(
        f"3 files renamed; no forbidden identifiers; "
        f"Purchase class + {len(required_funcs)} service functions present"
    )


def _find_forbidden(tree: ast.AST) -> list[str]:
    """Return a list of forbidden tokens still present as identifiers."""
    hits: list[str] = []
    for node in ast.walk(tree):
        candidates: list[str] = []
        if isinstance(node, ast.Name):
            candidates.append(node.id)
        elif isinstance(node, ast.Attribute):
            candidates.append(node.attr)
        elif isinstance(node, ast.ClassDef):
            candidates.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            candidates.append(node.name)
        elif isinstance(node, ast.arg):
            candidates.append(node.arg)
        elif isinstance(node, ast.alias):
            candidates.append(node.name)
            if node.asname:
                candidates.append(node.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # order_service module name should not remain after rename
                if "order_service" in node.module:
                    hits.append(f"ImportFrom:{node.module}")
        for c in candidates:
            if c in FORBIDDEN_TOKENS:
                hits.append(c)
            elif any(c == tok or c.startswith(tok + "_") or c.endswith("_" + tok) for tok in FORBIDDEN_TOKENS):
                hits.append(c)
    return sorted(set(hits))


if __name__ == "__main__":
    main()
