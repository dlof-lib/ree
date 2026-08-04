"""تسلسل أخطاء REE — يحمل موقع الخطأ (سطر/عمود) ويطبعه بشكل احترافي مع مقتطف من الشيفرة."""


class REEError(Exception):
    """الفئة الأساسية لكل أخطاء REE (لغوية، نحوية، أو تنفيذية)."""

    def __init__(self, message: str, line: int = None, col: int = None, source: str = None):
        self.message = message
        self.line = line
        self.col = col
        self.source = source
        super().__init__(self.format())

    def format(self) -> str:
        loc = ""
        if self.line is not None:
            loc = f" (سطر {self.line}"
            if self.col is not None:
                loc += f"، عمود {self.col}"
            loc += ")"
        head = f"{self.__class__.__name__}: {self.message}{loc}"
        if self.source and self.line is not None:
            lines = self.source.splitlines()
            if 0 < self.line <= len(lines):
                snippet = lines[self.line - 1]
                pointer = " " * max((self.col or 1) - 1, 0) + "^"
                head += f"\n    {snippet}\n    {pointer}"
        return head


class LexError(REEError):
    """خطأ في مرحلة التحليل اللفظي (رموز غير معروفة، سلاسل غير مغلقة...)."""


class ParseError(REEError):
    """خطأ في مرحلة التحليل النحوي (بنية غير متوقعة)."""


class EngineError(REEError):
    """خطأ أثناء التنفيذ (متغير غير معرّف، كتلة غير مدعومة، عملية غير صالحة...)."""
