#!/usr/bin/env python3
"""
자동 의존성 설치 스크립트
Music Merger Project의 모든 필수 라이브러리를 자동으로 설치
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class DependencyInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        
        print("🎵 Music Merger Project 의존성 설치 도구")
        print("=" * 50)
        print(f"📊 시스템: {platform.system()} {platform.release()}")
        print(f"🐍 Python 버전: {sys.version}")
        print(f"📂 프로젝트 경로: {self.project_root}")
        print("=" * 50)
    
    def check_python_version(self):
        """Python 버전 확인"""
        print("\n🔍 Python 버전 확인...")
        
        if self.python_version < (3, 9):
            print("❌ Python 3.9 이상이 필요합니다")
            print(f"   현재 버전: {sys.version}")
            print("   Python을 업그레이드하고 다시 시도해주세요")
            return False
        
        print(f"✅ Python {self.python_version.major}.{self.python_version.minor} 호환")
        return True
    
    def check_virtual_environment(self):
        """가상 환경 확인 및 권장"""
        print("\n🔍 가상 환경 확인...")
        
        # 가상 환경 내부인지 확인
        in_venv = (hasattr(sys, 'real_prefix') or 
                  (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
        
        if in_venv:
            print("✅ 가상 환경 내에서 실행 중")
            return True
        else:
            print("⚠️ 가상 환경을 사용하지 않고 있습니다")
            print("💡 권장사항: 가상 환경 사용")
            print("   python -m venv venv")
            print("   source venv/bin/activate  # Linux/macOS")
            print("   venv\\Scripts\\activate      # Windows")
            
            response = input("계속 진행하시겠습니까? (y/N): ").lower().strip()
            return response in ['y', 'yes', '예']
    
    def upgrade_pip(self):
        """pip 업그레이드"""
        print("\n📦 pip 업그레이드...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True, text=True)
            print("✅ pip 업그레이드 완료")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️ pip 업그레이드 실패: {e}")
            print("계속 진행합니다...")
            return False
    
    def install_system_dependencies(self):
        """시스템 의존성 확인 및 안내"""
        print("\n🔧 시스템 의존성 확인...")
        
        # FFmpeg 확인
        try:
            subprocess.run(["ffmpeg", "-version"], 
                         capture_output=True, check=True)
            print("✅ FFmpeg 설치됨")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ FFmpeg가 설치되지 않음")
            self._print_ffmpeg_install_guide()
        
        # Java 확인 (KoNLPy용)
        try:
            result = subprocess.run(["java", "-version"], 
                                  capture_output=True, check=True, text=True)
            print("✅ Java 설치됨")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ Java가 설치되지 않음 (한국어 처리 기능 제한)")
            self._print_java_install_guide()
    
    def _print_ffmpeg_install_guide(self):
        """FFmpeg 설치 안내"""
        print("\n📋 FFmpeg 설치 방법:")
        if self.system == "windows":
            print("   1. https://ffmpeg.org/download.html 에서 다운로드")
            print("   2. 압축 해제 후 bin 폴더를 PATH에 추가")
        elif self.system == "darwin":  # macOS
            print("   brew install ffmpeg")
        else:  # Linux
            print("   sudo apt install ffmpeg  # Ubuntu/Debian")
            print("   sudo yum install ffmpeg  # CentOS/RHEL")
    
    def _print_java_install_guide(self):
        """Java 설치 안내"""
        print("\n📋 Java 설치 방법:")
        if self.system == "windows":
            print("   https://www.oracle.com/java/technologies/downloads/")
        elif self.system == "darwin":  # macOS
            print("   brew install openjdk@11")
        else:  # Linux
            print("   sudo apt install openjdk-11-jdk  # Ubuntu/Debian")
    
    def install_requirements(self):
        """requirements.txt 파일 기반 설치"""
        print("\n📦 패키지 설치 중...")
        
        if not self.requirements_file.exists():
            print(f"❌ requirements.txt 파일을 찾을 수 없습니다: {self.requirements_file}")
            return False
        
        try:
            # requirements.txt 설치
            print("📋 requirements.txt 파일 설치 중...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "-r", str(self.requirements_file)
            ], check=True, capture_output=True, text=True)
            
            print("✅ 모든 패키지 설치 완료")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 패키지 설치 실패")
            print(f"오류 메시지: {e.stderr}")
            
            # 개별 설치 시도
            print("\n🔄 개별 패키지 설치 시도...")
            return self._install_packages_individually()
    
    def _install_packages_individually(self):
        """개별 패키지 설치 (실패 시 대안)"""
        essential_packages = [
            "Flask==3.0.0",
            "beautifulsoup4==4.12.2",
            "requests>=2.31.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "lxml==4.9.3",
            "scikit-learn>=1.3.2"
        ]
        
        optional_packages = [
            "spotipy==2.23.0",
            "praw==7.7.1",
            "konlpy>=0.6.0",
            "vaderSentiment==3.3.2"
        ]
        
        # 필수 패키지 설치
        print("🔧 필수 패키지 설치...")
        essential_success = 0
        for package in essential_packages:
            if self._install_single_package(package, required=True):
                essential_success += 1
        
        # 선택적 패키지 설치
        print("\n🎨 선택적 패키지 설치...")
        optional_success = 0
        for package in optional_packages:
            if self._install_single_package(package, required=False):
                optional_success += 1
        
        print(f"\n📊 설치 결과:")
        print(f"   필수 패키지: {essential_success}/{len(essential_packages)}")
        print(f"   선택적 패키지: {optional_success}/{len(optional_packages)}")
        
        return essential_success >= len(essential_packages) * 0.8
    
    def _install_single_package(self, package, required=True):
        """단일 패키지 설치"""
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True, text=True)
            
            package_name = package.split("==")[0].split(">=")[0]
            print(f"  ✅ {package_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            package_name = package.split("==")[0].split(">=")[0]
            status = "❌" if required else "⚠️"
            print(f"  {status} {package_name}")
            return False
    
    def verify_installation(self):
        """설치 검증"""
        print("\n🔍 설치 검증...")
        
        test_imports = [
            ("Flask", "flask"),
            ("BeautifulSoup", "bs4"),
            ("requests", "requests"),
            ("pandas", "pandas"),
            ("numpy", "numpy"),
            ("Last.fm Connector", "lastfm_connector"),
            ("Billboard Connector", "billboard_connector"),
        ]
        
        success_count = 0
        for name, module in test_imports:
            try:
                __import__(module)
                print(f"  ✅ {name}")
                success_count += 1
            except ImportError:
                print(f"  ❌ {name}")
        
        print(f"\n📊 검증 결과: {success_count}/{len(test_imports)} 모듈 로드 성공")
        return success_count >= len(test_imports) * 0.8
    
    def create_env_template(self):
        """환경변수 템플릿 생성"""
        print("\n📝 환경변수 템플릿 생성...")
        
        env_template = """# Music Merger Project 환경변수
# API 키들을 설정하세요

# Last.fm API
LASTFM_API_KEY=your_lastfm_api_key_here
LASTFM_API_SECRET=your_lastfm_secret_here

# Spotify API
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# YouTube API
YOUTUBE_API_KEY=your_youtube_api_key_here

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=MusicTrendAnalyzer/1.0
"""
        
        env_file = self.project_root / ".env.template"
        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(env_template)
            print(f"✅ 템플릿 생성됨: {env_file}")
            print("💡 .env.template을 .env로 복사하고 API 키를 설정하세요")
        except Exception as e:
            print(f"❌ 템플릿 생성 실패: {e}")
    
    def run_test(self):
        """테스트 실행"""
        print("\n🧪 기본 테스트 실행...")
        
        test_file = self.project_root / "test_new_chart_apis.py"
        if test_file.exists():
            try:
                subprocess.run([sys.executable, str(test_file)], 
                             check=True, timeout=30)
                print("✅ 테스트 완료")
            except subprocess.CalledProcessError:
                print("⚠️ 일부 테스트 실패 (API 키 미설정 가능)")
            except subprocess.TimeoutExpired:
                print("⚠️ 테스트 시간 초과")
        else:
            print("⚠️ 테스트 파일을 찾을 수 없습니다")
    
    def install(self):
        """전체 설치 프로세스 실행"""
        print("🚀 설치 시작...\n")
        
        # 1. Python 버전 확인
        if not self.check_python_version():
            return False
        
        # 2. 가상 환경 확인
        if not self.check_virtual_environment():
            print("설치를 중단합니다.")
            return False
        
        # 3. pip 업그레이드
        self.upgrade_pip()
        
        # 4. 시스템 의존성 확인
        self.install_system_dependencies()
        
        # 5. Python 패키지 설치
        if not self.install_requirements():
            print("❌ 패키지 설치에 실패했습니다")
            return False
        
        # 6. 설치 검증
        if not self.verify_installation():
            print("⚠️ 일부 모듈 로드에 실패했습니다")
        
        # 7. 환경변수 템플릿 생성
        self.create_env_template()
        
        # 8. 기본 테스트
        self.run_test()
        
        print("\n🎉 설치 완료!")
        print("=" * 50)
        print("다음 단계:")
        print("1. .env.template을 .env로 복사")
        print("2. .env 파일에 API 키 설정")
        print("3. python app.py 실행")
        print("4. http://localhost:5000 접속")
        
        return True

def main():
    """메인 함수"""
    installer = DependencyInstaller()
    
    try:
        success = installer.install()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 설치가 중단되었습니다")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()