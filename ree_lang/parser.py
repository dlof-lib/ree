"""محلل نحوي تنازلي متكرر (recursive-descent) للغة REE -> AST.
يدعم: الكتل الوصفية، المتغيرات (let)، الشروط (if/else)، الحلقات (for..in)،
الدوال المعرّفة (define)، الاستيراد (import)، والتعبيرات الحسابية/المنطقية
الكاملة بترتيب أسبقية صحيح."""
from typing import Any, List

from .ast_nodes import (
    Block, BinOp, BoolLit, DefineStmt, FloatLit, ForStmt, FuncCall, IfStmt,
    ImportStmt, LetStmt, ListLit, MemberAccess, NullLit, NumberLit, Program,
    RangeVal, Template, UnaryOp, Var,
)
from .errors import ParseError
from .lexer import Token, tokenize


class Parser:
    def __init__(self, tokens: List[Token], source: str = ""):
        self.tokens = tokens
        self.pos = 0
        self.source = source

    # ---- أدوات مساعدة ----
    def peek(self, offset: int = 0) -> Token:
        idx = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def check(self, kind: str) -> bool:
        return self.peek().kind == kind

    def expect(self, kind: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise ParseError(
                f"متوقع {kind} لكن وُجد {tok.kind} ('{tok.value}')",
                line=tok.line, col=tok.col, source=self.source,
            )
        return self.advance()

    # ---- البرنامج والعبارات ----
    def parse_program(self) -> Program:
        program = Program()
        if self.check("IDENT") and self.peek().value == "REE":
            self.advance()
            self.expect("LBRACE")
            program.body = self.parse_stmt_list("RBRACE")
            self.expect("RBRACE")
        else:
            program.body = self.parse_stmt_list("EOF")
        return program

    def parse_stmt_list(self, end_kind: str) -> List[Any]:
        stmts = []
        while not self.check(end_kind) and not self.check("EOF"):
            stmts.append(self.parse_statement())
        return stmts

    def parse_statement(self) -> Any:
        kind = self.peek().kind
        if kind == "IMPORT":
            return self.parse_import()
        if kind == "LET":
            return self.parse_let()
        if kind == "IF":
            return self.parse_if()
        if kind == "FOR":
            return self.parse_for()
        if kind == "DEFINE":
            return self.parse_define()
        if kind == "IDENT":
            return self.parse_block()
        tok = self.peek()
        raise ParseError(f"عبارة غير متوقعة: '{tok.value}'", line=tok.line, col=tok.col, source=self.source)

    def parse_import(self) -> ImportStmt:
        tok = self.advance()
        path_expr = self.parse_expr()
        return ImportStmt(path=path_expr, line=tok.line)

    def parse_let(self) -> LetStmt:
        tok = self.advance()
        name = self.expect("IDENT").value
        self.expect("ASSIGN")
        value = self.parse_expr()
        return LetStmt(name=name, value=value, line=tok.line)

    def parse_if(self) -> IfStmt:
        self.advance()
        self.expect("LPAREN")
        cond = self.parse_expr()
        self.expect("RPAREN")
        self.expect("LBRACE")
        then_body = self.parse_stmt_list("RBRACE")
        self.expect("RBRACE")
        else_body: List[Any] = []
        if self.check("ELSE"):
            self.advance()
            if self.check("IF"):
                else_body = [self.parse_if()]
            else:
                self.expect("LBRACE")
                else_body = self.parse_stmt_list("RBRACE")
                self.expect("RBRACE")
        return IfStmt(condition=cond, then_body=then_body, else_body=else_body)

    def parse_for(self) -> ForStmt:
        self.advance()
        var_name = self.expect("IDENT").value
        self.expect("IN")
        iterable = self.parse_expr()
        self.expect("LBRACE")
        body = self.parse_stmt_list("RBRACE")
        self.expect("RBRACE")
        return ForStmt(var=var_name, iterable=iterable, body=body)

    def parse_define(self) -> DefineStmt:
        self.advance()
        name = self.expect("IDENT").value
        self.expect("LPAREN")
        params = []
        while not self.check("RPAREN"):
            params.append(self.expect("IDENT").value)
            if self.check("COMMA"):
                self.advance()
        self.expect("RPAREN")
        self.expect("LBRACE")
        body = self.parse_expr()
        self.expect("RBRACE")
        return DefineStmt(name=name, params=params, body=body)

    def parse_block(self) -> Block:
        name_tok = self.expect("IDENT")
        self.expect("LBRACE")
        props = {}
        while not self.check("RBRACE"):
            key_tok = self.expect("IDENT")
            self.expect("COLON")
            value = self.parse_expr()
            props[key_tok.value] = value
            if self.check("COMMA"):
                self.advance()
        self.expect("RBRACE")
        return Block(role=name_tok.value, props=props, line=name_tok.line)

    # ---- التعبيرات (precedence climbing) ----
    def parse_expr(self) -> Any:
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.check("OR"):
            self.advance()
            left = BinOp("||", left, self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.check("AND"):
            self.advance()
            left = BinOp("&&", left, self.parse_equality())
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while self.peek().kind in ("EQ", "NE"):
            op = self.advance().value
            left = BinOp(op, left, self.parse_comparison())
        return left

    def parse_comparison(self):
        left = self.parse_term()
        while self.peek().kind in ("LT", "GT", "LE", "GE"):
            op = self.advance().value
            left = BinOp(op, left, self.parse_term())
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.peek().kind in ("PLUS", "MINUS"):
            op = self.advance().value
            left = BinOp(op, left, self.parse_factor())
        return left

    def parse_factor(self):
        left = self.parse_unary()
        while self.peek().kind in ("STAR", "SLASH", "PERCENT"):
            op = self.advance().value
            left = BinOp(op, left, self.parse_unary())
        return left

    def parse_unary(self):
        if self.peek().kind in ("NOT", "MINUS"):
            op = self.advance().value
            return UnaryOp(op, self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.check("DOT"):
                self.advance()
                attr = self.expect("IDENT").value
                expr = MemberAccess(expr, attr)
            elif self.check("LPAREN") and isinstance(expr, Var):
                self.advance()
                args, kwargs = [], {}
                while not self.check("RPAREN"):
                    if self.check("IDENT") and self.peek(1).kind == "COLON":
                        k = self.advance().value
                        self.expect("COLON")
                        kwargs[k] = self.parse_expr()
                    else:
                        args.append(self.parse_expr())
                    if self.check("COMMA"):
                        self.advance()
                self.expect("RPAREN")
                expr = FuncCall(name=expr.name, args=args, kwargs=kwargs)
            else:
                break
        return expr

    def parse_primary(self):
        tok = self.peek()

        if tok.kind == "STRING":
            self.advance()
            return Template(tok.value)
        if tok.kind == "NUMBER":
            self.advance()
            return NumberLit(int(tok.value))
        if tok.kind == "FLOAT":
            self.advance()
            return FloatLit(float(tok.value))
        if tok.kind == "TRUE":
            self.advance()
            return BoolLit(True)
        if tok.kind == "FALSE":
            self.advance()
            return BoolLit(False)
        if tok.kind == "NULL":
            self.advance()
            return NullLit()
        if tok.kind == "RANGE":
            self.advance()
            start, end = tok.value.split("..")
            return RangeVal(int(start), int(end))
        if tok.kind == "LBRACKET":
            self.advance()
            items = []
            while not self.check("RBRACKET"):
                items.append(self.parse_expr())
                if self.check("COMMA"):
                    self.advance()
            self.expect("RBRACKET")
            return ListLit(items)
        if tok.kind == "LPAREN":
            self.advance()
            expr = self.parse_expr()
            self.expect("RPAREN")
            return expr
        if tok.kind == "IDENT":
            self.advance()
            return Var(tok.value)

        raise ParseError(f"قيمة غير متوقعة '{tok.value}'", line=tok.line, col=tok.col, source=self.source)


def parse(source: str) -> Program:
    tokens = tokenize(source)
    return Parser(tokens, source=source).parse_program()
