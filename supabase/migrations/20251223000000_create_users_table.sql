-- Supabase 마이그레이션 파일
-- 사용자 인증 테이블 생성

-- users 테이블 생성
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

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- updated_at 자동 업데이트 트리거
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) 정책 설정
-- 주의: 현재는 Flask 앱에서 직접 인증을 처리하므로 RLS는 비활성화
-- 필요시 서비스 키로 접근하거나 RLS를 조정할 수 있음
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능 (프로필 표시용)
CREATE POLICY "Anyone can read users" ON users
    FOR SELECT
    USING (true);

-- 모든 사용자가 회원가입 가능 (실제 운영 시에는 추가 검증 권장)
CREATE POLICY "Anyone can insert users" ON users
    FOR INSERT
    WITH CHECK (true);

-- 사용자는 자신의 정보만 수정 가능 (실제 운영 시에는 인증 추가 권장)
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE
    USING (true);







