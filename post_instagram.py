"""
boyel* 인스타그램 자동 게시 스크립트

posts.json 에서 게시 시간이 지났고 아직 안 올라간 게시물을 찾아
Instagram Graph API(공식)로 올린 뒤, posts.json 에 결과를 기록합니다.

필요한 환경변수
  IG_USER_ID       인스타 비즈니스 계정 ID (숫자)
  IG_ACCESS_TOKEN  페이지 액세스 토큰 (setup_token.py 로 발급)
  IMAGE_BASE_URL   (선택) 이미지 주소의 앞부분. 비우면 GitHub 저장소 주소로 자동 생성
  GRAPH_VERSION    (선택) Graph API 버전. 기본 v24.0
  DRY_RUN          (선택) 1 이면 실제로 올리지 않고 무엇을 올릴지만 출력
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

POSTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posts.json")
GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v24.0")
GRAPH = f"https://graph.facebook.com/{GRAPH_VERSION}"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


def image_base_url() -> str:
    base = os.environ.get("IMAGE_BASE_URL", "").strip()
    if base:
        return base.rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY")  # 예: myname/boyel-insta (GitHub Actions 가 자동으로 넣어 줌)
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if not repo:
        sys.exit("이미지 주소를 만들 수 없어요. IMAGE_BASE_URL 을 넣거나 GitHub Actions 에서 실행하세요.")
    return f"https://raw.githubusercontent.com/{repo}/{branch}"


def api(method: str, path: str, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    r = requests.request(method, f"{GRAPH}/{path}", data=params if method == "POST" else None,
                         params=params if method == "GET" else None, timeout=60)
    body = r.json()
    if r.status_code != 200 or "error" in body:
        raise RuntimeError(f"Graph API 오류 ({path}): {body.get('error', body)}")
    return body


def wait_until_ready(container_id: str, tries: int = 20):
    for _ in range(tries):
        status = api("GET", container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"인스타가 이미지를 처리하지 못했어요 (컨테이너 {container_id}). JPG인지, 4:5~1.91:1 비율인지 확인하세요.")
        time.sleep(5)
    raise RuntimeError("이미지 처리 시간이 너무 오래 걸려요. 다음 실행 때 다시 시도합니다.")


def publish(post: dict, base: str) -> str:
    ig = os.environ["IG_USER_ID"]
    images = post.get("images") or [post["image"]]
    urls = [f"{base}/{p.lstrip('/')}" for p in images]

    if len(urls) == 1:
        container = api("POST", f"{ig}/media", image_url=urls[0], caption=post["caption"])["id"]
    else:  # 캐러셀 (2~10장)
        children = []
        for u in urls:
            child = api("POST", f"{ig}/media", image_url=u, is_carousel_item="true")["id"]
            wait_until_ready(child)
            children.append(child)
        container = api("POST", f"{ig}/media", media_type="CAROUSEL",
                        children=",".join(children), caption=post["caption"])["id"]

    wait_until_ready(container)
    return api("POST", f"{ig}/media_publish", creation_id=container)["id"]


def main():
    with open(POSTS_FILE, encoding="utf-8") as f:
        posts = json.load(f)

    now = datetime.now(timezone.utc)
    kst = timezone(timedelta(hours=9))
    now_kst = now.astimezone(kst)

    def is_due(p):
        at = datetime.fromisoformat(p["publish_at"]).astimezone(kst)
        # 예약 시각이 지났고, 밀린 게시물도 '오늘의 같은 시각'(예: 저녁 9시)이 된 뒤에만 올린다
        return at <= now and now_kst.time() >= at.time()

    due = [p for p in posts if not p.get("posted") and is_due(p)]
    due.sort(key=lambda p: p["publish_at"])  # 예약 시간 순서대로 (그리드 순서가 이걸로 정해져요)

    # 하루 최대 게시 수 (기본 1개). 토큰 연결이 늦어져 밀려도 한꺼번에 쏟아지지 않게 하루 하나씩만 올린다
    max_per_day = int(os.environ.get("MAX_POSTS_PER_DAY", "1"))
    posted_today = sum(1 for p in posts if p.get("posted") and p.get("posted_at")
                       and datetime.fromisoformat(p["posted_at"]).astimezone(kst).date() == now_kst.date())
    due = due[:max(0, max_per_day - posted_today)]

    if not due:
        print("지금 올릴 게시물이 없어요.")
        return

    base = image_base_url() if not DRY_RUN else os.environ.get("IMAGE_BASE_URL", "https://example.com")
    changed = False
    for post in due:
        print(f"→ {post['id']} 게시 중 ({post['publish_at']})")
        if DRY_RUN:
            print("   [DRY_RUN] 이미지:", post.get("images") or [post["image"]])
            print("   [DRY_RUN] 캡션 첫 줄:", post["caption"].splitlines()[0])
            continue
        try:
            media_id = publish(post, base)
        except Exception as e:  # 한 개가 실패해도 기록하고 멈춤 → 순서가 꼬이지 않게
            post["last_error"] = str(e)
            changed = True
            print("   실패:", e)
            break
        post["posted"] = True
        post["media_id"] = media_id
        post["posted_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        post.pop("last_error", None)
        changed = True
        print("   완료! media id:", media_id)
        time.sleep(10)

    if changed:
        with open(POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
