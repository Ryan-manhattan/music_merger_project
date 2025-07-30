# Moodo 프로젝트 정리 가이드

## 📋 전체 구조 분석 결과

### 🔧 핵심 애플리케이션 파일 (절대 삭제 금지)
- `app.py` - 메인 Flask 애플리케이션 (핵심)
- `app_lite.py` - 경량화 버전 (백업용)
- `simple_app.py` - 단순화 버전 (테스트용)
- `run_server.py` - 서버 실행 스크립트

### 🎵 음악 처리 모듈 (필수)
- `audio_processor.py` - 오디오 파일 처리 핵심
- `video_processor.py` - 비디오 생성 기능
- `link_extractor.py` - YouTube 링크 처리
- `utils.py` - 공통 유틸리티 함수

### 📊 차트 & 분석 모듈 (기능별 선택)
- `chart_analysis.py` - 차트 분석 (필수)
- `chart_scheduler.py` - 자동 수집 스케줄러
- `music_analyzer.py` - 음악 분석 엔진
- `music_service.py` - 음악 서비스 통합
- `database.py` - 데이터베이스 관리

### 🌐 외부 API 연동 모듈 (선택적)
- `spotify_connector.py` - Spotify API (차트 기능용)
- `youtube_chart_collector.py` - YouTube 차트 수집
- `korea_music_charts_connector.py` - 한국 차트 연동
- `melon_connector.py` - 멜론 차트 연동
- `reddit_connector.py` - Reddit 트렌드 분석용
- `lyria_client.py` - Lyria API 클라이언트

### 📈 트렌드 분석 모듈 (고급 기능)
- `music_trend_analyzer_v2.py` - 메인 트렌드 분석기
- `keyword_trend_analyzer.py` - 키워드 분석
- `comment_trend_analyzer.py` - 댓글 감정 분석

### 🗂️ 웹 인터페이스 (필수)
- `app/templates/` - HTML 템플릿 전체
- `app/static/` - CSS/JS 파일 전체

## 🗑️ 삭제 가능한 파일들

### 📦 임시/테스트 파일
- `test_openai_image.py` - 테스트 파일 **삭제 가능**
- `nul` - 빈 파일 **삭제 가능**
- `temp-audio.m4a` - 임시 오디오 **삭제 가능**
- `image.png` - 테스트 이미지 **삭제 가능**

### 📁 업로드/처리 파일 정리
- `app/uploads/` - 오래된 업로드 파일들 **부분 정리 가능**
  - 7일 이상 된 파일들 삭제 권장
- `app/processed/` - 생성된 결과물들 **부분 정리 가능**
  - 용량이 큰 오래된 동영상 파일들 정리

### 📊 데이터 파일 정리
- `chart_data/` - 오래된 차트 데이터 **부분 정리 가능**
  - `latest_*.json` 파일들은 유지
- `chart_analysis/visualizations/` - 분석 이미지들 **부분 정리 가능**

### 🔧 개발 환경 파일
- `venv/` - 가상환경 폴더 **재생성 가능** (필요시 삭제 후 재설치)

### 📄 백업 템플릿
- `app/templates/index_backup.html` **삭제 가능**
- `app/templates/index_new.html` **삭제 가능**
- `app/templates/test_spotify.html` **삭제 가능**

## 📋 삭제 권장 우선순위

### 🔴 즉시 삭제 (안전)
1. `test_openai_image.py`
2. `nul`
3. `temp-audio.m4a`
4. `image.png`
5. `app/templates/index_backup.html`
6. `app/templates/index_new.html`
7. `app/templates/test_spotify.html`

### 🟡 조건부 삭제 (신중하게)
1. `app/uploads/` 내 7일 이상 된 파일들
2. `app/processed/` 내 큰 용량의 오래된 비디오
3. 오래된 차트 분석 이미지들

### 🟢 보류 (기능 확인 후)
1. `venv/` - 재설치 가능하지만 시간 소요
2. 외부 API 모듈들 - 사용하지 않는 차트 연동 모듈들

## 🔒 절대 삭제 금지 목록

### 핵심 시스템
- `app.py`, `requirements.txt`, `CLAUDE.md`
- `audio_processor.py`, `video_processor.py`
- `app/static/`, `app/templates/base.html`, `app/templates/index.html`

### 설정 파일
- `render.yaml`, `Procfile`, `runtime.txt`
- 모든 `.sh`, `.bat`, `.command` 실행 스크립트들

### 중요 데이터
- `music_analysis.db` - 분석 데이터베이스
- `service-account-key.json` - 인증 키
- `latest_*.json` - 최신 차트 데이터

## 💾 예상 절약 용량
- 즉시 삭제 파일들: ~50MB
- 조건부 삭제 (업로드/처리 파일): ~500MB-2GB
- venv 재생성: ~200MB

## ⚠️ 주의사항
1. 삭제 전 현재 사용 중인 기능 확인 필요
2. 중요 파일은 백업 후 진행
3. 단계별로 진행하여 기능 이상 여부 확인