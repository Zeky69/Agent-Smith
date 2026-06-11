import re, json

def _to_call(name: str, args: dict) -> str:
    a = ", ".join(f"{k}={v!r}" for k, v in args.items())
    return f"result = {name}({a})\nprint(result)"

def extract_code(text: str) -> tuple[str | None, str | None]:
    """-> (code, warning). code=None si rien d'exploitable."""
    m = re.search(r"```(?:python|py)?\s*\n(.*?)(?:```|$)", text, re.DOTALL)
    if m:
        code = m.group(1).strip()
        warn = None if "```" in text[m.start(1):] else \
            "code block was not closed with ``` — interpreted until end of message"
        return code, warn
    
    m = re.search(r'<invoke name="([\w.-]+)">(.*?)</invoke>', text, re.DOTALL)
    if m:
        params = dict(re.findall(
            r'<parameter name="(\w+)">(.*?)</parameter>', m.group(2), re.DOTALL))
        return _to_call(m.group(1), params), "converted XML tool call to Python"

    m = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, re.DOTALL)
    if m:
        try:
            c = json.loads(m.group(1))
            return _to_call(c["name"], c.get("arguments", {})), \
                   "converted JSON tool call to Python"
        except (json.JSONDecodeError, KeyError):
            return None, "found <tool_call> but JSON was malformed"

    m = re.search(r"Action:\s*([\w.-]+)\s*\nAction Input:\s*(\{.*?\})",
                  text, re.DOTALL)
    if m:
        try:
            return _to_call(m.group(1), json.loads(m.group(2))), \
                   "converted ReAct format to Python"
        except json.JSONDecodeError:
            return None, "found ReAct action but input JSON was malformed"

    return None, None