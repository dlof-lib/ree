"""img {} — توليد صور بسيطة (أيقونات/أختام) وفق وصف."""


def run_img(props: dict, ctx: dict) -> dict:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return {"result": None, "error": "مكتبة Pillow غير مثبتة — نفّذ: pip install Pillow"}

    size_str = props.get("size", "512x512")
    w, h = (int(x) for x in size_str.lower().split("x"))
    bg = props.get("bg", "#0e5265")
    glyph = props.get("glyph", "REE")
    out = props.get("out", "output.png")
    shape = props.get("shape", "rounded-square")

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if shape == "rounded-square":
        radius = int(min(w, h) * 0.18)
        draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=bg)
    else:
        draw.rectangle([0, 0, w - 1, h - 1], fill=bg)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=int(h * 0.28))
    except Exception:
        font = ImageFont.load_default()

    text = glyph.strip("{}")
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) / 2, (h - th) / 2 - bbox[1]), text, font=font, fill="white")

    img.save(out)
    return {"result": out, "size": size_str}
