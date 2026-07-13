# Pulda Runtime Event Processing Model v0.1

This document describes Runtime behavior. Human/AI/Notion/Git/Builder governance is defined in [`governance/OPERATING-MODEL.md`](governance/OPERATING-MODEL.md).

## 입력

사용자는 구조를 선택하지 않고 자연어 Event만 입력한다.

## 처리

1. 원문 보존
2. 역할 추론
3. 영역 추론
4. 일정 Event / Task 후보 / 단순 Event 구분
5. 중요도와 긴급도 산정
6. Inbox 저장
7. 오늘 실행 후보 제안
8. 상태 변화 기록
9. 일일 Review
10. 외부 시스템 동기화

## 자가행동 범위

- 서버 실행 중 스케줄러가 매일 Review 생성
- 설정 시 Notion과 GitHub 자동 동기화
- 실패 로그 저장
- 미완료 항목 재노출

## 사람의 승인 필요 영역

- 외부 메시지 발송
- 비용 발생
- 계약/법률/의료 결정
- 데이터 삭제
- 우선순위가 충돌하는 가족/사업/성당 의사결정
