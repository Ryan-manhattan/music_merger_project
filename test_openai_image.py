#!/usr/bin/env python3
"""
OpenAI DALL-E 3 이미지 생성 테스트 모듈
"""

import os
import requests
import traceback
from datetime import datetime
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

def test_openai_image_generation():
    """OpenAI DALL-E 3 API 테스트"""
    
    print("🎨 OpenAI DALL-E 3 이미지 생성 테스트 시작")
    print("=" * 50)
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다")
        return False
        
    print(f"✅ API 키 확인됨: {api_key[:8]}...")
    
    try:
        # OpenAI 라이브러리 import 테스트
        print("\n📦 OpenAI 라이브러리 import 중...")
        from openai import OpenAI
        print("✅ OpenAI 라이브러리 import 성공")

        # 디버깅: 관련 환경 변수 확인
        print("\n🔍 프록시 관련 환경 변수 확인...")
        for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
            print(f"  - {var}: {os.getenv(var)}")

        # 디버깅: httpx 라이브러리 정보 확인
        try:
            import httpx
            print(f"📦 httpx 라이브러리 버전: {httpx.__version__}")
        except ImportError:
            print("❌ httpx 라이브러리가 설치되지 않음")

        # 클라이언트 초기화
        print("\n🔧 OpenAI 클라이언트 초기화 중...")
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI 클라이언트 초기화 성공")
        
        # 테스트 프롬프트
        test_prompt = "A beautiful sunset over mountains, digital art style, vibrant colors"
        print(f"\n🎯 테스트 프롬프트: {test_prompt}")
        
        # 이미지 생성 요청
        print("\n🚀 DALL-E 3 API 호출 중...")
        response = client.images.generate(
            model="dall-e-3",
            prompt=test_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        print("✅ DALL-E 3 API 호출 성공")
        
        # 생성된 이미지 URL 확인
        image_url = response.data[0].url
        print(f"\n🖼️ 생성된 이미지 URL: {image_url}")
        
        # 이미지 다운로드 테스트
        print("\n💾 이미지 다운로드 중...")
        image_response = requests.get(image_url)
        
        if image_response.status_code == 200:
            # 테스트 이미지 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_dalle3_image_{timestamp}.png"
            
            # uploads 폴더에 저장
            uploads_dir = os.path.join(os.path.dirname(__file__), 'app', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            file_path = os.path.join(uploads_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(image_response.content)
            
            file_size = len(image_response.content) / 1024 / 1024  # MB
            print(f"✅ 이미지 다운로드 성공: {filename}")
            print(f"📁 저장 경로: {file_path}")
            print(f"📊 파일 크기: {file_size:.2f} MB")
            
            return True
        else:
            print(f"❌ 이미지 다운로드 실패: HTTP {image_response.status_code}")
            return False
            
    except ImportError as e:
        print(f"❌ OpenAI 라이브러리 import 실패: {e}")
        print("💡 해결방법: pip install openai")
        return False
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print(f"🔍 오류 타입: {type(e).__name__}")
        print("\n traceback")
        traceback.print_exc()
        return False

def test_environment():
    """환경 설정 테스트"""
    
    print("\n🔧 환경 설정 확인")
    print("-" * 30)
    
    # Python 버전
    import sys
    print(f"🐍 Python 버전: {sys.version}")
    
    # 필요한 폴더 확인
    base_dir = os.path.dirname(__file__)
    uploads_dir = os.path.join(base_dir, 'app', 'uploads')
    
    print(f"📁 프로젝트 경로: {base_dir}")
    print(f"📁 업로드 폴더: {uploads_dir}")
    print(f"📁 업로드 폴더 존재: {os.path.exists(uploads_dir)}")
    
    # 환경변수 확인
    env_file = os.path.join(base_dir, '.env')
    print(f"⚙️ .env 파일 존재: {os.path.exists(env_file)}")
    
    # OpenAI 라이브러리 확인
    try:
        import openai
        print(f"📦 OpenAI 라이브러리 버전: {openai.__version__}")
    except ImportError:
        print("❌ OpenAI 라이브러리가 설치되지 않음")

if __name__ == "__main__":
    print("🧪 OpenAI DALL-E 3 테스트 모듈")
    print("=" * 50)
    
    # 환경 설정 테스트
    test_environment()
    
    # 자동으로 테스트 진행
    print("\n" + "=" * 50)
    print("🚀 OpenAI API 테스트 자동 시작...")
    
    success = test_openai_image_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ OpenAI DALL-E 3 API가 정상 작동합니다")
    else:
        print("❌ 테스트 실패")
        print("🔧 위의 오류 메시지를 확인하고 문제를 해결해주세요")