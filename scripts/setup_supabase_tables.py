#!/usr/bin/env python3
"""
Supabase 테이블 자동 생성 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.supabase_client import SupabaseClient

def setup_tables():
    """Supabase에 모든 테이블 생성"""
    try:
        client = SupabaseClient()
        
        # SQL 파일 읽기
        sql_file = project_root / 'supabase' / 'setup_all_tables.sql'
        
        if not sql_file.exists():
            print(f"❌ SQL 파일을 찾을 수 없습니다: {sql_file}")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("📋 Supabase 테이블 생성 시작...")
        print("=" * 50)
        
        # SQL을 세미콜론으로 분리하여 실행
        # 주의: Supabase Python 클라이언트는 직접 SQL 실행을 지원하지 않으므로
        # Supabase SQL Editor에서 수동 실행이 필요합니다.
        
        print("⚠️  Supabase Python 클라이언트는 직접 SQL 실행을 지원하지 않습니다.")
        print("📝 다음 단계를 따라주세요:")
        print()
        print("1. Supabase 대시보드 접속:")
        print("   https://supabase.com/dashboard/project/ilqhifguxtnsrucawgcm/sql/new")
        print()
        print("2. 다음 파일의 내용을 복사하여 SQL Editor에 붙여넣기:")
        print(f"   {sql_file}")
        print()
        print("3. Run 버튼 클릭")
        print()
        print("또는 다음 명령어로 Supabase CLI 사용:")
        print(f"   supabase db push --file {sql_file}")
        print()
        
        # 연결 테스트
        if client.test_connection():
            print("✅ Supabase 연결 성공!")
            print("📊 현재 테이블 상태 확인 중...")
            
            # 테이블 존재 확인
            tables_to_check = ['posts', 'tracks', 'track_comments', 'users']
            existing_tables = []
            
            for table in tables_to_check:
                try:
                    # 간단한 SELECT로 테이블 존재 확인
                    result = client.client.table(table).select("id").limit(1).execute()
                    existing_tables.append(table)
                    print(f"   ✅ {table} 테이블 존재")
                except Exception as e:
                    if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                        print(f"   ❌ {table} 테이블 없음")
                    else:
                        print(f"   ⚠️  {table} 테이블 확인 중 오류: {e}")
            
            if len(existing_tables) == len(tables_to_check):
                print()
                print("✅ 모든 테이블이 이미 생성되어 있습니다!")
            else:
                missing = set(tables_to_check) - set(existing_tables)
                print()
                print(f"⚠️  다음 테이블이 없습니다: {', '.join(missing)}")
                print("   SQL Editor에서 setup_all_tables.sql을 실행해주세요.")
        else:
            print("❌ Supabase 연결 실패")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Supabase 테이블 설정 스크립트")
    print("=" * 50)
    print()
    
    success = setup_tables()
    
    print()
    print("=" * 50)
    if success:
        print("✅ 설정 완료!")
    else:
        print("❌ 설정 실패")
    print("=" * 50)






