"""Lexer (tokenizer) for the REE descriptive language."""
from dataclasses import dataclass
from typing import List


@dataclass
class Token:
    kind: str
    value: str
    line: int


KEYWORD_SYMBOLS = {
    "{": "LBRACE", "}": "RBRACE",
    "[": "LBRACKET", "]": "RBRACKET",
    "(": "LPAREN", ")": "RPAREN",
    ":": "COLON", ",": "COMMA", ".": "DOT",
}


class LexError(Exception):
    pass


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line = 1
    n = len(source)

    while i < n:
        ch = source[i]

        # whitespace
        if ch in " \t\r":
            i += 1
            continue
        if ch == "\n":
            line += 1
            i += 1
            continue

        # comments
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            while i < n and source[i] != "\n":
                i += 1
            continue

        # strings
        if ch == '"':
            j = i + 1
            buf = []
            while j < n and source[j] != '"':
                if source[j] == "\\" and j + 1 < n:
                    buf.append(source[j + 1])
                    j += 2
                    continue
                buf.append(source[j])
                j += 1
            if j >= n:
                raise LexError(f"سلسلة نصية غير مغلقة عند السطر {line}")
            tokens.append(Token("STRING", "".join(buf), line))
            i = j + 1
            continue

        # range like 1..5 or number
        if ch.isdigit():
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
                tokens.append(Token("RANGE", f"{start}..{end}", line))
                i = m
                continue
            tokens.append(Token("NUMBER", source[i:j], line))
            i = j
            continue

        # identifiers / keywords
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (source[j].isalnum() or source[j] == "_"):
                j += 1
            tokens.append(Token("IDENT", source[i:j], line))
            i = j
            continue

        if ch in KEYWORD_SYMBOLS:
            tokens.append(Token(KEYWORD_SYMBOLS[ch], ch, line))
            i += 1
            continue

        raise LexError(f"رمز غير معروف '{ch}' عند السطر {line}")

    tokens.append(Token("EOF", "", line))
    return tokens
