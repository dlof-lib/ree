"""REE — لغة وصفية متقدمة لتوليد الامتدادات والمسارات والتشفير والضغط،
مع دعم المتغيرات، الشروط، الحلقات، الدوال المعرّفة، والاستيراد بين الملفات."""
from .engine import Interpreter, run, run_file
from .errors import EngineError, LexError, ParseError, REEError
from .parser import parse

__all__ = [
    "run", "run_file", "parse", "Interpreter",
    "REEError", "LexError", "ParseError", "EngineError",
]
__version__ = "0.2.0"
