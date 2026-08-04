"""سجل كتل REE — HANDLERS قابل للتوسعة عبر register_block دون تعديل هذا الملف.

مثال لإضافة كتلة مخصّصة من كود خارجي:
    from ree_lang.blocks import register_block

    @register_block("notify")
    def run_notify(props: dict, ctx: dict) -> dict:
        return {"result": f"sent: {props.get('message')}"}
"""
from typing import Callable, Dict

HANDLERS: Dict[str, Callable] = {}


def register_block(name: str):
    """مُزخرف (decorator) يسجّل معالج كتلة جديد باسم `name` في HANDLERS."""

    def decorator(func: Callable) -> Callable:
        HANDLERS[name] = func
        return func

    return decorator


from .ext_block import run_ext      # noqa: E402
from .path_block import run_path    # noqa: E402
from .crypt_block import run_crypt  # noqa: E402
from .zip_block import run_zip      # noqa: E402
from .img_block import run_img      # noqa: E402

HANDLERS.update(
    {
        "ext": run_ext,
        "path": run_path,
        "crypt": run_crypt,
        "zip": run_zip,
        "img": run_img,
    }
)
