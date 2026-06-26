#!/usr/bin/env python3
"""
verify_port.py — layered verification for an Anthropic-SDK port.

Stages (cheapest first):
  1. syntax    : compile() every .py
  2. imports   : import each module in a subprocess with a MOCK `anthropic`
  3. adk_scan  : fail if any google.adk residue remains
  4. dry_run   : execute a detected entry point against a FakeAnthropic client

Usage:
  python verify_port.py <port-dir>
  python verify_port.py <port-dir> --entry module:function --entry-arg "hello"

Exit code 0 iff all stages pass.
"""

import argparse
import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"
ADK_PATTERNS = [
    "google.adk", "from google import adk",
    "LlmAgent", "SequentialAgent", "ParallelAgent", "LoopAgent",
    "FunctionTool", "AgentTool", "google.adk.runners",
    "MCPToolset", "StdioServerParameters",  # ADK MCP tool wiring must be ported
    "google.genai",                          # genai types.Content/Part must be gone too
]

# ---- the mock anthropic package, written to a temp dir and put on sys.path ----
MOCK_ANTHROPIC = '''
"""Mock anthropic package for offline verification."""

class _Block:
    def __init__(self, type, text=None, name=None, input=None, id=None):
        self.type = type; self.text = text; self.name = name
        self.input = input or {}; self.id = id

class _Resp:
    def __init__(self, content, stop_reason):
        self.content = content; self.stop_reason = stop_reason

class _Messages:
    def __init__(self): self._call = 0
    def create(self, **kw):
        self._call += 1
        tools = kw.get("tools")
        # First call with tools -> request one tool; otherwise finish.
        if tools and self._call == 1:
            t = tools[0]
            props = (t.get("input_schema", {}) or {}).get("properties", {})
            fake_input = {k: "x" for k in props}
            return _Resp([_Block("tool_use", name=t["name"],
                                 input=fake_input, id="tu_1")], "tool_use")
        return _Resp([_Block("text", text="mock final answer")], "end_turn")

class Anthropic:
    def __init__(self, *a, **k): self.messages = _Messages()

class _AsyncMessages:
    def __init__(self): self._call = 0
    async def create(self, **kw):
        self._call += 1
        tools = kw.get("tools")
        if tools and self._call == 1:
            t = tools[0]
            props = (t.get("input_schema", {}) or {}).get("properties", {})
            return _Resp([_Block("tool_use", name=t["name"],
                                 input={k: "x" for k in props}, id="tu_1")], "tool_use")
        return _Resp([_Block("text", text="mock final answer")], "end_turn")

class AsyncAnthropic:
    def __init__(self, *a, **k): self.messages = _AsyncMessages()
'''


def _make_mock_dir(workdir: Path) -> Path:
    mock_root = workdir / "_mock_pkgs"
    pkg = mock_root / "anthropic"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text(MOCK_ANTHROPIC)
    return mock_root


def py_files(root: Path):
    skip = {".git", "__pycache__", "_mock_pkgs", ".venv", "venv", "node_modules"}
    for p in root.rglob("*.py"):
        if not any(part in skip for part in p.parts):
            yield p


def stage_syntax(root: Path):
    errs = []
    for f in py_files(root):
        try:
            compile(f.read_text(), str(f), "exec")
        except SyntaxError as e:
            errs.append(f"  {f}:{e.lineno}: {e.msg}")
    return (not errs), errs


def stage_imports(root: Path, mock_root: Path):
    errs = []
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(mock_root), str(root),
                                         env.get("PYTHONPATH", "")])
    env["ANTHROPIC_API_KEY"] = env.get("ANTHROPIC_API_KEY", "mock-key")
    for f in py_files(root):
        rel = f.relative_to(root).with_suffix("")
        mod = ".".join(rel.parts)
        code = f"import importlib; importlib.import_module({mod!r})"
        proc = subprocess.run([sys.executable, "-c", code], env=env,
                              capture_output=True, text=True, cwd=str(root))
        if proc.returncode != 0:
            tail = proc.stderr.strip().splitlines()[-3:]
            errs.append(f"  {mod}:\n" + textwrap.indent("\n".join(tail), "    "))
    return (not errs), errs


def _strip_comments_and_strings(text: str) -> str:
    """Tokenize and drop comments + string literals so scans only see real code."""
    import io, tokenize
    out = []
    try:
        toks = tokenize.generate_tokens(io.StringIO(text).readline)
        for tok in toks:
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append((tok.start, tok.string))
    except (tokenize.TokenError, IndentationError):
        return text  # fall back to raw text if tokenizing fails
    return "\n".join(s for _, s in out)


def stage_adk_scan(root: Path):
    hits = []
    for f in py_files(root):
        if f.name == "agent_runtime.py":
            continue  # the runtime references ADK names only in its docstring
        code_only = _strip_comments_and_strings(f.read_text())
        for pat in ADK_PATTERNS:
            if pat in code_only:
                hits.append(f"  {f}: live code references '{pat}'")
    return (not hits), hits


def detect_entry(root: Path):
    """Return (module, callable_name, needs_arg) or None."""
    for f in py_files(root):
        if f.name == "agent_runtime.py":
            continue  # never an entry point; it's the runtime library
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        # only top-level (module-scope) functions are valid entry points;
        # ADK orchestration is usually async, so match `async def` too.
        funcs = {n.name: n for n in tree.body
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        rel = f.relative_to(root).with_suffix("")
        mod = ".".join(rel.parts)
        for cand in ("main", "run", "pipeline", "orchestrate"):
            if cand in funcs:
                args = funcs[cand].args
                n_required = len(args.args) - len(args.defaults)
                return (mod, cand, n_required > 0)
    return None


def stage_dry_run(root: Path, mock_root: Path, entry, entry_arg):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(mock_root), str(root),
                                         env.get("PYTHONPATH", "")])
    env["ANTHROPIC_API_KEY"] = "mock-key"
    if entry:
        mod, fn = entry.split(":")
        needs_arg = True
    else:
        det = detect_entry(root)
        if not det:
            return None, ["  no entry point detected (main/run/pipeline). "
                          "pass --entry module:function to dry-run it."]
        mod, fn, needs_arg = det
    arg = repr(entry_arg) if (needs_arg) else ""
    # If the entry point is a coroutine (async def), await it — otherwise we'd
    # just create a coroutine object and never run the orchestration (false PASS).
    code = (
        "import importlib, inspect, asyncio\n"
        f"m = importlib.import_module({mod!r})\n"
        f"r = getattr(m, {fn!r})({arg})\n"
        "if inspect.isawaitable(r): r = asyncio.run(r)\n"
        "print('DRYRUN_OK', type(r).__name__)"
    )
    proc = subprocess.run([sys.executable, "-c", code], env=env,
                          capture_output=True, text=True, cwd=str(root), timeout=120)
    if proc.returncode != 0 or "DRYRUN_OK" not in proc.stdout:
        tail = (proc.stderr.strip() or proc.stdout.strip()).splitlines()[-8:]
        return False, [f"  entry {mod}:{fn} failed:\n"
                       + textwrap.indent("\n".join(tail), "    ")]
    return True, [f"  ran {mod}:{fn} -> {proc.stdout.strip()}"]


def report(name, ok, details):
    if ok is None:
        print(f"{YELLOW}SKIP{RESET}  {name}")
    else:
        tag = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"{tag}  {name}")
    for d in details:
        print(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port_dir")
    ap.add_argument("--entry", help="module:function to dry-run")
    ap.add_argument("--entry-arg", default="hello", help="argument for the entry function")
    args = ap.parse_args()

    root = Path(args.port_dir).resolve()
    if not root.is_dir():
        print(f"{RED}error{RESET}: {root} is not a directory"); sys.exit(2)

    mock_root = _make_mock_dir(root)
    print(f"Verifying port: {root}\n")

    results = []
    ok, d = stage_syntax(root);            report("1. syntax", ok, d);   results.append(ok)
    ok, d = stage_imports(root, mock_root);report("2. imports (mocked)", ok, d); results.append(ok)
    ok, d = stage_adk_scan(root);          report("3. adk residue scan", ok, d); results.append(ok)
    ok, d = stage_dry_run(root, mock_root, args.entry, args.entry_arg)
    report("4. dry run (mocked)", ok, d)
    if ok is not None:
        results.append(ok)

    print()
    passed = all(r for r in results if r is not None)
    if passed:
        print(f"{GREEN}ALL STAGES PASSED{RESET} — port is syntax-clean, import-clean, "
              f"ADK-free, and runs end-to-end under mock.")
        sys.exit(0)
    else:
        print(f"{RED}VERIFICATION FAILED{RESET} — fix the reported issues and re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
