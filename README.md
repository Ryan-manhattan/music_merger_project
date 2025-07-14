# 🎵 Music Merger

음악 파일을 자동으로 이어붙이는 웹 서비스입니다.

## 📋 프로젝트 개요

Music Merger는 여러 음악 파일을 업로드하고 개별 설정(페이드인/아웃, 볼륨 등)을 적용하여 하나의 연속 재생 파일로 합쳐주는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **다중 파일 업로드**: 드래그 앤 드롭 지원
- **개별 곡 설정**: 페이드인/아웃, 볼륨, 간격 조절
- **전체 설정**: 볼륨 정규화, 크로스페이드
- **다양한 포맷 지원**: MP3, WAV, M4A, FLAC

## 🛠️ 기술 스택

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Audio Processing**: pydub, numpy

## 📦 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/music_merger_project.git
cd music_merger_project
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. FFmpeg 설치 (pydub 필수 요구사항)
- Mac: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg`
- Windows: [FFmpeg 다운로드](https://ffmpeg.org/download.html)

## 🏃‍♂️ 실행 방법

```bash
python app.py
```

브라우저에서 `http://localhost:5000` 접속

## 📁 프로젝트 구조

```
music_merger_project/
├── app.py              # 메인 Flask 애플리케이션
├── requirements.txt    # Python 의존성
├── README.md          # 프로젝트 문서
├── .gitignore         # Git 제외 파일
├── app/
│   ├── templates/     # HTML 템플릿
│   │   ├── base.html
│   │   └── index.html
│   ├── static/        # 정적 파일
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   ├── uploads/       # 업로드된 파일 임시 저장
│   └── processed/     # 처리된 파일 저장
└── docs/              # 프로젝트 문서
    ├── 기획서.md
    └── 개발계획서.md
```

## 🔧 개발 현황

### Phase 1: 프로젝트 기반 구축 ✅
- [x] 프로젝트 구조 생성
- [x] Flask 기본 설정
- [x] HTML/CSS/JS 기본 파일

### Phase 2: 파일 업로드 시스템 (진행중)
- [x] 다중 파일 업로드
- [x] 드래그 앤 드롭
- [x] 파일 목록 관리
- [ ] 파일 유효성 검증 강화

### Phase 3: 개별 곡 설정 인터페이스
- [x] 설정 UI 컴포넌트
- [x] 설정값 관리
- [ ] 설정값 백엔드 연동

### Phase 4: 오디오 처리 엔진
- [ ] pydub 기반 처리
- [ ] 페이드 효과
- [ ] 볼륨 조절
- [ ] 파일 합치기

### Phase 5: 결과물 출력
- [ ] 진행상황 표시
- [ ] 파일 다운로드
- [ ] 미리듣기

### Phase 6: 테스트 및 배포
- [ ] 테스트
- [ ] 최적화
- [ ] 배포

## 📝 라이선스

MIT License

## 👥 기여자

- 프로젝트 개발자

## 📞 문의

프로젝트 관련 문의사항은 이슈를 등록해주세요.
