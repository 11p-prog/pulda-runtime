# 실행 및 Builder 인계서

## 인계 원칙

Replit, Codex, Claude Code, Copilot 등은 교체 가능한 Builder다. 특정 도구 내부에만 남아 코드, 데이터, 결정, 테스트, 환경, 배포, 미완료 작업을 다음 Builder가 재현할 수 없으면 완료가 아니다.

작업 전 루트 `AGENTS.md`, `docs/governance/OPERATING-MODEL.md`, 활성 CR, 관련 ADR/RFC와 테스트를 읽는다. Notion의 관련 운영 DNA와 최신 사용자 결정도 대조한다.

## 사용자가 할 일

1. 압축 해제
2. Python 3.12 또는 Docker 설치 확인
3. `.env.example`을 `.env`로 복사
4. 실행
5. 브라우저에서 Event 입력
6. Notion 자동동기화를 원하면 Integration Token과 대상 Page ID 입력
7. GitHub 자동동기화를 원하면 PAT와 저장소명 입력

## Builder가 할 일

- 저장소 Import와 정확한 commit/ref 기록
- Secrets와 환경변수 등록 및 목록화
- 승인된 CR 범위만 구현
- 자동 테스트와 Runtime 실행 증거 반환
- 데이터 변경 시 Migration, export/import, rollback 검증
- 미완성 작업, 알려진 오류, 다음 행동 기록
- GitHub Actions: 테스트 및 배포 자동화

## ChatGPT가 할 일

- 매 작업 전 Notion/Git/Runtime/긴급패치 기준선 작성
- Theory/Architecture/Domain 정책 및 충돌 검토
- 사용 로그 리뷰
- 분류 규칙과 안전장치 개선 제안
- Notion 지식 저장소 문서 업데이트
- 릴리스 검토

## 필수 인계 묶음

- 실행 및 전체 테스트 명령
- 환경변수 이름과 목적(값 제외)
- 데이터 스키마와 Migration 상태
- AI provider/model/prompt/DNA 버전
- CR, commit, test, Runtime evidence, user verification 링크
- 배포 절차와 플랫폼 종속 요소
- export/import/restore 절차와 최근 검증 결과
- 미완료 작업, 오류, 위험, 다음 최소 행동

## 2026-07-14 상태

GitHub 저장소는 존재하며 로컬 clone도 생성되었다. ChatGPT GitHub integration은 읽기 가능하지만 쓰기 작업은 403으로 차단되었으므로, 변경은 로컬에 적용한 뒤 GitHub Desktop에서 검토·commit·push해야 한다.
