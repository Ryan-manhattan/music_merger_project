# 🎵 Music Merger Project 설치 가이드

## 📋 목차
- [사전 요구사항](#사전-요구사항)
- [가상 환경 설정](#가상-환경-설정)
- [의존성 설치](#의존성-설치)
- [API 키 설정](#api-키-설정)
- [실행 방법](#실행-방법)
- [문제 해결](#문제-해결)

---

## 🔧 사전 요구사항

### 1. Python 3.9+ 설치
```bash
# Python 버전 확인
python --version
# 또는
python3 --version
```

### 2. FFmpeg 설치 (오디오 처리용)
- **Windows**: [FFmpeg 다운로드](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`

### 3. Java JDK 8+ (한국어 자연어 처리용)
- **Windows**: [Oracle JDK](https://www.oracle.com/java/technologies/downloads/) 또는 OpenJDK
- **macOS**: `brew install openjdk@11`
- **Ubuntu/Debian**: `sudo apt install openjdk-11-jdk`

---

## 🐍 가상 환경 설정

### Option 1: venv 사용 (권장)
```bash
# 1. 프로젝트 디렉토리로 이동
cd music_merger_project

# 2. 가상 환경 생성
python -m venv venv

# 3. 가상 환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 4. pip 업그레이드
python -m pip install --upgrade pip
```

### Option 2: conda 사용
```bash
# 1. conda 환경 생성
conda create -n music_merger python=3.11

# 2. 환경 활성화
conda activate music_merger

# 3. pip 설치
conda install pip
```

---

## 📦 의존성 설치

### 1. 기본 라이브러리 설치
```bash
# requirements.txt 파일을 사용한 일괄 설치
pip install -r requirements.txt
```

### 2. 개별 설치 (문제 발생 시)
```bash
# 웹 프레임워크
pip install Flask==3.0.0 flask-cors==4.0.0

# 오디오 처리
pip install pydub==0.25.1 numpy>=1.24.0

# 새로운 차트 API 의존성
pip install beautifulsoup4==4.12.2 lxml==4.9.3
pip install requests>=2.31.0

# 데이터 분석
pip install pandas>=2.0.0 scikit-learn>=1.3.2

# API 연동
pip install spotipy==2.23.0 praw==7.7.1
pip install google-api-python-client==2.144.0

# 자연어 처리
pip install textblob==0.17.1 nltk==3.8.1
pip install vaderSentiment==3.3.2

# 한국어 처리 (선택적)
pip install konlpy>=0.6.0 JPype1>=1.4.1
```

### 3. 특별한 설치 방법

#### KoNLPy (한국어 자연어 처리)
```bash
# Windows
pip install konlpy

# macOS (추가 설정 필요)
pip install konlpy
# JDK 경로 설정 필요 시:
export JAVA_HOME=/usr/libexec/java_home

# Ubuntu/Debian
sudo apt-get install g++ openjdk-8-jdk python3-dev python3-pip curl
pip install konlpy
```

---

## 🔑 API 키 설정

### 1. 환경변수 파일 생성
프로젝트 루트에 `.env` 파일 생성:
```bash
# .env 파일
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
```

### 2. API 키 발급 방법

#### Last.fm API
1. [Last.fm API 계정](https://www.last.fm/api/account/create) 생성
2. API 키와 시크릿 발급
3. `.env` 파일에 추가

#### Spotify API
1. [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/login) 접속
2. "Create an App" 클릭
3. Client ID와 Client Secret 복사
4. `.env` 파일에 추가

#### YouTube API
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. YouTube Data API v3 활성화
3. API 키 생성
4. `.env` 파일에 추가

#### Reddit API
1. [Reddit Apps](https://www.reddit.com/prefs/apps) 접속
2. "Create App" 또는 "Create Another App" 클릭
3. 앱 타입: "script" 선택
4. Client ID와 Secret 복사
5. `.env` 파일에 추가

---

## 🚀 실행 방법

### 1. 기본 실행
```bash
# 가상 환경 활성화 확인
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Flask 앱 실행
python app.py
```

### 2. 개발 모드 실행
```bash
# 환경 변수 설정
export FLASK_ENV=development
export FLASK_DEBUG=1

# 실행
python app.py
```

### 3. 테스트 실행
```bash
# 새로운 차트 API 테스트
python test_new_chart_apis.py

# 전체 시스템 테스트
python run_test.py
```

---

## 🛠️ 문제 해결

### 일반적인 오류들

#### 1. `ModuleNotFoundError: No module named 'bs4'`
```bash
pip install beautifulsoup4
```

#### 2. `ModuleNotFoundError: No module named 'pandas'`
```bash
pip install pandas>=2.0.0
```

#### 3. `ImportError: cannot import name 'SRILM'`
```bash
# KoNLPy 설치 오류 - Java 환경 확인
java -version
export JAVA_HOME=/path/to/java
pip install --upgrade konlpy
```

#### 4. FFmpeg 관련 오류
```bash
# FFmpeg 설치 확인
ffmpeg -version

# Windows에서 PATH 설정 필요한 경우:
# 시스템 환경변수에 FFmpeg bin 경로 추가
```

#### 5. `pip install` 권한 오류 (Linux/macOS)
```bash
# 가상 환경 사용 권장
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 또는 사용자 디렉토리에 설치
pip install --user -r requirements.txt
```

### 의존성 충돌 해결

#### 1. numpy 버전 충돌
```bash
pip uninstall numpy
pip install numpy>=1.24.0,<2.0.0
```

#### 2. pandas 버전 충돌
```bash
pip uninstall pandas
pip install pandas>=2.0.0,<3.0.0
```

#### 3. 전체 재설치
```bash
# 가상 환경 삭제 후 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 시스템별 특별 설정

#### Windows 사용자
```bash
# Windows에서 일부 패키지 설치 전 필요한 도구
# Microsoft C++ Build Tools 설치
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 또는 conda 사용 권장
conda install -c conda-forge beautifulsoup4 lxml pandas scikit-learn
```

#### macOS 사용자
```bash
# Homebrew 사용 권장
brew install python@3.11 ffmpeg openjdk@11

# Java 환경변수 설정
echo 'export JAVA_HOME=$(/usr/libexec/java_home)' >> ~/.zshrc
source ~/.zshrc
```

#### Ubuntu/Debian 사용자
```bash
# 시스템 패키지 설치
sudo apt update
sudo apt install python3-venv python3-pip ffmpeg
sudo apt install openjdk-11-jdk python3-dev build-essential

# 가상 환경 생성 후 설치
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📞 지원

문제가 계속 발생하는 경우:

1. **GitHub Issues**: 프로젝트 저장소에 이슈 등록
2. **로그 확인**: `logs/` 디렉토리의 오류 로그 확인
3. **환경 확인**: `python check_env.py` 실행하여 환경 상태 점검
4. **테스트 실행**: `python test_new_chart_apis.py`로 개별 모듈 테스트

---

## 🎉 설치 완료 확인

설치가 완료되면 다음 명령어로 확인:

```bash
# 테스트 실행
python test_new_chart_apis.py

# 웹 서버 시작
python app.py
```

브라우저에서 `http://localhost:5000` 접속하여 정상 작동 확인!