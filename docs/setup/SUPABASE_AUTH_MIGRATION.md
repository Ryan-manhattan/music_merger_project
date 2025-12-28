# Supabase Auth로 Google OAuth 전환 가이드

## 📋 현재 상황

**현재 구현:**
- Flask-Dance로 Google OAuth 직접 처리
- Flask-Login으로 세션 관리
- Supabase는 데이터베이스로만 사용

**Supabase Auth 장점:**
- Supabase 대시보드에서 OAuth 설정 관리
- 자동 세션 관리 및 토큰 갱신
- RLS 정책과 자연스러운 통합
- 더 간단한 코드

## 🔄 전환 옵션

### 옵션 1: Supabase Auth로 완전 전환 (권장)

**장점:**
- Supabase가 OAuth 플로우 전체 관리
- 세션/토큰 자동 관리
- RLS 정책 활용 용이
- 코드 단순화

**단점:**
- 기존 코드 대폭 수정 필요
- Supabase Auth 세션 방식으로 변경

### 옵션 2: 현재 방식 유지 + Supabase Auth 병행

**장점:**
- 기존 코드 최소 변경
- 점진적 전환 가능

**단점:**
- 두 가지 인증 시스템 병행
- 복잡도 증가

## 🚀 Supabase Auth 설정 방법

### 1. Supabase 대시보드에서 Google OAuth 설정

1. **Supabase 대시보드 접속**
   https://supabase.com/dashboard/project/ilqhifguxtnsrucawgcm

2. **Authentication > Providers** 이동

3. **Google** 클릭하여 활성화

4. **Google OAuth 설정:**
   - **Client ID (for OAuth)**: Google Cloud Console에서 복사한 Client ID
   - **Client Secret (for OAuth)**: Google Cloud Console에서 복사한 Client Secret
   - **Authorized Client IDs**: (선택) 추가 클라이언트 ID

5. **Redirect URLs 확인:**
   Supabase가 자동으로 생성하는 리다이렉트 URL:
   ```
   https://ilqhifguxtnsrucawgcm.supabase.co/auth/v1/callback
   ```
   이 URL을 Google Cloud Console의 **Authorized redirect URIs**에 추가해야 합니다.

### 2. Google Cloud Console 설정 업데이트

1. **Google Cloud Console 접속**
   https://console.cloud.google.com/apis/credentials

2. **OAuth 2.0 Client ID 편집**

3. **Authorized redirect URIs**에 추가:
   ```
   https://ilqhifguxtnsrucawgcm.supabase.co/auth/v1/callback
   ```

### 3. 코드 변경 (옵션 1 선택 시)

Supabase Auth를 사용하려면:
- `app.py`에서 Flask-Dance 제거
- Supabase Auth 클라이언트 사용
- 세션 관리를 Supabase Auth로 변경

## 💡 추천

**현재 상황에서는 옵션 2 (현재 방식 유지)를 추천합니다:**

1. **이미 구현 완료**: Flask-Dance로 Google OAuth가 작동 중
2. **안정성**: 검증된 방식
3. **유연성**: Flask-Login으로 세션 관리 가능

**Supabase Auth로 전환하는 경우:**
- 새로운 프로젝트 시작 시
- RLS 정책을 적극 활용할 때
- Supabase의 다른 Auth 기능이 필요할 때

## 🔧 현재 방식 개선 (권장)

현재 Flask-Dance 방식에서 발생한 500 오류는 이미 수정했습니다:
- `user_id` 문자열 변환
- 에러 핸들링 개선

배포 후 정상 작동할 것으로 예상됩니다.

## ❓ 선택

어떤 방식을 원하시나요?

1. **현재 방식 유지** (Flask-Dance) - 이미 구현됨, 배포 후 테스트
2. **Supabase Auth로 전환** - 코드 대폭 수정 필요, 새로 구현



