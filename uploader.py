import base64
import json
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
        ACCOUNTS.append({
            "idx":  i,
            "user": user,
            "pass": pw,
            "name": f"계정{i}",
        })


def _get_client(account: dict) -> Client:
    cl = Client()
    cl.delay_range = [1, 3]

    # GitHub Actions: Secret 세션 사용 (재로그인 없음)
    session_b64 = os.getenv(f"IG_ACCOUNT_{account['idx']}_SESSION")
    if session_b64:
        padded = session_b64 + "=" * (-len(session_b64) % 4)
        cl.set_settings(json.loads(base64.b64decode(padded).decode()))
        return cl

    # 로컬: 세션 파일 또는 비밀번호 로그인
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


def upload_to_all(cards: dict[str, list[str]], captions: dict[str, str]):
    """
    모든 계정에 업로드.
    계정1 = 일본어, 계정2 = 한국어
    cards: {"ko": [경로], "ja": [경로]}
    captions: {"ko": "한국어 캡션", "ja": "일본어 캡션"}
    """
    if not ACCOUNTS:
        raise RuntimeError(".env에 IG_ACCOUNT_1_USER / IG_ACCOUNT_1_PASS 설정이 없습니다.")

    lang_order = ["ja", "ko"]  # 계정1=ja, 계정2=ko

    for i, account in enumerate(ACCOUNTS):
        lang = lang_order[i] if i < len(lang_order) else lang_order[-1]
        card_paths = cards.get(lang, cards.get("ko", []))
        caption = captions.get(lang, "")
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
