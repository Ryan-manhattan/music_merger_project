# 🎵 Music Merger Project - To-Do List

## 📋 현재 상황 (2025-07-17)

### ✅ **완료된 작업**
- [x] YouTube Data API v3 키 설정
- [x] Google Cloud Vertex AI 설정
- [x] 로컬 환경 테스트 성공
- [x] 환경 변수 JSON 처리 로직 구현
- [x] GitHub 코드 업로드 완료
- [x] YouTube 음악 분석 기능 작동 확인

### ❌ **현재 문제점**

#### **1. Render 배포 오류**
- **JavaScript 오류**: 
  ```
  Uncaught TypeError: Cannot read properties of null (reading 'addEventListener')
  at setupEventListeners (main.js:24:15)
  ```
- **API 500 오류**: 
  ```
  api/music-analysis/analyze:1 Failed to load resource: the server responded with a status of 500
  ```

#### **2. 환경 변수 설정 문제**
- Render에서 `GOOGLE_APPLICATION_CREDENTIALS_JSON` 설정 필요
- JSON 형식 오류 가능성

## 🔧 **해결해야 할 작업**

### **🚨 우선순위 높음**

#### **1. Render 환경 변수 설정**
- [ ] `GOOGLE_APPLICATION_CREDENTIALS_JSON` 재설정
- [ ] JSON 형식 확인 (중괄호 포함 필수)
- [ ] 압축된 JSON 한 줄 형태로 설정

**설정할 환경 변수**:
```
YOUTUBE_API_KEY=AIzaSyC56v9gGaWoU-GsDKFYvp3jguUB-SIY-Ds
GOOGLE_CLOUD_PROJECT_ID=pelagic-sorter-457711-n6
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
FLASK_ENV=production
DEBUG=False
```

#### **2. JavaScript 오류 수정**
- [ ] `main.js` 파일에서 null 체크 추가
- [ ] 요소 존재 확인 후 이벤트 리스너 추가
- [ ] 페이지별 스크립트 분리 검토

**수정 필요한 코드**:
```javascript
// 현재 (오류 발생)
fileInput.addEventListener('change', handleFileSelect);

// 수정 후
if (fileInput) {
    fileInput.addEventListener('change', handleFileSelect);
}
```

#### **3. API 500 오류 디버깅**
- [ ] Render 로그 확인
- [ ] 환경 변수 로딩 확인
- [ ] Google Cloud 인증 상태 확인

### **🔄 추가 개선 사항**

#### **1. 음악 생성 기능 완성**
- [ ] 실제 음악 파일 생성 기능 구현
- [ ] 다른 AI 음악 생성 서비스 연동 검토
- [ ] 현재는 분석 → 프롬프트 생성까지만 작동

#### **2. 사용자 경험 개선**
- [ ] 로딩 상태 표시 개선
- [ ] 오류 메시지 사용자 친화적으로 수정
- [ ] 모바일 반응형 개선

#### **3. 보안 및 성능**
- [ ] API 키 보안 강화
- [ ] 파일 업로드 크기 제한 검토
- [ ] 캐싱 전략 수립

## 🎯 **다음 단계**

1. **즉시 수정**: JavaScript null 체크 추가
2. **환경 변수 재설정**: Render에서 JSON 형식 확인
3. **테스트**: 로컬 → Render 순서로 테스트
4. **모니터링**: 로그 확인 및 오류 추적

## 📞 **참고 정보**

### **로컬 테스트 성공 확인**
- 서버: `http://localhost:5001`
- YouTube 분석 API: 정상 작동
- 환경 변수: 모든 설정 완료

### **Render 배포 URL**
- [배포 URL 추가 필요]

### **GitHub 저장소**
- https://github.com/Ryan-manhattan/music_merger_project

---

**💡 중요**: 환경 변수의 JSON 설정 시 중괄호 `{}`는 JSON 형식의 일부이므로 **반드시 포함**해야 함!

**📝 업데이트**: 문제 해결 시 이 파일을 업데이트하고 완료된 항목에 체크 표시

---

## 🎵 **새로운 음악 트렌드 분석 시스템 V2** (2025-07-18)

### ✅ **완료된 작업**
- [x] **현재 music_merger_project의 음악 트렌드 분석 구조 파악 및 개선점 분석**
- [x] **Reddit API 연동을 위한 PRAW 라이브러리 설정 및 인증 구조 설계**
- [x] **Spotify API 연동을 위한 Spotipy 라이브러리 설정 및 인증 구조 설계**
- [x] **키워드 중심 트렌드 분석 로직 설계** (해시태그, 언급빈도, 감정어 분석)
- [x] **댓글 중심 트렌드 분석 로직 설계** (감정분석, 토픽모델링, 키워드 추출)
- [x] **필요한 Python 패키지 설치 및 requirements.txt 업데이트**
- [x] **통합 트렌드 분석 모듈 (music_trend_analyzer_v2.py) 개발**

### 🔧 **개발된 새로운 모듈들**

#### **1. 핵심 분석 모듈**
- `reddit_connector.py` - Reddit 음악 커뮤니티 데이터 수집
- `spotify_connector.py` - Spotify 차트 & 오디오 특성 분석  
- `keyword_trend_analyzer.py` - 해시태그, 키워드 빈도, 감정어 분석
- `comment_trend_analyzer.py` - 댓글 감정분석, 토픽모델링
- `music_trend_analyzer_v2.py` - 모든 모듈 통합 분석

#### **2. 새로운 데이터 소스**
- **Reddit**: 음악 서브레딧 트렌딩 게시물 & 댓글
- **Spotify**: 한국/글로벌 차트, 오디오 특성, 아티스트 데이터
- **기존 유지**: Google Trends, YouTube, SQLite 데이터베이스

#### **3. 키워드 & 댓글 중심 분석 기능**
- 해시태그 패턴 분석 및 카테고리 분류
- 감정어 자동 추출 및 가중치 계산
- 토픽 모델링 (LDA) 및 음악 관련성 점수
- 시간별/플랫폼별 트렌드 변화 추적

### 🚨 **우선순위 높음 - 다음 단계**

#### **1. API 설정 및 테스트**
- [ ] **Reddit API 키 설정 및 PRAW 라이브러리 테스트**
  - Reddit Developer 계정 생성
  - Client ID, Client Secret 발급
  - 환경변수 REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET 설정
  
- [ ] **Spotify API 키 설정 및 Spotipy 라이브러리 테스트**
  - Spotify Developer 계정 생성
  - Client Credentials 발급
  - 환경변수 SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET 설정

- [ ] **각 분석 모듈 개별 기능 테스트 및 디버깅**
  - 모듈별 단위 테스트 실행
  - 오류 발생 시 디버깅 및 수정

### 📊 **우선순위 중간 - 시스템 통합**

#### **1. 웹 UI 통합**
- [ ] **웹 UI에 새로운 트렌드 분석 결과 통합** (키워드, 댓글, Reddit, Spotify)
  - 기존 시장 분석 탭 확장
  - 새로운 분석 결과 표시 UI 추가

- [ ] **키워드 & 댓글 중심 트렌드 대시보드 UI 개발**
  - 실시간 키워드 트렌드 차트
  - 감정 분석 결과 시각화
  - 플랫폼별 트렌드 비교 대시보드

#### **2. 백엔드 API 확장**
- [ ] **Flask 앱에 music_trend_analyzer_v2 API 엔드포인트 추가**
  - `/api/trends/v2/analyze` - 종합 트렌드 분석
  - `/api/trends/v2/keywords` - 키워드 검색 분석
  - `/api/trends/v2/status` - 시스템 상태 확인

#### **3. 실전 테스트**
- [ ] **실제 트렌딩 키워드로 통합 분석 시스템 실전 테스트**
  - 현재 인기 음악/아티스트로 테스트
  - 분석 결과 정확성 검증
  - 성능 최적화

### 📝 **우선순위 낮음 - 문서화**
- [ ] **환경변수 설정 문서 및 API 키 설정 가이드 작성**
  - README.md 업데이트
  - API 키 발급 가이드
  - 설치 및 설정 매뉴얼

### 🎯 **시스템 특징**
- **키워드 중심**: 해시태그, 언급빈도, 감정어 실시간 분석
- **댓글 중심**: 다중 감정분석, 토픽모델링, 패턴 분석  
- **다중 데이터 소스**: Reddit + Spotify + Google Trends + YouTube
- **실시간 트렌드**: 시간 가중치 적용한 종합 트렌드 점수
- **한국 특화**: 한국어 형태소 분석, K-pop 특화 키워드

### 📋 **설치 필요 패키지**
```
praw==7.7.1                    # Reddit API
spotipy==2.23.0                # Spotify API  
konlpy==0.6.0                  # 한국어 자연어 처리
vaderSentiment==3.3.2          # 감정 분석
scikit-learn==1.3.2            # 머신러닝 (토픽모델링)
textblob==0.17.1               # 영어 자연어 처리
```

---

## 🎯 **새로운 차트 API 통합 시스템** (2025-07-22)

### ✅ **완료된 작업**

#### **1. 새로운 차트 데이터 소스 통합**
- [x] **Last.fm API 연동 모듈** (`lastfm_connector.py`)
  - 글로벌 실시간 사용자 청취 데이터
  - Top 트랙/아티스트 차트 (7일/1개월/전체 기간)
  - 트렌딩 태그 및 장르 분석
  - Rate limiting 및 오류 처리

- [x] **Billboard 차트 모듈** (`billboard_connector.py`)
  - Hot 100, Billboard 200, Global 200 차트
  - 웹 스크래핑 기반 데이터 수집
  - BeautifulSoup 의존성 없이도 작동하는 대체 파싱
  - 차트 히스토리 검색 기능

- [x] **통합 차트 수집기** (`integrated_chart_collector.py`)
  - 4개 차트 소스 통합 (Last.fm, Billboard, Spotify, YouTube)
  - 가중치 기반 종합 점수 계산 시스템
  - 차트 간 겹침 분석 및 비교
  - 일관성 및 트렌드 강도 측정

- [x] **기존 시스템 통합**
  - `music_trend_analyzer_v2.py`에 새 API들 연결
  - 모든 모듈이 통합 분석 시스템에 완전 통합

#### **2. 의존성 설치 지원 시스템**
- [x] **requirements.txt 업데이트**
  - 새로운 차트 API 의존성 추가
  - BeautifulSoup4, lxml, html5lib (Billboard용)
  - requests, hashlib-compat 등 필수 라이브러리

- [x] **자동 설치 도구 개발**
  - `install_dependencies.py` - Python 자동 설치 스크립트
  - `install.sh` - Linux/macOS 자동 설치 스크립트
  - `install.bat` - Windows 자동 설치 스크립트
  - `SETUP_GUIDE.md` - 상세 설치 및 설정 가이드

- [x] **환경 설정 지원**
  - `.env.template` 자동 생성
  - API 키 발급 가이드 포함
  - 시스템별 의존성 설치 지원

#### **3. 테스트 및 검증 시스템**
- [x] **통합 테스트 스크립트** (`test_new_chart_apis.py`)
  - 모든 새로운 API 개별 테스트
  - 통합 시스템 호환성 검증
  - 의존성 설치 상태 확인

### 🚨 **우선순위 높음 - 남은 작업**

#### **1. API 키 설정 및 전체 시스템 테스트**
- [ ] **Last.fm API 키 설정**
  - Last.fm Developer 계정 생성
  - API 키 발급 및 환경변수 설정
  - 실제 데이터 수집 테스트

- [ ] **의존성 라이브러리 설치 완료**
  - BeautifulSoup4 설치 (`pip install beautifulsoup4`)
  - pandas, numpy 최신 버전 설치
  - 누락된 라이브러리 설치 완료

- [ ] **통합 차트 시스템 실전 테스트**
  - 4개 소스 동시 데이터 수집 테스트
  - 통합 점수 계산 알고리즘 검증
  - 성능 최적화 및 오류 처리

#### **2. 웹 인터페이스 업데이트**
- [ ] **새로운 차트 탭 추가**
  - 통합 차트 대시보드 UI 개발
  - Last.fm, Billboard 차트 표시
  - 차트 간 비교 및 분석 UI

- [ ] **차트 시각화 기능**
  - 실시간 차트 순위 표시
  - 트렌드 강도 및 일관성 시각화
  - 소스별 가중치 및 기여도 표시

#### **3. Flask API 엔드포인트 확장**
- [ ] **새로운 차트 API 엔드포인트 추가**
  - `/api/charts/integrated` - 통합 차트 데이터
  - `/api/charts/lastfm` - Last.fm 차트
  - `/api/charts/billboard` - Billboard 차트
  - `/api/charts/comparison` - 차트 간 비교 분석

### 📊 **우선순위 중간 - 기능 확장**

#### **1. 차트 분석 기능 고도화**
- [ ] **예측 알고리즘 개발**
  - 차트 순위 변동 예측
  - 트렌드 지속성 분석
  - 바이럴 가능성 예측

- [ ] **사용자 맞춤 차트**
  - 지역별 차트 필터링
  - 장르별 차트 분류
  - 개인화된 추천 차트

#### **2. 데이터 저장 및 히스토리**
- [ ] **차트 데이터 히스토리 저장**
  - SQLite 데이터베이스 스키마 확장
  - 일별/주별 차트 변화 추적
  - 장기 트렌드 분석 데이터

### 📝 **우선순위 낮음 - 최적화**

#### **1. 성능 최적화**
- [ ] **API 호출 최적화**
  - 캐싱 시스템 구현
  - 병렬 처리 최적화
  - Rate limiting 개선

- [ ] **데이터 품질 개선**
  - 중복 데이터 제거 알고리즘
  - 데이터 정규화 개선
  - 오류 데이터 필터링

#### **2. 문서화 완성**
- [ ] **API 문서 작성**
  - 새로운 엔드포인트 문서화
  - 차트 데이터 구조 설명
  - 사용 예시 및 샘플 코드

### 🎯 **새로운 차트 시스템 특징**

#### **데이터 소스 및 가중치**
| 소스 | 특징 | 가중치 | 업데이트 주기 |
|------|------|--------|---------------|
| **Last.fm** | 실제 사용자 청취 데이터 | 25% | 실시간 |
| **Billboard** | 공식 상업적 성공 차트 | 30% | 주간 |
| **Spotify** | 스트리밍 인기도 | 25% | 일간 |
| **YouTube** | 동영상 조회수/바이럴 | 20% | 동적 |

#### **핵심 기능**
- **통합 점수 계산**: 4개 소스 가중치 기반 종합 점수
- **트렌드 강도 분류**: Very Strong, Strong, Moderate, Weak
- **일관성 측정**: 차트 간 순위 일관성 0-1 점수
- **겹침 분석**: 차트 간 공통 트랙 비율 분석

### 📋 **환경변수 추가 설정**
```bash
# 새로운 차트 API 키
LASTFM_API_KEY=your_lastfm_api_key_here
LASTFM_API_SECRET=your_lastfm_secret_here

# 기존 API 키들 (유지)
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### 🔧 **설치 명령어**
```bash
# 자동 설치 (권장)
python install_dependencies.py

# 또는 플랫폼별 스크립트
./install.sh  # Linux/macOS
install.bat   # Windows

# 수동 설치
pip install -r requirements.txt
```