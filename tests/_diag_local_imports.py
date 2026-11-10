"""Diagnostic: find function-local imports whose names are used outside the
branch that imports them — a latent UnboundLocalError.

Background: combat_engine.py had `from wonderland_curses import
get_shadow_skip_chance` inside the player's turn branch, then used the name in
the ally branch. Python treats any imported name as function-local, so the ally
call raised UnboundLocalError when an ally acted before the player's branch
had run. This script flags that class of bug elsewhere.

Usage:
    .venv\\Scripts\\python.exe tests/_diag_local_imports.py

Heuristic: an import nested inside a branch is "safe" for a usage only if the
usage is inside the exact same statement list as the import (or deeper in that
same list). Usages in sibling branches (elif/else), or after the enclosing
branch, are reported.
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    list(ROOT.glob("*.py"))
    + list((ROOT / "combat").rglob("*.py"))
    + list((ROOT / "gui").rglob("*.py"))
    + list((ROOT / "facilities").rglob("*.py"))
    + list((ROOT / "resources").rglob("*.py"))
)

LIST_FIELDS = ("body", "orelse", "finalbody", "handlers", "items")


def build_parents(tree):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def chain(node, parents, stop):
    """Return [(container, field, index), ...] from node up to (excluding) stop."""
    out = []
    cur = node
    while True:
        parent = parents.get(cur)
        if parent is None or parent is stop:
            break
        for field in LIST_FIELDS:
            seq = getattr(parent, field, None)
            if isinstance(seq, list) and cur in seq:
                out.append((parent, field, seq.index(cur)))
                break
        cur = parent
    return out


def dominated_by(imp_chain, use_chain):
    """True if the import is in an ancestor statement list of the usage,
    positioned before the statement that contains the usage.

    Chains run innermost→outermost; compare from the root (outermost) end.
    """
    if not imp_chain:
        return False  # caller handles top-of-function imports via line order
    rip = list(reversed(imp_chain))
    rus = list(reversed(use_chain))
    for idx, ic in enumerate(rip):
        if idx >= len(rus):
            return False
        uc = rus[idx]
        if ic[:2] != uc[:2]:
            return False
        if idx < len(rip) - 1:
            if ic[2] != uc[2]:
                return False  # intermediate levels must be the same statement
        elif ic[2] > uc[2]:
            return False      # import must come before the usage's statement
    return True


SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def iter_scope(node):
    """Yield descendants of `node` without entering nested scopes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, SCOPE_NODES):
            continue
        yield child
        yield from iter_scope(child)


def check_file(path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    parents = build_parents(tree)
    grouped = {}
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        imports = {}   # name -> [(chain, line), ...]
        for node in iter_scope(func):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                ch = chain(node, parents, func)
                for alias in node.names:
                    name = (alias.asname or alias.name).split(".")[0]
                    imports.setdefault(name, []).append((ch, node.lineno))
        if not imports:
            continue
        for node in iter_scope(func):
            if not (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
                    and node.id in imports):
                continue
            use_chain = chain(node, parents, func)
            entries = imports[node.id]
            if any(
                (not ch and line <= node.lineno)
                or (ch and dominated_by(ch, use_chain))
                for ch, line in entries
            ):
                continue
            key = (path, func.name, node.id)
            info = grouped.setdefault(key, {"imp": min(l for _, l in entries), "uses": []})
            info["uses"].append(node.lineno)
    return [
        (path, func, name, info["imp"],
         ", ".join(str(l) for l in sorted(set(info["uses"]))))
        for (path, func, name), info in grouped.items()
    ]


def main():
    total = 0
    for path in TARGETS:
        for rel, func, name, imp_line, uses in sorted(check_file(path)):
            total += 1
            print(f"{rel.relative_to(ROOT)}: {func}() — '{name}' imported at "
                  f"line {imp_line}, suspicious uses: {uses}")
    print(f"\n{total} potential issue(s) found.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
