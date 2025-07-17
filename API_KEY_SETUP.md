# 🔑 API 키 설정 가이드

## 📋 필수 설정 항목

### 1. YouTube Data API v3 키 설정
```bash
YOUTUBE_API_KEY=AIzaSyExample123456789
```

### 2. Google Cloud 프로젝트 설정
```bash
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## 🚀 빠른 설정 단계

### 1단계: Google Cloud Console 접속
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성 또는 기존 프로젝트 선택

### 2단계: YouTube Data API v3 활성화
1. **APIs & Services** → **Library** 이동
2. **YouTube Data API v3** 검색 후 활성화
3. **Credentials** → **Create Credentials** → **API Key** 선택
4. 생성된 키를 `.env` 파일의 `YOUTUBE_API_KEY`에 입력

### 3단계: Vertex AI 설정
1. **Vertex AI** 검색 후 활성화
2. **IAM & Admin** → **Service Accounts** 이동
3. **Create Service Account** 클릭
4. 다음 권한 부여:
   - `Vertex AI User`
   - `Storage Object Admin`
5. **Keys** → **Add Key** → **Create New Key** (JSON 형식)
6. 다운로드한 JSON 파일을 프로젝트 폴더에 저장
7. 파일 경로를 `.env`의 `GOOGLE_APPLICATION_CREDENTIALS`에 입력

## ⚠️ 주의사항

1. **API 키 보안**
   - `.env` 파일을 Git에 커밋하지 마세요
   - API 키는 절대 공개하지 마세요

2. **권한 설정**
   - API 키에 IP 제한 설정 권장
   - 서비스 계정 최소 권한 원칙 적용

3. **비용 관리**
   - YouTube API 할당량 확인 (일일 10,000 units)
   - Vertex AI 사용량 모니터링

## 🔧 설정 완료 후 확인

`.env` 파일이 다음과 같이 설정되어야 합니다:

```bash
# YouTube Data API v3 설정
YOUTUBE_API_KEY=AIzaSyExample123456789

# Google Cloud 설정
GOOGLE_CLOUD_PROJECT_ID=my-music-project
GOOGLE_APPLICATION_CREDENTIALS=/Users/username/music_merger_project/service-account-key.json
```

## 📞 문제 해결

설정 중 문제가 발생하면:
1. API_SETUP_GUIDE.md 참조
2. 환경 변수 검증 스크립트 실행
3. 서비스 상태 확인 API 호출