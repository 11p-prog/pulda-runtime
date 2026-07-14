# Git workflow addendum — user decision 2026-07-14

Insert the following section into `docs/governance/OPERATING-MODEL.md` before its final `Updated` line:

## Standard Git change workflow

ChatGPT's GitHub integration is a read-only verification path. Do not spend work cycles retrying GitHub connector writes.

1. The AI or Builder changes only the approved scope in the user's local repository folder.
2. The AI or Builder returns the diff, test evidence, affected CR, and suggested commit message.
3. The user reviews, commits, and pushes through GitHub Desktop.
4. The AI re-reads the remote default branch and exact commit to verify publication.
5. The verified commit is linked back to the Notion CR and status.

A local working-tree change or patch bundle is `Prepared locally`, not `Implemented`. `Implemented` requires the remote commit and automated regression evidence. An emergency patch ZIP is a fallback handoff only when the active session cannot access the user's local repository.

Add the following under `## Change rules` in root `AGENTS.md`:

- Treat the GitHub integration as read-only. Prepare changes in the user's local repository; the user commits and pushes with GitHub Desktop.
- After the user pushes, re-read the remote commit and affected files before reporting reconciliation.
- Do not retry connector writes unless the user explicitly changes this operating decision.

Replace the final `## 2026-07-14 상태` section in `docs/HANDOFF.md` with:

## 2026-07-14 Git 표준 업무 흐름

ChatGPT의 GitHub 연결은 원격 기준 확인용 읽기 경로로만 사용한다. 일반적인 변경은 사용자의 로컬 저장소 폴더에서 준비하고 검증한다. 사용자가 GitHub Desktop에서 diff를 검토한 뒤 commit·push한다. AI는 원격 commit과 변경 파일을 다시 읽어 반영을 확인하고 Notion CR 상태를 정합화한다.

로컬 변경 또는 패치 생성만으로는 `Implemented`가 아니다. 원격 commit과 자동테스트 증거가 확인되어야 한다. 긴급패치 ZIP은 해당 세션이 로컬 저장소에 접근할 수 없을 때만 사용하는 보조 인계수단이다.
