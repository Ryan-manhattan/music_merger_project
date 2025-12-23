# Google OAuth 리다이렉트 URI 설정 가이드

## 📍 설정 위치

**Google Cloud Console**에서 설정합니다.

## 🔗 접속 링크

1. **Google Cloud Console**: https://console.cloud.google.com/apis/credentials
2. 또는: https://console.cloud.google.com → **APIs & Services** > **Credentials**

## 📝 설정 방법

### 1. OAuth 클라이언트 ID 찾기

1. **Credentials** 페이지에서
2. **OAuth 2.0 Client IDs** 섹션 찾기
3. 기존 클라이언트 ID가 있으면 **편집 아이콘 (연필)** 클릭
4. 없으면 **+ CREATE CREDENTIALS** > **OAuth client ID** 클릭

### 2. Authorized redirect URIs 추가

**Authorized redirect URIs** 섹션에서 다음 URL들을 추가:

```
http://localhost:5000/login/google/authorized
https://music-merger-project.onrender.com/login/google/authorized
```

**⚠️ 중요:**
- URL 끝에 `/` 없이 정확히 입력
- 두 URL 모두 추가 (로컬 개발용 + 배포용)
- 대소문자 구분

### 3. 저장

1. **SAVE** 또는 **UPDATE** 클릭
2. 변경사항이 즉시 적용됨 (재배포 불필요)

## 🎯 현재 프로젝트 리다이렉트 URI

현재 Flask-Dance를 사용하므로:
- **로컬**: `http://localhost:5000/login/google/authorized`
- **배포**: `https://music-merger-project.onrender.com/login/google/authorized`

## ✅ 확인 방법

1. Google Cloud Console에서 **OAuth client ID** 편집
2. **Authorized redirect URIs** 섹션 확인
3. 위 두 URL이 정확히 있는지 확인

## 🔧 문제 해결

### "redirect_uri_mismatch" 오류 발생 시

1. **Authorized redirect URIs**에 정확한 URL이 있는지 확인
2. URL 끝에 `/` 없이 입력했는지 확인
3. 대소문자 정확히 입력했는지 확인
4. 변경 후 몇 분 기다린 후 다시 시도

### URL 수정 방법

1. Google Cloud Console → **Credentials**
2. OAuth 클라이언트 ID **편집**
3. **Authorized redirect URIs** 섹션에서:
   - 잘못된 URL 삭제
   - 올바른 URL 추가
4. **SAVE** 클릭

## 📸 스크린샷 위치

Google Cloud Console에서:
```
APIs & Services
  └─ Credentials
      └─ OAuth 2.0 Client IDs
          └─ [클라이언트 ID 편집]
              └─ Authorized redirect URIs ← 여기!
```

