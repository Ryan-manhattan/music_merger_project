## agents/ (에이전트 문서 관리)

- 목적: 에이전트(모델/역할)별 지침과 HR 감리 기준을 **docs와 분리**해서 관리한다.
- 원칙: 제품/기획/결정의 SSOT는 `docs/planning/`이며, 에이전트 문서는 `agents/`에서 관리한다.

---

## 구성
- 모델별 지침
  - `agents/CLAUDE.md`
  - `agents/GEMINI.md`

- 역할별 지침
  - DEV: `agents/dev/00_DEV_AGENT_PLAYBOOK.md`
  - DESIGN: `agents/design/00_DESIGN_AGENT_PLAYBOOK.md`
  - HR: `agents/hr/07_HR_GOVERNANCE.md`

---

## docs와의 관계(중요)
- `agents/planning/`은 **결재/범위/정책(기획/결정/보고/회의)**의 단일 진실 소스(SSOT)
- `agents/`는 **업무 수행 방식/보고 포맷/감리 기준**의 단일 진실 소스(SSOT)

---

## (공지) SSOT 최신 기준(사장님/HR 지시 반영)
- 위 “SSOT는 `docs/planning/`” 문구는 **과거 기준**이며, 현재 최신 기준은 아래와 같습니다.
- **planning 문서 SSOT**: `agents/planning/`
- **docs/planning/**: 참고/이력 보관용(삭제/덮어쓰기 금지 원칙 유지)
