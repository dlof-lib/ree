"""REE Engine — يحل المراجع وينفّذ الكتل بالترتيب."""
import datetime
import os
import re

from .ast_nodes import FuncCall, RangeVal, Template
from .blocks import HANDLERS
from .parser import parse

REF_RE = re.compile(r"\{([a-zA-Z0-9_\.]+)\}")


class EngineError(Exception):
    pass


def _lookup(ctx: dict, dotted: str):
    parts = dotted.split(".")
    cur = ctx
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def _resolve_template(template: Template, ctx: dict) -> str:
    def repl(m: re.Match) -> str:
        val = _lookup(ctx, m.group(1))
        # مرجع غير معروف بعد (مثل {n} داخل sequence) يُترك كما هو ليُستبدل لاحقًا
        return m.group(0) if val is None else str(val)
    return REF_RE.sub(repl, template.raw)


def _eval_func(call: FuncCall, ctx: dict):
    if call.name == "env":
        var = _resolve_value(call.args[0], ctx) if call.args else ""
        return os.environ.get(str(var), "")
    if call.name == "date":
        fmt = _resolve_value(call.args[0], ctx) if call.args else "YYYY-MM-DD"
        py_fmt = fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
        return datetime.datetime.now().strftime(py_fmt)
    if call.name == "sequence":
        pattern = _resolve_value(call.args[0], ctx) if call.args else ""
        rng = call.kwargs.get("n")
        start, end = (rng.start, rng.end) if isinstance(rng, RangeVal) else (1, 1)
        return {"kind": "sequence", "pattern": pattern, "n": (start, end)}
    if call.name == "random":
        charset = _resolve_value(call.args[0], ctx) if len(call.args) > 0 else None
        length = _resolve_value(call.args[1], ctx) if len(call.args) > 1 else 6
        return {"kind": "random", "charset": charset, "length": int(length)}
    if call.name == "hash":
        algo = _resolve_value(call.args[0], ctx) if call.args else "sha256"
        return {"kind": "hash", "algo": algo}
    if call.name == "derive":
        passphrase = _resolve_value(call.args[0], ctx) if len(call.args) > 0 else ""
        return str(passphrase)
    raise EngineError(f"دالة غير معروفة: {call.name}")


def _resolve_value(value, ctx: dict):
    if isinstance(value, Template):
        resolved = _resolve_template(value, ctx)
        return resolved
    if isinstance(value, FuncCall):
        return _eval_func(value, ctx)
    if isinstance(value, RangeVal):
        return (value.start, value.end)
    if isinstance(value, list):
        return [_resolve_value(v, ctx) for v in value]
    return value


def run(source: str, verbose: bool = False) -> dict:
    program = parse(source)
    ctx: dict = {}

    for block in program.blocks:
        resolved_props = {k: _resolve_value(v, ctx) for k, v in block.props.items()}

        if block.role == "meta":
            ctx["meta"] = resolved_props
            continue

        handler = HANDLERS.get(block.role)
        if handler is None:
            raise EngineError(f"كتلة غير مدعومة: {block.role}")

        result = handler(resolved_props, ctx)
        ctx[block.role] = result

        if verbose:
            print(f"[{block.role}] -> {result}")

    return ctx


def run_file(path: str, verbose: bool = False) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return run(f.read(), verbose=verbose)
