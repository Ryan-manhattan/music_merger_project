# Google OAuth 2.0 설정 가이드

## 🚀 빠른 설정 (5분)

### 1. Google Cloud Console 접속 및 로그인
1. https://console.cloud.google.com/ 접속
2. Google 계정으로 로그인

### 2. 프로젝트 선택/생성
1. 상단 프로젝트 선택 드롭다운 클릭
2. 기존 프로젝트 선택 또는 **새 프로젝트** 생성
   - 프로젝트 이름: `off-community` (또는 원하는 이름)
   - 생성 버튼 클릭

### 3. OAuth 동의 화면 설정
1. 왼쪽 메뉴: **APIs & Services** > **OAuth consent screen**
2. **User Type** 선택:
   - **External** (일반 사용자용) 선택
   - **Create** 클릭
3. **App information** 입력:
   - App name: `OFF THE COMMUNITY`
   - User support email: 본인 이메일
   - App logo: (선택사항)
   - **Save and Continue** 클릭
4. **Scopes** 설정:
   - **Add or Remove Scopes** 클릭
   - 다음 스코프 추가:
     - `.../auth/userinfo.email`
     - `.../auth/userinfo.profile`
   - **Update** 클릭
   - **Save and Continue** 클릭
5. **Test users** (선택사항):
   - 테스트 사용자 이메일 추가 (선택)
   - **Save and Continue** 클릭
6. **Summary** 확인 후 **Back to Dashboard** 클릭

### 4. OAuth 2.0 클라이언트 ID 생성
1. 왼쪽 메뉴: **APIs & Services** > **Credentials**
2. 상단 **+ CREATE CREDENTIALS** 클릭
3. **OAuth client ID** 선택
4. **Application type**: **Web application** 선택
5. **Name**: `off-community-web-client` (또는 원하는 이름)
6. **Authorized redirect URIs** 추가:
   ```
   http://localhost:5000/login/google/authorized
   https://music-merger-project.onrender.com/login/google/authorized
   ```
   (로컬 개발용과 Render 배포용 URL 모두 추가)
   
   **⚠️ 중요**: 두 URL 모두 정확히 입력해야 합니다!
7. **CREATE** 클릭

### 5. 클라이언트 ID와 시크릿 복사
생성 후 팝업에서:
- **Client ID** 복사
- **Client secret** 복사 (Show 버튼 클릭 후 복사)

### 6. 환경변수 설정
`.env` 파일에 추가:
```bash
GOOGLE_CLIENT_ID=복사한_클라이언트_ID
GOOGLE_CLIENT_SECRET=복사한_클라이언트_시크릿
```

또는 Render 배포 환경에서:
1. Render 대시보드: https://dashboard.render.com
2. 서비스 선택 → Environment 탭
3. 다음 환경변수 추가:
   - Key: `GOOGLE_CLIENT_ID` → Value: (복사한 클라이언트 ID)
   - Key: `GOOGLE_CLIENT_SECRET` → Value: (복사한 클라이언트 시크릿)
4. **Save Changes** 클릭
5. 서비스 자동 재배포됨

### 7. 서버 재시작
```bash
python3 app.py
```

## ✅ 완료 확인
1. http://localhost:5000/login 접속
2. "GOOGLE로 로그인" 버튼이 표시되는지 확인
3. 클릭 시 Google 로그인 페이지로 이동하는지 확인

## 🔧 문제 해결

### "redirect_uri_mismatch" 오류
- Authorized redirect URIs에 정확한 URL이 추가되었는지 확인
- 로컬: `http://localhost:5000/login/google/authorized`
- 배포: `https://your-domain.com/login/google/authorized`

### "access_denied" 오류
- OAuth consent screen에서 테스트 사용자로 등록되었는지 확인
- 또는 앱을 "Published" 상태로 변경 (프로덕션 환경)

## 📝 배포 사이트 설정 (Render)

### Render 서비스 URL 확인
1. Render 대시보드 접속: https://dashboard.render.com
2. 서비스 선택
3. **Settings** 탭에서 **Service URL** 확인
   - 예: `https://off-community.onrender.com`

### Google OAuth 리다이렉트 URI 설정
Google Cloud Console의 OAuth 클라이언트 설정에서:
- **Authorized redirect URIs**에 다음 추가:
  ```
  http://localhost:5000/login/google/authorized
  https://music-merger-project.onrender.com/login/google/authorized
  ```
  **두 URL 모두 추가해야 합니다!**

### Render 환경변수 설정
1. Render 대시보드 → 서비스 → **Environment** 탭
2. 다음 환경변수 추가:
   - `GOOGLE_CLIENT_ID`: Google OAuth 클라이언트 ID
   - `GOOGLE_CLIENT_SECRET`: Google OAuth 클라이언트 시크릿
3. **Save Changes** 클릭
4. 서비스가 자동으로 재배포됨

### 배포 후 확인
1. 배포된 사이트 접속: https://music-merger-project.onrender.com/login
2. "GOOGLE로 로그인" 버튼 클릭
3. Google 로그인 후 정상적으로 리다이렉트되는지 확인

## 📝 참고
- 로컬 개발: `http://localhost:5000/login/google/authorized`
- Render 배포: `https://music-merger-project.onrender.com/login/google/authorized`
