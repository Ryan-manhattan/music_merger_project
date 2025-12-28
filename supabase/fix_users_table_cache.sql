-- users 테이블 캐시 문제 해결
-- Supabase PostgREST 캐시를 강제로 갱신하기 위한 SQL

-- 1. 테이블이 존재하는지 확인하고 없으면 생성
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    google_id TEXT UNIQUE,
    picture TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- 2. 인덱스 재생성 (캐시 갱신 유도)
DROP INDEX IF EXISTS idx_users_username;
CREATE INDEX idx_users_username ON users(username);

DROP INDEX IF EXISTS idx_users_email;
CREATE INDEX idx_users_email ON users(email);

DROP INDEX IF EXISTS idx_users_google_id;
CREATE INDEX idx_users_google_id ON users(google_id);

-- 3. RLS 정책 재생성
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read users" ON users;
CREATE POLICY "Anyone can read users" ON users
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Anyone can insert users" ON users;
CREATE POLICY "Anyone can insert users" ON users
    FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own data" ON users;
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE
    USING (true);

-- 4. 트리거 재생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 5. 테이블에 더미 데이터 삽입 후 삭제 (캐시 갱신 유도)
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- 더미 데이터 삽입
    INSERT INTO users (username, email, password_hash)
    VALUES ('_cache_refresh_test', '_cache@test.com', 'test')
    ON CONFLICT (email) DO NOTHING
    RETURNING id INTO test_id;
    
    -- 즉시 삭제
    IF test_id IS NOT NULL THEN
        DELETE FROM users WHERE id = test_id;
    END IF;
END $$;

-- 완료 메시지
SELECT 'users 테이블 캐시 갱신 완료!' as message;





