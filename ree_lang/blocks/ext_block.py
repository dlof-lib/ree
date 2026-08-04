"""ext {} — توليد امتدادات الملفات."""
import hashlib
import random
import string


def run_ext(props: dict, ctx: dict) -> dict:
    base = props.get("base", "")
    rule = props.get("rule")

    results = []
    if rule is None:
        out = props.get("out", "")
        results = [out] if out else [base]
    elif rule.get("kind") == "sequence":
        pattern = rule["pattern"]
        start, end = rule["n"]
        results = [pattern.replace("{n}", str(n)) for n in range(start, end + 1)]
    elif rule.get("kind") == "random":
        charset = rule.get("charset", string.ascii_lowercase + string.digits)
        length = rule.get("length", 6)
        results = ["." + "".join(random.choice(charset) for _ in range(length))]
    elif rule.get("kind") == "hash":
        algo = rule.get("algo", "sha256")
        data = (ctx.get("source_bytes") or base.encode()) if isinstance(ctx.get("source_bytes"), (bytes, type(None))) else base.encode()
        h = hashlib.new(algo.replace("-", "_"), data).hexdigest()[:8]
        results = ["." + h]
    else:
        results = [base]

    return {"base": base, "result": results[0], "all": results}
