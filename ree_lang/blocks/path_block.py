"""path {} — توليد وتركيب مسارات الملفات."""
import os


def run_path(props: dict, ctx: dict) -> dict:
    root = props.get("root", ".")
    segments = props.get("segments", [])
    collision = props.get("collision", "none")

    full = os.path.join(root, *[s for s in segments if s])
    full = os.path.normpath(full)

    if collision == "increment":
        base, ext = os.path.splitext(full)
        n = 1
        candidate = full
        while os.path.exists(candidate):
            candidate = f"{base}({n}){ext}"
            n += 1
        full = candidate

    return {"root": root, "segments": segments, "result": full}
