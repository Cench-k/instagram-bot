"""
예약 업로드 스케줄러.

사용법:
  python scheduler.py

posts.json에 등록된 게시물을 scheduled_at 시간에 맞춰 자동 업로드합니다.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from uploader import upload_carousel, upload_image

POSTS_FILE = Path(__file__).parent / "posts.json"


def load_posts() -> list[dict]:
    if not POSTS_FILE.exists():
        return []
    return json.loads(POSTS_FILE.read_text(encoding="utf-8"))


def save_posts(posts: list[dict]):
    POSTS_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")


def process_post(post: dict):
    caption = post.get("caption", "")
    images = post.get("images", [])

    if len(images) == 1:
        upload_image(images[0], caption=caption)
    elif len(images) >= 2:
        upload_carousel(images, caption=caption)
    else:
        raise ValueError(f"이미지 URL이 없습니다: {post}")


def run():
    print("스케줄러 시작. Ctrl+C로 종료.")
    while True:
        posts = load_posts()
        now = datetime.now()
        updated = False

        for post in posts:
            if post.get("done"):
                continue
            scheduled = datetime.fromisoformat(post["scheduled_at"])
            if now >= scheduled:
                print(f"\n[{now:%Y-%m-%d %H:%M}] 업로드 시작: {post.get('caption', '')[:30]}")
                try:
                    process_post(post)
                    post["done"] = True
                    updated = True
                except Exception as e:
                    print(f"  오류: {e}")
                    post["error"] = str(e)
                    updated = True

        if updated:
            save_posts(posts)

        time.sleep(30)  # 30초마다 확인


if __name__ == "__main__":
    run()
