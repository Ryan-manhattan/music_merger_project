# Google OAuth 빠른 설정 가이드 (배포 사이트 포함)

## 🎯 배포 사이트 정보
- **배포 URL**: https://music-merger-project.onrender.com
- **리다이렉트 URI**: https://music-merger-project.onrender.com/login/google/authorized

## 📋 설정 단계

### 1. Google Cloud Console 접속
https://console.cloud.google.com/apis/credentials

### 2. OAuth 동의 화면 설정 (처음 한 번만)
1. 왼쪽 메뉴: **APIs & Services** > **OAuth consent screen**
2. **External** 선택 → **Create**
3. **App information**:
   - App name: `OFF THE COMMUNITY`
   - User support email: 본인 이메일
   - **Save and Continue**
4. **Scopes**: 기본값 그대로 → **Save and Continue**
5. **Test users**: (선택) → **Save and Continue**
6. **Summary** 확인 → **Back to Dashboard**

### 3. OAuth 클라이언트 ID 생성
1. **APIs & Services** > **Credentials**
2. **+ CREATE CREDENTIALS** > **OAuth client ID**
3. **Application type**: **Web application**
4. **Name**: `off-community-oauth`
5. **Authorized redirect URIs**에 다음 **두 개 모두** 추가:
   ```
   http://localhost:5000/login/google/authorized
   https://music-merger-project.onrender.com/login/google/authorized
   ```
6. **CREATE** 클릭

### 4. 클라이언트 ID와 시크릿 복사
팝업에서:
- **Client ID** 복사
- **Client secret** 복사 (Show 클릭 후)

### 5. Render 환경변수 설정
1. https://dashboard.render.com 접속
2. `music-merger-project` 서비스 선택
3. **Environment** 탭
4. 다음 환경변수 추가:
   ```
   GOOGLE_CLIENT_ID=복사한_클라이언트_ID
   GOOGLE_CLIENT_SECRET=복사한_클라이언트_시크릿
   ```
5. **Save Changes** 클릭
6. 자동 재배포됨 (약 2-3분 소요)

### 6. 로컬 .env 파일 설정 (선택)
로컬에서도 테스트하려면:
```bash
GOOGLE_CLIENT_ID=복사한_클라이언트_ID
GOOGLE_CLIENT_SECRET=복사한_클라이언트_시크릿
```

## ✅ 확인
1. 배포 사이트: https://music-merger-project.onrender.com/login
2. "GOOGLE로 로그인" 버튼 확인
3. 클릭 → Google 로그인 → 정상 리다이렉트 확인

## 🔧 문제 해결

### redirect_uri_mismatch 오류
- Authorized redirect URIs에 정확히 다음이 있는지 확인:
  - `http://localhost:5000/login/google/authorized`
  - `https://music-merger-project.onrender.com/login/google/authorized`
- URL 끝에 `/` 없이 정확히 입력

### access_denied 오류
- OAuth consent screen에서 테스트 사용자로 본인 이메일 추가
- 또는 앱을 "Published" 상태로 변경
