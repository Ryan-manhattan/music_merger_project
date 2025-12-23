# users 테이블 캐시 문제 해결 가이드

## 🔴 문제
users 테이블을 생성했는데도 "Could not find the table 'public.users' in the schema cache" 오류 발생

## 🔧 해결 방법

### 방법 1: Supabase 서비스 재시작 (가장 빠름)
1. Supabase 대시보드: https://supabase.com/dashboard/project/ilqhifguxtnsrucawgcm
2. **Settings** → **General**
3. **Restart Project** 클릭
4. 몇 분 대기 후 다시 시도

### 방법 2: 캐시 갱신 SQL 실행
1. SQL Editor 접속: https://supabase.com/dashboard/project/ilqhifguxtnsrucawgcm/sql/new
2. `supabase/fix_users_table_cache.sql` 파일 내용 복사
3. 실행
4. 1-2분 대기 후 다시 시도

### 방법 3: Table Editor에서 확인
1. Table Editor 접속: https://supabase.com/dashboard/project/ilqhifguxtnsrucawgcm/editor
2. 왼쪽에서 `users` 테이블이 보이는지 확인
3. 보이면 테이블은 정상 생성됨 (캐시 문제)
4. 안 보이면 테이블 생성 SQL 다시 실행

## ✅ 확인
다음 명령어로 확인:
```bash
python3 -c "from utils.supabase_client import SupabaseClient; c = SupabaseClient(); c.client.table('users').select('*').limit(1).execute(); print('✅ 성공!')"
```



