#!/usr/bin/env python3
"""L3 verifier - requests -> httpx sync port."""

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        fail(f"syntax error: {e}")

    # No `import requests` anywhere; must have `import httpx`.
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(("import", alias.name))
        elif isinstance(node, ast.ImportFrom):
            imports.append(("from", node.module or ""))

    names = {name for _, name in imports}
    if "requests" in names:
        fail("`import requests` is still present — must be removed")
    if "httpx" not in names:
        fail("`import httpx` is missing — module must use httpx")

    # No bare `requests.` attribute access in the code (strings are ignored by
    # AST walking attribute nodes).
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "requests":
                fail(f"`requests.{node.attr}` attribute access still present")

    # Confirm httpx is actually used — at least five attribute accesses
    # against either `httpx` or a client instance that was built from httpx.
    httpx_usage = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "httpx"
    )
    # Count Client() constructor usage as an httpx usage.
    client_ctor = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "httpx"
        and node.func.attr in ("get", "post", "Client")
    )
    if httpx_usage + client_ctor < 3:
        fail(
            f"too few httpx references ({httpx_usage} attrs + {client_ctor} calls). "
            "At least the three module-level funcs (fetch_json, fetch_text, post_json) "
            "must go through httpx.get / httpx.post."
        )

    # No async anywhere.
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.AsyncWith, ast.AsyncFor, ast.Await)):
            fail("async machinery present — this port must be sync only")

    # AsyncClient must not appear.
    if re.search(r"\bAsyncClient\b", code):
        fail("AsyncClient referenced — this port must be sync only (use httpx.Client)")

    # Public function signatures preserved.
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    for required in ("fetch_json", "fetch_text", "post_json", "retry_get"):
        if required not in funcs:
            fail(f"required function `{required}` missing")

    # ApiClient class + its four methods.
    classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    if "ApiClient" not in classes:
        fail("ApiClient class missing")
    api_methods = {
        m.name
        for m in classes["ApiClient"].body
        if isinstance(m, ast.FunctionDef)
    }
    for m in ("__init__", "get", "post", "close"):
        if m not in api_methods:
            fail(f"ApiClient missing method `{m}`")

    ok(
        f"requests removed; httpx imported; {httpx_usage + client_ctor} httpx call sites; "
        "no async; signatures preserved"
    )


if __name__ == "__main__":
    main()
