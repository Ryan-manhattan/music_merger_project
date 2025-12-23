## T-004: Track Data 패널 정리(기본 메타 UX)

- **상태**: PM 스펙 작성 완료
- **우선순위**: Should

---

## 1) 목표
- 곡 상세의 Track_Data를 “사용자가 함께 확인하는 정보”로 더 읽기 쉽게 만든다.

## 2) 스코프
- 기본 메타만 대상(지표/통계는 별도)

## 3) 노출 항목(확정)
- Source(YouTube/SoundCloud)
- Uploader/Artist
- Duration
- Added_At
- Source Link

## 4) 표시 규칙
- Source_ID는 일반 사용자에겐 숨김(디버그 토글로만 노출 가능)
- Added_At는 사용자 로컬 타임존 기준 표시(가능 시)
- 링크는 항상 새 탭으로 열기

## 5) 수용 기준(AC)
- [ ] Track_Data 패널에서 Source Link가 명확히 보임
- [ ] Source_ID는 기본 화면에서 노출되지 않음
- [ ] 항목명이 사용자 친화적으로 정리됨(영문/한글 톤 합의)





