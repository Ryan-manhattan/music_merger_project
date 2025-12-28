## T-005: 외부 지표 수집 + stats 적재 + 곡 상세 표시

- **상태**: Ready for DEV
- **우선순위**: Could (사장님 결재 완료)
- **전제(결재)**: 안건1=3, 안건2=최소 키셋

---

## 1) 목표
- YouTube/SoundCloud의 지표를 주기적으로/요청 시 수집하여 `tracks.metadata.stats`에 저장하고, 곡 상세에서 표시한다.

## 2) 스코프
- 수집 대상
  - YouTube: `views`, `likes`, `comments`
  - SoundCloud: `plays`, `likes`, `comments`
- 공통
  - `comment_count`(내부) 계산
  - `last_synced_at` 업데이트

## 3) 데이터 모델(확정 키)
- `tracks.metadata.stats`
  - `comment_count`: number
  - `last_synced_at`: ISO string
  - `views`/`likes`/`comments` (YouTube)
  - `plays`/`likes`/`comments` (SoundCloud)

## 4) 동작 정책(초안)
- 초기: Track Detail 진입 시 “필요하면 동기화” 또는 “수동 Sync 버튼” 중 택1(DEV가 구현 난이도/리스크 고려해 제안)
- 실패 시: 지표 영역은 숨김 + “동기화 불가”만 표시

## 5) 수용 기준(AC)
- [ ] YouTube 트랙(영상)에서 stats 3종이 정상 표기된다(값 + last_synced_at)
- [ ] SoundCloud 트랙에서 stats 3종이 정상 표기된다(값 + last_synced_at)
- [ ] 외부 API 실패 시에도 페이지/코멘트 기능은 정상 동작한다(degrade)
- [ ] stats는 `tracks.metadata.stats`에 저장되고, 키명이 SSOT와 일치한다

## 6) 리스크/주의
- API 키/토큰/쿼터/레이트리밋/정책 변경
- 개인정보/보안: 키/토큰은 절대 커밋 금지(.env)







