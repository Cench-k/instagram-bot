"""
다음 뉴스 월드 섹션 크롤러.
기사 URL 목록을 가져오고, 각 기사에서 제목/본문/이미지를 추출합니다.
"""

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


@dataclass
class Article:
    url: str
    title: str = ""
    body: str = ""
    image_urls: list[str] = field(default_factory=list)


def fetch_article_urls(section_url: str = "https://news.daum.net/world", limit: int = 5) -> list[str]:
    """섹션 페이지에서 기사 URL 목록 반환."""
    res = requests.get(section_url, headers=HEADERS, timeout=10)
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


def fetch_article(url: str) -> Article:
    """개별 기사 페이지에서 제목, 본문, 이미지 URL 추출."""
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 제목
    title_tag = soup.select_one(".tit_view, h3.tit_view, h4.tit_view")
    if not title_tag:
        og = soup.select_one("meta[property='og:title']")
        title = og.get("content", "") if og else ""
    else:
        title = title_tag.get_text(strip=True)

    # 본문
    body_tag = soup.select_one("div.article_view")
    if body_tag:
        body = body_tag.get_text(separator="\n", strip=True)
    else:
        og_desc = soup.select_one("meta[property='og:description']")
        body = og_desc.get("content", "") if og_desc else ""

    # 이미지 (본문 영역 내 이미지 우선)
    image_urls = []
    if body_tag:
        for img in body_tag.select("img[src]"):
            src = img["src"]
            if src.startswith("http") and not src.endswith(".gif"):
                image_urls.append(src)

    # 본문 이미지 없으면 og:image 메타태그에서 가져오기
    if not image_urls:
        og_img = soup.select_one("meta[property='og:image']")
        if og_img and og_img.get("content"):
            image_urls.append(og_img["content"])

    return Article(url=url, title=title, body=body[:3000], image_urls=image_urls)


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
