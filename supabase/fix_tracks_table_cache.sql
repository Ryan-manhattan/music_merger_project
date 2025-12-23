-- tracks 테이블 캐시 문제 해결
-- Supabase PostgREST 캐시를 강제로 갱신하기 위한 SQL

-- 1. tracks 테이블이 존재하는지 확인하고 없으면 생성
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

-- 2. 인덱스 재생성 (캐시 갱신 유도)
DROP INDEX IF EXISTS idx_tracks_created_at;
CREATE INDEX idx_tracks_created_at ON tracks(created_at DESC);

DROP INDEX IF EXISTS idx_tracks_source;
CREATE INDEX idx_tracks_source ON tracks(source);

DROP INDEX IF EXISTS idx_tracks_url;
CREATE INDEX idx_tracks_url ON tracks(url);

-- 3. RLS 정책 재생성
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

-- 4. 트리거 재생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_tracks_updated_at ON tracks;
CREATE TRIGGER update_tracks_updated_at 
    BEFORE UPDATE ON tracks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 5. 테이블에 더미 데이터 삽입 후 삭제 (캐시 갱신 유도)
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- 더미 데이터 삽입
    INSERT INTO tracks (url, source, title)
    VALUES ('_cache_refresh_test_url', 'test', '_cache_refresh_test')
    ON CONFLICT (url) DO NOTHING
    RETURNING id INTO test_id;
    
    -- 즉시 삭제
    IF test_id IS NOT NULL THEN
        DELETE FROM tracks WHERE id = test_id;
    END IF;
END $$;

-- 완료 메시지
SELECT 'tracks 테이블 캐시 갱신 완료!' as message;



