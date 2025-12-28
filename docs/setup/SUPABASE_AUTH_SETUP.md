# Supabase Auth로 Google OAuth 설정 가이드

## 📋 전환 완료

Flask-Dance에서 Supabase Auth로 전환했습니다.

## 🔧 Supabase 대시보드 설정

### 1. Supabase 대시보드 접속
https://supabase.com/dashboard/project/ilqhifguxtnsrucawgcm

### 2. Authentication > Providers 설정

1. 왼쪽 메뉴: **Authentication** > **Providers**
2. **Google** 클릭
3. **Enable Google** 토글 활성화
4. **Client ID (for OAuth)** 입력:
   - Google Cloud Console에서 복사한 Client ID
5. **Client Secret (for OAuth)** 입력:
   - Google Cloud Console에서 복사한 Client Secret
6. **Save** 클릭

### 3. Site URL 설정

1. **Authentication** > **URL Configuration**
2. **Site URL** 확인:
   ```
   https://music-merger-project.onrender.com
   ```
3. **Redirect URLs**에 추가:
   ```
   https://music-merger-project.onrender.com/login/google/authorized
   http://localhost:5000/login/google/authorized
   ```

## 🔗 Google Cloud Console 설정

### Authorized redirect URIs 업데이트

1. **Google Cloud Console** 접속:
   https://console.cloud.google.com/apis/credentials

2. **OAuth 2.0 Client ID** 편집

3. **Authorized redirect URIs**에 **Supabase Auth 콜백 URL** 추가:
   ```
   https://ilqhifguxtnsrucawgcm.supabase.co/auth/v1/callback
   ```

   **⚠️ 중요**: 이 URL은 Supabase가 자동으로 생성하는 콜백 URL입니다.

4. 기존 Flask-Dance URL도 유지 (선택):
   ```
   http://localhost:5000/login/google/authorized
   https://music-merger-project.onrender.com/login/google/authorized
   ```

5. **SAVE** 클릭

## 🔄 변경 사항

### 코드 변경
- ✅ Flask-Dance 제거
- ✅ Supabase Auth 클라이언트 추가 (`utils/supabase_auth.py`)
- ✅ Google OAuth 로그인 라우트 변경 (`/login/google`)
- ✅ 콜백 처리 변경 (`/login/google/authorized`)

### 환경변수
- ❌ `GOOGLE_CLIENT_ID` 제거 (Supabase에서 관리)
- ❌ `GOOGLE_CLIENT_SECRET` 제거 (Supabase에서 관리)
- ✅ `SUPABASE_URL` 유지
- ✅ `SUPABASE_KEY` 유지

## ✅ 테스트

1. **로컬 테스트**:
   ```bash
   python3 app.py
   ```
   http://localhost:5000/login 접속

2. **Google 로그인 버튼 클릭**
   - Supabase Auth로 리다이렉트
   - Google 로그인 후 콜백 처리

3. **배포 후 테스트**:
   - https://music-merger-project.onrender.com/login 접속
   - Google 로그인 테스트

## 🔧 문제 해결

### "redirect_uri_mismatch" 오류
- Google Cloud Console의 **Authorized redirect URIs**에 다음이 있는지 확인:
  ```
  https://ilqhifguxtnsrucawgcm.supabase.co/auth/v1/callback
  ```

### Supabase Auth 초기화 실패
- `SUPABASE_URL`과 `SUPABASE_KEY` 환경변수 확인
- Supabase 대시보드에서 Google Provider 활성화 확인

### 로그인 후 콜백 처리 실패
- Supabase 대시보드의 **Redirect URLs**에 콜백 URL 추가 확인
- Render 환경변수 확인

## 📝 참고

- Supabase Auth는 클라이언트 사이드에서도 사용 가능
- 현재는 서버 사이드에서 토큰을 받아 Flask-Login과 통합
- 향후 클라이언트 사이드로 전환 가능


