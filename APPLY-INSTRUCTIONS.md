# Pulda Runtime CR-0017 / CR-0018 적용 안내

기준 원격 커밋: `d71f5073bc2fe2fc456e43c9e95bf78d1fbff6c1`

## 적용

1. 로컬 `11p-prog/pulda-runtime` 저장소가 위 기준 커밋을 포함하는지 확인합니다.
2. 이 ZIP의 폴더 구조를 유지한 채 저장소 루트에 덮어씁니다.
3. GitHub Desktop에서 아래 9개 파일만 변경되었는지 Diff를 확인합니다.
4. 테스트 환경에서 `pytest -q`를 실행합니다. 기대 결과는 `35 passed`입니다.
5. 커밋 후 push합니다.
6. 원격 커밋을 확인한 뒤 Replit PostgreSQL 비공개 백업을 먼저 생성하고 배포합니다.

## 변경 파일

- `docs/HELP.md`
- `docs/cr/STATUS.md`
- `docs/cr/CR-0017.md`
- `docs/cr/CR-0018.md`
- `pulda/app.py`
- `pulda/db.py`
- `pulda/service.py`
- `pulda/templates/index.html`
- `tests/test_runtime.py`

## 주의

- 실제 Runtime DB, 백업, 개인정보, 첨부파일은 이 ZIP에 포함되지 않습니다.
- DB Migration이 있으므로 Replit 배포 전에 반드시 비공개 DB 백업·복구 가능성을 확인합니다.
- 기존 `inbox / planned` 상태는 `recorded`로 전환되며 원래 값은 `legacy_status`에 보존됩니다.
- 사용자 실사용 확인 전에는 CR을 `User Verified` 또는 `Closed`로 변경하지 않습니다.
