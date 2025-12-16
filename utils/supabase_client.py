# -*- coding: utf-8 -*-
"""
Supabase 클라이언트 모듈
PostgreSQL 기반 클라우드 데이터베이스 연동
"""
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils import app_settings
except ImportError:
    import app_settings

try:
    from supabase import create_client, Client
except ImportError:
    print("[WARN] supabase가 설치되지 않았습니다. 'pip install supabase'를 실행하세요.")
    Client = None
    create_client = None


class SupabaseClient:
    """
    Supabase 클라이언트
    커뮤니티 게시글을 PostgreSQL 데이터베이스에 저장
    """
    
    def __init__(self, url: str = None, key: str = None):
        """
        초기화
        
        Args:
            url: Supabase 프로젝트 URL
            key: Supabase API 키 (anon key)
        """
        if Client is None or create_client is None:
            raise ImportError("supabase가 설치되지 않았습니다. 'pip install supabase'를 실행하세요.")
        
        self.url = url or app_settings.SUPABASE_URL
        self.key = key or app_settings.SUPABASE_KEY
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL과 SUPABASE_KEY가 설정되지 않았습니다.")
        
        # Supabase 클라이언트 초기화
        self.client: Client = create_client(self.url, self.key)
    
    def create_post(self, title: str, content: str, author: str = "Anonymous") -> Optional[str]:
        """
        게시글 생성
        
        Args:
            title: 제목
            content: 내용
            author: 작성자 (기본값: Anonymous)
        
        Returns:
            Optional[str]: 생성된 레코드 ID
        """
        try:
            data = {
                "title": title,
                "content": content,
                "author": author,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.client.table("posts").insert(data).execute()
            
            if response.data:
                record_id = response.data[0].get("id")
                print(f"[INFO] Supabase 게시글 생성 성공: {record_id}")
                return str(record_id)
            else:
                print("[ERROR] Supabase 게시글 생성 실패: 응답 데이터 없음")
                return None
                
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 생성 실패: {e}")
            return None
    
    def get_posts(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        게시글 목록 조회
        
        Args:
            limit: 조회 개수 제한
            offset: 오프셋
        
        Returns:
            List[Dict]: 게시글 리스트
        """
        try:
            response = (
                self.client.table("posts")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 조회 실패: {e}")
            return []
    
    def get_post(self, post_id: str) -> Optional[Dict]:
        """
        게시글 상세 조회
        
        Args:
            post_id: 게시글 ID
        
        Returns:
            Optional[Dict]: 게시글 정보
        """
        try:
            response = (
                self.client.table("posts")
                .select("*")
                .eq("id", post_id)
                .single()
                .execute()
            )
            
            return response.data if response.data else None
            
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 조회 실패: {e}")
            return None
    
    def update_post(self, post_id: str, title: str = None, content: str = None) -> bool:
        """
        게시글 수정
        
        Args:
            post_id: 게시글 ID
            title: 제목 (선택)
            content: 내용 (선택)
        
        Returns:
            bool: 성공 여부
        """
        try:
            data = {
                "updated_at": datetime.now().isoformat()
            }
            
            if title:
                data["title"] = title
            if content:
                data["content"] = content
            
            response = (
                self.client.table("posts")
                .update(data)
                .eq("id", post_id)
                .execute()
            )
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 수정 실패: {e}")
            return False
    
    def delete_post(self, post_id: str) -> bool:
        """
        게시글 삭제
        
        Args:
            post_id: 게시글 ID
        
        Returns:
            bool: 성공 여부
        """
        try:
            response = (
                self.client.table("posts")
                .delete()
                .eq("id", post_id)
                .execute()
            )
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 삭제 실패: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Supabase 연결 테스트
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            # 간단한 쿼리로 연결 테스트
            response = self.client.table("posts").select("id").limit(1).execute()
            print("[INFO] Supabase 연결 성공!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Supabase 연결 실패: {e}")
            return False


def main():
    """테스트용 메인 함수"""
    try:
        client = SupabaseClient()
        print("=== Supabase 연결 테스트 ===")
        print()
        
        # 연결 테스트
        if client.test_connection():
            print("✓ 연결 성공!")
        else:
            print("✗ 연결 실패")
            
    except Exception as e:
        print(f"[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

