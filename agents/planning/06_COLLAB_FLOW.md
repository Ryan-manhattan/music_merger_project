## 최신 내용 공유/진행 플로우(기획 ↔ 개발)

## 1) 단일 진실 소스(SSOT)
- 기획/결정: `agents/planning/`
- 최종 보고 누적: `agents/planning/reports/`
- 회의 기록/결정: `agents/planning/meetings/`
- (참고) 개발자 에이전트 행동 지침: `agents/dev/`

## 2) 진행 사이클
- **(A) 결재 필요 사항 발생** → 기획자가 보고서(옵션/추천 포함) 작성 → 사장님 결재
- **(B) 구현 착수** → 개발자 에이전트가 스펙을 구현
- **(C) 공유/동기화** → 구현 결과를 보고서/회의록에 업데이트

## 3) 파일 네이밍 규칙
- 최종 보고: `YYYY-MM-DD_HH-MM-SS__REPORT.md`
- 회의록: `YYYY-MM-DD_HH-MM-SS__MEETING.md`

## 4) 현재 확정된 제품 범위(결재 반영)
- **중심 컨텐츠 범위(1차)**: YouTube + SoundCloud
- **확장 원칙**: 컨텐츠 타입 추가는 결재 후 반영

---

## (공지) 에이전트 문서 위치 변경
- 에이전트 관련 문서(행동지침/감리 기준/모델별 지침)는 `docs/`가 아니라 `agents/`에서 관리합니다.
  - DEV 플레이북: `agents/dev/00_DEV_AGENT_PLAYBOOK.md`
  - HR 감리 기준: `agents/hr/07_HR_GOVERNANCE.md`

---

## (공지) planning 문서 관리 위치 변경
- `planning` 문서(기획/결정/보고/회의)는 `docs/planning/`이 아니라 `agents/planning/`에서 관리합니다.
