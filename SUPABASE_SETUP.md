# Supabase 테이블 설정 가이드

## 🚀 빠른 설정

### 1. Supabase SQL Editor에서 실행

1. [Supabase 대시보드](https://supabase.com/dashboard/project/ilqhifguxtnsrucawgcm) 접속
2. 왼쪽 메뉴에서 **SQL Editor** 클릭
3. **New query** 클릭
4. `supabase/setup_all_tables.sql` 파일의 내용을 복사하여 붙여넣기
5. **Run** 버튼 클릭

### 2. 생성되는 테이블

- ✅ **posts** - 커뮤니티 게시글
- ✅ **tracks** - 곡 정보 (SoundCloud, YouTube 등)
- ✅ **track_comments** - 곡별 감상 코멘트
- ✅ **users** - 사용자 정보 (Google OAuth)

### 3. 테이블 확인

SQL Editor에서 다음 쿼리로 확인:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('posts', 'tracks', 'track_comments', 'users')
ORDER BY table_name;
```

## 📋 테이블 구조

### posts (커뮤니티 게시글)
- `id` - UUID (Primary Key)
- `title` - 제목
- `content` - 내용
- `author` - 작성자
- `created_at` - 생성일시
- `updated_at` - 수정일시

### tracks (곡 정보)
- `id` - UUID (Primary Key)
- `url` - 곡 URL (Unique)
- `source` - 출처 (soundcloud, youtube 등)
- `source_id` - 출처 ID
- `title` - 제목
- `artist` - 아티스트
- `duration_seconds` - 길이(초)
- `thumbnail_url` - 썸네일 URL
- `metadata` - JSONB 메타데이터
- `created_at` - 생성일시
- `updated_at` - 수정일시

### track_comments (곡 코멘트)
- `id` - UUID (Primary Key)
- `track_id` - 곡 ID (Foreign Key)
- `author` - 작성자
- `content` - 내용
- `created_at` - 생성일시
- `updated_at` - 수정일시

### users (사용자 정보)
- `id` - UUID (Primary Key)
- `username` - 사용자명 (Unique)
- `email` - 이메일 (Unique)
- `password_hash` - 비밀번호 해시 (선택)
- `google_id` - Google OAuth ID (Unique)
- `picture` - 프로필 사진 URL
- `created_at` - 생성일시
- `updated_at` - 수정일시
- `last_login` - 마지막 로그인

## 🔒 RLS (Row Level Security)

모든 테이블에 RLS가 활성화되어 있으며, 현재는 모든 사용자가 읽기/쓰기 가능하도록 설정되어 있습니다.

실제 운영 시에는 인증 기반으로 정책을 수정하는 것을 권장합니다.

## ✅ 설정 완료 확인

모든 테이블이 정상적으로 생성되었는지 확인:

```sql
-- 테이블 목록 확인
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- 각 테이블의 컬럼 확인
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'posts';
```
