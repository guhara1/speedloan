# -*- coding: utf-8 -*-
"""스피드대출 대표 썸네일(og:image, 1200x630) 생성.

사용법:
    python3 make_og.py            # assets/og-image.png 생성 후 generate.py로 재빌드 필요

폰트: Noto Sans KR(가변)을 fonts/NotoSansKR.ttf 경로에서 찾고, 없으면 시스템 폰트로 대체.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 1200, 630

NAVY = (10, 27, 51)
NAVY2 = (27, 58, 99)
GOLD = (201, 169, 106)
WHITE = (255, 255, 255)
LIGHT = (217, 210, 194)
CARD = (255, 255, 255, 26)
CARD_LINE = (255, 255, 255, 60)

FONT_CANDIDATES = [
    os.path.join(ROOT, "fonts", "NotoSansKR.ttf"),
    "/tmp/NotoSansKR.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def font(size, weight=700):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            f = ImageFont.truetype(path, size)
            try:
                f.set_variation_by_axes([weight])
            except OSError:
                pass
            return f
    raise RuntimeError("사용 가능한 한글 폰트가 없습니다.")


def main():
    img = Image.new("RGB", (W, H), NAVY)
    # 대각선 그라데이션 배경
    for y in range(H):
        t = y / H
        row = tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * t) for i in range(3))
        img.paste(Image.new("RGB", (W, 1), row), (0, y))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # 배경 장식 원
    d.ellipse((W - 320, -160, W + 160, 320), outline=(255, 255, 255, 22), width=3)
    d.ellipse((W - 260, -100, W + 100, 260), outline=(255, 255, 255, 16), width=3)
    d.ellipse((-120, H - 200, 200, H + 120), outline=(255, 255, 255, 18), width=3)

    # 오른쪽 정보 카드 3장 (대출조건 비교 느낌)
    cards = [(795, 150, 1115, 252), (825, 282, 1145, 384), (795, 414, 1115, 516)]
    f_card = font(26, 700)
    labels = ["대출 조건", "신용점수", "상환 계획"]
    for (x1, y1, x2, y2), label in zip(cards, labels):
        d.rounded_rectangle((x1, y1, x2, y2), radius=16, fill=CARD, outline=CARD_LINE, width=2)
        # 체크 동그라미
        cy = (y1 + y2) // 2
        d.ellipse((x1 + 18, cy - 19, x1 + 56, cy + 19), fill=GOLD)
        d.line((x1 + 27, cy, x1 + 34, cy + 8), fill=NAVY, width=4)
        d.line((x1 + 34, cy + 8, x1 + 48, cy - 8), fill=NAVY, width=4)
        d.text((x1 + 72, y1 + 16), label, font=f_card, fill=WHITE)
        # 내용 줄 표현
        d.rounded_rectangle((x1 + 72, y1 + 56, x2 - 80, y1 + 68), radius=6, fill=(255, 255, 255, 70))
        d.rounded_rectangle((x1 + 72, y1 + 76, x2 - 130, y1 + 86), radius=5, fill=(255, 255, 255, 45))

    # 로고: 골드 다이아몬드 + 사이트명
    cx, cy, r = 92, 102, 30
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=GOLD)
    d.polygon([(cx, cy - 12), (cx + 12, cy), (cx, cy + 12), (cx - 12, cy)], fill=NAVY)
    d.text((140, 78), "스피드대출", font=font(40, 700), fill=WHITE)

    # 헤드라인
    d.text((80, 208), "대출상품 조건과", font=font(78, 800), fill=WHITE)
    d.text((80, 308), "신용관리 정보", font=font(78, 800), fill=GOLD)
    d.text((80, 426), "쉽게 정리한 생활금융 가이드", font=font(42, 600), fill=LIGHT)

    # 하단 키워드 칩
    f_chip = font(26, 600)
    x = 80
    for word in ["대출조건", "신용점수", "상환계획", "금융안전"]:
        bbox = d.textbbox((0, 0), word, font=f_chip)
        tw = bbox[2] - bbox[0]
        d.rounded_rectangle((x, 524, x + tw + 44, 574), radius=25,
                            outline=(255, 255, 255, 90), width=2)
        d.text((x + 22, 533), word, font=f_chip, fill=LIGHT)
        x += tw + 64

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    out = os.path.join(ROOT, "assets", "og-image.png")
    img.save(out, optimize=True)
    print("저장:", out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
