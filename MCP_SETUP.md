# Supabase MCP 설정 완료

## ✅ 설정 완료

`.cursor/mcp.json` 파일에 Supabase MCP 서버 설정을 추가했습니다.

## 🔄 다음 단계

**Cursor를 재시작**하면 Supabase MCP 서버가 활성화됩니다.

재시작 후:
1. Supabase MCP 서버가 자동으로 연결됩니다
2. 브라우저에서 Supabase 로그인을 요청할 수 있습니다
3. 마이그레이션을 MCP를 통해 실행할 수 있습니다

## 📋 마이그레이션 실행 방법

### 방법 1: MCP를 통한 실행 (Cursor 재시작 후)

Cursor 재시작 후 다음 명령으로 마이그레이션 실행:
```
Supabase MCP를 사용하여 supabase/run_new_migrations.sql 파일을 실행해줘
```

### 방법 2: Supabase 대시보드에서 직접 실행

1. https://supabase.com/dashboard/project/ilqhifguxtnsrucawgcm/sql/new 접속
2. `supabase/run_new_migrations.sql` 파일 내용 복사
3. SQL Editor에 붙여넣고 실행

## 🔧 MCP 설정 내용

```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp",
      "projectRef": "ilqhifguxtnsrucawgcm"
    }
  }
}
```

## 📝 마이그레이션 내용

1. **users 테이블 생성** (이미 존재할 수 있음)
2. **tracks 테이블에 user_id 추가**
3. **posts 테이블에 user_id 추가**

모든 마이그레이션은 `IF NOT EXISTS`를 사용하여 안전하게 실행됩니다.
