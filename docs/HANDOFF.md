# 실행 및 Builder 인계서

## 인계 원칙

Replit, Codex, Claude Code, Copilot 등은 교체 가능한 Builder다. 특정 도구 내부에만 남아 코드, 데이터, 결정, 테스트, 환경, 배포, 미완료 작업을 다음 Builder가 재현할 수 없으면 완료가 아니다.

작업 전 루트 `AGENTS.md`, `docs/governance/OPERATING-MODEL.md`, 활성 CR, 관련 ADR/RFC와 테스트를 읽는다. Notion의 관련 운영 DNA와 최신 사용자 결정도 대조한다.

## 사용자가 할 일

1. 전달 ZIP을 저장소 루트에 압축 해제한다.
2. ZIP 내부 경로를 유지한 채 완성본 파일을 덮어쓴다.
3. GitHub Desktop에서 diff를 검토한다.
4. 전체 테스트를 실행한다.
5. commit·push한다.
6. AI에게 원격 commit 확인을 요청한다.

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
- 완성본 파일 또는 정확한 VS Code 영역 수정 지시 제공
- push 이후 원격 commit과 변경 파일 재검증

## Git 전달 원칙

- 기본은 대상 경로에 그대로 복사·덮어쓰기 가능한 완성본 파일이다.
- 부분 패치 지시문을 실제 기준 파일명으로 제공하지 않는다.
- 전체 덮어쓰기가 다른 내용을 유실할 위험이 있을 때만 VS Code 영역 수정을 사용한다.
- 영역 수정 시 파일 경로, 기존 anchor 문자열, 교체 범위, 새 내용이 모두 명확해야 한다.
- ZIP 생성만으로 `Implemented`가 아니다.

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

원격 `main`의 commit `3a7b272aa326b8db2d5ac8319b95f0e706a4a8cd`는 확인되었다. 다만 일부 기준 파일이 완성본 대신 패치 지시문으로 덮어써져 저장소 정합화가 필요하다. ChatGPT의 GitHub 연결은 원격 확인용 읽기 경로로 사용하고, 변경은 로컬 저장소에 적용한 뒤 사용자가 GitHub Desktop으로 검토·commit·push한다. AI는 push 후 원격 commit과 변경 파일을 재확인한다.

CR-0013은 `Approved`이며 Runtime 구현은 아직 시작하지 않았다. 다음 작업은 이 인계 묶음으로 기준 파일을 복구한 뒤 전체 테스트를 실행하고 원격 정합화를 확인하는 것이다.
