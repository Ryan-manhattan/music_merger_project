-- visitor_logs 테이블 생성
-- 방문자 로그 기록용 테이블

CREATE TABLE IF NOT EXISTS visitor_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ip_address TEXT,
    user_agent TEXT,
    page_url TEXT,
    referer TEXT,
    visited_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_visitor_logs_visited_at ON visitor_logs(visited_at DESC);
CREATE INDEX IF NOT EXISTS idx_visitor_logs_ip_address ON visitor_logs(ip_address);

-- RLS 설정 (선택사항 - 모든 사용자가 읽기/쓰기 가능)
ALTER TABLE visitor_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read visitor_logs" ON visitor_logs;
CREATE POLICY "Anyone can read visitor_logs" ON visitor_logs
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Anyone can insert visitor_logs" ON visitor_logs;
CREATE POLICY "Anyone can insert visitor_logs" ON visitor_logs
    FOR INSERT
    WITH CHECK (true);
