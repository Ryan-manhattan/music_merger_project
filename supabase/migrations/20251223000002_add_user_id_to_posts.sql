-- posts 테이블에 user_id 컬럼 추가
-- 작성자 본인 삭제 기능을 위한 마이그레이션

-- 1. user_id 컬럼 추가 (NULL 허용 - 기존 데이터 호환)
ALTER TABLE posts 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- 2. user_id 인덱스 추가 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);

-- 완료 메시지
SELECT '✅ posts 테이블에 user_id 컬럼 추가 완료!' as message;




