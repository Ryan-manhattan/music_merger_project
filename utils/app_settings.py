"""
설정 관리 모듈
시스템 구성, 파일 경로, API 키 등의 설정 정보를 중앙 관리합니다.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, encoding="utf-8-sig")

# 루트 디렉토리 설정
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # anon key








