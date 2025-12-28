-- tracks 테이블에 user_id 컬럼 추가
-- 사용자별로 본인이 추가한 song archive 구분

-- 1. user_id 컬럼 추가 (NULL 허용 - 기존 데이터 호환)
ALTER TABLE tracks 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- 2. (url, user_id) 조합으로 유니크 제약 변경
-- 기존 url UNIQUE 제약 제거
ALTER TABLE tracks DROP CONSTRAINT IF EXISTS tracks_url_key;

-- (url, user_id) 조합 유니크 인덱스 생성 (NULL user_id는 별도 처리)
CREATE UNIQUE INDEX IF NOT EXISTS idx_tracks_url_user_id 
ON tracks(url, COALESCE(user_id, '00000000-0000-0000-0000-000000000000'::uuid));

-- 3. user_id 인덱스 추가 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_tracks_user_id ON tracks(user_id);

-- 4. RLS 정책 수정: Flask-Login 사용 중이므로 모든 작업 허용 (앱 레벨에서 필터링)
ALTER TABLE tracks ENABLE ROW LEVEL SECURITY;

-- 기존 정책 삭제
DROP POLICY IF EXISTS "Anyone can read tracks" ON tracks;
DROP POLICY IF EXISTS "Anyone can insert tracks" ON tracks;
DROP POLICY IF EXISTS "Anyone can update tracks" ON tracks;
DROP POLICY IF EXISTS "Anyone can delete tracks" ON tracks;

-- 새 정책: 모든 사용자 조회 가능 (공개, 앱에서 user_id로 필터링)
CREATE POLICY "Anyone can read tracks" ON tracks
    FOR SELECT
    USING (true);

-- 새 정책: 모든 사용자 추가 가능 (앱에서 user_id 설정)
CREATE POLICY "Anyone can insert tracks" ON tracks
    FOR INSERT
    WITH CHECK (true);

-- 새 정책: 모든 사용자 수정 가능 (앱에서 user_id 확인)
CREATE POLICY "Anyone can update tracks" ON tracks
    FOR UPDATE
    USING (true);

-- 새 정책: 모든 사용자 삭제 가능 (앱에서 user_id 확인)
CREATE POLICY "Anyone can delete tracks" ON tracks
    FOR DELETE
    USING (true);

-- 완료 메시지
SELECT '✅ tracks 테이블에 user_id 컬럼 추가 완료!' as message;






