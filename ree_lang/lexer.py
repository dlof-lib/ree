"""Lexer (tokenizer) للغة REE — يدعم القيم الحرفية، المعاملات، والكلمات المفتاحية،
مع تتبع دقيق للسطر والعمود لأجل رسائل خطأ احترافية."""
from dataclasses import dataclass
from typing import List

from .errors import LexError


@dataclass
class Token:
    kind: str
    value: str
    line: int
    col: int


KEYWORDS = {"true", "false", "null", "let", "if", "else", "for", "in", "define", "import"}

SYMBOLS = {
    "{": "LBRACE", "}": "RBRACE",
    "[": "LBRACKET", "]": "RBRACKET",
    "(": "LPAREN", ")": "RPAREN",
    ":": "COLON", ",": "COMMA", ".": "DOT",
}

# يجب مطابقة المعاملات المزدوجة قبل المفردة
OPERATORS = [
    ("==", "EQ"), ("!=", "NE"), ("<=", "LE"), (">=", "GE"),
    ("&&", "AND"), ("||", "OR"),
    ("+", "PLUS"), ("-", "MINUS"), ("*", "STAR"), ("/", "SLASH"), ("%", "PERCENT"),
    ("<", "LT"), (">", "GT"), ("=", "ASSIGN"), ("!", "NOT"),
]


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line = 1
    col = 1
    n = len(source)

    while i < n:
        ch = source[i]

        if ch in " \t\r":
            i += 1
            col += 1
            continue
        if ch == "\n":
            i += 1
            line += 1
            col = 1
            continue

        # تعليق سطر واحد
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            while i < n and source[i] != "\n":
                i += 1
            continue

        # تعليق متعدد الأسطر
        if ch == "/" and i + 1 < n and source[i + 1] == "*":
            start_line, start_col = line, col
            i += 2
            col += 2
            closed = False
            while i < n:
                if source[i] == "\n":
                    line += 1
                    col = 1
                    i += 1
                    continue
                if source[i] == "*" and i + 1 < n and source[i + 1] == "/":
                    i += 2
                    col += 2
                    closed = True
                    break
                i += 1
                col += 1
            if not closed:
                raise LexError("تعليق متعدد الأسطر غير مغلق", line=start_line, col=start_col, source=source)
            continue

        # سلاسل نصية (تدعم الهروب \n \t \\ \")
        if ch == '"':
            start_line, start_col = line, col
            j = i + 1
            buf = []
            while j < n and source[j] != '"':
                if source[j] == "\\" and j + 1 < n:
                    esc = source[j + 1]
                    buf.append({"n": "\n", "t": "\t", "\\": "\\", '"': '"'}.get(esc, esc))
                    j += 2
                    continue
                if source[j] == "\n":
                    raise LexError(
                        "سلسلة نصية غير مغلقة (سطر جديد داخل السلسلة)",
                        line=start_line, col=start_col, source=source,
                    )
                buf.append(source[j])
                j += 1
            if j >= n:
                raise LexError("سلسلة نصية غير مغلقة", line=start_line, col=start_col, source=source)
            tokens.append(Token("STRING", "".join(buf), start_line, start_col))
            col += (j - i) + 1
            i = j + 1
            continue

        # أعداد صحيحة، عشرية، أو مجال (range) مثل 1..5
        if ch.isdigit():
            start_col = col
            j = i
            while j < n and source[j].isdigit():
                j += 1
            if j + 1 < n and source[j] == "." and source[j + 1] == ".":
                start = source[i:j]
                k = j + 2
                m = k
                while m < n and source[m].isdigit():
                    m += 1
                end = source[k:m]
                tokens.append(Token("RANGE", f"{start}..{end}", line, start_col))
                col += (m - i)
                i = m
                continue
            if j < n and source[j] == "." and j + 1 < n and source[j + 1].isdigit():
                k = j + 1
                while k < n and source[k].isdigit():
                    k += 1
                tokens.append(Token("FLOAT", source[i:k], line, start_col))
                col += (k - i)
                i = k
                continue
            tokens.append(Token("NUMBER", source[i:j], line, start_col))
            col += (j - i)
            i = j
            continue

        # معرّفات وكلمات مفتاحية
        if ch.isalpha() or ch == "_":
            start_col = col
            j = i
            while j < n and (source[j].isalnum() or source[j] == "_"):
                j += 1
            word = source[i:j]
            kind = word.upper() if word in KEYWORDS else "IDENT"
            tokens.append(Token(kind, word, line, start_col))
            col += (j - i)
            i = j
            continue

        matched = False
        for sym, kind in OPERATORS:
            if source.startswith(sym, i):
                tokens.append(Token(kind, sym, line, col))
                i += len(sym)
                col += len(sym)
                matched = True
                break
        if matched:
            continue

        if ch in SYMBOLS:
            tokens.append(Token(SYMBOLS[ch], ch, line, col))
            i += 1
            col += 1
            continue

        raise LexError(f"رمز غير معروف '{ch}'", line=line, col=col, source=source)

    tokens.append(Token("EOF", "", line, col))
    return tokens
