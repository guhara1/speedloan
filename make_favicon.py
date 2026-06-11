# -*- coding: utf-8 -*-
"""스피드대출 파비콘 생성 — 골드 다이아몬드(✦) 온 네이비.

사용법:
    python3 make_favicon.py    # assets/ 에 favicon 파일 생성 후 generate.py 재빌드

생성물:
    assets/favicon.svg          벡터(최신 브라우저)
    assets/favicon.ico          16/32/48 멀티사이즈(레거시·검색엔진)
    assets/favicon-32.png       일반 PNG 파비콘
    assets/favicon-192.png      안드로이드/검색용
    assets/apple-touch-icon.png 180x180 iOS 홈 화면용
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")

NAVY = (10, 27, 51)
GOLD = (201, 169, 106)

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#0a1b33"/>
<path d="M32 9 L53 32 L32 55 L11 32 Z" fill="#c9a96a"/>
<path d="M32 23 L40.5 32 L32 41 L23.5 32 Z" fill="#0a1b33"/>
</svg>
"""


def base_image(size=512):
    """둥근 사각 네이비 배경 + 골드 다이아몬드 + 내부 네이비 다이아몬드."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = size * 12 // 64
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=NAVY)
    cx = cy = size // 2
    r_out = int(size * 0.36)
    r_in = int(size * 0.14)
    d.polygon([(cx, cy - r_out), (cx + r_out, cy), (cx, cy + r_out), (cx - r_out, cy)], fill=GOLD)
    d.polygon([(cx, cy - r_in), (cx + r_in, cy), (cx, cy + r_in), (cx - r_in, cy)], fill=NAVY)
    return img


def main():
    os.makedirs(ASSETS, exist_ok=True)
    base = base_image(512)

    def save_png(size, name):
        base.resize((size, size), Image.LANCZOS).save(os.path.join(ASSETS, name), optimize=True)

    save_png(32, "favicon-32.png")
    save_png(192, "favicon-192.png")
    save_png(180, "apple-touch-icon.png")

    # 멀티사이즈 ICO (16/32/48 — 구글 검색결과 파비콘은 48px 이상 권장)
    base.resize((48, 48), Image.LANCZOS).save(
        os.path.join(ASSETS, "favicon.ico"),
        sizes=[(16, 16), (32, 32), (48, 48)])

    with open(os.path.join(ASSETS, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(SVG)

    for name in ("favicon.svg", "favicon.ico", "favicon-32.png", "favicon-192.png", "apple-touch-icon.png"):
        path = os.path.join(ASSETS, name)
        print("저장:", name, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
