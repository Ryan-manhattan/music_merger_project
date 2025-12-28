# tracks 테이블 user_id 추가 가이드

## 📋 변경 사항

로그인한 사용자별로 본인이 추가한 song archive가 구분되도록 `tracks` 테이블에 `user_id` 컬럼을 추가했습니다.

## 🔧 마이그레이션 실행

### 방법 1: Supabase SQL Editor에서 실행 (권장)

1. Supabase 대시보드 접속: https://supabase.com/dashboard/project/ilqhifguxtnsrucawgcm/sql/new
2. `supabase/migrations/20251223000001_add_user_id_to_tracks.sql` 파일 내용 복사
3. SQL Editor에 붙여넣고 실행

### 방법 2: fix_all_tables_cache.sql 사용

모든 테이블 캐시 갱신과 함께 user_id도 추가하려면:
1. `supabase/fix_all_tables_cache.sql` 파일 내용을 SQL Editor에서 실행
2. 이 파일에는 user_id가 포함된 tracks 테이블 정의가 포함되어 있습니다.

## ✅ 변경 내용

1. **tracks 테이블에 user_id 컬럼 추가**
   - `user_id UUID REFERENCES users(id) ON DELETE CASCADE`
   - 기존 데이터는 `user_id = NULL`로 유지 (호환성)

2. **유니크 제약 변경**
   - 기존: `url`만 유니크
   - 변경: `(url, user_id)` 조합으로 유니크
   - 같은 URL이라도 사용자별로 개별 추가 가능

3. **인덱스 추가**
   - `idx_tracks_user_id`: user_id로 빠른 조회

4. **코드 변경**
   - `utils/supabase_client.py`: `create_track()`, `get_tracks()`, `get_track_by_url()`에 `user_id` 파라미터 추가
   - `app.py`: `create_track_api()`에서 `current_user.id` 전달
   - `app.py`: tracks 페이지에서 `current_user.id`로 필터링

## 🎯 동작 방식

- **로그인한 사용자**: 본인이 추가한 tracks만 조회/추가
- **로그인하지 않은 사용자**: `user_id = NULL`인 tracks만 조회 (기존 데이터 호환)
- **중복 방지**: 같은 URL이라도 사용자별로 개별 추가 가능

## 📝 확인 방법

마이그레이션 후 다음 명령어로 확인:

```sql
-- tracks 테이블 구조 확인
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'tracks' AND column_name = 'user_id';

-- user_id별 tracks 개수 확인
SELECT user_id, COUNT(*) as count 
FROM tracks 
GROUP BY user_id;
```





