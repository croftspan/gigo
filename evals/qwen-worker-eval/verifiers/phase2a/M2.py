#!/usr/bin/env python3
"""M2 verifier - add __repr__ and __eq__ to six plain classes."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract import extract_fenced, fail, ok, read_stdin


EXPECTED_CLASSES = {
    "Point": ("x", "y"),
    "Rectangle": ("width", "height", "label"),
    "Circle": ("radius",),
    "Color": ("r", "g", "b", "alpha"),
    "User": ("username", "email", "active"),
    "Employee": ("name", "department", "salary", "manager"),
}


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        fail(f"syntax error: {e}")

    # Check no `@dataclass` decorator is used anywhere.
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for dec in node.decorator_list:
                dec_name = _name_of(dec)
                if dec_name == "dataclass":
                    fail(f"class {node.name} is decorated with @dataclass — not allowed")

    classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    missing = set(EXPECTED_CLASSES) - set(classes)
    if missing:
        fail(f"missing classes: {sorted(missing)}")

    for cls_name in EXPECTED_CLASSES:
        cls = classes[cls_name]
        methods = {m.name for m in cls.body if isinstance(m, ast.FunctionDef)}
        for dunder in ("__repr__", "__eq__"):
            if dunder not in methods:
                fail(f"class {cls_name} missing method {dunder}")

    # Exec and check behaviour.
    ns: dict = {}
    runner = getattr(__builtins__, "exec", None) or __builtins__["exec"]
    try:
        runner(code, ns)
    except Exception as e:
        fail(f"exec raised: {type(e).__name__}: {e}")

    Point = ns["Point"]
    Rectangle = ns["Rectangle"]
    Circle = ns["Circle"]
    User = ns["User"]

    # repr shape check
    if repr(Point(1, 2)) != "Point(x=1, y=2)":
        fail(f"repr(Point(1, 2)) = {repr(Point(1, 2))!r}, expected \"Point(x=1, y=2)\"")
    if repr(Circle(5)) != "Circle(radius=5)":
        fail(f"repr(Circle(5)) = {repr(Circle(5))!r}, expected \"Circle(radius=5)\"")
    if repr(Rectangle(3, 4, "room")) != "Rectangle(width=3, height=4, label='room')":
        fail(
            f"repr(Rectangle(3, 4, 'room')) = {repr(Rectangle(3, 4, 'room'))!r}, "
            "expected \"Rectangle(width=3, height=4, label='room')\""
        )

    # eq: equal values, same type
    if not (Rectangle(3, 4, "room") == Rectangle(3, 4, "room")):
        fail("Rectangle(3,4,'room') == Rectangle(3,4,'room') should be True")

    # eq: equal values, different class — must NOT be equal (strict type check)
    if Rectangle(3, 4, "room") == Point(3, 4):
        fail("Rectangle(3,4,'room') == Point(3,4) should be False (strict type check required)")

    # eq: different values, same class
    if Rectangle(3, 4, "room") == Rectangle(3, 4, "other"):
        fail("Rectangle(3,4,'room') == Rectangle(3,4,'other') should be False")

    # User eq on all three fields
    if not (User("a", "b@x", True) == User("a", "b@x", True)):
        fail("User('a','b@x',True) equality failed on identical instances")
    if User("a", "b@x", True) == User("a", "b@x", False):
        fail("User differing on active should not be equal")

    ok("all 6 classes have __repr__ + __eq__ with correct shape and semantics")


def _name_of(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _name_of(node.func)
    return None


if __name__ == "__main__":
    main()
