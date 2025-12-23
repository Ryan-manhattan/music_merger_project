# -*- coding: utf-8 -*-
"""
인증 모듈
사용자 로그인, 회원가입, 세션 관리
"""
import os
import sys
from datetime import datetime
from typing import Optional, Dict
from werkzeug.security import generate_password_hash, check_password_hash

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils import app_settings
    from utils.supabase_client import SupabaseClient
except ImportError:
    import app_settings
    from supabase_client import SupabaseClient


class AuthManager:
    """
    인증 관리자
    사용자 로그인, 회원가입, 비밀번호 검증 등을 처리
    """
    
    def __init__(self):
        """초기화"""
        self.supabase = SupabaseClient()
    
    def register_user(self, username: str, email: str, password: str) -> Dict:
        """
        사용자 회원가입
        
        Args:
            username: 사용자명
            email: 이메일
            password: 비밀번호
        
        Returns:
            Dict: {'success': bool, 'message': str, 'user_id': str}
        """
        try:
            # 입력 검증
            if not username or len(username.strip()) < 3:
                return {'success': False, 'message': '사용자명은 3자 이상이어야 합니다.'}
            
            if not email or '@' not in email:
                return {'success': False, 'message': '올바른 이메일 주소를 입력해주세요.'}
            
            if not password or len(password) < 6:
                return {'success': False, 'message': '비밀번호는 6자 이상이어야 합니다.'}
            
            # 중복 확인
            existing_user = self.get_user_by_username(username)
            if existing_user:
                return {'success': False, 'message': '이미 사용 중인 사용자명입니다.'}
            
            existing_email = self.get_user_by_email(email)
            if existing_email:
                return {'success': False, 'message': '이미 사용 중인 이메일입니다.'}
            
            # 비밀번호 해시 생성
            password_hash = generate_password_hash(password)
            
            # 사용자 생성
            data = {
                "username": username.strip(),
                "email": email.strip().lower(),
                "password_hash": password_hash,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.supabase.client.table("users").insert(data).execute()
            
            if response.data:
                user_id = response.data[0].get("id")
                return {
                    'success': True,
                    'message': '회원가입이 완료되었습니다.',
                    'user_id': str(user_id)
                }
            else:
                return {'success': False, 'message': '회원가입에 실패했습니다.'}
                
        except Exception as e:
            print(f"[ERROR] 회원가입 실패: {e}")
            return {'success': False, 'message': f'오류가 발생했습니다: {str(e)}'}
    
    def login_user(self, username: str, password: str) -> Dict:
        """
        사용자 로그인
        
        Args:
            username: 사용자명 또는 이메일
            password: 비밀번호
        
        Returns:
            Dict: {'success': bool, 'message': str, 'user': Dict}
        """
        try:
            if not username or not password:
                return {'success': False, 'message': '사용자명과 비밀번호를 입력해주세요.'}
            
            # 사용자 조회 (사용자명 또는 이메일로)
            user = None
            if '@' in username:
                user = self.get_user_by_email(username)
            else:
                user = self.get_user_by_username(username)
            
            if not user:
                return {'success': False, 'message': '사용자명 또는 비밀번호가 올바르지 않습니다.'}
            
            # 비밀번호 검증
            if not check_password_hash(user.get('password_hash'), password):
                return {'success': False, 'message': '사용자명 또는 비밀번호가 올바르지 않습니다.'}
            
            # last_login 업데이트
            try:
                self.supabase.client.table("users").update({
                    "last_login": datetime.now().isoformat()
                }).eq("id", user['id']).execute()
            except:
                pass  # 업데이트 실패해도 로그인은 성공
            
            # 비밀번호 해시는 반환하지 않음
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user.get('created_at'),
                'last_login': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'message': '로그인 성공',
                'user': user_data
            }
                
        except Exception as e:
            print(f"[ERROR] 로그인 실패: {e}")
            return {'success': False, 'message': f'오류가 발생했습니다: {str(e)}'}
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """사용자명으로 사용자 조회"""
        try:
            response = (
                self.supabase.client.table("users")
                .select("*")
                .eq("username", username)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[ERROR] 사용자 조회 실패: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """이메일로 사용자 조회"""
        try:
            response = (
                self.supabase.client.table("users")
                .select("*")
                .eq("email", email.lower().strip())
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[ERROR] 사용자 조회 실패: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """ID로 사용자 조회"""
        try:
            response = (
                self.supabase.client.table("users")
                .select("id, username, email, created_at, last_login")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[ERROR] 사용자 조회 실패: {e}")
            return None
    
    def create_google_user(self, google_id: str, email: str, name: str, picture: str = None) -> Dict:
        """
        Google OAuth 사용자 생성
        
        Args:
            google_id: Google 사용자 ID
            email: 이메일
            name: 이름
            picture: 프로필 사진 URL
        
        Returns:
            Dict: {'success': bool, 'message': str, 'user_id': str}
        """
        try:
            # 이메일로 기존 사용자 확인
            existing_user = self.get_user_by_email(email)
            if existing_user:
                # 기존 사용자 업데이트 (Google ID 추가)
                try:
                    self.supabase.client.table("users").update({
                        "google_id": google_id,
                        "picture": picture,
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", existing_user['id']).execute()
                except:
                    pass  # 필드가 없어도 계속 진행
                
                return {
                    'success': True,
                    'message': '기존 사용자 로그인',
                    'user_id': str(existing_user['id'])
                }
            
            # 새 사용자 생성
            # 사용자명 중복 확인 및 생성
            base_username = name or email.split('@')[0]
            username = base_username
            counter = 1
            while self.get_user_by_username(username):
                username = f"{base_username}{counter}"
                counter += 1
            
            data = {
                "username": username,
                "email": email.lower().strip(),
                "google_id": google_id,
                "picture": picture,
                "password_hash": "",  # Google OAuth는 비밀번호 없음
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.supabase.client.table("users").insert(data).execute()
            
            if response.data:
                user_id = response.data[0].get("id")
                return {
                    'success': True,
                    'message': 'Google 사용자 생성 완료',
                    'user_id': str(user_id)
                }
            else:
                return {'success': False, 'message': '사용자 생성에 실패했습니다.'}
                
        except Exception as e:
            print(f"[ERROR] Google 사용자 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'오류가 발생했습니다: {str(e)}'}
