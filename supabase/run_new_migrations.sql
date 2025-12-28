-- 새로운 마이그레이션만 실행 (기존 테이블/정책은 건너뛰기)

-- ============================================
-- 1. users 테이블 (이미 존재할 수 있음)
-- ============================================
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

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- 트리거 함수가 없으면 생성
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

-- RLS 정책
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can read users" ON users;
CREATE POLICY "Anyone can read users" ON users FOR SELECT USING (true);
DROP POLICY IF EXISTS "Anyone can insert users" ON users;
CREATE POLICY "Anyone can insert users" ON users FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS "Users can update own data" ON users;
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (true);

-- ============================================
-- 2. tracks 테이블에 user_id 추가
-- ============================================
ALTER TABLE tracks 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- 기존 url UNIQUE 제약 제거 (있을 경우)
ALTER TABLE tracks DROP CONSTRAINT IF EXISTS tracks_url_key;

-- (url, user_id) 조합 유니크 인덱스
DROP INDEX IF EXISTS idx_tracks_url_user_id;
CREATE UNIQUE INDEX IF NOT EXISTS idx_tracks_url_user_id 
ON tracks(url, COALESCE(user_id, '00000000-0000-0000-0000-000000000000'::uuid));

-- user_id 인덱스
CREATE INDEX IF NOT EXISTS idx_tracks_user_id ON tracks(user_id);

-- ============================================
-- 3. posts 테이블에 user_id 추가
-- ============================================
ALTER TABLE posts 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- user_id 인덱스
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);

-- 완료 메시지
SELECT '✅ 모든 마이그레이션 완료!' as message;


