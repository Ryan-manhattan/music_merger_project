# 두 웹사이트에서 하나의 데이터베이스 공유 시 충돌 가능성

## 📋 현재 상황

### 사용 중인 테이블
- **off_community**: `posts` 테이블
- **finance_stock_manhattan**: `stocks`, `watched_stocks`, `overseas_stock_history`, `stock_anomalies`, `stock_orders`, `kis_tokens` 테이블

### ✅ 좋은 소식
**테이블이 다르므로 기본적으로 충돌이 없습니다!**

## 🔍 충돌이 발생할 수 있는 경우

### 1. **같은 테이블을 사용하는 경우**
두 웹사이트가 같은 테이블에 동시에 쓰기 작업을 하면:
- **INSERT**: UUID를 PK로 사용하므로 충돌 가능성 낮음 ✅
- **UPDATE**: 같은 레코드를 동시에 수정하면 마지막 쓰기가 승리 (Lost Update 문제)
- **DELETE**: 동시 삭제 시도 시 오류 가능

### 2. **동시성 문제 예시**

```python
# 웹사이트 A와 B가 동시에 같은 게시글을 수정하려고 할 때
# 웹사이트 A: 게시글 제목을 "제목1"로 변경
# 웹사이트 B: 게시글 제목을 "제목2"로 변경
# 결과: 마지막에 실행된 변경사항만 저장됨 (Lost Update)
```

## 🛡️ 해결 방법

### 1. **Optimistic Locking (낙관적 잠금)**
```sql
-- 테이블에 version 컬럼 추가
ALTER TABLE posts ADD COLUMN version INTEGER DEFAULT 1;

-- 업데이트 시 version 체크
UPDATE posts 
SET title = '새 제목', version = version + 1
WHERE id = '...' AND version = 1;  -- version이 변경되었으면 실패
```

### 2. **Pessimistic Locking (비관적 잠금)**
```python
# PostgreSQL의 SELECT FOR UPDATE 사용
BEGIN;
SELECT * FROM posts WHERE id = '...' FOR UPDATE;
UPDATE posts SET title = '새 제목' WHERE id = '...';
COMMIT;
```

### 3. **트랜잭션 사용**
```python
# Supabase는 자동으로 트랜잭션을 처리하지만,
# 복잡한 작업은 명시적으로 트랜잭션 사용 권장
```

### 4. **테이블 분리 (현재 방식)**
- 각 웹사이트가 다른 테이블을 사용 → 충돌 없음 ✅
- 가장 안전한 방법

## 📊 PostgreSQL/Supabase의 동시성 제어

### ACID 속성
- **Atomicity (원자성)**: 트랜잭션은 모두 성공하거나 모두 실패
- **Consistency (일관성)**: 데이터 무결성 보장
- **Isolation (격리성)**: 동시 실행 트랜잭션 간 격리
- **Durability (지속성)**: 커밋된 데이터는 영구 저장

### 격리 수준 (Isolation Level)
PostgreSQL 기본값: **READ COMMITTED**
- Dirty Read: ❌ 방지
- Non-repeatable Read: ⚠️ 가능
- Phantom Read: ⚠️ 가능

## ✅ 현재 프로젝트의 안전성

### 1. **테이블 분리**
- `posts` vs `stocks` 등 → 충돌 없음

### 2. **UUID Primary Key**
- `gen_random_uuid()` 사용 → INSERT 충돌 가능성 매우 낮음

### 3. **RLS (Row Level Security)**
- 현재 모든 사용자에게 모든 권한 부여
- 필요시 사용자별 권한 제한 가능

## 🚨 주의사항

### 같은 테이블을 공유해야 하는 경우

1. **동시 수정 방지**
   - Optimistic Locking 구현
   - 또는 업데이트 전 데이터 확인

2. **트랜잭션 사용**
   - 복잡한 작업은 트랜잭션으로 묶기

3. **인덱스 최적화**
   - 동시 읽기 성능 향상

4. **RLS 정책 강화**
   - 사용자별 권한 제한

## 💡 권장사항

### 현재 상황 (테이블 분리)
✅ **안전합니다!** 충돌 걱정 없이 사용 가능

### 같은 테이블 공유 시
1. Optimistic Locking 구현
2. 트랜잭션 사용
3. 충돌 감지 및 재시도 로직
4. 로깅 및 모니터링

## 📝 예시 코드

### Optimistic Locking 구현 예시
```python
def update_post_with_version(post_id: str, title: str, current_version: int):
    """버전 체크를 통한 안전한 업데이트"""
    try:
        response = (
            client.table("posts")
            .update({
                "title": title,
                "version": current_version + 1
            })
            .eq("id", post_id)
            .eq("version", current_version)  # 버전 체크
            .execute()
        )
        
        if response.data:
            return True
        else:
            # 버전이 변경되어 업데이트 실패
            return False
    except Exception as e:
        print(f"업데이트 실패: {e}")
        return False
```










