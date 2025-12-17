# 방문자 로그 설정 가이드

## Supabase 테이블 생성

방문자 로그 기능을 사용하려면 Supabase에 `visitor_logs` 테이블을 생성해야 합니다.

### SQL 쿼리 (Supabase SQL Editor에서 실행)

```sql
-- visitor_logs 테이블 생성
CREATE TABLE IF NOT EXISTS visitor_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    page_url TEXT NOT NULL,
    referer TEXT,
    visited_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_visitor_logs_visited_at ON visitor_logs(visited_at DESC);
CREATE INDEX IF NOT EXISTS idx_visitor_logs_ip_address ON visitor_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_visitor_logs_page_url ON visitor_logs(page_url);

-- RLS (Row Level Security) 정책 설정 (선택사항)
-- 모든 사용자가 로그를 조회할 수 있도록 설정 (필요시 수정)
ALTER TABLE visitor_logs ENABLE ROW LEVEL SECURITY;

-- 익명 사용자도 로그를 읽을 수 있도록 정책 추가
CREATE POLICY "Allow anonymous read access" ON visitor_logs
    FOR SELECT
    USING (true);

-- 익명 사용자가 로그를 삽입할 수 있도록 정책 추가
CREATE POLICY "Allow anonymous insert access" ON visitor_logs
    FOR INSERT
    WITH CHECK (true);
```

### 테이블 구조

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | UUID | 고유 ID (자동 생성) |
| ip_address | VARCHAR(45) | 방문자 IP 주소 |
| user_agent | TEXT | 브라우저/디바이스 정보 |
| page_url | TEXT | 방문한 페이지 URL |
| referer | TEXT | 이전 페이지 URL (선택) |
| visited_at | TIMESTAMPTZ | 방문 시간 |
| created_at | TIMESTAMPTZ | 레코드 생성 시간 |

### 설정 방법

1. Supabase 대시보드에 로그인
2. SQL Editor 메뉴로 이동
3. 위의 SQL 쿼리를 복사하여 실행
4. 테이블이 생성되었는지 확인

### 로그 조회 예시

```sql
-- 최근 방문자 로그 조회
SELECT * FROM visitor_logs 
ORDER BY visited_at DESC 
LIMIT 100;

-- 일별 방문자 수 통계
SELECT 
    DATE(visited_at) as visit_date,
    COUNT(*) as visit_count,
    COUNT(DISTINCT ip_address) as unique_visitors
FROM visitor_logs
GROUP BY DATE(visited_at)
ORDER BY visit_date DESC;

-- 페이지별 방문 통계
SELECT 
    page_url,
    COUNT(*) as visit_count
FROM visitor_logs
GROUP BY page_url
ORDER BY visit_count DESC;
```

### 주의사항

- 방문자 로그는 시간이 지나면서 데이터가 쌓이므로, 주기적으로 오래된 로그를 삭제하는 것을 권장합니다.
- 개인정보 보호를 위해 IP 주소를 해시 처리하거나 일정 기간 후 삭제하는 정책을 고려하세요.
