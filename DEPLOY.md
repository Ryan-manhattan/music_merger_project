# 배포 가이드

## 🚀 Render 배포

### 1. Git 저장소 준비

```bash
# 변경사항 커밋
git add .
git commit -m "배포 준비: 커뮤니티 기능 추가"
git push origin master
```

### 2. Render 대시보드 설정

1. **Render 대시보드 접속**: https://dashboard.render.com
2. **새 Web Service 생성** 또는 **기존 서비스 업데이트**
3. **GitHub 저장소 연결**

### 3. 환경변수 설정

Render 대시보드에서 다음 환경변수를 설정하세요:

#### 필수 환경변수
```
SUPABASE_URL=https://ilqhifguxtnsrucawgcm.supabase.co
SUPABASE_KEY=sb_publishable_3T468Q9xGIudxuYL-tuGOg_q2eK8ufb
```

#### 선택적 환경변수 (기능별)
```
# YouTube API
YOUTUBE_API_KEY=AIzaSyC56v9gGaWoU-GsDKFYvp3jguUB-SIY-Ds

# Google Cloud
GOOGLE_CLOUD_PROJECT_ID=pelagic-sorter-457711-n6
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS_JSON={...}

# Google OAuth (로그인 기능)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# OpenAI
OPENAI_API_KEY=...

# Spotify (선택)
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...

# Reddit (선택)
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=MusicTrendAnalyzer/1.0
```

### 4. 배포 설정

- **Build Command**: `./scripts/build.sh`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
- **Python Version**: 3.11.9

### 5. 배포 확인

배포 완료 후:
- 서비스 URL 확인
- 커뮤니티 페이지 접속 테스트
- 글쓰기 기능 테스트

## 📝 주의사항

1. **데이터베이스**: Supabase에 posts 테이블이 생성되어 있어야 합니다
2. **환경변수**: .env 파일의 내용을 Render 환경변수에 설정해야 합니다
3. **디스크**: 파일 업로드를 위한 디스크가 마운트되어 있습니다

## 🔧 문제 해결

### 배포 실패 시
1. Render 로그 확인
2. 환경변수 설정 확인
3. requirements.txt 의존성 확인

### Supabase 연결 실패 시
1. SUPABASE_URL과 SUPABASE_KEY 확인
2. Supabase 대시보드에서 posts 테이블 존재 확인
3. RLS 정책 확인


