"""
피드 게시물 자동 좋아요.
python liker.py
"""

import time
import random
from uploader import ACCOUNTS, _get_client


def like_feed(account: dict, count: int = 10):
    cl = _get_client(account)
    feed = cl.get_timeline_feed()
    items = feed.get("feed_items", [])

    liked = 0
    for item in items:
        if liked >= count:
            break
        media = item.get("media_or_ad")
        if not media:
            continue
        media_id = media.get("pk") or media.get("id")
        if not media_id:
            continue
        if media.get("has_liked"):
            continue
        try:
            cl.media_like(media_id)
            liked += 1
            print(f"  [{account['name']}] 좋아요 {liked}/{count}")
            time.sleep(random.uniform(3, 7))
        except Exception as e:
            print(f"  [{account['name']}] 좋아요 실패: {e}")

    print(f"[{account['name']}] 완료 ({liked}개)")


if __name__ == "__main__":
    for account in ACCOUNTS:
        print(f"\n[{account['name']}] 좋아요 시작...")
        try:
            like_feed(account, count=10)
        except Exception as e:
            print(f"  [{account['name']}] 오류: {e}")
