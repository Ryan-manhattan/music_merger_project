-- Add expandable metadata JSON for tracks
-- Purpose: store provider/raw fields now (basic meta) and leave room for future metrics/stats without schema churn.

ALTER TABLE tracks
    ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Optional (future): add a GIN index if we start querying inside metadata frequently.
-- CREATE INDEX IF NOT EXISTS idx_tracks_metadata_gin ON tracks USING GIN (metadata);









