#!/usr/bin/env python3
"""
환경 변수 검증 스크립트
YouTube Data API와 Lyria 설정 상태 확인
"""

import os
import sys
from dotenv import load_dotenv

def check_env_setup():
    """환경 변수 설정 상태 확인"""
    print("🔍 환경 변수 설정 상태 확인\n")
    
    # .env 파일 로드
    load_dotenv()
    
    # 필수 환경 변수 목록
    required_vars = {
        'YOUTUBE_API_KEY': 'YouTube Data API v3 키',
        'GOOGLE_CLOUD_PROJECT_ID': 'Google Cloud 프로젝트 ID',
        'GOOGLE_APPLICATION_CREDENTIALS': '서비스 계정 JSON 파일 경로'
    }
    
    # 선택적 환경 변수
    optional_vars = {
        'GOOGLE_CLOUD_LOCATION': 'Vertex AI 위치',
        'LYRIA_MODEL': 'Lyria 모델명',
        'DEFAULT_MUSIC_DURATION': '기본 음악 길이',
        'MAX_MUSIC_DURATION': '최대 음악 길이'
    }
    
    missing_vars = []
    configured_vars = []
    
    print("📋 필수 환경 변수 확인:")
    print("-" * 50)
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value.strip():
            print(f"✅ {var}: 설정됨")
            configured_vars.append(var)
            
            # 파일 경로 검증
            if var == 'GOOGLE_APPLICATION_CREDENTIALS':
                if os.path.exists(value):
                    print(f"   📁 파일 존재: {value}")
                else:
                    print(f"   ❌ 파일 없음: {value}")
                    missing_vars.append(f"{var} (파일 없음)")
        else:
            print(f"❌ {var}: 미설정 - {description}")
            missing_vars.append(var)
    
    print(f"\n📋 선택적 환경 변수 확인:")
    print("-" * 50)
    
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and value.strip():
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: 기본값 사용 - {description}")
    
    print(f"\n📊 설정 요약:")
    print("-" * 50)
    print(f"✅ 설정 완료: {len(configured_vars)}/{len(required_vars)}")
    print(f"❌ 설정 필요: {len(missing_vars)}")
    
    if missing_vars:
        print(f"\n🔧 설정이 필요한 항목:")
        for var in missing_vars:
            print(f"   - {var}")
        print(f"\n💡 설정 방법은 API_KEY_SETUP.md 참고")
        return False
    else:
        print(f"\n🎉 모든 필수 환경 변수가 설정되었습니다!")
        return True

def test_api_connections():
    """API 연결 테스트"""
    print(f"\n🔌 API 연결 테스트")
    print("-" * 50)
    
    # YouTube API 테스트
    youtube_key = os.getenv('YOUTUBE_API_KEY')
    if youtube_key:
        try:
            from googleapiclient.discovery import build
            youtube = build('youtube', 'v3', developerKey=youtube_key)
            # 간단한 검색 테스트
            request = youtube.search().list(
                part='snippet',
                q='test',
                maxResults=1
            )
            response = request.execute()
            print("✅ YouTube Data API v3: 연결 성공")
        except Exception as e:
            print(f"❌ YouTube Data API v3: 연결 실패 - {str(e)}")
    else:
        print("⚠️  YouTube Data API v3: API 키 없음")
    
    # Vertex AI 테스트
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if project_id and credentials_path:
        try:
            import vertexai
            from google.auth import default
            
            # 인증 테스트
            credentials, project = default()
            vertexai.init(project=project_id, location='us-central1')
            print("✅ Google Cloud Vertex AI: 연결 성공")
        except Exception as e:
            print(f"❌ Google Cloud Vertex AI: 연결 실패 - {str(e)}")
    else:
        print("⚠️  Google Cloud Vertex AI: 설정 없음")

def main():
    """메인 실행 함수"""
    print("🎵 Music Merger - 환경 설정 검증")
    print("=" * 50)
    
    # 환경 변수 확인
    env_ok = check_env_setup()
    
    if env_ok:
        # API 연결 테스트
        test_api_connections()
        
        print(f"\n🚀 다음 단계:")
        print("1. 서버 실행: python app.py")
        print("2. 브라우저에서 http://localhost:5000 접속")
        print("3. 음악 분석 기능 테스트")
        
        return 0
    else:
        print(f"\n❌ 설정을 완료한 후 다시 실행해주세요")
        return 1

if __name__ == '__main__':
    sys.exit(main())