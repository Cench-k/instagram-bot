"""
Pillow로 카드뉴스 이미지 합성.

레이아웃 (참조 디자인 기준):
  - 캔버스: 1080 x 1350 (인스타그램 4:5 세로)
  - 전체: 기사 이미지 풀블리드
  - 하단: 검은 박스 (위→아래 투명→불투명 그라데이션)
  - 텍스트: 따옴표 키워드 + 헤드라인 정확히 2줄 (흰색)
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CARD_W, CARD_H = 1080, 1350

FONT_PATH = os.environ.get("FONT_PATH", "C:/Windows/Fonts/NotoSansKR-VF.ttf")

PAD_X       = 56          # 좌우 여백
PAD_BOTTOM  = 160         # 하단 여백 (텍스트 위로 올림)

# 그라데이션 박스: 하단 40% 지점부터 시작
GRAD_START_RATIO = 0.60   # 전체 높이의 60% 지점부터 어두워짐
GRAD_MAX_ALPHA   = 225    # 최하단 불투명도

TAG_COLOR      = (240, 240, 240)
TAG_BG_COLOR   = (0, 0, 0, 140)   # 태그 배경 (반투명 검정)
TAG_BG_PAD     = (10, 6, 10, 6)   # 배경 패딩 (좌, 상, 우, 하)
TEXT_COLOR     = (255, 255, 255)
HL_SIZE        = 60           # 헤드라인 폰트 크기
TAG_SIZE       = 28           # 키워드 태그 폰트 크기
LINE_GAP       = 12           # 헤드라인 줄 간격 (px)


def _font(size: int, weight: int = 700) -> ImageFont.FreeTypeFont:
    """
    Noto Sans KR Variable Font 로드.
    weight: 100(Thin) ~ 900(Black). 700=Bold, 800=ExtraBold
    """
    try:
        font = ImageFont.truetype(FONT_PATH, size)
        # Variable font axis 설정 (wght)
        try:
            font.set_variation_by_axes([weight])
        except (AttributeError, Exception):
            pass
        return font
    except OSError:
        return ImageFont.load_default()


def _crop_fill(img: Image.Image, w: int, h: int) -> Image.Image:
    """중앙 크롭 후 w×h로 리사이즈."""
    sw, sh = img.size
    if sw / sh > w / h:
        nw, nh = int(sh * w / h), sh
    else:
        nw, nh = sw, int(sw * h / w)
    left, top = (sw - nw) // 2, (sh - nh) // 2
    return img.crop((left, top, left + nw, top + nh)).resize((w, h), Image.LANCZOS)



def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    """한국어 글자 단위 줄바꿈."""
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, cur = [], ""
    for ch in text:
        if dummy.textlength(cur + ch, font=font) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def _two_lines(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> tuple[str, str]:
    """
    텍스트를 정확히 2줄로 분리.
    - 자동 줄바꿈이 2줄 이상 → 앞 두 줄 사용
    - 1줄로 끝나면 무게중심(pixel 기준 중간) 지점에서 강제 분리
    """
    lines = _wrap(text, font, max_w)

    if len(lines) >= 2:
        line1 = lines[0]
        # 나머지를 두 번째 줄로 합침 (max_w 초과 시 잘라냄)
        rest = "".join(lines[1:])
        dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        while rest and dummy.textlength(rest, font=font) > max_w:
            rest = rest[:-1]
        return line1, rest

    # 1줄: 픽셀 무게중심으로 분리
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    total_w = dummy.textlength(text, font=font)
    half_w = total_w / 2
    cum = 0.0
    split = len(text) // 2
    for i, ch in enumerate(text):
        cum += dummy.textlength(ch, font=font)
        if cum >= half_w:
            split = i + 1
            break
    return text[:split], text[split:]


def _draw_gradient_box(canvas: Image.Image) -> Image.Image:
    """하단 검은 박스를 위→아래 투명→불투명 그라데이션으로 그림."""
    grad_start_y = int(CARD_H * GRAD_START_RATIO)
    overlay = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    grad_h = CARD_H - grad_start_y
    for i in range(grad_h):
        t = i / grad_h
        alpha = int(GRAD_MAX_ALPHA * (t ** 1.4))
        y = grad_start_y + i
        draw.line([(0, y), (CARD_W, y)], fill=(0, 0, 0, alpha))

    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def make_card(
    image_path: str,
    keyword: str,
    headline: str,
    output_path: str,
) -> str:
    """
    카드 1장 생성.
    keyword : 따옴표로 감쌀 소제목 (예: '사쿠라지마')
    headline: 헤드라인 — 자동으로 정확히 2줄 처리
    """
    canvas = Image.new("RGB", (CARD_W, CARD_H))

    # 1. 이미지 풀블리드
    raw = Image.open(image_path).convert("RGB")
    photo = _crop_fill(raw, CARD_W, CARD_H)
    canvas.paste(photo, (0, 0))

    # 2. 하단 그라데이션 박스
    canvas = _draw_gradient_box(canvas)

    # 3. 텍스트
    draw = ImageDraw.Draw(canvas)
    font_hl  = _font(HL_SIZE,  800)   # ExtraBold
    font_tag = _font(TAG_SIZE, 400)   # Regular

    line_h = HL_SIZE + LINE_GAP
    max_w  = CARD_W - PAD_X * 2

    line1, line2 = _two_lines(headline, font_hl, max_w)

    # 텍스트 총 높이 계산 → 하단 기준으로 배치
    total_text_h = TAG_SIZE + 16 + line_h + line_h
    text_top = CARD_H - PAD_BOTTOM - total_text_h

    # 키워드 태그 — 반투명 배경 박스 + 텍스트
    tag_text = f'"{keyword}"'
    tag_w = int(draw.textlength(tag_text, font=font_tag))
    pl, pt, pr, pb = TAG_BG_PAD
    box = [
        PAD_X - pl,
        text_top - pt,
        PAD_X + tag_w + pr,
        text_top + TAG_SIZE + pb,
    ]
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(box, radius=6, fill=TAG_BG_COLOR)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    draw.text((PAD_X, text_top), tag_text, font=font_tag, fill=TAG_COLOR)
    y = text_top + TAG_SIZE + 20

    # 헤드라인 2줄
    draw.text((PAD_X, y),           line1, font=font_hl, fill=TEXT_COLOR)
    draw.text((PAD_X, y + line_h),  line2, font=font_hl, fill=TEXT_COLOR)

    canvas.save(output_path, "PNG", optimize=True)
    return output_path


def make_cards(
    image_path: str,
    keyword: str,
    headline: str,
    output_dir: str,
) -> list[str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    card_path = str(out / "card.png")
    make_card(image_path, keyword, headline, card_path)
    print(f"  [카드] {card_path}")
    return [card_path]
