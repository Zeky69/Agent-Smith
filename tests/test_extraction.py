import pytest
from core.extraction import extract_code


# ── fenced code blocks ────────────────────────────────────────────────────────

def test_python_fence():
    code, warn = extract_code("```python\nprint('hi')\n```")
    assert code == "print('hi')"
    assert warn is None

def test_py_fence():
    code, warn = extract_code("```py\nx = 1\n```")
    assert code == "x = 1"
    assert warn is None

def test_plain_fence():
    code, warn = extract_code("```\nresult = 42\n```")
    assert code == "result = 42"
    assert warn is None

def test_fence_with_surrounding_text():
    code, warn = extract_code("Sure!\n```python\nfoo()\n```\nDone.")
    assert code == "foo()"
    assert warn is None

# ── unclosed block ────────────────────────────────────────────────────────────

def test_unclosed_block_returns_code_and_warning():
    code, warn = extract_code("```python\nprint('oops')\n")
    assert code == "print('oops')"
    assert warn is not None
    assert "not closed" in warn

# ── two blocks — first wins ───────────────────────────────────────────────────

def test_two_blocks_first_wins():
    text = "```python\nfirst()\n```\n```python\nsecond()\n```"
    code, _ = extract_code(text)
    assert code == "first()"

# ── XML invoke ────────────────────────────────────────────────────────────────

def test_xml_invoke_basic():
    text = (
        '<invoke name="run_shell">'
        '<parameter name="cmd">ls -la</parameter>'
        '</invoke>'
    )
    code, warn = extract_code(text)
    assert "run_shell" in code
    assert "cmd=" in code
    assert warn == "converted XML tool call to Python"

def test_xml_invoke_multiple_params():
    text = (
        '<invoke name="write_file">'
        '<parameter name="path">/tmp/x</parameter>'
        '<parameter name="content">hello</parameter>'
        '</invoke>'
    )
    code, warn = extract_code(text)
    assert "write_file" in code
    assert "path=" in code
    assert "content=" in code

# ── JSON tool_call ────────────────────────────────────────────────────────────

def test_json_tool_call_basic():
    text = '<tool_call>\n{"name": "add", "arguments": {"a": 1, "b": 2}}\n</tool_call>'
    code, warn = extract_code(text)
    assert "add" in code
    assert warn == "converted JSON tool call to Python"

def test_json_tool_call_no_arguments():
    text = '<tool_call>{"name": "ping"}</tool_call>'
    code, warn = extract_code(text)
    assert "ping()" in code

def test_json_tool_call_broken_json():
    text = "<tool_call>{name: broken}</tool_call>"
    code, warn = extract_code(text)
    assert code is None
    assert "malformed" in warn

def test_json_tool_call_missing_name_key():
    text = '<tool_call>{"arguments": {"x": 1}}</tool_call>'
    code, warn = extract_code(text)
    assert code is None
    assert "malformed" in warn

# ── ReAct format ──────────────────────────────────────────────────────────────

def test_react_basic():
    text = 'Action: search\nAction Input: {"query": "python"}'
    code, warn = extract_code(text)
    assert "search" in code
    assert "query=" in code
    assert warn == "converted ReAct format to Python"

def test_react_broken_json():
    text = "Action: search\nAction Input: {bad json}"
    code, warn = extract_code(text)
    assert code is None
    assert "malformed" in warn

# ── no match ──────────────────────────────────────────────────────────────────

def test_plain_text_returns_none():
    code, warn = extract_code("Just a regular sentence with no code.")
    assert code is None
    assert warn is None

def test_empty_string():
    code, warn = extract_code("")
    assert code is None
    assert warn is None
