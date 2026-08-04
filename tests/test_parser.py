import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from ree_lang.ast_nodes import BinOp, Block, ForStmt, IfStmt, LetStmt
from ree_lang.errors import ParseError
from ree_lang.parser import parse


def test_parses_block_with_props():
    program = parse('REE { path { root: "out" segments: ["a"] } }')
    assert len(program.body) == 1
    assert isinstance(program.body[0], Block)
    assert program.body[0].role == "path"


def test_parses_let_with_expression_precedence():
    program = parse("let x = 1 + 2 * 3")
    stmt = program.body[0]
    assert isinstance(stmt, LetStmt)
    assert isinstance(stmt.value, BinOp)
    assert stmt.value.op == "+"  # * يُقيَّم أولًا فيصبح جذر الشجرة +


def test_parses_if_else():
    program = parse('if (true) { let a = 1 } else { let a = 2 }')
    assert isinstance(program.body[0], IfStmt)
    assert len(program.body[0].then_body) == 1
    assert len(program.body[0].else_body) == 1


def test_parses_for_loop():
    program = parse('for x in [1, 2] { path { root: "r" segments: [] } }')
    assert isinstance(program.body[0], ForStmt)
    assert program.body[0].var == "x"


def test_missing_brace_raises_parse_error_with_location():
    with pytest.raises(ParseError) as exc:
        parse('REE { meta { name: } }')
    assert exc.value.line == 1
