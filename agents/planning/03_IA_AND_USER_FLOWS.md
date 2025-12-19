## IA(정보구조) & 유저 플로우(초안)

## 1) IA 초안(현재 코드 기반, 테마 비정합 기능은 보류)
- **Home**: Diary Community(기록 목록)
- **Write Entry**: 기록 작성
- **Entry Detail**: 기록 상세

(참고: 구현은 존재하지만, 사장님 지시에 따라 기획 우선순위에서 제외)
- Charts
- Music Analysis
- Video Studio
- Music Studio

## 2) 핵심 유저 플로우(현재 동작 기준)
- **열람 플로우**: Home(목록) → Entry Detail
- **작성 플로우**: Home → Write Entry → 저장 → Entry Detail

## 3) 목표 유저 플로우(서비스 목적 반영: "특정 컨텐츠 중심 기록")
- **콘텐츠 중심 기록 플로우(목표)**
  - Content 입력/선택 → (메타/프롬프트로 회상 유도) → 기록 작성 → 저장 → 회고(목록/필터)

## 4) 향후 IA 확장 규칙(원칙)
- 기능이 늘어나도 **메인 네비는 '기록'을 중심으로 유지**
- 도구성 기능(분석/스튜디오)은 '기록을 돕는 보조 모듈'로 종속

---

## (업데이트) 2025-12-19: Song Archive 중심 IA/플로우(현재 구현 반영)

## 1) IA(현재)
- **Home**: Song Archive(곡 목록/추가) — `/`
- **Track Detail**: 곡 상세 + 코멘트(일기처럼) — `/track/<track_id>`
- **Diary Feed(기존 일기)**: `/diary`
- **Diary Write**: `/diary/write` (기존 `/community/write`도 호환)

## 2) 핵심 유저 플로우(현재)
- **곡 추가 플로우**: Home(Song Archive) → YouTube/SoundCloud URL 입력 → 메타 수집 → Track Detail
- **감상 기록 플로우**: Track Detail → 코멘트 작성(일기처럼) → 저장 → 댓글 목록 갱신
- **일기 플로우(보조)**: Diary Feed → Write Diary → Diary Detail
