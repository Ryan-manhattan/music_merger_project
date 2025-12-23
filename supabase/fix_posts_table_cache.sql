-- posts 테이블 캐시 문제 해결
-- Supabase PostgREST 캐시를 강제로 갱신하기 위한 SQL

-- 1. posts 테이블이 존재하는지 확인하고 없으면 생성
CREATE TABLE IF NOT EXISTS posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'Anonymous',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 인덱스 재생성 (캐시 갱신 유도)
DROP INDEX IF EXISTS idx_posts_created_at;
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);

DROP INDEX IF EXISTS idx_posts_author;
CREATE INDEX idx_posts_author ON posts(author);

-- 3. RLS 정책 재생성
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

-- 4. 트리거 재생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_posts_updated_at ON posts;
CREATE TRIGGER update_posts_updated_at 
    BEFORE UPDATE ON posts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 5. 테이블에 더미 데이터 삽입 후 삭제 (캐시 갱신 유도)
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- 더미 데이터 삽입
    INSERT INTO posts (title, content, author)
    VALUES ('_cache_refresh_test', '_cache_refresh_content', '_cache_refresh_author')
    RETURNING id INTO test_id;
    
    -- 즉시 삭제
    IF test_id IS NOT NULL THEN
        DELETE FROM posts WHERE id = test_id;
    END IF;
END $$;

-- 완료 메시지
SELECT 'posts 테이블 캐시 갱신 완료!' as message;



