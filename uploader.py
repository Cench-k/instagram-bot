import os
from pathlib import Path
from dotenv import load_dotenv
from instagrapi import Client

load_dotenv()

ACCOUNTS: list[dict] = []
for i in range(1, 10):
    user = os.getenv(f"IG_ACCOUNT_{i}_USER")
    pw   = os.getenv(f"IG_ACCOUNT_{i}_PASS")
    if user and pw:
        ACCOUNTS.append({"user": user, "pass": pw, "name": f"계정{i}"})


def _get_client(account: dict) -> Client:
    cl = Client()
    cl.delay_range = [1, 3]
    session_path = Path(f"sessions/{account['user']}.json")
    session_path.parent.mkdir(exist_ok=True)

    if session_path.exists():
        try:
            cl.load_settings(session_path)
            cl.login(account["user"], account["pass"])
        except Exception:
            session_path.unlink(missing_ok=True)
            cl.login(account["user"], account["pass"])
    else:
        cl.login(account["user"], account["pass"])

    cl.dump_settings(session_path)
    return cl


def upload_to_all(card_paths: list[str], captions: dict[str, str]):
    """
    모든 계정에 업로드.
    card_paths: 로컬 이미지 경로 리스트
    captions: {"ko": "한국어 캡션", "ja": "일본어 캡션"}
    """
    if not ACCOUNTS:
        raise RuntimeError(".env에 IG_ACCOUNT_1_USER / IG_ACCOUNT_1_PASS 설정이 없습니다.")

    caption_list = [captions.get("ko", ""), captions.get("ja", "")]

    for i, account in enumerate(ACCOUNTS):
        caption = caption_list[i] if i < len(caption_list) else caption_list[-1]
        print(f"\n[{account['name']}] 업로드 시작...")
        try:
            cl = _get_client(account)
            if len(card_paths) == 1:
                cl.photo_upload(card_paths[0], caption)
            else:
                cl.album_upload(card_paths, caption)
            print(f"  [{account['name']}] 업로드 완료")
        except Exception as e:
            print(f"  [{account['name']}] 업로드 실패: {e}")
