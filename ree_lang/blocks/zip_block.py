"""zip {} — ضغط الموارد الناتجة."""
import gzip
import lzma
import os
import zipfile


def run_zip(props: dict, ctx: dict) -> dict:
    fmt = props.get("format", "gzip")
    level = props.get("level", 6)
    input_path = props.get("input")
    out_path = props.get("out")

    if not input_path or not os.path.exists(input_path):
        return {"format": fmt, "result": None, "error": f"ملف الإدخال غير موجود: {input_path}"}

    if not out_path:
        out_path = input_path + {"gzip": ".gz", "zip": ".zip", "brotli": ".br", "zstd": ".zst"}.get(fmt, ".gz")

    with open(input_path, "rb") as f:
        data = f.read()

    if fmt == "gzip":
        with gzip.open(out_path, "wb", compresslevel=max(1, min(level, 9))) as f:
            f.write(data)
    elif fmt == "zip":
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=max(1, min(level, 9))) as z:
            z.write(input_path, arcname=os.path.basename(input_path))
    elif fmt in ("xz", "lzma"):
        with lzma.open(out_path, "wb", preset=max(0, min(level, 9))) as f:
            f.write(data)
    elif fmt == "brotli":
        try:
            import brotli
        except ImportError:
            return {"format": fmt, "result": None, "error": "مكتبة brotli غير مثبتة"}
        with open(out_path, "wb") as f:
            f.write(brotli.compress(data, quality=max(0, min(level, 11))))
    elif fmt == "zstd":
        try:
            import zstandard as zstd
        except ImportError:
            return {"format": fmt, "result": None, "error": "مكتبة zstandard غير مثبتة"}
        cctx = zstd.ZstdCompressor(level=max(1, min(level, 22)))
        with open(out_path, "wb") as f:
            f.write(cctx.compress(data))
    else:
        return {"format": fmt, "result": None, "error": f"صيغة غير معروفة: {fmt}"}

    return {"format": fmt, "result": out_path, "size": os.path.getsize(out_path)}
