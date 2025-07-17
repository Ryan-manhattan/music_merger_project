# 🎵 Music Merger - AI 음악 생성 API 설정 가이드

## 📋 개요

이 가이드는 Music Merger 프로젝트의 AI 음악 생성 기능을 사용하기 위한 API 설정 방법을 안내합니다.

## 🔧 필요한 API 키

### 1. YouTube Data API v3
- **용도**: YouTube 음악 분석 및 메타데이터 수집
- **필수 여부**: 필수 (음악 분석 기능 사용 시)

### 2. Google Cloud Vertex AI (Lyria)
- **용도**: AI 음악 생성
- **필수 여부**: 필수 (AI 생성 기능 사용 시)

## 🎯 YouTube Data API v3 설정

### 1단계: Google Cloud Console 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 프로젝트 ID 기록 (나중에 사용)

### 2단계: YouTube Data API v3 활성화

1. Google Cloud Console에서 "APIs & Services" → "Library" 이동
2. "YouTube Data API v3" 검색
3. "Enable" 버튼 클릭

### 3단계: API 키 생성

1. "APIs & Services" → "Credentials" 이동
2. "+ CREATE CREDENTIALS" → "API key" 선택
3. 생성된 API 키 복사 및 안전하게 보관
4. (권장) API 키 제한 설정:
   - Application restrictions: IP 주소 또는 도메인 제한
   - API restrictions: YouTube Data API v3만 허용

## 🤖 Google Cloud Vertex AI 설정

### 1단계: Vertex AI API 활성화

1. Google Cloud Console에서 "Vertex AI" 검색
2. Vertex AI API 활성화
3. "Generative AI" 섹션에서 Lyria 모델 확인

### 2단계: 서비스 계정 생성

1. "IAM & Admin" → "Service Accounts" 이동
2. "+ CREATE SERVICE ACCOUNT" 클릭
3. 서비스 계정 정보 입력:
   - **Name**: music-merger-ai
   - **Description**: AI 음악 생성용 서비스 계정

### 3단계: 권한 부여

다음 역할을 서비스 계정에 부여:
- `Vertex AI User`
- `Storage Object Admin` (파일 저장용)

### 4단계: 서비스 계정 키 생성

1. 생성된 서비스 계정 클릭
2. "Keys" 탭 → "ADD KEY" → "Create new key"
3. JSON 형식 선택
4. 다운로드된 JSON 파일을 프로젝트 폴더에 저장
5. 파일 경로 기록

## 📁 환경 변수 설정

### 1단계: .env 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일 생성:

```bash
# YouTube Data API v3 설정
YOUTUBE_API_KEY=your_youtube_api_key_here

# Google Cloud 설정 (Lyria AI)
GOOGLE_CLOUD_PROJECT_ID=your_project_id_here
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# 음악 생성 설정
DEFAULT_MUSIC_DURATION=30
MAX_MUSIC_DURATION=300
LYRIA_MODEL=gemini-1.5-pro
```

### 2단계: 환경 변수 설정 예시

**Windows:**
```cmd
set YOUTUBE_API_KEY=AIzaSyExample123456789
set GOOGLE_CLOUD_PROJECT_ID=my-music-project
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account-key.json
```

**Linux/Mac:**
```bash
export YOUTUBE_API_KEY="AIzaSyExample123456789"
export GOOGLE_CLOUD_PROJECT_ID="my-music-project"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## 📦 의존성 설치

필요한 Python 패키지 설치:

```bash
pip install -r requirements.txt
```

주요 패키지:
- `google-api-python-client`: YouTube Data API
- `google-cloud-aiplatform`: Vertex AI
- `textblob`: 감성 분석
- `nltk`: 자연어 처리

## 🧪 설정 테스트

### 1단계: 서비스 상태 확인

서버 실행 후 다음 엔드포인트 호출:

```bash
curl http://localhost:5000/api/music-analysis/status
```

**예상 응답:**
```json
{
  "overall_status": "ready",
  "youtube_analyzer": {
    "available": true,
    "api_key_set": true,
    "status": "ready"
  },
  "lyria_client": {
    "available": true,
    "project_id_set": true,
    "status": "ready",
    "connection_test": {
      "success": true,
      "message": "Vertex AI 연결 성공"
    }
  }
}
```

### 2단계: YouTube 분석 테스트

```bash
curl -X POST http://localhost:5000/api/music-analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### 3단계: AI 생성 테스트

```bash
curl -X POST http://localhost:5000/api/music-analysis/generate \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "options": {
      "duration": 30,
      "style": "pop",
      "variations": 1
    }
  }'
```

## 🔒 보안 고려사항

### API 키 보안
- API 키를 코드에 직접 입력하지 마세요
- 환경 변수 또는 보안 설정 파일 사용
- 프로덕션 환경에서는 키 회전 정책 적용

### 서비스 계정 보안
- 서비스 계정 JSON 파일을 안전하게 보관
- 최소 권한 원칙 적용
- 정기적인 권한 검토

### 네트워크 보안
- API 키 IP 제한 설정
- HTTPS 사용 강제
- 방화벽 규칙 적용

## ⚠️ 할당량 및 제한사항

### YouTube Data API v3
- **일일 할당량**: 10,000 units (기본)
- **요청 제한**: 초당 100 요청
- **비용**: 무료 (할당량 내)

### Google Cloud Vertex AI
- **요청 제한**: 분당 60 요청
- **비용**: 사용량에 따라 과금
- **모델 가용성**: 지역별 상이

## 🛠️ 문제 해결

### 일반적인 오류

**1. API 키 관련 오류**
```
Error: API key not valid
```
- 해결: API 키 재확인 및 제한 사항 검토

**2. 권한 오류**
```
Error: User does not have permission
```
- 해결: 서비스 계정 권한 확인

**3. 할당량 초과**
```
Error: Quota exceeded
```
- 해결: 할당량 확인 및 요청 빈도 조절

### 디버깅 팁

1. **로그 확인**: 서버 콘솔에서 상세 로그 확인
2. **API 테스트**: 개별 API 직접 테스트
3. **환경 변수**: 환경 변수 정확한 설정 확인
4. **네트워크**: 방화벽 및 프록시 설정 확인

## 📞 지원

설정 관련 문제가 있으시면:

1. **로그 확인**: 서버 콘솔 로그 검토
2. **문서 참조**: [Google Cloud 문서](https://cloud.google.com/docs)
3. **커뮤니티**: Stack Overflow 또는 GitHub Issues

## 📚 추가 리소스

- [YouTube Data API v3 문서](https://developers.google.com/youtube/v3)
- [Google Cloud Vertex AI 문서](https://cloud.google.com/vertex-ai/docs)
- [Lyria AI 모델 가이드](https://cloud.google.com/vertex-ai/generative-ai/docs/music)

---

**⚡ 빠른 시작 체크리스트:**

- [ ] Google Cloud 프로젝트 생성
- [ ] YouTube Data API v3 활성화
- [ ] API 키 생성
- [ ] Vertex AI 활성화
- [ ] 서비스 계정 생성 및 권한 부여
- [ ] 서비스 계정 키 다운로드
- [ ] .env 파일 생성 및 설정
- [ ] 의존성 설치
- [ ] 서버 실행 및 테스트
- [ ] 서비스 상태 확인

설정 완료 후 `http://localhost:5000/music-analysis`에서 AI 음악 생성 기능을 사용할 수 있습니다!