# 새로운 폴더 구조

## 📁 폴더별 파일 정리 결과

### 🔧 `/core/` - 핵심 애플리케이션
- `app_lite.py` - 경량화 버전
- `simple_app.py` - 단순화 버전  
- `run_server.py` - 서버 실행 스크립트
- `database.py` - 데이터베이스 관리
- `music_service.py` - 음악 서비스 통합
- `utils.py` - 공통 유틸리티

### 🎵 `/processors/` - 처리 모듈
- `audio_processor.py` - 오디오 처리 핵심
- `video_processor.py` - 비디오 생성
- `link_extractor.py` - YouTube 링크 추출

### 📊 `/analyzers/` - 분석 모듈
- `music_analyzer.py` - 음악 분석 엔진
- `chart_analysis.py` - 차트 분석
- `chart_scheduler.py` - 자동 수집 스케줄러
- `music_trend_analyzer_v2.py` - 메인 트렌드 분석기
- `keyword_trend_analyzer.py` - 키워드 분석
- `comment_trend_analyzer.py` - 댓글 감정 분석

### 🌐 `/connectors/` - 외부 API 연동
- `spotify_connector.py` - Spotify API
- `youtube_chart_collector.py` - YouTube 차트
- `korea_music_charts_connector.py` - 한국 차트
- `melon_connector.py` - 멜론 차트
- `reddit_connector.py` - Reddit 트렌드
- `lyria_client.py` - Google Lyria AI

### ⚡ `/scripts/` - 실행 스크립트
- `build.sh` - Render 빌드 스크립트
- `quick_start.sh` - 빠른 시작
- `start_lite.sh` - 경량 버전 실행
- `start_music_merger.bat/.command/.sh` - 플랫폼별 실행

### ⚙️ `/config/` - 설정 파일
- `requirements.txt` - Python 패키지 목록
- `.env.example` - 환경변수 템플릿
- `Procfile` - Heroku 배포용
- `render.yaml` - Render 배포용
- `runtime.txt` - Python 버전
- `service-account-key.json` - Google Cloud 인증키
- `.gitignore` - Git 제외 목록

### 📄 `/docs/` - 문서 파일
- `README.md` - 프로젝트 설명서
- `CLAUDE.md` - Claude 작업 지침서
- `GEMINI.md` - Gemini AI 관련 문서
- `To-Do.md` - 작업 목록
- `project_cleanup_guide.md` - 정리 가이드
- `root_files_analysis.md` - 파일 분석 결과

### 💾 `/data/` - 데이터 파일
- `music_analysis.db` - SQLite 데이터베이스
- `.cache` - 캐시 파일
- `chart_data/` - 차트 데이터
- `chart_analysis/` - 분석 결과

### 🌐 루트에 남은 파일
- `app.py` - 메인 Flask 애플리케이션 (필수)
- `.env` - 환경변수 (비공개)
- `app/` - 웹 인터페이스 (templates, static, uploads, processed)
- `venv/` - 가상환경

## ⚠️ 주의사항
파일 경로가 변경되었으므로 import 구문 수정이 필요할 수 있습니다.