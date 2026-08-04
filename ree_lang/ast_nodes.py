"""عقد شجرة التركيب (AST) للغة REE — تشمل التعبيرات، العبارات، وتعريفات الكتل."""
from dataclasses import dataclass, field
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# تعبيرات (expressions) — تُقيَّم إلى قيمة
# ---------------------------------------------------------------------------
@dataclass
class FuncCall:
    name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Template:
    """سلسلة نصية قد تحتوي مراجع {ref} تُستبدل عند التنفيذ، مثل '.{variant}.ree'."""
    raw: str


@dataclass
class RangeVal:
    start: int
    end: int


@dataclass
class Var:
    name: str


@dataclass
class MemberAccess:
    obj: Any
    attr: str


@dataclass
class ListLit:
    items: List[Any] = field(default_factory=list)


@dataclass
class BinOp:
    op: str
    left: Any
    right: Any


@dataclass
class UnaryOp:
    op: str
    operand: Any


@dataclass
class NumberLit:
    value: int


@dataclass
class FloatLit:
    value: float


@dataclass
class BoolLit:
    value: bool


@dataclass
class NullLit:
    pass


# ---------------------------------------------------------------------------
# عبارات (statements) — تُنفَّذ ولا تُقيَّم بالضرورة لقيمة
# ---------------------------------------------------------------------------
@dataclass
class LetStmt:
    name: str
    value: Any
    line: int = 0


@dataclass
class IfStmt:
    condition: Any
    then_body: List[Any] = field(default_factory=list)
    else_body: List[Any] = field(default_factory=list)


@dataclass
class ForStmt:
    var: str
    iterable: Any
    body: List[Any] = field(default_factory=list)


@dataclass
class DefineStmt:
    """define name(params) { expr } — دالة مستخدم بجسم تعبير واحد."""
    name: str
    params: List[str]
    body: Any


@dataclass
class ImportStmt:
    path: Any
    line: int = 0


@dataclass
class Block:
    """كتلة وصفية مثل meta{} ext{} path{} crypt{} zip{} img{} أو كتلة مخصّصة مسجّلة."""
    role: str
    props: Dict[str, Any] = field(default_factory=dict)
    line: int = 0


@dataclass
class Program:
    body: List[Any] = field(default_factory=list)
