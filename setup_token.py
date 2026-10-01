"""
처음 한 번만 실행: 액세스 토큰을 '만료 없는 페이지 토큰'으로 바꾸고 인스타 계정 ID를 찾아 줍니다.

사용법 (컴퓨터 터미널 또는 Claude Code에서):
  pip install requests
  python setup_token.py

물어보는 값 3개를 붙여 넣으면 IG_USER_ID 와 IG_ACCESS_TOKEN 이 출력됩니다.
출력된 두 값을 GitHub 저장소 Settings > Secrets 에 넣으세요. (절대 파일에 저장하거나 공유하지 마세요)
"""

import os
import requests

GRAPH = f"https://graph.facebook.com/{os.environ.get('GRAPH_VERSION', 'v24.0')}"


def get(path, **params):
    r = requests.get(f"{GRAPH}/{path}", params=params, timeout=30)
    body = r.json()
    if "error" in body:
        raise SystemExit(f"오류: {body['error'].get('message')}")
    return body


def main():
    app_id = input("Meta 앱 ID: ").strip()
    app_secret = input("Meta 앱 시크릿 코드: ").strip()
    short_token = input("Graph API 탐색기에서 받은 사용자 토큰: ").strip()

    # 1) 짧은 사용자 토큰 → 60일짜리 사용자 토큰
    long_user = get("oauth/access_token", grant_type="fb_exchange_token",
                    client_id=app_id, client_secret=app_secret,
                    fb_exchange_token=short_token)["access_token"]

    # 2) 페이지 목록 + 페이지에 연결된 인스타 계정
    pages = get("me/accounts", access_token=long_user,
                fields="name,access_token,instagram_business_account{id,username}")["data"]
    if not pages:
        raise SystemExit("관리 중인 페이스북 페이지가 없어요. 페이지를 만들고 인스타와 연결했는지 확인하세요.")

    found = False
    for p in pages:
        ig = p.get("instagram_business_account")
        print(f"\n페이지: {p['name']}")
        if not ig:
            print("  연결된 인스타 계정 없음")
            continue
        found = True
        print(f"  인스타: @{ig.get('username')}")
        print(f"  IG_USER_ID      = {ig['id']}")
        # 60일 사용자 토큰으로 받은 페이지 토큰은 만료되지 않아요
        print(f"  IG_ACCESS_TOKEN = {p['access_token']}")
    if not found:
        print("\n인스타가 연결된 페이지가 없어요. 인스타 앱 > 설정 > 계정 센터에서 페이지와 연결하세요.")


if __name__ == "__main__":
    main()
