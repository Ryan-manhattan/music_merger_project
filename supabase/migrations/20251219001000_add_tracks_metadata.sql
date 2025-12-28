-- Supabase 마이그레이션 파일
-- tracks.metadata (jsonb) 확장 슬롯 추가
--
-- 목적:
-- - YouTube/SoundCloud 메타데이터 raw 적재
-- - 향후 stats/metrics 확장을 스키마 변경 없이 수용

ALTER TABLE tracks
    ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

-- (선택) JSON 검색을 위한 GIN 인덱스 (추후 필요 시 사용)
CREATE INDEX IF NOT EXISTS idx_tracks_metadata_gin ON tracks USING GIN (metadata);








