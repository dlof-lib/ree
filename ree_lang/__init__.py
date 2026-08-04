"""REE — لغة وصفية مخصصة لتوليد الامتدادات والمسارات والتشفير والضغط."""
from .engine import run, run_file
from .parser import parse

__all__ = ["run", "run_file", "parse"]
__version__ = "0.1.0"
