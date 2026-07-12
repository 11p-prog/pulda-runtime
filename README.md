# Pulda Runtime MVP v0.1

즉시 실행 가능한 Pulda OS 초기 런타임입니다.

## 현재 가능한 것

- 자유문장으로 Event 입력
- Event → Task 후보 자동 변환
- 역할/영역/긴급도/중요도/상태 자동 분류
- SQLite 영구 저장
- 오늘의 실행 목록 생성
- 미완료/보류 Event 재검토
- 일일 Review 생성
- 선택적 Notion 동기화
- 선택적 GitHub 문서 동기화
- 스케줄러에 의한 주기적 자가 처리
- 브라우저 UI와 REST API 제공

## 1분 실행

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m pulda.app
```

브라우저: http://127.0.0.1:8000

Docker:

```bash
docker compose up --build
```

## 핵심 원칙

1. 모든 입력은 먼저 Event로 저장한다.
2. 계층은 사용자가 먼저 고르지 않는다.
3. 시스템이 Task/Project/Goal 연결을 제안한다.
4. 일정과 실행항목을 구분한다.
5. 미완료 항목은 삭제하지 않고 다시 해석한다.
6. 자동화는 기록을 남기며, 외부 쓰기는 설정으로 통제한다.

## 외부 연동

`.env`에 다음 값을 넣으면 활성화됩니다.

### Notion

- `NOTION_TOKEN`
- `NOTION_PARENT_PAGE_ID`

Runtime은 지정 페이지 아래에 `Pulda Runtime Sync` 페이지를 만들거나, 이미 지정된 `NOTION_SYNC_PAGE_ID`에 운영 로그를 추가합니다.

### GitHub

- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY=owner/repo`
- `GITHUB_BRANCH=main`

Runtime은 `runtime-status/latest-review.md`를 갱신합니다.

## 안전장치

- 기본값은 외부 쓰기 비활성화
- `AUTO_SYNC_NOTION=true`, `AUTO_SYNC_GITHUB=true`일 때만 자동 동기화
- 모든 자동행동은 `audit_log` 테이블에 기록
- 실패는 숨기지 않고 `/api/health`와 UI에 표시

## 현재 한계

- 카카오톡/SMS/전화 직접 수집 없음
- LLM 없이 규칙 기반 분류
- Notion DB 구조 자동 생성은 최소 수준
- GitHub App 권한이 없으면 토큰 필요
- 장기 자율성은 실행 중인 서버 또는 배포 환경이 필요
