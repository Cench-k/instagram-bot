"""
다음/네이버 세계 뉴스 크롤러.
두 소스를 랜덤으로 시도해 기사 URL을 가져옵니다.
"""

import random
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

DAUM_URL  = "https://news.daum.net/world"
NAVER_URL = "https://news.naver.com/section/104"


@dataclass
class Article:
    url: str
    title: str = ""
    body: str = ""
    image_urls: list[str] = field(default_factory=list)


# ── URL 목록 수집 ──────────────────────────────────────────────

def _fetch_daum_urls(limit: int) -> list[str]:
    res = requests.get(DAUM_URL, headers=HEADERS, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    urls = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if "v.daum.net/v/" in href:
            clean = href.split("?")[0]
            if clean not in urls:
                urls.append(clean)
        if len(urls) >= limit:
            break
    return urls


def _fetch_naver_urls(limit: int) -> list[str]:
    res = requests.get(NAVER_URL, headers=HEADERS, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    urls = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if "n.news.naver.com/mnews/article/" in href or "n.news.naver.com/article/" in href:
            clean = href.split("?")[0]
            if clean not in urls:
                urls.append(clean)
        if len(urls) >= limit:
            break
    return urls


def fetch_article_urls(limit: int = 5) -> list[str]:
    """다음/네이버 세계 뉴스에서 기사 URL 반환. 두 소스 랜덤 시도."""
    fetchers = random.sample([_fetch_daum_urls, _fetch_naver_urls], 2)
    for fetch in fetchers:
        try:
            urls = fetch(limit)
            if urls:
                source = "다음" if fetch == _fetch_daum_urls else "네이버"
                print(f"  소스: {source} ({len(urls)}개)")
                return urls
        except Exception as e:
            print(f"  크롤링 실패: {e}")
    return []


# ── 개별 기사 파싱 ────────────────────────────────────────────

def _parse_daum(url: str, soup: BeautifulSoup) -> Article:
    title_tag = soup.select_one(".tit_view, h3.tit_view, h4.tit_view")
    if not title_tag:
        og = soup.select_one("meta[property='og:title']")
        title = og.get("content", "") if og else ""
    else:
        title = title_tag.get_text(strip=True)

    body_tag = soup.select_one("div.article_view")
    if body_tag:
        body = body_tag.get_text(separator="\n", strip=True)
    else:
        og_desc = soup.select_one("meta[property='og:description']")
        body = og_desc.get("content", "") if og_desc else ""

    image_urls = []
    if body_tag:
        for img in body_tag.select("img[src]"):
            src = img["src"]
            if src.startswith("http") and not src.endswith(".gif"):
                image_urls.append(src)
    if not image_urls:
        og_img = soup.select_one("meta[property='og:image']")
        if og_img and og_img.get("content"):
            image_urls.append(og_img["content"])

    return Article(url=url, title=title, body=body[:3000], image_urls=image_urls)


def _parse_naver(url: str, soup: BeautifulSoup) -> Article:
    title_tag = soup.select_one("h2#title_area span, .media_end_head_headline")
    if not title_tag:
        og = soup.select_one("meta[property='og:title']")
        title = og.get("content", "") if og else ""
    else:
        title = title_tag.get_text(strip=True)

    body_tag = soup.select_one("#dic_area, .newsct_article")
    if body_tag:
        body = body_tag.get_text(separator="\n", strip=True)
    else:
        og_desc = soup.select_one("meta[property='og:description']")
        body = og_desc.get("content", "") if og_desc else ""

    image_urls = []
    if body_tag:
        for img in body_tag.select("img[src]"):
            src = img.get("src", "")
            if src.startswith("http") and not src.endswith(".gif"):
                image_urls.append(src)
    if not image_urls:
        og_img = soup.select_one("meta[property='og:image']")
        if og_img and og_img.get("content"):
            image_urls.append(og_img["content"])

    return Article(url=url, title=title, body=body[:3000], image_urls=image_urls)


def fetch_article(url: str) -> Article:
    """개별 기사 페이지에서 제목, 본문, 이미지 URL 추출."""
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    if "naver.com" in url:
        return _parse_naver(url, soup)
    return _parse_daum(url, soup)


def download_image(url: str, save_path: str) -> bool:
    """이미지를 로컬에 저장. 성공 여부 반환."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(res.content)
        return True
    except Exception as e:
        print(f"  이미지 다운로드 실패 ({url}): {e}")
        return False
