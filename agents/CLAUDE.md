# Claude Instructions for Moodo Project

This file contains instructions and context for Claude when working on the Moodo project.

## Project Overview
Moodo is an all-in-one music processing application that combines and processes audio files, creates videos, and analyzes music charts.

## Development Commands
- `npm run dev` - Start development server
- `npm run build` - Build the project
- `npm run test` - Run tests
- `npm run lint` - Run linting
- `npm run typecheck` - Run TypeScript type checking

## Code Style Guidelines
- Follow existing code conventions in the project
- Use TypeScript for type safety
- Follow consistent naming conventions
- Add comments only when explicitly requested

## Testing
- Run tests before committing changes
- Ensure all type checks pass
- Run linting to maintain code quality

## Important Notes
- Always check existing dependencies before adding new ones
- Follow security best practices
- Never commit secrets or API keys
- Use existing patterns and libraries when possible

---

# [기본 작업 운영 지침서] 가장 중요

1. 절대 나의 동의 없이 임의로 진행하지말 것
2. 옵션 제시는 숫자로 할 것 추천 옵션도 함께 제시할 것
3. 오류 발생 시 원인 분석 후 해결 방법을 제시할 것
4. 모든 수정 및 진행 과정은 나에게 허락을 구하고 진행할 것
5. 모든 대답과 의견은 토큰을 가장 효율적으로 사용할 수 있는 방법으로 제시
6. 언제나 한글로 대답한다
5. md 문서의 기존 내용은 절대로 삭제하지 않고, 새로운 내용을 추가한다.(효율성 중심)
6. 새롭게 알게 된 사실이나 다시 참고해야하는 팁은 매번 룰로 생성한다 

## [작업 전/중/후 필수 규칙]

## 🚦 [진행 및 의사결정]

1. 모든 작업은 사용자에게 반드시 확인 후 수행
2. 이후 진행 여부 질문은 숫자 옵션과 추천 항목을 간단히 제시
2. 지시어 예시:
   - `ㄱ` = 진행
   - `ㅇㅇ` = 알겠어
   - `ㄱㄱㄱ` = 질문 없이 전체 자동 진행
   - `ㅁㅁㄹ` = memory.md 업데이트
   - `ㄹㄷㅁ` = READEME.md 업데이트
   - 'ㅌㄷ' = To-Do.md 업데이트 
   - 'ㅇㄹ' = error.md 업데이트
   - 'ㅂㄱ' = 작업 진행 하지말고 보고만 진행
   - 'ㄽㅅ' = 커서 프로젝트 룰 생성

## 🧠 [의견 및 옵션 제공 규칙]

1. 질문에 대한 답변만 제시하고 정답만 제시 할 것
2. 오류 발생 시:
   - 원인 분석 후 바로 조치 하지 말 것
   - 사용자에게 원인 및 해결 옵션 제시 할 것
   - 해결되면 반드시 룰로 생성

## 📂 [파일/폴더 관리 지침]

1. 생성 및 수정은 해당 프로젝트 폴더 내에서만 수행
2. 파일 용량 및 구조 최적화:
   - 한 파일은 **18KB 초과 금지**
   - 긴 파일은 **2~3개 단위 분할**
3. `docs/` 폴더에는 꼭 필요한 문서만 최소 용량으로 정리

## 🧪 [테스트/디버깅/코딩]

1. 테스트는 **MCP 도구(예: Playwright)** 사용
   - 브라우저 상에서 직접 클릭 → 결과 확인
3. 디버깅 시 **콘솔 로그 필수 확인**
4. 에러 발생시 디버깅 가능한 코드 추가

---

# 🎵 [Music Trend Analyzer V2 규칙] 2025-07-18

## 📊 [새로운 시스템 구조]

### **핵심 모듈들**
- `reddit_connector.py` - Reddit 음악 커뮤니티 데이터 수집
- `spotify_connector.py` - Spotify 차트 & 오디오 특성 분석  
- `keyword_trend_analyzer.py` - 해시태그, 키워드 빈도, 감정어 분석
- `comment_trend_analyzer.py` - 댓글 감정분석, 토픽모델링
- `music_trend_analyzer_v2.py` - 모든 모듈 통합 분석

### **데이터 소스 우선순위**
1. **Reddit**: 음악 서브레딧 트렌딩 게시물 & 댓글
2. **Spotify**: 한국/글로벌 차트, 오디오 특성
3. **Google Trends**: 검색 트렌드 (기존)
4. **YouTube**: 동영상 분석 (기존)

## 🔑 [API 설정 필수사항]

### **환경변수 설정**
```
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
REDDIT_USER_AGENT=MusicTrendAnalyzer/1.0
SPOTIFY_CLIENT_ID=xxx
SPOTIFY_CLIENT_SECRET=xxx
```

### **패키지 의존성**
- `praw==7.7.1` (Reddit API)
- `spotipy==2.23.0` (Spotify API)
- `konlpy==0.6.0` (한국어 자연어 처리)
- `vaderSentiment==3.3.2` (감정 분석)
- `scikit-learn==1.3.2` (머신러닝)
- `textblob==0.17.1` (영어 자연어 처리)

## 🎯 [분석 기능 규칙]

### **키워드 분석 우선순위**
1. **해시태그**: #으로 시작하는 태그 추출 및 분류
2. **감정어**: 음악 관련 감정 키워드 가중치 분석
3. **장르 키워드**: kpop, hiphop, ballad 등 장르별 분류
4. **트렌드 키워드**: viral, trending, chart 등

### **댓글 분석 로직**
1. **다중 감정분석**: VADER + TextBlob + 커스텀 음악 감정
2. **토픽모델링**: LDA 알고리즘으로 주제 추출
3. **시간 패턴**: 댓글 시간대별 분포 분석
4. **언어 패턴**: 한국어/영어/이모지 사용 비율

## ⚡ [성능 최적화 규칙]

### **데이터 수집 제한**
- Reddit: 게시물 100개, 댓글 20개/게시물
- Spotify: 트랙 50개, 오디오 특성 20개
- 텍스트 처리: 10KB 이하 청크 단위
- API 호출 간격: 0.1초 대기

### **메모리 관리**
- 대용량 텍스트는 스트리밍 처리
- 분석 결과는 최대 20개 항목만 저장
- 임시 데이터는 즉시 정리

## 🔄 [작업 플로우]

### **트렌드 분석 순서**
1. **데이터 수집**: Reddit → Spotify → Google Trends
2. **텍스트 처리**: 키워드 추출 → 감정 분석
3. **점수 계산**: 가중치 적용 종합 점수
4. **예측 생성**: 단기/장기 트렌드 예측
5. **추천 제공**: 분석 기반 실행 가능한 추천

### **오류 처리 우선순위**
1. **API 연결 실패**: 다른 데이터 소스로 대체
2. **데이터 부족**: 최소 임계값 확인 후 경고
3. **분석 오류**: 기본값 반환 + 로그 기록
4. **시간 초과**: 부분 결과라도 반환

## 📈 [분석 결과 품질 기준]

### **신뢰도 계산**
- 데이터 소스 4개 모두 수집: 100%
- 3개 수집: 75%, 2개: 50%, 1개: 25%
- 최소 임계값: 댓글 10개, 키워드 5개

### **트렌드 강도 분류**
- **Very Strong** (80+): 즉시 주목 필요
- **Strong** (60-79): 모니터링 강화
- **Moderate** (40-59): 일반적 관심
- **Weak** (20-39): 참고용
- **Minimal** (0-19): 무시 가능

## 🚨 [중요 주의사항]

### **한국어 처리**
- KoNLPy 설치 실패 시 → 단순 키워드 매칭으로 대체
- 한국어 감정 키워드 우선 → 영어 감정 분석 보조

### **API 제한 대응**
- Reddit API 제한 → 캐시된 데이터 활용
- Spotify API 제한 → 무료 계정 한도 고려
- 모든 API 실패 → 기존 데이터베이스만 활용

### **실시간 분석 최적화**
- 전체 분석: 5분 이내 완료
- 키워드 검색: 30초 이내 완료
- 시스템 상태 확인: 즉시 응답