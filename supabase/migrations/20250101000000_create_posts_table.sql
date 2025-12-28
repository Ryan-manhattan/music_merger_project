-- Supabase 마이그레이션 파일
-- 커뮤니티 게시글 테이블 생성

-- posts 테이블 생성
CREATE TABLE IF NOT EXISTS posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'Anonymous',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author);

-- updated_at 자동 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- updated_at 자동 업데이트 트리거
DROP TRIGGER IF EXISTS update_posts_updated_at ON posts;
CREATE TRIGGER update_posts_updated_at 
    BEFORE UPDATE ON posts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) 정책 설정 (선택사항)
-- 모든 사용자가 읽기 가능
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read posts" ON posts
    FOR SELECT
    USING (true);

-- 모든 사용자가 게시글 작성 가능
DROP POLICY IF EXISTS "Anyone can insert posts" ON posts;
CREATE POLICY "Anyone can insert posts" ON posts
    FOR INSERT
    WITH CHECK (true);

-- 모든 사용자가 게시글 수정 가능 (실제 운영 시에는 인증 추가 권장)
DROP POLICY IF EXISTS "Anyone can update posts" ON posts;
CREATE POLICY "Anyone can update posts" ON posts
    FOR UPDATE
    USING (true);

-- 모든 사용자가 게시글 삭제 가능 (실제 운영 시에는 인증 추가 권장)
DROP POLICY IF EXISTS "Anyone can delete posts" ON posts;
CREATE POLICY "Anyone can delete posts" ON posts
    FOR DELETE
    USING (true);








