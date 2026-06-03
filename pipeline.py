"""
메인 파이프라인.
사용법:
  python pipeline.py                   # 다음 세계 뉴스에서 자동으로 기사 가져오기
  python pipeline.py --url <기사URL>   # 특정 기사 URL 직접 지정
  python pipeline.py --no-upload       # 카드뉴스만 생성, 인스타 업로드 생략
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from crawler import fetch_article, fetch_article_urls, download_image
from summarizer import get_keyword, generate_caption
from card_maker import make_cards
from uploader import upload_to_all

OUTPUT_DIR = Path(__file__).parent / "output"


def run(article_url: str | None = None, upload: bool = True):
    # 1. 기사 URL 결정
    if article_url:
        urls = [article_url]
    else:
        print("다음 세계 뉴스에서 기사 목록 가져오는 중...")
        urls = fetch_article_urls(limit=1)
        if not urls:
            print("기사를 찾을 수 없습니다.")
            sys.exit(1)

    url = urls[0]
    print(f"\n기사 URL: {url}")

    # 2. 기사 크롤링
    print("기사 내용 크롤링 중...")
    article = fetch_article(url)
    if not article.title:
        print("제목을 가져오지 못했습니다.")
        sys.exit(1)
    print(f"제목: {article.title}")
    print(f"이미지 {len(article.image_urls)}개 발견")

    # 3. 이미지 다운로드
    if not article.image_urls:
        print("이미지가 없어 카드뉴스를 만들 수 없습니다.")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        tmp_img = f.name

    success = download_image(article.image_urls[0], tmp_img)
    if not success:
        print("이미지 다운로드 실패.")
        sys.exit(1)

    # 4. Gemini로 키워드 + 캡션 생성
    print("Gemini API로 처리 중...")
    try:
        keyword = get_keyword(article.title, article.body)
        captions = generate_caption(article.title, article.body)
        print(f"키워드: {keyword}")
        print(f"\n--- 캡션 (한국어) ---\n{captions['ko']}\n")
        print(f"--- 캡션 (일본어) ---\n{captions['ja']}\n-------------------")
    except Exception as e:
        print(f"Gemini 처리 실패: {e}")
        keyword = article.title.split()[0]
        captions = {"ko": article.title, "ja": article.title}

    # 5. 카드뉴스 이미지 생성
    slug = url.split("/")[-1][:20]
    card_dir = OUTPUT_DIR / slug
    print(f"\n카드뉴스 생성 중 → {card_dir}")
    card_paths = make_cards(
        image_path=tmp_img,
        keyword=keyword,
        headline=article.title,
        output_dir=str(card_dir),
    )
    os.unlink(tmp_img)
    print(f"카드뉴스 {len(card_paths)}장 생성 완료.")

    # 6. 인스타그램 업로드
    if not upload:
        print("\n[업로드 생략] --no-upload 옵션이 지정되었습니다.")
        print(f"생성된 파일: {card_dir}")
        return

    print("\n인스타그램 업로드 중...")
    upload_to_all(card_paths, captions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="기사 → 카드뉴스 → 인스타그램 파이프라인")
    parser.add_argument("--url", type=str, default=None, help="특정 기사 URL")
    parser.add_argument("--no-upload", action="store_true", help="인스타 업로드 생략")
    args = parser.parse_args()

    run(article_url=args.url, upload=not args.no_upload)
