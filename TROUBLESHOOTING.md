# 문제 해결 가이드

## 🔴 Supabase 401 오류 해결

### 오류 메시지
```
[ERROR] Supabase 게시글 조회 실패: {'message': 'JSON could not be generated', 'code': 401, 'hint': 'Refer to full message for details', 'details': 'b\'{"message":"Invalid API key"}\''}
```

### 원인
1. **API 키가 잘못되었거나 만료됨**
2. **서버가 이전 환경변수를 캐시하고 있음**
3. **배포 환경에서 환경변수가 설정되지 않음**

### 해결 방법

#### 1. 로컬 환경
```bash
# 1. 서버 재시작
pkill -f "python3 app.py"
python3 app.py

# 2. 환경변수 확인
cat .env | grep SUPABASE
```

#### 2. Supabase API 키 확인
1. Supabase 대시보드 접속:
   https://supabase.com/dashboard/project/ycmeslqlgijckhukfkcd/settings/api

2. **Project API keys** 섹션에서:
   - **anon public** 키 확인
   - 키가 변경되었다면 `.env` 파일 업데이트

3. `.env` 파일 업데이트:
   ```bash
   SUPABASE_URL=https://ycmeslqlgijckhukfkcd.supabase.co
   SUPABASE_KEY=<새로운_anon_key>
   ```

#### 3. Render 배포 환경
1. Render 대시보드 접속
2. 서비스 → Environment 탭
3. 다음 환경변수 확인:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
4. 값이 올바른지 확인하고 서비스 재배포

### 테스트
```bash
python3 -c "from utils.supabase_client import SupabaseClient; client = SupabaseClient(); print('✅ 연결 성공!' if client.test_connection() else '❌ 연결 실패')"
```

## 기타 문제

### posts 테이블이 없다는 오류
```sql
-- Supabase SQL Editor에서 실행
CREATE TABLE IF NOT EXISTS posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'Anonymous',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 서버가 시작되지 않음
- 포트 5000이 사용 중인지 확인
- 다른 포트 사용: `PORT=5001 python3 app.py`



