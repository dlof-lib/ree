"""crypt {} — تشفير / فك تشفير / بصمة (hash)."""
import hashlib
import os


def _derive_key(passphrase: str, salt: bytes, length: int = 32) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 100_000, dklen=length)


def run_crypt(props: dict, ctx: dict) -> dict:
    algo = props.get("algo", "SHA-256")
    mode = props.get("mode", "hash")
    target = props.get("target")
    key = props.get("key", "")

    data = b""
    if target and os.path.exists(target):
        with open(target, "rb") as f:
            data = f.read()
    elif target:
        data = str(target).encode()

    if mode == "hash" or algo.upper() in ("SHA-256", "SHA256", "BLAKE3", "MD5", "SHA-512"):
        algo_map = {
            "SHA-256": "sha256", "SHA256": "sha256",
            "SHA-512": "sha512", "MD5": "md5", "BLAKE3": "sha3_256",
        }
        h = hashlib.new(algo_map.get(algo.upper(), "sha256"), data).hexdigest()
        return {"algo": algo, "mode": "hash", "result": h}

    # symmetric encrypt/decrypt (AES-256-GCM / ChaCha20) via `cryptography` if available
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    except ImportError:
        return {
            "algo": algo, "mode": mode,
            "result": None,
            "error": "مكتبة 'cryptography' غير مثبتة — نفّذ: pip install cryptography",
        }

    salt = b"ree-static-salt"  # في الإنتاج استخدم ملحًا عشوائيًا مخزَّنًا مع الناتج
    derived = _derive_key(str(key), salt)
    nonce = os.urandom(12)

    if "CHACHA" in algo.upper():
        aead = ChaCha20Poly1305(derived)
    else:
        aead = AESGCM(derived)

    if mode == "encrypt":
        ct = aead.encrypt(nonce, data, None)
        out_bytes = nonce + ct
        out_path = target + ".enc" if target else None
        if out_path:
            with open(out_path, "wb") as f:
                f.write(out_bytes)
        return {"algo": algo, "mode": "encrypt", "result": out_path}

    if mode == "decrypt":
        nonce_in, ct = data[:12], data[12:]
        pt = aead.decrypt(nonce_in, ct, None)
        out_path = target[:-4] if target and target.endswith(".enc") else (target + ".dec")
        with open(out_path, "wb") as f:
            f.write(pt)
        return {"algo": algo, "mode": "decrypt", "result": out_path}

    return {"algo": algo, "mode": mode, "result": None, "error": "وضع غير معروف"}
