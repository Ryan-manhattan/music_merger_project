-- ============================================
-- Supabase 전체 테이블 생성 스크립트
-- 프로젝트: ilqhifguxtnsrucawgcm
-- 실행: Supabase SQL Editor에서 실행
-- ============================================

-- ============================================
-- 1. posts 테이블 (커뮤니티 게시글)
-- ============================================
CREATE TABLE IF NOT EXISTS posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'Anonymous',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author);

-- ============================================
-- 2. tracks 테이블 (곡 정보)
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

CREATE INDEX IF NOT EXISTS idx_tracks_created_at ON tracks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tracks_source ON tracks(source);
CREATE INDEX IF NOT EXISTS idx_tracks_url ON tracks(url);

-- ============================================
-- 3. track_comments 테이블 (곡 코멘트)
-- ============================================
CREATE TABLE IF NOT EXISTS track_comments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    author TEXT NOT NULL DEFAULT 'Anonymous',
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_track_comments_track_id_created_at
    ON track_comments(track_id, created_at DESC);

-- ============================================
-- 4. users 테이블 (사용자 정보 - Google OAuth)
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

-- ============================================
-- 트리거 함수 생성 (updated_at 자동 업데이트)
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- 트리거 생성
-- ============================================
DROP TRIGGER IF EXISTS update_posts_updated_at ON posts;
CREATE TRIGGER update_posts_updated_at 
    BEFORE UPDATE ON posts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tracks_updated_at ON tracks;
CREATE TRIGGER update_tracks_updated_at
    BEFORE UPDATE ON tracks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_track_comments_updated_at ON track_comments;
CREATE TRIGGER update_track_comments_updated_at
    BEFORE UPDATE ON track_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- RLS (Row Level Security) 설정
-- ============================================

-- posts 테이블 RLS
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read posts" ON posts;
CREATE POLICY "Anyone can read posts" ON posts
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Anyone can insert posts" ON posts;
CREATE POLICY "Anyone can insert posts" ON posts
    FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS "Anyone can update posts" ON posts;
CREATE POLICY "Anyone can update posts" ON posts
    FOR UPDATE
    USING (true);

DROP POLICY IF EXISTS "Anyone can delete posts" ON posts;
CREATE POLICY "Anyone can delete posts" ON posts
    FOR DELETE
    USING (true);

-- tracks 테이블 RLS
ALTER TABLE tracks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read tracks" ON tracks;
CREATE POLICY "Anyone can read tracks" ON tracks
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Anyone can insert tracks" ON tracks;
CREATE POLICY "Anyone can insert tracks" ON tracks
    FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS "Anyone can update tracks" ON tracks;
CREATE POLICY "Anyone can update tracks" ON tracks
    FOR UPDATE
    USING (true);

DROP POLICY IF EXISTS "Anyone can delete tracks" ON tracks;
CREATE POLICY "Anyone can delete tracks" ON tracks
    FOR DELETE
    USING (true);

-- track_comments 테이블 RLS
ALTER TABLE track_comments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read track_comments" ON track_comments;
CREATE POLICY "Anyone can read track_comments" ON track_comments
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Anyone can insert track_comments" ON track_comments;
CREATE POLICY "Anyone can insert track_comments" ON track_comments
    FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS "Anyone can update track_comments" ON track_comments;
CREATE POLICY "Anyone can update track_comments" ON track_comments
    FOR UPDATE
    USING (true);

DROP POLICY IF EXISTS "Anyone can delete track_comments" ON track_comments;
CREATE POLICY "Anyone can delete track_comments" ON track_comments
    FOR DELETE
    USING (true);

-- users 테이블 RLS
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

-- ============================================
-- 5. visitor_logs 테이블 (방문자 로그)
-- ============================================
CREATE TABLE IF NOT EXISTS visitor_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ip_address TEXT,
    user_agent TEXT,
    page_url TEXT,
    referer TEXT,
    visited_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_visitor_logs_visited_at ON visitor_logs(visited_at DESC);
CREATE INDEX IF NOT EXISTS idx_visitor_logs_ip_address ON visitor_logs(ip_address);

-- RLS 설정
ALTER TABLE visitor_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read visitor_logs" ON visitor_logs;
CREATE POLICY "Anyone can read visitor_logs" ON visitor_logs
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Anyone can insert visitor_logs" ON visitor_logs;
CREATE POLICY "Anyone can insert visitor_logs" ON visitor_logs
    FOR INSERT
    WITH CHECK (true);

-- ============================================
-- 완료 메시지
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '✅ 모든 테이블 생성 완료!';
    RAISE NOTICE '생성된 테이블: posts, tracks, track_comments, users, visitor_logs';
END $$;





