# Render 환경변수 설정 가이드

## 🚀 Google OAuth 환경변수 추가

### Render 대시보드에서 설정

1. **Render 대시보드 접속**
   - https://dashboard.render.com

2. **서비스 선택**
   - `music-merger-project` 서비스 클릭

3. **Environment 탭 이동**
   - 왼쪽 메뉴에서 **Environment** 클릭

4. **환경변수 추가**
   다음 두 개의 환경변수를 추가:

   ```
   Key: GOOGLE_CLIENT_ID
   Value: (Google Cloud Console에서 생성한 클라이언트 ID)
   ```

   ```
   Key: GOOGLE_CLIENT_SECRET
   Value: (Google Cloud Console에서 생성한 클라이언트 시크릿)
   ```
   
   **참고**: 실제 값은 Google Cloud Console에서 생성한 OAuth 클라이언트의 Client ID와 Client Secret을 사용하세요.

5. **Save Changes 클릭**
   - 자동으로 재배포가 시작됩니다 (약 2-3분 소요)

### ⚠️ 중요: 리다이렉트 URI 수정 필요

Google Cloud Console에서 리다이렉트 URI를 다음으로 수정해야 합니다:

1. https://console.cloud.google.com/apis/credentials 접속
2. 생성한 OAuth 클라이언트 클릭 (편집)
3. **승인된 리디렉션 URI** 섹션에서:
   - 기존: `http://localhost:5000/login/` 
   - 수정: `http://localhost:5000/login/google/authorized`
   
   - 기존: `https://music-merger-project.onrender.com/login/`
   - 수정: `https://music-merger-project.onrender.com/login/google/authorized`

4. **저장** 클릭

### ✅ 확인

재배포 완료 후:
1. https://music-merger-project.onrender.com/login 접속
2. "GOOGLE로 로그인" 버튼 확인
3. 클릭 → Google 로그인 → 정상 작동 확인



