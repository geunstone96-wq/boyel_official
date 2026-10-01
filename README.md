# boyel* 인스타 자동 게시 — 설정 안내서

한 번만 설정하면, 이후에는 **이미지와 캡션만 넣어 두면 정해진 시간에 자동으로 인스타에 올라가요.**
컴퓨터를 꺼 둬도 GitHub 서버가 대신 올려 줘요. (무료)

```
posts.json (게시 일정)  ─┐
images/ (사진)         ─┼→ GitHub Actions (매시간 확인) → Instagram 공식 API → 인스타 피드
```

---

## 0. 준비물 체크
- [ ] 보이엘 인스타 계정 (**프로페셔널 계정** 으로 전환)
- [ ] 개인 페이스북 계정 (페이지 관리자용, 광고와 화면에는 이름이 안 보여요)
- [ ] GitHub 계정 (github.com 무료 가입)
- 소요 시간: 처음 한 번 30분~1시간

---

## 1. 인스타를 프로페셔널 계정으로
인스타 앱 → 프로필 → ☰ → 설정 → **계정 유형 및 도구** → **프로페셔널 계정으로 전환** → 비즈니스 → 카테고리 "의류(브랜드)"

## 2. 페이스북 페이지 만들고 인스타 연결
1. 페이스북 → 페이지 → **새 페이지 만들기** → 이름 `boyel`
   - "친구 초대"는 누르지 마세요 (친구에게 알림 안 가게)
2. 인스타 앱 → 설정 → **계정 센터** 또는 프로필 편집 → **페이지 연결** → 방금 만든 boyel 페이지 선택

## 3. Meta 개발자 앱 만들기
1. https://developers.facebook.com → 로그인 → **내 앱 → 앱 만들기**
2. 사용 사례: **"Instagram에서 메시지 및 콘텐츠 관리"** (또는 "기타" → 유형 "비즈니스")
3. 앱 이름: `boyel-poster` → 만들기
4. 왼쪽 메뉴 **앱 설정 → 기본 설정** 에서 **앱 ID** 와 **앱 시크릿 코드** 를 메모

> 본인 계정에만 올리는 용도라 앱은 **개발 모드** 그대로 두면 돼요. 앱 관리자(본인)의 계정은 보통 심사 없이 게시 권한을 쓸 수 있어요.

## 4. 토큰 받기
1. https://developers.facebook.com/tools/explorer (Graph API 탐색기)
2. 오른쪽 **Meta 앱** 에서 `boyel-poster` 선택
3. **권한 추가** 에서 아래를 체크:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`
4. **Generate Access Token** → 로그인 창에서 boyel 페이지와 인스타 계정을 선택해 허용
5. 위에 생긴 긴 토큰을 복사

## 5. 만료 없는 토큰과 인스타 ID 받기
컴퓨터에서 (또는 Claude Code에 "setup_token.py 실행해줘"라고 하면 돼요):
```
pip install requests
python setup_token.py
```
앱 ID, 앱 시크릿, 4번 토큰을 붙여 넣으면 이렇게 나와요:
```
IG_USER_ID      = 1784...
IG_ACCESS_TOKEN = EAAG...
```
**이 두 값은 비밀번호와 같아요.** 아래 6번 외에는 어디에도 저장하거나 보내지 마세요.

## 6. GitHub 저장소 만들기
1. github.com → **New repository** → 이름 `boyel-insta` → **Public** 선택 → 만들기
   - 인스타가 이미지를 가져가려면 이미지 주소가 공개돼야 해서 Public이에요. 토큰은 7번의 Secrets에 숨겨져서 안전해요.
2. 이 폴더의 파일 전부를 업로드 (**Add file → Upload files**, `.github` 폴더 포함)

## 7. 비밀값 넣기
저장소 → **Settings → Secrets and variables → Actions → New repository secret**
- `IG_USER_ID` = 5번의 IG_USER_ID
- `IG_ACCESS_TOKEN` = 5번의 IG_ACCESS_TOKEN

## 8. 이미지 넣기
Claude 디자인 캔버스에서 피드 3장을 **JPG** 로 내보내기 (캔버스 → 공유/Share → Export)
→ 이름을 아래처럼 바꿔서 저장소 `images/` 폴더에 업로드

| 캔버스 보드 | 파일 이름 |
|---|---|
| Post 1 · Logo | `images/01_logo.jpg` |
| Post 2 · Slogan | `images/02_slogan.jpg` |
| Post 3 | `images/03_intro.jpg` |

> PNG로만 내보내지면 JPG로 변환해서 올리세요. **인스타 API는 JPG만 받아요.**

## 9. 시험 실행
저장소 → **Actions** 탭 → "Instagram 자동 게시" → **Run workflow**
- 예약 시간이 아직 안 됐으면 "지금 올릴 게시물이 없어요"가 정상이에요.
- 바로 테스트하려면 `posts.json` 의 첫 게시물 `publish_at` 을 지난 시간으로 바꾸고 실행하세요.

---

## 매주 쓰는 법
1. Claude에게 "이번 주 게시물 만들어줘"라고 하면 이미지와 캡션을 만들어 드려요.
2. 이미지는 `images/` 에, 캡션은 `posts.json` 에 추가 (Claude Code에서 이 폴더를 열고 맡기면 알아서 추가하고 push 해요)
3. 끝. 예약 시간이 되면 자동으로 올라가요.

`posts.json` 한 항목 예시:
```json
{
  "id": "2026-10-15-look01",
  "image": "images/look01.jpg",
  "publish_at": "2026-10-15T20:00:00+09:00",
  "caption": "캡션...",
  "posted": false
}
```
여러 장(캐러셀)은 `"image"` 대신 `"images": ["images/a.jpg", "images/b.jpg"]`

## 문제가 생기면
- 게시 실패 시 `posts.json` 해당 항목에 `last_error` 가 기록되고, 다음 시간에 다시 시도해요.
- **토큰 오류**(OAuthException, 190): 4~5번을 다시 해서 새 토큰을 Secrets에 바꿔 넣으세요.
- **버전 오류**: Meta가 오래된 API 버전을 종료하면 Secrets 옆 **Variables** 에 `GRAPH_VERSION` (예: `v25.0`)을 추가하고 워크플로의 env에 연결하면 돼요. Claude Code에 "Graph API 버전 올려줘"라고 하면 처리해요.
- 하루 최대 100개까지 올릴 수 있어요.
- 릴스(영상)는 다음 단계에서 추가할 수 있어요.
