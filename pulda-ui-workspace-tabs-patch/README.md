# Pulda OS workspace tabs regression patch

## 적용
저장소 루트에서 압축을 푼 뒤 실행합니다.

```bash
python apply_patch.py
python verify_patch.py
pytest -q
```

`templates/index.html.before-workspace-tabs.bak`가 자동 생성됩니다.

## 변경 범위
- `templates/index.html` 한 파일
- 중앙 작업 화면 탭 복원: Home / Project WBS / Event detail / Asset / Settings
- Event / Task / Goal / Project 엔티티 탭은 추가하지 않음
- DB, API, 라우트, 데이터 모델 변경 없음
- 기존 코드 삭제 없음

## 커밋 메시지

```text
fix(ui): restore central workspace tabs
```
