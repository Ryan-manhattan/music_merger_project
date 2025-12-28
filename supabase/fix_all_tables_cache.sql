-- 모든 테이블 캐시 문제 일괄 해결
-- Supabase PostgREST 캐시를 강제로 갱신하기 위한 SQL
-- 실행: Supabase SQL Editor에서 실행

-- ============================================
-- 1. tracks 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS tracks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    source_id TEXT,
    title TEXT NOT NULL,
    artist TEXT,
    duration_seconds INTEGER,
    thumbnail_url TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP INDEX IF EXISTS idx_tracks_created_at;
CREATE INDEX idx_tracks_created_at ON tracks(created_at DESC);
DROP INDEX IF EXISTS idx_tracks_source;
CREATE INDEX idx_tracks_source ON tracks(source);
DROP INDEX IF EXISTS idx_tracks_url;
CREATE INDEX idx_tracks_url ON tracks(url);
DROP INDEX IF EXISTS idx_tracks_user_id;
CREATE INDEX idx_tracks_user_id ON tracks(user_id);

ALTER TABLE tracks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can read tracks" ON tracks;
CREATE POLICY "Anyone can read tracks" ON tracks FOR SELECT USING (true);
DROP POLICY IF EXISTS "Anyone can insert tracks" ON tracks;
CREATE POLICY "Anyone can insert tracks" ON tracks FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS "Anyone can update tracks" ON tracks;
CREATE POLICY "Anyone can update tracks" ON tracks FOR UPDATE USING (true);
DROP POLICY IF EXISTS "Anyone can delete tracks" ON tracks;
CREATE POLICY "Anyone can delete tracks" ON tracks FOR DELETE USING (true);

-- ============================================
-- 2. users 테이블
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

DROP INDEX IF EXISTS idx_users_username;
CREATE INDEX idx_users_username ON users(username);
DROP INDEX IF EXISTS idx_users_email;
CREATE INDEX idx_users_email ON users(email);
DROP INDEX IF EXISTS idx_users_google_id;
CREATE INDEX idx_users_google_id ON users(google_id);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can read users" ON users;
CREATE POLICY "Anyone can read users" ON users FOR SELECT USING (true);
DROP POLICY IF EXISTS "Anyone can insert users" ON users;
CREATE POLICY "Anyone can insert users" ON users FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS "Users can update own data" ON users;
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (true);

-- ============================================
-- 3. posts 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'Anonymous',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP INDEX IF EXISTS idx_posts_created_at;
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
DROP INDEX IF EXISTS idx_posts_author;
CREATE INDEX idx_posts_author ON posts(author);

ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can read posts" ON posts;
CREATE POLICY "Anyone can read posts" ON posts FOR SELECT USING (true);
DROP POLICY IF EXISTS "Anyone can insert posts" ON posts;
CREATE POLICY "Anyone can insert posts" ON posts FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS "Anyone can update posts" ON posts;
CREATE POLICY "Anyone can update posts" ON posts FOR UPDATE USING (true);
DROP POLICY IF EXISTS "Anyone can delete posts" ON posts;
CREATE POLICY "Anyone can delete posts" ON posts FOR DELETE USING (true);

-- ============================================
-- 4. track_comments 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS track_comments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    author TEXT NOT NULL DEFAULT 'Anonymous',
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP INDEX IF EXISTS idx_track_comments_track_id_created_at;
CREATE INDEX idx_track_comments_track_id_created_at ON track_comments(track_id, created_at DESC);

ALTER TABLE track_comments ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can read track_comments" ON track_comments;
CREATE POLICY "Anyone can read track_comments" ON track_comments FOR SELECT USING (true);
DROP POLICY IF EXISTS "Anyone can insert track_comments" ON track_comments;
CREATE POLICY "Anyone can insert track_comments" ON track_comments FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS "Anyone can update track_comments" ON track_comments;
CREATE POLICY "Anyone can update track_comments" ON track_comments FOR UPDATE USING (true);
DROP POLICY IF EXISTS "Anyone can delete track_comments" ON track_comments;
CREATE POLICY "Anyone can delete track_comments" ON track_comments FOR DELETE USING (true);

-- ============================================
-- 5. visitor_logs 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS visitor_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ip_address TEXT,
    user_agent TEXT,
    page_url TEXT,
    referer TEXT,
    visited_at TIMESTAMPTZ DEFAULT NOW()
);

DROP INDEX IF EXISTS idx_visitor_logs_visited_at;
CREATE INDEX idx_visitor_logs_visited_at ON visitor_logs(visited_at DESC);
DROP INDEX IF EXISTS idx_visitor_logs_ip_address;
CREATE INDEX idx_visitor_logs_ip_address ON visitor_logs(ip_address);

ALTER TABLE visitor_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can read visitor_logs" ON visitor_logs;
CREATE POLICY "Anyone can read visitor_logs" ON visitor_logs FOR SELECT USING (true);
DROP POLICY IF EXISTS "Anyone can insert visitor_logs" ON visitor_logs;
CREATE POLICY "Anyone can insert visitor_logs" ON visitor_logs FOR INSERT WITH CHECK (true);

-- ============================================
-- 트리거 함수 및 트리거
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_tracks_updated_at ON tracks;
CREATE TRIGGER update_tracks_updated_at BEFORE UPDATE ON tracks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_posts_updated_at ON posts;
CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON posts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_track_comments_updated_at ON track_comments;
CREATE TRIGGER update_track_comments_updated_at BEFORE UPDATE ON track_comments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 캐시 갱신을 위한 더미 데이터 삽입/삭제
-- ============================================
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- tracks 테이블
    INSERT INTO tracks (url, source, title)
    VALUES ('_cache_refresh_tracks', 'test', '_cache_refresh')
    ON CONFLICT (url) DO NOTHING
    RETURNING id INTO test_id;
    IF test_id IS NOT NULL THEN DELETE FROM tracks WHERE id = test_id; END IF;
    
    -- users 테이블
    INSERT INTO users (username, email, password_hash)
    VALUES ('_cache_refresh_user', '_cache_user@test.com', 'test')
    ON CONFLICT (email) DO NOTHING
    RETURNING id INTO test_id;
    IF test_id IS NOT NULL THEN DELETE FROM users WHERE id = test_id; END IF;
    
    -- posts 테이블
    INSERT INTO posts (title, content, author)
    VALUES ('_cache_refresh_post', '_cache_refresh_content', '_cache_refresh_author')
    RETURNING id INTO test_id;
    IF test_id IS NOT NULL THEN DELETE FROM posts WHERE id = test_id; END IF;
    
    -- track_comments 테이블 (tracks 테이블이 있어야 하므로 tracks 먼저 확인)
    -- tracks에 임시 데이터가 있으면 comments도 테스트
    INSERT INTO tracks (url, source, title)
    VALUES ('_cache_refresh_tracks_for_comments', 'test', '_cache_refresh')
    ON CONFLICT (url) DO NOTHING
    RETURNING id INTO test_id;
    
    IF test_id IS NOT NULL THEN
        -- track_comments 테스트
        DECLARE
            comment_id UUID;
        BEGIN
            INSERT INTO track_comments (track_id, author, content)
            VALUES (test_id, '_cache_refresh', '_cache_refresh_comment')
            RETURNING id INTO comment_id;
            IF comment_id IS NOT NULL THEN DELETE FROM track_comments WHERE id = comment_id; END IF;
        END;
        DELETE FROM tracks WHERE id = test_id;
    END IF;
    
    -- visitor_logs 테이블
    INSERT INTO visitor_logs (ip_address, page_url)
    VALUES ('_cache_refresh', '_cache_refresh')
    RETURNING id INTO test_id;
    IF test_id IS NOT NULL THEN DELETE FROM visitor_logs WHERE id = test_id; END IF;
END $$;

-- 완료 메시지
SELECT '✅ 모든 테이블 캐시 갱신 완료!' as message;





