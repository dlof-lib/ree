"""AST node definitions for REE."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union


@dataclass
class FuncCall:
    name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Ref:
    """A reference like {variant} or {path.result} or env vars used inline."""
    path: str  # dotted path, e.g. "variant" or "path.result"


@dataclass
class Template:
    """A string possibly containing {refs} to interpolate, e.g. '.{variant}.ree'"""
    raw: str


@dataclass
class RangeVal:
    start: int
    end: int


@dataclass
class Block:
    role: str  # meta | ext | path | crypt | zip | img
    props: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Program:
    blocks: List[Block] = field(default_factory=list)
