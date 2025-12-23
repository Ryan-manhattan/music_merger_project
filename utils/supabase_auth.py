# -*- coding: utf-8 -*-
"""
Supabase Auth 모듈
Supabase Authentication을 사용한 사용자 인증
"""
import os
import sys
from typing import Optional, Dict
from datetime import datetime

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


class SupabaseAuth:
    """
    Supabase Authentication 클라이언트
    Google OAuth 및 사용자 인증 관리
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
    
    def get_google_oauth_url(self, redirect_to: str = None) -> str:
        """
        Google OAuth 로그인 URL 생성 (Supabase Auth)
        
        Args:
            redirect_to: 로그인 후 리다이렉트할 URL (앱의 콜백 URL)
        
        Returns:
            Google OAuth 로그인 URL
        """
        # Supabase Auth의 Google OAuth URL
        # redirect_to는 Supabase 대시보드에서 설정한 Redirect URLs 중 하나여야 함
        oauth_url = f"{self.url}/auth/v1/authorize?provider=google"
        
        if redirect_to:
            # redirect_to는 URL 인코딩 필요
            from urllib.parse import quote
            oauth_url += f"&redirect_to={quote(redirect_to)}"
        
        return oauth_url
    
    def sign_in_with_oauth(self, provider: str = "google", redirect_to: str = None) -> Dict:
        """
        OAuth 제공자로 로그인 (서버 사이드)
        
        Args:
            provider: OAuth 제공자 (google, github 등)
            redirect_to: 로그인 후 리다이렉트할 URL (앱의 콜백 URL)
        
        Returns:
            Dict: {'url': str} - 리다이렉트할 URL
        """
        try:
            # Supabase Auth OAuth URL 생성
            oauth_url = self.get_google_oauth_url(redirect_to=redirect_to)
            
            return {
                'success': True,
                'url': oauth_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_from_session(self, access_token: str) -> Optional[Dict]:
        """
        액세스 토큰으로 사용자 정보 조회
        
        Args:
            access_token: Supabase Auth 액세스 토큰
        
        Returns:
            사용자 정보 Dict 또는 None
        """
        try:
            # Supabase Python 클라이언트는 토큰을 직접 받지 않고 세션을 설정해야 함
            # 대신 REST API를 직접 호출
            import requests
            
            headers = {
                'apikey': self.key,
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.get(
                f'{self.url}/auth/v1/user',
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'id': user_data.get('id'),
                    'email': user_data.get('email'),
                    'user_metadata': user_data.get('user_metadata', {}),
                    'app_metadata': user_data.get('app_metadata', {})
                }
            else:
                print(f"[ERROR] Supabase Auth 사용자 조회 실패: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"[ERROR] Supabase Auth 사용자 조회 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def sign_out(self, access_token: str) -> bool:
        """
        로그아웃
        
        Args:
            access_token: Supabase Auth 액세스 토큰
        
        Returns:
            성공 여부
        """
        try:
            self.client.auth.sign_out(access_token)
            return True
        except Exception as e:
            print(f"[ERROR] Supabase Auth 로그아웃 실패: {e}")
            return False
