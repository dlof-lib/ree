"""Recursive-descent parser for REE -> AST."""
from typing import Any, List

from .ast_nodes import Block, FuncCall, Program, RangeVal, Template
from .lexer import Token, tokenize


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ---- helpers ----
    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise ParseError(
                f"متوقع {kind} لكن وُجد {tok.kind} ('{tok.value}') عند السطر {tok.line}"
            )
        return self.advance()

    # ---- grammar ----
    def parse_program(self) -> Program:
        program = Program()
        # optional outer wrapper: REE { ... }
        if self.peek().kind == "IDENT" and self.peek().value == "REE":
            self.advance()
            self.expect("LBRACE")
            while self.peek().kind != "RBRACE":
                program.blocks.append(self.parse_block())
            self.expect("RBRACE")
        else:
            while self.peek().kind != "EOF":
                program.blocks.append(self.parse_block())
        return program

    def parse_block(self) -> Block:
        name_tok = self.expect("IDENT")
        self.expect("LBRACE")
        props = {}
        while self.peek().kind != "RBRACE":
            key_tok = self.expect("IDENT")
            self.expect("COLON")
            value = self.parse_value()
            props[key_tok.value] = value
            if self.peek().kind == "COMMA":
                self.advance()
        self.expect("RBRACE")
        return Block(role=name_tok.value, props=props)

    def parse_value(self) -> Any:
        tok = self.peek()

        if tok.kind == "STRING":
            self.advance()
            return Template(tok.value)

        if tok.kind == "NUMBER":
            self.advance()
            return int(tok.value)

        if tok.kind == "RANGE":
            self.advance()
            start, end = tok.value.split("..")
            return RangeVal(int(start), int(end))

        if tok.kind == "LBRACKET":
            self.advance()
            items = []
            while self.peek().kind != "RBRACKET":
                items.append(self.parse_value())
                if self.peek().kind == "COMMA":
                    self.advance()
            self.expect("RBRACKET")
            return items

        if tok.kind == "IDENT":
            # could be func_call(...) or a bare identifier/dotted path value
            name = self.advance().value
            if self.peek().kind == "LPAREN":
                self.advance()
                args = []
                kwargs = {}
                while self.peek().kind != "RPAREN":
                    # kwarg? ident ':' value
                    if (
                        self.peek().kind == "IDENT"
                        and self.tokens[self.pos + 1].kind == "COLON"
                    ):
                        k = self.advance().value
                        self.expect("COLON")
                        kwargs[k] = self.parse_value()
                    else:
                        args.append(self.parse_value())
                    if self.peek().kind == "COMMA":
                        self.advance()
                self.expect("RPAREN")
                return FuncCall(name=name, args=args, kwargs=kwargs)
            # dotted path e.g. path.result
            dotted = name
            while self.peek().kind == "DOT":
                self.advance()
                dotted += "." + self.expect("IDENT").value
            return Template("{" + dotted + "}")

        raise ParseError(f"قيمة غير متوقعة '{tok.value}' عند السطر {tok.line}")


def parse(source: str) -> Program:
    tokens = tokenize(source)
    return Parser(tokens).parse_program()
