import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from ree_lang import run, run_file
from ree_lang.errors import EngineError

EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "examples", "example.ree")


def test_original_example_still_runs():
    ctx = run_file(EXAMPLE_PATH)
    assert ctx["ext"]["all"] == [".v1", ".v2", ".v3"]
    assert ctx["path"]["result"].endswith("config.v1")
    assert len(ctx["crypt"]["result"]) == 64  # بصمة SHA-256


def test_variables_and_arithmetic_precedence():
    ctx = run("let y = 2 + 3 * 4")
    assert ctx["y"] == 14


def test_string_concatenation_with_plus():
    ctx = run('let s = "a" + "b" + str(1)')
    assert ctx["s"] == "ab1"


def test_if_else_merges_branch_scope_outward():
    ctx = run('''
        let flag = true
        if (flag) { let mode = "on" } else { let mode = "off" }
    ''')
    assert ctx["mode"] == "on"


def test_for_loop_runs_block_per_item():
    ctx = run('''
        for lang in ["ar", "en"] {
            path { root: "locales" segments: [lang] }
        }
    ''')
    assert ctx["path"]["segments"] == ["en"]  # آخر تكرار يبقى في النطاق الخارجي


def test_define_function_call():
    ctx = run('''
        define double(n) { n * 2 }
        let z = double(21)
    ''')
    assert ctx["z"] == 42


def test_unresolved_template_ref_left_untouched_for_later_substitution():
    ctx = run('ext { base: "config" rule: sequence(".v{n}", n: 1..2) }')
    assert ctx["ext"]["all"] == [".v1", ".v2"]


def test_undefined_variable_raises_engine_error():
    with pytest.raises(EngineError):
        run("let x = undefined_var")


def test_import_merges_definitions(tmp_path):
    common = tmp_path / "common.ree"
    common.write_text('let shared = "value"', encoding="utf-8")
    main = tmp_path / "main.ree"
    main.write_text('import "common.ree"\nlet copy = shared', encoding="utf-8")
    ctx = run_file(str(main))
    assert ctx["copy"] == "value"
