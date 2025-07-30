# 루트 폴더 파일 상세 분석 결과

## 🔴 즉시 삭제 가능 (안전)
- **`.DS_Store`** - macOS 시스템 파일, 삭제 가능
- **`nul`** - 빈 파일, 이미 삭제됨
- **`temp-audio.m4a`** - 임시 오디오, 이미 삭제됨
- **`claude_desktop_config.json`** - Claude Desktop 개발용 설정, 삭제 가능

## 🟡 조건부 삭제 (사용 여부 확인 필요)
- **`project_cleanup_guide.md`** - 방금 생성한 정리 가이드 (작업 완료 후 삭제 가능)
- **`start_lite.sh`** - 경량 버전 실행 스크립트 (app_lite.py 사용시 필요)
- **`GEMINI.md`** - Gemini AI 관련 문서 (사용하지 않으면 삭제 가능)

## 🟢 보관 필요 (중요 기능)

### 핵심 애플리케이션 파일
- **`app.py`** - 메인 Flask 애플리케이션 (필수)
- **`app_lite.py`** - 경량화 버전 (백업용)
- **`simple_app.py`** - 단순화 버전 (테스트용)
- **`run_server.py`** - 서버 실행 스크립트

### 음악 처리 모듈
- **`audio_processor.py`** - 오디오 처리 핵심 모듈
- **`video_processor.py`** - 비디오 생성 모듈
- **`link_extractor.py`** - YouTube 링크 추출
- **`utils.py`** - 공통 유틸리티

### 분석 & 차트 모듈
- **`music_analyzer.py`** - 음악 분석 엔진
- **`music_service.py`** - 음악 서비스 통합
- **`chart_analysis.py`** - 차트 분석
- **`chart_scheduler.py`** - 자동 수집 스케줄러
- **`database.py`** - 데이터베이스 관리

### 외부 API 연동
- **`spotify_connector.py`** - Spotify API
- **`youtube_chart_collector.py`** - YouTube 차트
- **`korea_music_charts_connector.py`** - 한국 차트
- **`melon_connector.py`** - 멜론 차트
- **`reddit_connector.py`** - Reddit 트렌드
- **`lyria_client.py`** - Google Lyria AI

### 트렌드 분석
- **`music_trend_analyzer_v2.py`** - 메인 트렌드 분석기
- **`keyword_trend_analyzer.py`** - 키워드 분석
- **`comment_trend_analyzer.py`** - 댓글 감정 분석

### 설정 & 배포 파일
- **`requirements.txt`** - Python 패키지 목록 (필수)
- **`.env.example`** - 환경변수 템플릿 (필수)
- **`.env`** - 실제 환경변수 (비공개, 필수)
- **`.gitignore`** - Git 제외 목록 (필수)
- **`Procfile`** - Heroku 배포용 (필수)
- **`render.yaml`** - Render 배포용 (필수)
- **`runtime.txt`** - Python 버전 지정 (필수)
- **`service-account-key.json`** - Google Cloud 인증키 (필수)

### 실행 스크립트
- **`build.sh`** - Render 빌드 스크립트 (필수)
- **`quick_start.sh`** - 빠른 시작 스크립트
- **`start_music_merger.sh/.bat/.command`** - 플랫폼별 실행 스크립트

### 문서 파일
- **`README.md`** - 프로젝트 설명서 (필수)
- **`CLAUDE.md`** - Claude 작업 지침서 (필수)
- **`To-Do.md`** - 작업 목록

### 데이터 파일
- **`music_analysis.db`** - SQLite 데이터베이스 (분석 데이터 저장)
- **`.cache`** - 캐시 파일 (성능 최적화용)

## 삭제 권장 사항

### 즉시 삭제 가능
1. `.DS_Store` - macOS 시스템 파일
2. `claude_desktop_config.json` - 개발용 설정파일

### 총 예상 절약 용량
- 즉시 삭제: ~10MB
- 조건부 삭제 추가시: ~15MB

## 결론
대부분의 파일이 프로젝트 기능에 필요한 파일들입니다. 불필요한 시스템 파일과 개발용 설정 파일만 삭제하는 것이 안전합니다.