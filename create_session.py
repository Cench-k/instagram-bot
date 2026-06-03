"""
PC에서 Instagram 로그인 후 세션을 GitHub Secret용 문자열로 출력.
python create_session.py
"""

import base64
import json
import os
from dotenv import load_dotenv
from instagrapi import Client

load_dotenv()

for i in range(1, 10):
    user = os.getenv(f"IG_ACCOUNT_{i}_USER")
    pw   = os.getenv(f"IG_ACCOUNT_{i}_PASS")
    if not user or not pw:
        break

    print(f"\n계정{i} ({user}) 로그인 중...")
    cl = Client()
    cl.login(user, pw)
    session_b64 = base64.b64encode(json.dumps(cl.get_settings()).encode()).decode()

    print(f"[OK] 로그인 성공")
    print(f"\nGitHub Secret에 추가하세요:")
    print(f"  이름: IG_ACCOUNT_{i}_SESSION")
    print(f"  값:")
    print(session_b64)
    print("-" * 60)
