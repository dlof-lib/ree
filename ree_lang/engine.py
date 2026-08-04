"""REE Engine — مفسّر شجرة-تركيب (tree-walking interpreter).
يحل المتغيرات، الشروط، الحلقات، الدوال المعرّفة، الاستيراد، ثم ينفّذ الكتل
الوصفية (meta/ext/path/crypt/zip/img أو أي كتلة مسجّلة) بالترتيب الذي وردت به."""
import datetime
import os
import re
import uuid

from .ast_nodes import (
    Block, BinOp, BoolLit, DefineStmt, FloatLit, ForStmt, FuncCall, IfStmt,
    ImportStmt, LetStmt, ListLit, MemberAccess, NullLit, NumberLit, RangeVal,
    Template, UnaryOp, Var,
)
from .blocks import HANDLERS
from .errors import EngineError
from .parser import parse

REF_RE = re.compile(r"\{([a-zA-Z0-9_.]+)\}")

_MISSING = object()


class Environment:
    """نطاق متغيرات متسلسل — كل كتلة شرط/حلقة/دالة تفتح نطاقًا ابنًا يرث من والده."""

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.get(name)
        return _MISSING

    def set(self, name, value):
        self.vars[name] = value

    def child(self) -> "Environment":
        return Environment(parent=self)

    def flat(self) -> dict:
        """قاموس مسطّح يجمع كل النطاقات — يُستخدم لاستبدال المراجع {ref} ولتمرير ctx للكتل."""
        merged = {} if self.parent is None else self.parent.flat()
        merged.update(self.vars)
        return merged


def truthy(v) -> bool:
    if v is None:
        return False
    if isinstance(v, (list, dict, str)):
        return len(v) > 0
    return bool(v)


def _lookup(ctx: dict, dotted: str):
    parts = dotted.split(".")
    cur = ctx
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


class Interpreter:
    """مفسّر REE — يحمل جدول الدوال المعرّفة وسجل الاستيرادات عبر التنفيذ."""

    def __init__(self, base_dir: str = ".", strict: bool = False):
        self.base_dir = base_dir
        self.strict = strict
        self.functions = {}
        self.imported_files = set()
        self.source = ""

    # ---- نقطة الدخول ----
    def run(self, source: str, verbose: bool = False) -> dict:
        self.source = source
        program = parse(source)
        env = Environment()
        self.exec_stmts(program.body, env, verbose)
        return env.flat()

    # ---- تنفيذ العبارات ----
    def exec_stmts(self, stmts, env, verbose):
        for stmt in stmts:
            self.exec_stmt(stmt, env, verbose)

    def exec_stmt(self, stmt, env, verbose):
        if isinstance(stmt, ImportStmt):
            self._exec_import(stmt, env, verbose)
        elif isinstance(stmt, LetStmt):
            env.set(stmt.name, self.eval_expr(stmt.value, env))
        elif isinstance(stmt, DefineStmt):
            self.functions[stmt.name] = stmt
        elif isinstance(stmt, IfStmt):
            self._exec_if(stmt, env, verbose)
        elif isinstance(stmt, ForStmt):
            self._exec_for(stmt, env, verbose)
        elif isinstance(stmt, Block):
            self._exec_block(stmt, env, verbose)
        else:
            raise EngineError(f"عبارة غير مدعومة: {type(stmt).__name__}", source=self.source)

    def _exec_if(self, stmt: IfStmt, env, verbose):
        cond = self.eval_expr(stmt.condition, env)
        branch_env = env.child()
        if truthy(cond):
            self.exec_stmts(stmt.then_body, branch_env, verbose)
        else:
            self.exec_stmts(stmt.else_body, branch_env, verbose)
        # ما يُعرَّف داخل الفرع يُدمج في النطاق الخارجي (مفيد لتهيئة كتل لاحقة شرطيًا)
        for k, v in branch_env.vars.items():
            env.set(k, v)

    def _exec_for(self, stmt: ForStmt, env, verbose):
        iterable = self.eval_expr(stmt.iterable, env)
        items = self._iterable_items(iterable)
        loop_env = env.child()
        for item in items:
            loop_env.set(stmt.var, item)
            self.exec_stmts(stmt.body, loop_env, verbose)
        for k, v in loop_env.vars.items():
            if k != stmt.var:
                env.set(k, v)

    def _iterable_items(self, iterable):
        if isinstance(iterable, tuple) and len(iterable) == 2:
            start, end = iterable
            return list(range(start, end + 1))
        if isinstance(iterable, list):
            return iterable
        raise EngineError(f"قيمة غير قابلة للتكرار في for: {iterable!r}", source=self.source)

    def _exec_block(self, block: Block, env, verbose):
        resolved_props = {k: self.eval_expr(v, env) for k, v in block.props.items()}
        if block.role == "meta":
            env.set("meta", resolved_props)
            return
        handler = HANDLERS.get(block.role)
        if handler is None:
            raise EngineError(f"كتلة غير مدعومة: {block.role}", line=block.line, source=self.source)
        result = handler(resolved_props, env.flat())
        env.set(block.role, result)
        if verbose:
            print(f"[{block.role}] -> {result}")

    def _exec_import(self, stmt: ImportStmt, env, verbose):
        rel_path = str(self.eval_expr(stmt.path, env))
        full_path = os.path.normpath(os.path.join(self.base_dir, rel_path))
        if full_path in self.imported_files:
            return
        self.imported_files.add(full_path)
        if not os.path.exists(full_path):
            raise EngineError(f"ملف الاستيراد غير موجود: {full_path}", line=stmt.line, source=self.source)
        with open(full_path, "r", encoding="utf-8") as f:
            sub_source = f.read()
        sub_program = parse(sub_source)
        prev_source = self.source
        self.source = sub_source
        self.exec_stmts(sub_program.body, env, verbose)
        self.source = prev_source

    # ---- تقييم التعبيرات ----
    def eval_expr(self, node, env):
        if isinstance(node, (NumberLit, FloatLit, BoolLit)):
            return node.value
        if isinstance(node, NullLit):
            return None
        if isinstance(node, RangeVal):
            return (node.start, node.end)
        if isinstance(node, Template):
            return self._resolve_template(node, env)
        if isinstance(node, ListLit):
            return [self.eval_expr(i, env) for i in node.items]
        if isinstance(node, Var):
            val = env.get(node.name)
            if val is _MISSING:
                raise EngineError(f"غير معرّف: {node.name}", source=self.source)
            return val
        if isinstance(node, MemberAccess):
            obj = self.eval_expr(node.obj, env)
            if isinstance(obj, dict):
                return obj.get(node.attr)
            return getattr(obj, node.attr, None)
        if isinstance(node, BinOp):
            return self._eval_binop(node, env)
        if isinstance(node, UnaryOp):
            return self._eval_unaryop(node, env)
        if isinstance(node, FuncCall):
            return self._eval_func(node, env)
        if isinstance(node, list):
            return [self.eval_expr(v, env) for v in node]
        return node

    def _resolve_template(self, template: Template, env) -> str:
        ctx = env.flat()

        def repl(m: re.Match) -> str:
            val = _lookup(ctx, m.group(1))
            # مرجع غير معروف بعد (مثل {n} داخل sequence) يُترك كما هو ليُستبدل لاحقًا
            return m.group(0) if val is None else str(val)

        return REF_RE.sub(repl, template.raw)

    def _eval_binop(self, node: BinOp, env):
        op = node.op
        left = self.eval_expr(node.left, env)
        if op == "&&":
            return truthy(left) and truthy(self.eval_expr(node.right, env))
        if op == "||":
            return truthy(left) or truthy(self.eval_expr(node.right, env))
        right = self.eval_expr(node.right, env)
        try:
            if op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    return f"{left}{right}"
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                return left / right
            if op == "%":
                return left % right
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
        except TypeError:
            raise EngineError(
                f"عملية غير صالحة '{op}' بين {type(left).__name__} و {type(right).__name__}",
                source=self.source,
            )
        raise EngineError(f"مُعامل غير معروف: {op}", source=self.source)

    def _eval_unaryop(self, node: UnaryOp, env):
        val = self.eval_expr(node.operand, env)
        if node.op == "-":
            return -val
        if node.op == "!":
            return not truthy(val)
        raise EngineError(f"مُعامل أحادي غير معروف: {node.op}", source=self.source)

    def _eval_func(self, call: FuncCall, env):
        # دالة معرّفة عبر define
        if call.name in self.functions:
            fn: DefineStmt = self.functions[call.name]
            if len(call.args) != len(fn.params):
                raise EngineError(
                    f"عدد المعاملات غير مطابق للدالة {call.name} "
                    f"(متوقع {len(fn.params)}، تم تمرير {len(call.args)})",
                    source=self.source,
                )
            call_env = env.child()
            for pname, pexpr in zip(fn.params, call.args):
                call_env.set(pname, self.eval_expr(pexpr, env))
            return self.eval_expr(fn.body, call_env)

        name = call.name
        args = [self.eval_expr(a, env) for a in call.args]
        kwargs = {k: self.eval_expr(v, env) for k, v in call.kwargs.items()}

        if name == "env":
            return os.environ.get(str(args[0]) if args else "", "")
        if name in ("date", "now"):
            fmt = args[0] if args else "YYYY-MM-DD"
            py_fmt = (
                fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
                .replace("HH", "%H").replace("mm", "%M").replace("ss", "%S")
            )
            return datetime.datetime.now().strftime(py_fmt)
        if name == "uuid":
            return str(uuid.uuid4())
        if name == "sequence":
            pattern = args[0] if args else ""
            rng = kwargs.get("n")
            start, end = rng if isinstance(rng, tuple) else (1, 1)
            return {"kind": "sequence", "pattern": pattern, "n": (start, end)}
        if name == "random":
            charset = args[0] if len(args) > 0 else None
            length = args[1] if len(args) > 1 else kwargs.get("length", 6)
            return {"kind": "random", "charset": charset, "length": int(length)}
        if name == "hash":
            algo = args[0] if args else "sha256"
            return {"kind": "hash", "algo": algo}
        if name == "derive":
            return str(args[0]) if args else ""
        if name == "upper":
            return str(args[0]).upper() if args else ""
        if name == "lower":
            return str(args[0]).lower() if args else ""
        if name == "concat":
            return "".join(str(a) for a in args)
        if name == "length":
            return len(args[0]) if args else 0
        if name == "min":
            return min(args)
        if name == "max":
            return max(args)
        if name == "round":
            return round(args[0], int(args[1]) if len(args) > 1 else 0)
        if name == "str":
            return str(args[0]) if args else ""
        if name == "int":
            return int(args[0]) if args else 0
        raise EngineError(f"دالة غير معروفة: {name}", source=self.source)


# ---------------------------------------------------------------------------
# واجهة على مستوى الوحدة (متوافقة مع الإصدار السابق: run / run_file)
# ---------------------------------------------------------------------------
def run(source: str, verbose: bool = False, base_dir: str = ".") -> dict:
    return Interpreter(base_dir=base_dir).run(source, verbose=verbose)


def run_file(path: str, verbose: bool = False) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return run(source, verbose=verbose, base_dir=os.path.dirname(os.path.abspath(path)) or ".")
