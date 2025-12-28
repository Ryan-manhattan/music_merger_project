-- Supabase 마이그레이션 파일
-- 곡(tracks) + 곡 코멘트(track_comments) 테이블 생성

-- 1) tracks: 사용자 참여형 곡 등록 + 메타데이터 저장
CREATE TABLE IF NOT EXISTS tracks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,                 -- 'soundcloud' | 'youtube' 등
    source_id TEXT,                       -- YouTube video id 등(선택)
    title TEXT NOT NULL,
    artist TEXT,                          -- uploader/channel 등(선택)
    duration_seconds INTEGER,             -- 길이(초, 선택)
    thumbnail_url TEXT,                   -- 썸네일(선택)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tracks_created_at ON tracks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tracks_source ON tracks(source);

-- 2) track_comments: 곡별 감상(일기처럼) 코멘트
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

-- updated_at 자동 업데이트 트리거 함수(이미 있을 수 있으므로 OR REPLACE)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- updated_at 자동 업데이트 트리거
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

-- RLS (Row Level Security)
ALTER TABLE tracks ENABLE ROW LEVEL SECURITY;
ALTER TABLE track_comments ENABLE ROW LEVEL SECURITY;

-- 누구나 읽기
DROP POLICY IF EXISTS "Anyone can read tracks" ON tracks;
CREATE POLICY "Anyone can read tracks" ON tracks
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Anyone can read track_comments" ON track_comments;
CREATE POLICY "Anyone can read track_comments" ON track_comments
    FOR SELECT
    USING (true);

-- 누구나 추가(참여형)
DROP POLICY IF EXISTS "Anyone can insert tracks" ON tracks;
CREATE POLICY "Anyone can insert tracks" ON tracks
    FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS "Anyone can insert track_comments" ON track_comments;
CREATE POLICY "Anyone can insert track_comments" ON track_comments
    FOR INSERT
    WITH CHECK (true);

-- 서버에서 메타데이터 갱신 가능하도록 업데이트/삭제도 허용 (운영 시 제한 권장)
DROP POLICY IF EXISTS "Anyone can update tracks" ON tracks;
CREATE POLICY "Anyone can update tracks" ON tracks
    FOR UPDATE
    USING (true);

DROP POLICY IF EXISTS "Anyone can update track_comments" ON track_comments;
CREATE POLICY "Anyone can update track_comments" ON track_comments
    FOR UPDATE
    USING (true);

DROP POLICY IF EXISTS "Anyone can delete tracks" ON tracks;
CREATE POLICY "Anyone can delete tracks" ON tracks
    FOR DELETE
    USING (true);

DROP POLICY IF EXISTS "Anyone can delete track_comments" ON track_comments;
CREATE POLICY "Anyone can delete track_comments" ON track_comments
    FOR DELETE
    USING (true);








