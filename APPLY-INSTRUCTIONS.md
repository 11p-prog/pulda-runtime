# 적용 지침 — 2026-07-14 저장소 정합화

## 적용 방식

이 ZIP은 **완성본 덮어쓰기 방식**이다.

1. ZIP을 임시 폴더에 푼다.
2. 내부의 `README.md`, `AGENTS.md`, `docs/` 폴더를 `pulda-runtime` 저장소 루트에 복사한다.
3. Windows에서 “대상 폴더의 파일 바꾸기”를 선택한다.
4. 경로를 변경하거나 파일 내용을 일부만 복사하지 않는다.
5. GitHub Desktop에서 아래 5개 파일만 변경되었는지 확인한다.

## 덮어쓰기 대상

- `README.md`
- `AGENTS.md`
- `docs/cr/STATUS.md`
- `docs/governance/OPERATING-MODEL.md`
- `docs/HANDOFF.md`

## 변경되면 안 되는 것

- 소스 코드
- 테스트 코드
- DB 및 Migration
- `.env`와 비밀정보
- 다른 CR/ADR/RFC 문서

## 검증

```powershell
pytest -q
```

기존 프로젝트의 정식 전체 테스트 명령이 별도로 있다면 그 명령도 실행한다.

## 권장 commit message

`docs: restore canonical files and record living-loop workflow`

## 상태 경계

이 작업은 저장소 기준 문서 정합화다. CR-0013 Runtime 구현이 아니며, 테스트가 통과하고 원격 commit이 확인되어도 CR-0013 상태는 `Approved`를 유지한다.
