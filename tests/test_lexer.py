import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from ree_lang.errors import LexError
from ree_lang.lexer import tokenize


def test_tokenizes_operators_and_keywords():
    kinds = [t.kind for t in tokenize('let x = 1 + 2 * 3 == true && false')]
    assert kinds == [
        "LET", "IDENT", "ASSIGN", "NUMBER", "PLUS", "NUMBER", "STAR",
        "NUMBER", "EQ", "TRUE", "AND", "FALSE", "EOF",
    ]


def test_tokenizes_float_and_range_distinctly():
    kinds_vals = [(t.kind, t.value) for t in tokenize("1.5 1..5")]
    assert kinds_vals[0] == ("FLOAT", "1.5")
    assert kinds_vals[1] == ("RANGE", "1..5")


def test_string_escapes():
    toks = tokenize(r'"line\nend"')
    assert toks[0].value == "line\nend"


def test_unterminated_string_raises_with_location():
    with pytest.raises(LexError) as exc:
        tokenize('"oops')
    assert exc.value.line == 1


def test_unknown_symbol_raises():
    with pytest.raises(LexError):
        tokenize("meta { x: @ }")
