from .ext_block import run_ext
from .path_block import run_path
from .crypt_block import run_crypt
from .zip_block import run_zip
from .img_block import run_img

HANDLERS = {
    "ext": run_ext,
    "path": run_path,
    "crypt": run_crypt,
    "zip": run_zip,
    "img": run_img,
}
