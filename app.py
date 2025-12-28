#!/usr/bin/env python3
"""
off the community - 음악 파일 처리 웹 서비스
메인 Flask 애플리케이션 파일
"""

import os

# FFmpeg 경로를 환경 변수에 추가 (로컬 개발용)
if os.name == 'nt':  # Windows에서만 실행
    ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg-master-latest-win64-gpl', 'bin')
    if os.path.exists(ffmpeg_path):
        current_path = os.environ.get('PATH', '')
        if ffmpeg_path not in current_path:
            os.environ['PATH'] = ffmpeg_path + os.pathsep + current_path

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_login import login_required
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# Flask-Dance 제거, Supabase Auth 사용
# from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.utils import secure_filename
from datetime import datetime
from typing import Optional
import json
import threading
import uuid
from core.utils import validate_audio_file, generate_safe_filename, get_file_size_mb
from processors.audio_processor import AudioProcessor
from processors.link_extractor import LinkExtractor
from processors.video_processor import VideoProcessor
# 무거운 의존성들을 선택적으로 로드
try:
    from core.music_service import MusicService
    music_service_available = True
except ImportError as e:
    print(f"MusicService 로드 실패: {e}")
    music_service_available = False

try:
    from core.database import DatabaseManager
    database_available = True
except ImportError as e:
    print(f"DatabaseManager 로드 실패: {e}")
    database_available = False

try:
    from analyzers.music_trend_analyzer_v2 import MusicTrendAnalyzerV2
    trend_analyzer_available = True
except ImportError as e:
    print(f"MusicTrendAnalyzerV2 로드 실패: {e}")
    trend_analyzer_available = False

try:
    from connectors.melon_connector import MelonConnector
    melon_connector_available = True
except ImportError as e:
    print(f"MelonConnector 로드 실패: {e}")
    melon_connector_available = False

try:
    from connectors.korea_music_charts_connector import KoreaMusicChartsConnector
    korea_charts_connector_available = True
except ImportError as e:
    print(f"KoreaMusicChartsConnector 로드 실패: {e}")
    korea_charts_connector_available = False

try:
    from analyzers.chart_scheduler import get_scheduler, start_chart_scheduler, stop_chart_scheduler
    chart_scheduler_available = True
except ImportError as e:
    print(f"ChartScheduler 로드 실패: {e}")
    chart_scheduler_available = False

try:
    from analyzers.chart_analysis import ChartAnalyzer
    chart_analyzer_available = True
except ImportError as e:
    print(f"ChartAnalyzer 로드 실패: {e}")
    chart_analyzer_available = False

try:
    from utils.supabase_client import SupabaseClient
    supabase_available = True
except ImportError as e:
    print(f"SupabaseClient 로드 실패: {e}")
    supabase_available = False

# Flask 앱 초기화 (Windows 경로 대응)
app = Flask(__name__, 
           template_folder='app/templates', 
           static_folder='app/static')
CORS(app, supports_credentials=True)

# 설정
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB 제한
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'app', 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.path.dirname(__file__), 'app', 'processed')
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'm4a', 'flac', 'mp4', 'webm'}
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'bmp', 'gif'}
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-1225-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24시간

# 폴더 생성 확인
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# 콘솔 로그 함수 (디버깅용)
class console:
    @staticmethod
    def log(message):
        """콘솔 로그 출력"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # UTF-8 문자를 안전하게 처리
        try:
            safe_message = str(message).encode('cp949', 'ignore').decode('cp949')
        except:
            safe_message = str(message).encode('ascii', 'ignore').decode('ascii')
        
        log_msg = f"[{timestamp}] {safe_message}"
        print(log_msg)
        # 즉시 플러시하여 버퍼링 방지
        import sys
        sys.stdout.flush()

# Flask-Login 초기화
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '로그인이 필요합니다.'
login_manager.login_message_category = 'info'

# Supabase Auth 초기화
try:
    from utils.supabase_auth import SupabaseAuth
    supabase_auth = SupabaseAuth()
    console.log("[Auth] Supabase Auth 초기화 완료")
except Exception as e:
    console.log(f"[WARN] Supabase Auth 초기화 실패: {e}")
    supabase_auth = None

# 서비스 초기화 (환경 변수 설정 후)
music_service = None
db_manager = None

# YouTube 분석만 활성화 (Lyria AI 생성은 비활성화)
try:
    from music_analyzer import MusicAnalyzer
    music_analyzer = MusicAnalyzer(
        api_key=os.getenv('YOUTUBE_API_KEY'),
        console_log=lambda msg: console.log(msg)
    )
    console.log("YouTube 음악 분석기 초기화 완료 (분석 전용 모드)")
except Exception as e:
    music_analyzer = None
    console.log(f"YouTube 분석기 초기화 실패: {str(e)}")

# 멜론 커넥터 초기화
melon_connector = None
if melon_connector_available:
    try:
        melon_connector = MelonConnector(console_log=lambda msg: console.log(msg))
        console.log("멜론 커넥터 초기화 완료")
    except Exception as e:
        console.log(f"멜론 커넥터 초기화 실패: {str(e)}")
        melon_connector = None

if database_available:
    try:
        # 프로젝트 루트의 기본 DB 파일 사용
        db_path = os.path.join(os.path.dirname(__file__), 'music_analysis.db')
        db_manager = DatabaseManager(db_path=db_path, console_log=lambda msg: console.log(msg))
        console.log("데이터베이스 매니저 초기화 완료")
    except Exception as e:
        db_manager = None
        console.log(f"데이터베이스 매니저 초기화 실패: {str(e)}")
else:
    db_manager = None
    console.log("데이터베이스 기능 비활성화")

if trend_analyzer_available:
    try:
        trends_analyzer = MusicTrendAnalyzerV2(console_log=lambda msg: console.log(msg))
        console.log("트렌드 분석기 초기화 완료")
    except Exception as e:
        trends_analyzer = None
        console.log(f"트렌드 분석기 초기화 실패: {str(e)}")
else:
    trends_analyzer = None
    console.log("트렌드 분석 기능 비활성화")


# Music Trend Analyzer V2는 위에서 trends_analyzer로 이미 초기화됨
trend_analyzer_v2 = trends_analyzer


# 음악 분석 작업 저장소
music_analysis_jobs = {}


# =========================
# 커뮤니티 기본 설정
# =========================
# - “노래 들으면서 생각 남기기”에 맞는 최소 UX/방어 로직
COMMUNITY_TITLE_MAX_LEN = 200
COMMUNITY_CONTENT_MAX_LEN = 10000
COMMUNITY_AUTHOR_MAX_LEN = 50

COMMUNITY_PER_PAGE_DEFAULT = 20
COMMUNITY_PER_PAGE_MAX = 50

# 간단한 스팸 방지(서버 메모리 기반): 같은 IP에서 너무 빠른 연속 작성 제한
COMMUNITY_POST_MIN_INTERVAL_SECONDS = 10
_community_last_post_at_by_ip = {}

TRACKS_PER_PAGE_DEFAULT = 20
TRACKS_PER_PAGE_MAX = 50
TRACK_URL_MAX_LEN = 500
TRACK_TITLE_MAX_LEN = 200
TRACK_ARTIST_MAX_LEN = 200

TRACK_COMMENT_MAX_LEN = 4000
TRACK_COMMENT_AUTHOR_MAX_LEN = 50
TRACK_COMMENT_MIN_INTERVAL_SECONDS = 5
_track_last_comment_at_by_ip = {}


def _get_client_ip() -> str:
    """프록시 환경(X-Forwarded-For) 고려한 클라이언트 IP 추출"""
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_address:
        return ip_address.split(',')[0].strip()
    return request.remote_addr or 'Unknown'


def _validate_post_payload(title: str, content: str, author: str) -> Optional[str]:
    """게시글 입력값 검증. 문제 있으면 에러 메시지 반환, 아니면 None."""
    if not title or not content:
        return "제목과 내용을 입력해주세요."

    if len(title) > COMMUNITY_TITLE_MAX_LEN:
        return f"제목은 {COMMUNITY_TITLE_MAX_LEN}자 이하로 입력해주세요."
    if len(content) > COMMUNITY_CONTENT_MAX_LEN:
        return f"내용은 {COMMUNITY_CONTENT_MAX_LEN}자 이하로 입력해주세요."
    if author and len(author) > COMMUNITY_AUTHOR_MAX_LEN:
        return f"닉네임은 {COMMUNITY_AUTHOR_MAX_LEN}자 이하로 입력해주세요."

    return None


def _format_duration(seconds: Optional[int]) -> str:
    """초를 mm:ss 형식으로 변환 (간단 표기)"""
    if not seconds or seconds <= 0:
        return ""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def _guess_track_source(url: str) -> str:
    """URL로 소스 추정 (SoundCloud/YouTube만 MVP 지원)"""
    u = (url or "").lower()
    if "soundcloud.com" in u:
        return "soundcloud"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    return "unknown"


def allowed_file(filename):
    """파일 확장자 검증"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def allowed_image_file(filename):
    """이미지 파일 확장자 검증"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_IMAGE_EXTENSIONS']


# cleanup 함수 제거 - 파일 자동 삭제 방지


@app.before_request
def log_visitor():
    """모든 요청에 대해 방문자 로그 기록"""
    # 정적 파일, API 엔드포인트는 제외
    excluded_paths = ['/static/', '/api/', '/favicon.ico', '/robots.txt']
    path = request.path
    
    # 제외 경로 체크
    if any(path.startswith(excluded) for excluded in excluded_paths):
        return None
    
    # 방문자 로그 기록 (비동기로 처리하여 응답 속도에 영향 없도록)
    if supabase_available:
        try:
            # IP 주소 가져오기 (프록시 환경 고려)
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address:
                ip_address = ip_address.split(',')[0].strip()
            else:
                ip_address = request.remote_addr or 'Unknown'
            
            # User-Agent 가져오기
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            # 현재 페이지 URL
            page_url = request.url
            
            # Referer 가져오기
            referer = request.headers.get('Referer')
            
            # 비동기로 로그 기록 (응답 속도에 영향 없도록)
            def log_async():
                try:
                    supabase = SupabaseClient()
                    supabase.log_visitor(
                        ip_address=ip_address,
                        user_agent=user_agent,
                        page_url=page_url,
                        referer=referer
                    )
                except Exception as e:
                    # 로그 기록 실패해도 앱은 계속 동작
                    console.log(f"[WARN] 방문자 로그 기록 실패: {e}")
            
            # 별도 스레드에서 실행
            thread = threading.Thread(target=log_async)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            # 로그 기록 실패해도 앱은 계속 동작
            console.log(f"[WARN] 방문자 로그 초기화 실패: {e}")
    
    return None


# User 클래스 (Flask-Login용)
class User(UserMixin):
    """사용자 클래스"""
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email
    
    @staticmethod
    def get(user_id):
        """사용자 ID로 사용자 객체 반환"""
        try:
            from utils.auth import AuthManager
            auth_manager = AuthManager()
            user_data = auth_manager.get_user_by_id(user_id)
            if user_data:
                return User(
                    user_id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email']
                )
        except Exception as e:
            console.log(f"[ERROR] 사용자 조회 실패: {e}")
        return None


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login용 사용자 로더"""
    return User.get(user_id)


@app.route('/login')
def login():
    """로그인 페이지"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Supabase Auth 활성화 여부를 템플릿에 전달
    google_oauth_enabled = supabase_auth is not None
    return render_template('login.html', google_oauth_enabled=google_oauth_enabled)


@app.route('/login/google')
def google_login():
    """Google OAuth 로그인 시작 (Supabase Auth)"""
    if not supabase_auth:
        console.log("[ERROR] Supabase Auth가 초기화되지 않았습니다.")
        return redirect(url_for('login'))
    
    try:
        # Supabase Auth Google OAuth URL로 리다이렉트
        # redirect_to는 Supabase 대시보드의 Redirect URLs에 등록된 URL이어야 함
        # 동적으로 현재 호스트와 스킵을 사용하여 URL 생성
        scheme = request.scheme  # http 또는 https
        host = request.host  # 호스트명과 포트 포함
        
        # 환경 변수에서 명시적으로 설정된 경우 사용 (배포 환경)
        if os.environ.get('SITE_URL'):
            site_url = os.environ.get('SITE_URL').rstrip('/')
            redirect_to = f"{site_url}/login/google/authorized"
        else:
            # 로컬 개발 환경에서는 request에서 가져온 정보 사용
            redirect_to = f"{scheme}://{host}/login/google/authorized"
        
        # 모바일 브라우저 감지 (User-Agent 확인)
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
        
        console.log(f"[INFO] Google OAuth 리다이렉트 URL: {redirect_to}")
        console.log(f"[INFO] 모바일 브라우저 감지: {is_mobile}")
        console.log(f"[INFO] Supabase 대시보드의 Redirect URLs에 '{redirect_to}'가 등록되어 있는지 확인하세요.")
        if is_mobile:
            console.log(f"[INFO] 모바일 브라우저에서 로그인 시도 - 외부 브라우저에서 열립니다.")
        
        # Supabase Auth는 기본적으로 외부 브라우저를 사용하므로
        # skip_browser_redirect는 사용하지 않음 (Supabase가 자동 처리)
        result = supabase_auth.sign_in_with_oauth(
            provider="google", 
            redirect_to=redirect_to
        )
        
        if result.get('success'):
            console.log(f"[INFO] Google OAuth URL 생성 성공: {result['url']}")
            return redirect(result['url'])
        else:
            console.log(f"[ERROR] Google OAuth URL 생성 실패: {result.get('error')}")
            return redirect(url_for('login'))
    except Exception as e:
        console.log(f"[ERROR] Google 로그인 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('login'))


@app.route('/login/google/authorized')
def google_login_callback():
    """Supabase Auth Google OAuth 콜백 처리 (클라이언트 사이드에서 토큰 처리)"""
    # Supabase Auth는 URL fragment(#)에 토큰을 전달하므로
    # 클라이언트 사이드 JavaScript로 처리하는 페이지 렌더링
    return render_template('oauth_callback.html')


@app.route('/api/auth/supabase/callback', methods=['POST'])
def supabase_auth_callback_api():
    """Supabase Auth 콜백 API (클라이언트에서 토큰 전달)"""
    if not supabase_auth:
        return jsonify({'success': False, 'error': 'Supabase Auth가 초기화되지 않았습니다.'}), 500
    
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        
        if not access_token:
            return jsonify({'success': False, 'error': '토큰이 없습니다.'}), 400
        
        # Supabase Auth로 사용자 정보 가져오기
        user_info = supabase_auth.get_user_from_session(access_token)
        
        if not user_info:
            return jsonify({'success': False, 'error': '사용자 정보 조회 실패'}), 401
        
        email = user_info.get('email')
        user_metadata = user_info.get('user_metadata', {})
        name = user_metadata.get('full_name') or user_metadata.get('name') or (email.split('@')[0] if email else 'User')
        picture = user_metadata.get('avatar_url') or user_metadata.get('picture')
        
        if not email:
            return jsonify({'success': False, 'error': '이메일 정보 없음'}), 400
        
        # Supabase users 테이블에 사용자 저장 또는 조회
        from utils.auth import AuthManager
        auth_manager = AuthManager()
        
        # 이메일로 기존 사용자 확인
        existing_user = auth_manager.get_user_by_email(email)
        
        if existing_user:
            # 기존 사용자 로그인
            user = User(
                user_id=str(existing_user['id']),
                username=existing_user.get('username', name),
                email=existing_user.get('email', email)
            )
        else:
            # 새 사용자 생성 (Google OAuth 사용자)
            google_id = user_info.get('id')
            result = auth_manager.create_google_user(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture
            )
            
            if result.get('success'):
                user_id = result.get('user_id')
                if not user_id:
                    return jsonify({'success': False, 'error': '사용자 생성 실패'}), 500
                
                user = User(
                    user_id=str(user_id),
                    username=name,
                    email=email
                )
            else:
                error_msg = result.get('message', '알 수 없는 오류')
                return jsonify({'success': False, 'error': error_msg}), 500
        
        # Flask-Login으로 로그인
        login_user(user, remember=True)
        # 세션 저장 보장
        session.permanent = True
        # 세션 저장 강제
        from flask import session as flask_session
        flask_session.permanent = True
        # 세션 저장 확인
        try:
            flask_session.modified = True
        except:
            pass
        console.log(f"[INFO] Google 로그인 성공: {user.username} ({user.email}), 세션 저장 완료")
        
        # 리다이렉트 URL 동적 생성 (현재 요청의 호스트 사용)
        scheme = request.scheme  # http 또는 https
        host = request.host  # 호스트명과 포트 포함
        
        # 환경 변수에서 명시적으로 설정된 경우 사용 (배포 환경)
        if os.environ.get('SITE_URL'):
            site_url = os.environ.get('SITE_URL').rstrip('/')
            redirect_url = site_url
        else:
            # 로컬 개발 환경에서는 request에서 가져온 정보 사용
            redirect_url = f"{scheme}://{host}"
        
        console.log(f"[INFO] 리다이렉트 URL: {redirect_url}")
        
        return jsonify({
            'success': True,
            'redirect': request.args.get('next') or redirect_url
        })
        
    except Exception as e:
        console.log(f"[ERROR] Supabase Auth 콜백 API 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/register')
def register():
    """회원가입 페이지"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """로그아웃"""
    logout_user()
    # Supabase Auth 세션은 클라이언트 사이드에서 관리
    return redirect(url_for('index'))


@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """회원가입 API"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        from utils.auth import AuthManager
        auth_manager = AuthManager()
        result = auth_manager.register_user(username, email, password)
        
        return jsonify(result)
    except Exception as e:
        console.log(f"[ERROR] 회원가입 API 오류: {e}")
        return jsonify({'success': False, 'message': '오류가 발생했습니다.'}), 500


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """로그인 API"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        from utils.auth import AuthManager
        auth_manager = AuthManager()
        result = auth_manager.login_user(username, password)
        
        if result['success']:
            # Flask-Login으로 사용자 로그인
            user = User(
                user_id=result['user']['id'],
                username=result['user']['username'],
                email=result['user']['email']
            )
            login_user(user, remember=True)
            # 세션 저장 보장
            session.permanent = True
            try:
                session.modified = True
            except:
                pass
            console.log(f"[INFO] 로그인 성공: {user.username} (ID: {user.id}), 세션 저장 완료")
            
            # 리다이렉트 URL 동적 생성 (현재 요청의 호스트 사용)
            scheme = request.scheme  # http 또는 https
            host = request.host  # 호스트명과 포트 포함
            
            # 환경 변수에서 명시적으로 설정된 경우 사용 (배포 환경)
            if os.environ.get('SITE_URL'):
                site_url = os.environ.get('SITE_URL').rstrip('/')
                redirect_url = site_url
            else:
                # 로컬 개발 환경에서는 request에서 가져온 정보 사용
                redirect_url = f"{scheme}://{host}"
            
            console.log(f"[INFO] 리다이렉트 URL: {redirect_url}")
            result['redirect'] = request.args.get('next') or redirect_url
        
        return jsonify(result)
    except Exception as e:
        console.log(f"[ERROR] 로그인 API 오류: {e}")
        return jsonify({'success': False, 'message': '오류가 발생했습니다.'}), 500


@app.route('/api/auth/me')
def api_me():
    """현재 로그인한 사용자 정보"""
    if current_user.is_authenticated:
        return jsonify({
            'success': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email
            }
        })
    return jsonify({'success': False, 'message': '로그인되지 않았습니다.'}), 401


@app.route('/')
def index():
    """랜딩 페이지"""
    console.log("[Route] / - 랜딩 페이지 요청")
    
    featured_track = None
    daily_curator_track = None
    recent_diary = None
    activity_stats = {
        'total_tracks': 0,
        'total_comments': 0,
        'total_posts': 0,
        'growth': 12.4
    }
    
    # 로그인한 사용자인지 확인
    is_authenticated = current_user.is_authenticated
    current_user_id = str(current_user.id) if is_authenticated else None
    
    try:
        if supabase_available:
            supabase = SupabaseClient()
            
            if is_authenticated and current_user_id:
                # 로그인한 사용자: 자신의 콘텐츠만 표시
                # LIVE BROADCAST: 현재 사용자의 최신 곡 1개 (다른 사용자 곡 표시 안 함)
                user_tracks = supabase.get_tracks(limit=1, offset=0, user_id=current_user_id, playlist_id=None)
                if user_tracks:
                    featured_track = user_tracks[0]
                    if featured_track.get("duration_seconds"):
                        featured_track["duration_str"] = _format_duration(featured_track.get("duration_seconds"))
                # 사용자 곡이 없으면 featured_track은 None으로 유지 (템플릿에서 "곡이 없습니다" 표시)
                
                # DAILY CURATOR: 현재 사용자의 랜덤 곡 1개 (다른 사용자 곡 표시 안 함)
                random_tracks = supabase.get_random_tracks(count=1, user_id=current_user_id, exclude_ids=None)
                if random_tracks:
                    daily_curator_track = random_tracks[0]
                    if daily_curator_track.get("duration_seconds"):
                        daily_curator_track["duration_str"] = _format_duration(daily_curator_track.get("duration_seconds"))
                # 사용자 곡이 없으면 daily_curator_track은 None으로 유지
                
                # 최근 다이어리 게시글 1개 (현재 사용자만)
                user_posts = supabase.get_posts(limit=1, offset=0, user_id=current_user_id)
                if user_posts:
                    recent_diary = user_posts[0]
                # 사용자 게시글이 없으면 recent_diary는 None으로 유지
                
                # 활동 통계 (현재 사용자)
                try:
                    user_tracks_count = supabase.get_tracks(limit=1000, offset=0, user_id=current_user_id, playlist_id=None)
                    activity_stats['total_tracks'] = len(user_tracks_count) if user_tracks_count else 0
                except:
                    pass
                
                try:
                    user_posts_count = supabase.get_posts(limit=1000, offset=0, user_id=current_user_id)
                    activity_stats['total_posts'] = len(user_posts_count) if user_posts_count else 0
                except:
                    pass
            else:
                # 로그인하지 않은 사용자: 곡 정보 표시 안 함
                # featured_track, daily_curator_track, recent_diary는 모두 None으로 유지
                # 템플릿에서 "로그인이 필요합니다" 메시지 표시
                pass
                
    except Exception as e:
        print(f"[ERROR] 인덱스 페이지 데이터 로드 실패: {e}")
        import traceback
        traceback.print_exc()
    
    return render_template(
        'index.html',
        featured_track=featured_track,
        daily_curator_track=daily_curator_track,
        recent_diary=recent_diary,
        activity_stats=activity_stats,
        is_authenticated=is_authenticated
    )


@app.route('/tracks')
@app.route('/archive')
def playlists():
    """플레이리스트 목록 페이지"""
    console.log("[Route] /tracks - 플레이리스트 목록 페이지 요청")
    
    # 로그인 체크
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    error_message = None

    try:
        if supabase_available:
            supabase = SupabaseClient()
            current_user_id = str(current_user.id)
            
            # 현재 로그인한 사용자의 플레이리스트 조회
            playlists = supabase.get_playlists(user_id=current_user_id, limit=100, offset=0)
            
            # 플레이리스트에 속하지 않은 곡들 조회
            unassigned_tracks = supabase.get_tracks(limit=100, offset=0, user_id=current_user_id, playlist_id="")
            
            # duration_str 생성
            for t in unassigned_tracks:
                try:
                    t["duration_str"] = _format_duration(t.get("duration_seconds"))
                except Exception:
                    t["duration_str"] = ""
        else:
            playlists = []
            unassigned_tracks = []
    except Exception as e:
        print(f"[ERROR] 플레이리스트 조회 실패: {e}")
        error_message = "플레이리스트 목록을 불러오지 못했어요. 잠시 후 다시 시도해주세요."
        playlists = []
    
    # 다음 페이지 유무는 “가득 찼는지”로만 판단(정확한 total count 없이도 최소 UX 제공)

    return render_template(
        'playlists.html',
        playlists=playlists,
        unassigned_tracks=unassigned_tracks,
        error=error_message
    )


@app.route('/worldcup')
def worldcup():
    """이상형 월드컵 페이지"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    return render_template('worldcup.html')


@app.route('/api/worldcup/tracks', methods=['GET'])
def get_worldcup_tracks():
    """이상형 월드컵용 랜덤 곡 2개 조회 (모든 사용자의 곡, 이미 본 곡 제외)"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503
        
        supabase = SupabaseClient()
        
        # exclude 파라미터에서 이미 본 곡 ID 목록 가져오기
        exclude_ids = []
        exclude_param = request.args.get('exclude', '')
        if exclude_param:
            exclude_ids = [tid.strip() for tid in exclude_param.split(',') if tid.strip()]
        
        # 모든 사용자의 곡 중에서 랜덤 곡 2개 조회 (이미 본 곡 제외)
        tracks = supabase.get_random_tracks(count=2, user_id=None, exclude_ids=exclude_ids)
        
        if len(tracks) < 2:
            return jsonify({'success': False, 'error': '더 이상 볼 곡이 없습니다. 모든 곡을 다 보셨습니다.'}), 400
        
        # duration_str 추가
        for t in tracks:
            t["duration_str"] = _format_duration(t.get("duration_seconds"))
        
        return jsonify({'success': True, 'tracks': tracks}), 200
    except Exception as e:
        print(f"[ERROR] 월드컵 곡 조회 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/worldcup/vote', methods=['POST'])
def vote_worldcup():
    """이상형 월드컵 투표 저장"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503
        
        data = request.get_json() or {}
        track_a_id = data.get('track_a_id')
        track_b_id = data.get('track_b_id')
        winner_id = data.get('winner_id')
        
        if not track_a_id or not track_b_id or not winner_id:
            return jsonify({'success': False, 'error': '필수 파라미터가 없습니다.'}), 400
        
        if winner_id not in [track_a_id, track_b_id]:
            return jsonify({'success': False, 'error': '잘못된 선택입니다.'}), 400
        
        supabase = SupabaseClient()
        current_user_id = str(current_user.id)
        
        # 투표 저장
        battle_id = supabase.create_track_battle(
            user_id=current_user_id,
            track_a_id=track_a_id,
            track_b_id=track_b_id,
            winner_id=winner_id
        )
        
        if battle_id:
            return jsonify({'success': True, 'battle_id': battle_id}), 201
        else:
            return jsonify({'success': False, 'error': '투표 저장에 실패했습니다.'}), 500
    except Exception as e:
        print(f"[ERROR] 월드컵 투표 저장 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/diary')
def diary():
    """일기(기존 커뮤니티) 피드 - 전체 사용자 접근 가능"""
    console.log("[Route] /diary - 일기 피드 페이지 요청")
    
    error_message = None

    # 페이지네이션
    try:
        page = int(request.args.get('page', '1'))
    except Exception:
        page = 1

    if page < 1:
        page = 1

    try:
        per_page = int(request.args.get('per_page', str(COMMUNITY_PER_PAGE_DEFAULT)))
    except Exception:
        per_page = COMMUNITY_PER_PAGE_DEFAULT

    if per_page < 1:
        per_page = COMMUNITY_PER_PAGE_DEFAULT
    if per_page > COMMUNITY_PER_PAGE_MAX:
        per_page = COMMUNITY_PER_PAGE_MAX

    offset = (page - 1) * per_page

    try:
        if supabase_available:
            supabase = SupabaseClient()
            # 전체 사용자의 게시글 조회 (user_id 필터 제거)
            posts = supabase.get_posts(limit=per_page, offset=offset, user_id=None)
        else:
            posts = []
    except Exception as e:
        print(f"[ERROR] 커뮤니티 게시글 조회 실패: {e}")
        error_message = "게시글을 불러오지 못했어요. 잠시 후 다시 시도해주세요."
        posts = []

    has_next = len(posts) == per_page
    return render_template(
        'community.html',
        posts=posts,
        error=error_message,
        page=page,
        per_page=per_page,
        has_next=has_next
    )


@app.route('/studio')
@app.route('/music-studio')
def music_studio():
    """음악 스튜디오 페이지"""
    console.log("[Route] /studio - 음악 스튜디오 페이지 요청")
    return render_template('index.html')


@app.route('/music-analysis')
@app.route('/analysis-studio')
def music_analysis():
    """분석 스튜디오 페이지"""
    console.log("[Route] /music-analysis | /analysis-studio - 분석 스튜디오 페이지 요청")
    return render_template('music_analysis.html')


@app.route('/music-video')
@app.route('/video-studio')
def music_video():
    """영상 스튜디오 페이지"""
    console.log("[Route] /music-video | /video-studio - 영상 스튜디오 페이지 요청")
    return render_template('music_video.html')


@app.route('/community')
def community():
    """커뮤니티 페이지 (리다이렉트)"""
    return redirect(url_for('diary'))


@app.route('/community/post/<post_id>')
@app.route('/diary/post/<post_id>')
def community_post(post_id):
    """커뮤니티 게시글 상세 페이지"""
    console.log(f"[Route] /community/post/{post_id} - 게시글 상세 페이지 요청")
    try:
        if supabase_available:
            supabase = SupabaseClient()
            post = supabase.get_post(post_id)
        else:
            post = None
    except Exception as e:
        print(f"[ERROR] 게시글 조회 실패: {e}")
        post = None
    
    if not post:
        return render_template('community.html', error="게시글을 찾을 수 없습니다."), 404
    
    return render_template('community_post.html', post=post, post_id=post_id)


@app.route('/community/write')
@app.route('/diary/write')
def community_write():
    """글쓰기 페이지"""
    console.log("[Route] /community/write - 글쓰기 페이지 요청")
    return render_template('community_write.html')


@app.route('/track/<track_id>')
def track_detail(track_id):
    """곡 상세 + 코멘트"""
    console.log(f"[Route] /track/{track_id} - 트랙 상세 페이지 요청")
    if not supabase_available:
        return render_template('tracks.html', error="Supabase 연결이 불가능합니다.", tracks=[]), 503

    supabase = SupabaseClient()
    track = supabase.get_track(track_id)
    if not track:
        return render_template('tracks.html', error="곡을 찾을 수 없습니다.", tracks=[]), 404

    track["duration_str"] = _format_duration(track.get("duration_seconds"))

    source = track.get("source")
    embed = {"type": source, "url": track.get("url"), "source_id": track.get("source_id")}

    # 현재 로그인한 사용자 ID (이미 로그인 체크 완료)
    current_user_id = str(current_user.id)
    
    # 트랙을 추가한 사용자 ID
    track_user_id = track.get('user_id')
    
    # 코멘트 조회 (본인이 추가한 곡이면 본인 코멘트만, 아니면 모든 코멘트)
    comments = supabase.get_track_comments(
        track_id, 
        limit=50, 
        offset=0,
        track_user_id=track_user_id,
        current_user_id=current_user_id
    )
    
    return render_template('track_detail.html', track=track, embed=embed, comments=comments)


@app.route('/playlist/<playlist_id>')
def playlist_detail(playlist_id):
    """플레이리스트 상세 페이지 - 곡 목록/추가"""
    console.log(f"[Route] /playlist/{playlist_id} - 플레이리스트 상세 페이지 요청")
    
    # 로그인 체크
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    if not supabase_available:
        return render_template('playlist_detail.html', error="Supabase 연결이 불가능합니다.", playlist=None, tracks=[]), 503

    supabase = SupabaseClient()
    playlist = supabase.get_playlist(playlist_id)
    
    if not playlist:
        return render_template('playlist_detail.html', error="플레이리스트를 찾을 수 없습니다.", playlist=None, tracks=[]), 404
    
    # 플레이리스트 소유자 확인
    current_user_id = str(current_user.id)
    if playlist.get('user_id') != current_user_id:
        return render_template('playlist_detail.html', error="접근 권한이 없습니다.", playlist=None, tracks=[]), 403
    
    # 플레이리스트의 곡 목록 조회
    tracks = supabase.get_playlist_tracks(playlist_id, limit=100, offset=0)
    
    # duration_str 생성
    for t in tracks:
        try:
            t["duration_str"] = _format_duration(t.get("duration_seconds"))
        except Exception:
            t["duration_str"] = ""

    return render_template('playlist_detail.html', playlist=playlist, tracks=tracks, error=None)


@app.route('/api/playlists', methods=['POST'])
def create_playlist_api():
    """플레이리스트 생성 API"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503
        
        data = request.get_json() or {}
        # 기본 이름으로 자동 생성
        name = "playlist"
        description = None
        
        supabase = SupabaseClient()
        current_user_id = str(current_user.id)
        
        playlist_id = supabase.create_playlist(name, description, current_user_id)
        
        if playlist_id:
            return jsonify({'success': True, 'playlist_id': playlist_id}), 201
        else:
            return jsonify({'success': False, 'error': '플레이리스트 생성에 실패했습니다.'}), 500
    except Exception as e:
        print(f"[ERROR] 플레이리스트 생성 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/playlists/<playlist_id>', methods=['PUT'])
def update_playlist_api(playlist_id):
    """플레이리스트 수정 API"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503
        
        supabase = SupabaseClient()
        playlist = supabase.get_playlist(playlist_id)
        
        if not playlist:
            return jsonify({'success': False, 'error': '플레이리스트를 찾을 수 없습니다.'}), 404
        
        # 소유자 확인
        current_user_id = str(current_user.id)
        if playlist.get('user_id') != current_user_id:
            return jsonify({'success': False, 'error': '본인의 플레이리스트만 수정할 수 있습니다.'}), 403
        
        data = request.get_json() or {}
        name = data.get('name')
        description = data.get('description')
        icon_url = data.get('icon_url')
        
        success = supabase.update_playlist(playlist_id, name=name, description=description, icon_url=icon_url)
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': '플레이리스트 수정에 실패했습니다.'}), 500
    except Exception as e:
        print(f"[ERROR] 플레이리스트 수정 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/playlists/<playlist_id>', methods=['DELETE'])
def delete_playlist_api(playlist_id):
    """플레이리스트 삭제 API"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503
        
        supabase = SupabaseClient()
        playlist = supabase.get_playlist(playlist_id)
        
        if not playlist:
            return jsonify({'success': False, 'error': '플레이리스트를 찾을 수 없습니다.'}), 404
        
        # 소유자 확인
        current_user_id = str(current_user.id)
        if playlist.get('user_id') != current_user_id:
            return jsonify({'success': False, 'error': '본인의 플레이리스트만 삭제할 수 있습니다.'}), 403
        
        success = supabase.delete_playlist(playlist_id)
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': '플레이리스트 삭제에 실패했습니다.'}), 500
    except Exception as e:
        print(f"[ERROR] 플레이리스트 삭제 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tracks', methods=['POST'])
def create_track_api():
    """참여형 곡 추가 (URL → 메타데이터 자동 수집) - 플레이리스트에 추가"""
    try:
        data = request.get_json() or {}
        url = str(data.get("url", "")).strip()
        playlist_id = data.get("playlist_id")  # 플레이리스트 ID (optional)
        
        if not url:
            return jsonify({"success": False, "error": "URL이 필요합니다."}), 400
        if len(url) > TRACK_URL_MAX_LEN:
            return jsonify({"success": False, "error": "URL이 너무 깁니다."}), 400

        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503

        source = _guess_track_source(url)
        if source == "unknown":
            return jsonify({"success": False, "error": "현재는 SoundCloud/YouTube 링크만 지원합니다."}), 400

        supabase = SupabaseClient()
        
        # 현재 로그인한 사용자 ID 가져오기
        user_id = None
        if current_user.is_authenticated:
            user_id = str(current_user.id)
        else:
            return jsonify({"success": False, "error": "로그인이 필요합니다."}), 401
        
        # playlist_id가 제공된 경우 소유자 확인
        if playlist_id:
            playlist = supabase.get_playlist(playlist_id)
            if not playlist:
                return jsonify({"success": False, "error": "플레이리스트를 찾을 수 없습니다."}), 404
            
            if playlist.get('user_id') != user_id:
                return jsonify({"success": False, "error": "본인의 플레이리스트에만 곡을 추가할 수 있습니다."}), 403
            
            # 같은 플레이리스트에 같은 URL이 있는지 확인
            existing = supabase.get_track_by_url(url, user_id=user_id, playlist_id=playlist_id)
        else:
            # 플레이리스트 없이 추가하는 경우, 같은 사용자의 같은 URL이 있는지 확인 (플레이리스트 없는 것만)
            existing = supabase.get_track_by_url(url, user_id=user_id, playlist_id=None)
        existing_id = existing.get("id") if existing else None

        extractor = LinkExtractor(console_log=console.log)

        title = None
        artist = None
        duration = None
        thumbnail = None
        source_id = None

        if source == "youtube":
            source_id = extractor.extract_video_id(url)
            info = extractor.get_video_info(url)
            if info and info.get("success"):
                title = info.get("title")
                artist = info.get("uploader")
                duration = info.get("duration")
                thumbnail = info.get("thumbnail")

        if not title:
            # fallback: yt-dlp 기반 메타 (soundcloud 포함)
            meta = extractor.get_stream_url(url)
            if meta.get("success"):
                title = meta.get("title")
                artist = meta.get("uploader")
                duration = meta.get("duration")
                thumbnail = meta.get("thumbnail")

        title = (title or "Unknown").strip()[:TRACK_TITLE_MAX_LEN]
        artist = (artist or "").strip()[:TRACK_ARTIST_MAX_LEN] or None
        duration_seconds = int(duration) if isinstance(duration, (int, float)) else None

        # 확장 가능한 메타데이터(JSON) 저장: 지금은 기본 메타만 넣고, 추후 지표/통계(stats) 추가 여지를 남김
        fetched_at = datetime.now().isoformat()
        metadata = {
            "source": source,
            "source_id": source_id,
            "original_url": url,
            "fetched_at": fetched_at,
            "provider": {
                "title": title,
                "uploader": artist,
                "duration_seconds": duration_seconds,
                "thumbnail_url": thumbnail,
            },
            "stats": {},  # future: views/likes/plays/etc
        }

        # 이미 등록된 트랙이면: metadata가 비어있을 때만 보강(비용/변경 최소화)
        if existing_id:
            try:
                existing_meta = existing.get("metadata")
                is_empty_meta = (existing_meta is None) or (existing_meta == {}) or (existing_meta == "null")
            except Exception:
                is_empty_meta = True

            if is_empty_meta:
                supabase.update_track(existing_id, {
                    "source": source,
                    "source_id": source_id,
                    "title": title,
                    "artist": artist,
                    "duration_seconds": duration_seconds,
                    "thumbnail_url": thumbnail,
                    "metadata": metadata,
                })

            return jsonify({"success": True, "track_id": existing_id, "playlist_id": playlist_id, "existing": True}), 200

        track_id = supabase.create_track(
            url=url,
            source=source,
            source_id=source_id,
            title=title,
            artist=artist,
            duration_seconds=duration_seconds,
            thumbnail_url=thumbnail,
            metadata=metadata,
            user_id=user_id,
            playlist_id=playlist_id,
        )

        if not track_id:
            return jsonify({"success": False, "error": "곡 등록에 실패했습니다."}), 500

        # playlist_id가 있으면 플레이리스트 상세 페이지로, 없으면 플레이리스트 목록 페이지로
        return jsonify({"success": True, "track_id": track_id, "playlist_id": playlist_id, "existing": False}), 201
    except Exception as e:
        print(f"[ERROR] 트랙 생성 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tracks/<track_id>/playlist', methods=['PUT'])
def add_track_to_playlist_api(track_id):
    """곡을 플레이리스트에 추가"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503
        
        supabase = SupabaseClient()
        track = supabase.get_track(track_id)
        
        if not track:
            return jsonify({'success': False, 'error': '곡을 찾을 수 없습니다.'}), 404
        
        # 소유자 확인
        current_user_id = str(current_user.id)
        if track.get('user_id') != current_user_id:
            return jsonify({'success': False, 'error': '본인의 곡만 플레이리스트에 추가할 수 있습니다.'}), 403
        
        data = request.get_json() or {}
        playlist_id = data.get('playlist_id')
        
        if not playlist_id:
            return jsonify({'success': False, 'error': '플레이리스트 ID가 필요합니다.'}), 400
        
        # 플레이리스트 소유자 확인
        playlist = supabase.get_playlist(playlist_id)
        if not playlist:
            return jsonify({'success': False, 'error': '플레이리스트를 찾을 수 없습니다.'}), 404
        
        if playlist.get('user_id') != current_user_id:
            return jsonify({'success': False, 'error': '본인의 플레이리스트에만 곡을 추가할 수 있습니다.'}), 403
        
        # 곡을 플레이리스트에 추가
        success = supabase.update_track(track_id, {"playlist_id": playlist_id})
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': '플레이리스트에 추가에 실패했습니다.'}), 500
    except Exception as e:
        print(f"[ERROR] 곡을 플레이리스트에 추가 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tracks/<track_id>', methods=['DELETE'])
def delete_track_api(track_id):
    """곡 삭제 API (작성자 본인만 가능)"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503

        supabase = SupabaseClient()
        
        # 트랙 조회
        track = supabase.get_track(track_id)
        if not track:
            return jsonify({'success': False, 'error': '곡을 찾을 수 없습니다.'}), 404
        
        # 작성자 본인인지 확인
        track_user_id = track.get('user_id')
        current_user_id = str(current_user.id)
        
        # user_id가 있으면 user_id로 확인
        if track_user_id:
            if str(track_user_id) != current_user_id:
                return jsonify({'success': False, 'error': '본인이 추가한 곡만 삭제할 수 있습니다.'}), 403
        else:
            # user_id가 없는 경우 삭제 불가 (비로그인 상태의 곡은 이미 삭제됨)
            return jsonify({'success': False, 'error': '삭제할 수 없는 곡입니다.'}), 403
        
        # 삭제 진행
        ok = supabase.delete_track(track_id)
        if not ok:
            return jsonify({"success": False, "error": "삭제에 실패했습니다."}), 500
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"[ERROR] track 삭제 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tracks/order', methods=['PUT'])
def update_tracks_order_api():
    """곡 순서 변경 API"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503

        data = request.get_json() or {}
        track_orders = data.get('tracks', [])
        
        if not track_orders or not isinstance(track_orders, list):
            return jsonify({'success': False, 'error': '잘못된 요청입니다.'}), 400
        
        supabase = SupabaseClient()
        current_user_id = str(current_user.id)
        
        # 모든 트랙이 본인 것인지 확인
        for item in track_orders:
            track_id = item.get('id')
            if not track_id:
                continue
            track = supabase.get_track(track_id)
            if not track:
                return jsonify({'success': False, 'error': f'곡을 찾을 수 없습니다: {track_id}'}), 404
            track_user_id = track.get('user_id')
            if not track_user_id or str(track_user_id) != current_user_id:
                return jsonify({'success': False, 'error': '본인이 추가한 곡만 순서를 변경할 수 있습니다.'}), 403
        
        # 순서 업데이트
        ok = supabase.update_tracks_order(track_orders)
        if not ok:
            return jsonify({"success": False, "error": "순서 변경에 실패했습니다."}), 500
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"[ERROR] tracks 순서 변경 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tracks/<track_id>/comments', methods=['POST'])
def create_track_comment_api(track_id):
    """곡 코멘트 작성 API"""
    try:
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503

        data = request.get_json() or {}
        content = str(data.get("content", "")).strip()
        author = str(data.get("author", "Anonymous")).strip() or "Anonymous"

        if not content:
            return jsonify({"success": False, "error": "내용을 입력해주세요."}), 400
        if len(content) > TRACK_COMMENT_MAX_LEN:
            return jsonify({"success": False, "error": f"내용은 {TRACK_COMMENT_MAX_LEN}자 이하로 입력해주세요."}), 400
        if len(author) > TRACK_COMMENT_AUTHOR_MAX_LEN:
            return jsonify({"success": False, "error": f"닉네임은 {TRACK_COMMENT_AUTHOR_MAX_LEN}자 이하로 입력해주세요."}), 400

        ip_address = _get_client_ip()
        now = datetime.now()
        last_at = _track_last_comment_at_by_ip.get(ip_address)
        if last_at and (now - last_at).total_seconds() < TRACK_COMMENT_MIN_INTERVAL_SECONDS:
            return jsonify({"success": False, "error": "너무 빠르게 작성하고 있어요. 잠시 후 다시 시도해주세요."}), 429

        supabase = SupabaseClient()
        # 현재 로그인한 사용자 ID
        user_id = None
        if current_user.is_authenticated:
            user_id = str(current_user.id)
            # 로그인한 경우 author를 사용자명으로 설정
            if author == 'Anonymous' or not author:
                author = current_user.username
        
        comment_id = supabase.create_track_comment(track_id, content=content, author=author, user_id=user_id)
        if not comment_id:
            return jsonify({"success": False, "error": "코멘트 저장에 실패했습니다."}), 500

        _track_last_comment_at_by_ip[ip_address] = now
        return jsonify({"success": True, "comment_id": comment_id}), 201
    except Exception as e:
        print(f"[ERROR] track_comments 생성 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/track_comments/<comment_id>', methods=['DELETE'])
def delete_track_comment_api(comment_id):
    """곡 코멘트 삭제 API (작성자 본인만 가능)"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if not supabase_available:
            return jsonify({"success": False, "error": "Supabase 연결이 불가능합니다."}), 503

        supabase = SupabaseClient()
        
        # 코멘트 조회
        try:
            comment_response = (
                supabase.client.table("track_comments")
                .select("*")
                .eq("id", comment_id)
                .single()
                .execute()
            )
            comment = comment_response.data if comment_response.data else None
        except:
            comment = None
        
        if not comment:
            return jsonify({'success': False, 'error': '코멘트를 찾을 수 없습니다.'}), 404
        
        # 작성자 본인인지 확인
        comment_user_id = comment.get('user_id')
        current_user_id = str(current_user.id)
        
        # user_id가 있으면 user_id로 확인, 없으면 author로 확인 (기존 데이터 호환)
        if comment_user_id:
            # UUID 타입일 수 있으므로 string으로 변환하여 비교
            if str(comment_user_id) != current_user_id:
                return jsonify({'success': False, 'error': '본인이 작성한 코멘트만 삭제할 수 있습니다.'}), 403
        else:
            # user_id가 없는 경우 author로 확인 (기존 데이터)
            if comment.get('author') != current_user.username:
                return jsonify({'success': False, 'error': '본인이 작성한 코멘트만 삭제할 수 있습니다.'}), 403
        
        # 삭제 진행
        ok = supabase.delete_track_comment(comment_id)
        if not ok:
            return jsonify({"success": False, "error": "삭제에 실패했습니다."}), 500
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"[ERROR] track_comment 삭제 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/community/posts', methods=['POST'])
def create_post():
    """게시글 생성 API"""
    try:
        data = request.get_json()
        data = data or {}

        title = str(data.get('title', '')).strip()
        content = str(data.get('content', '')).strip()
        author = str(data.get('author', 'Anonymous')).strip() or 'Anonymous'

        # 기본 스팸 방지(연속 작성 제한)
        ip_address = _get_client_ip()
        now = datetime.now()
        last_at = _community_last_post_at_by_ip.get(ip_address)
        if last_at and (now - last_at).total_seconds() < COMMUNITY_POST_MIN_INTERVAL_SECONDS:
            return jsonify({'success': False, 'error': '너무 빠르게 작성하고 있어요. 잠시 후 다시 시도해주세요.'}), 429

        validation_error = _validate_post_payload(title, content, author)
        if validation_error:
            return jsonify({'success': False, 'error': validation_error}), 400
        
        if supabase_available:
            supabase = SupabaseClient()
            
            # 현재 로그인한 사용자 ID 가져오기
            user_id = None
            if current_user.is_authenticated:
                user_id = str(current_user.id)
                # 로그인한 경우 author를 사용자명으로 설정
                if author == 'Anonymous' or not author:
                    author = current_user.username
            
            post_id = supabase.create_post(title, content, author, user_id=user_id)
            
            if post_id:
                _community_last_post_at_by_ip[ip_address] = now
                return jsonify({'success': True, 'post_id': post_id}), 201
            else:
                return jsonify({'success': False, 'error': '게시글 생성에 실패했습니다.'}), 500
        else:
            return jsonify({'success': False, 'error': 'Supabase 연결이 불가능합니다.'}), 503
            
    except Exception as e:
        print(f"[ERROR] 게시글 생성 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/community/posts/<post_id>', methods=['PUT'])
def update_post_api(post_id):
    """게시글 수정 API"""
    try:
        data = request.get_json() or {}
        title = str(data.get('title', '')).strip()
        content = str(data.get('content', '')).strip()

        # 수정은 닉네임 변경을 받지 않지만(현재 스키마/UX 기준), 검증은 동일하게 적용
        validation_error = _validate_post_payload(title, content, author="")
        if validation_error:
            return jsonify({'success': False, 'error': validation_error}), 400
        
        if supabase_available:
            supabase = SupabaseClient()
            success = supabase.update_post(post_id, title, content)
            
            if success:
                return jsonify({'success': True}), 200
            else:
                return jsonify({'success': False, 'error': '게시글 수정에 실패했습니다.'}), 500
        else:
            return jsonify({'success': False, 'error': 'Supabase 연결이 불가능합니다.'}), 503
            
    except Exception as e:
        print(f"[ERROR] 게시글 수정 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/community/posts/<post_id>', methods=['DELETE'])
def delete_post_api(post_id):
    """게시글 삭제 API (작성자 본인만 가능)"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        
        if supabase_available:
            supabase = SupabaseClient()
            
            # 게시글 조회
            post = supabase.get_post(post_id)
            if not post:
                return jsonify({'success': False, 'error': '게시글을 찾을 수 없습니다.'}), 404
            
            # 작성자 본인인지 확인
            post_user_id = post.get('user_id')
            current_user_id = str(current_user.id)
            
            # user_id가 있으면 user_id로 확인, 없으면 author로 확인 (기존 데이터 호환)
            if post_user_id:
                # UUID 타입일 수 있으므로 string으로 변환하여 비교
                if str(post_user_id) != current_user_id:
                    return jsonify({'success': False, 'error': '본인이 작성한 게시글만 삭제할 수 있습니다.'}), 403
            else:
                # user_id가 없는 경우 author로 확인 (기존 데이터)
                if post.get('author') != current_user.username:
                    return jsonify({'success': False, 'error': '본인이 작성한 게시글만 삭제할 수 있습니다.'}), 403
            
            # 삭제 진행
            success = supabase.delete_post(post_id)
            
            if success:
                return jsonify({'success': True}), 200
            else:
                return jsonify({'success': False, 'error': '게시글 삭제에 실패했습니다.'}), 500
        else:
            return jsonify({'success': False, 'error': 'Supabase 연결이 불가능합니다.'}), 503
            
    except Exception as e:
        print(f"[ERROR] 게시글 삭제 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/upload', methods=['POST'])
def upload_files():
    """파일 업로드 처리"""
    console.log("[Route] /upload - 파일 업로드 요청")
    
    if 'files' not in request.files:
        console.log("[Upload] 파일이 없음")
        return jsonify({'error': '파일이 없습니다'}), 400
    
    files = request.files.getlist('files')
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # 안전한 파일명 생성
            filename = generate_safe_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            console.log(f"[Upload] 파일 저장 경로: {filepath}")
            console.log(f"[Upload] 폴더 존재 여부: {os.path.exists(app.config['UPLOAD_FOLDER'])}")
            
            # 파일 저장
            file.save(filepath)
            console.log(f"[Upload] 파일 저장 완료: {filename}")
            
            # Windows에서 파일 저장 후 잠시 대기
            import time
            time.sleep(0.1)
            
            console.log(f"[Upload] 저장된 파일 존재 확인: {os.path.exists(filepath)}")
            console.log(f"[Upload] 파일 크기: {os.path.getsize(filepath) if os.path.exists(filepath) else 'N/A'}")
            
            # 파일이 실제로 존재하는지 재확인
            if not os.path.exists(filepath):
                console.log(f"[Upload] 파일 저장 실패: {filepath}")
                return jsonify({
                    'success': False,
                    'error': f"{file.filename}: 파일 저장에 실패했습니다"
                }), 400
            
            # 오디오 파일 검증
            validation = validate_audio_file(filepath)
            
            if validation['valid']:
                # 파일 정보 수집
                file_info = {
                    'filename': filename,
                    'original_name': file.filename,
                    'size': os.path.getsize(filepath),
                    'size_mb': get_file_size_mb(filepath),
                    'duration': validation['info']['duration'],
                    'duration_str': validation['info']['duration_str'],
                    'format': validation['info']['format'],
                    'path': filepath
                }
                uploaded_files.append(file_info)
                console.log(f"[Upload] 검증 통과: {filename}")
            else:
                # 검증 실패 시 파일 삭제
                os.remove(filepath)
                console.log(f"[Upload] 검증 실패: {validation['error']}")
                return jsonify({
                    'success': False,
                    'error': f"{file.filename}: {validation['error']}"
                }), 400
        else:
            console.log(f"[Upload] 허용되지 않은 파일: {file.filename}")
            return jsonify({
                'success': False,
                'error': f"{file.filename}: 지원하지 않는 파일 형식입니다"
            }), 400
    
    return jsonify({
        'success': True,
        'files': uploaded_files,
        'count': len(uploaded_files)
    })


# 처리 작업 저장소
processing_jobs = {}

@app.route('/process', methods=['POST'])
def process_audio():
    """오디오 파일 처리"""
    console.log("[Route] /process - 오디오 처리 요청")
    
    data = request.get_json()
    console.log(f"[Process] 받은 데이터: {json.dumps(data, indent=2)}")
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # 처리 작업 시작
    thread = threading.Thread(
        target=process_audio_job,
        args=(job_id, data)
    )
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': '처리를 시작했습니다'
    })


def process_audio_job(job_id, data):
    """백그라운드 오디오 처리 작업"""
    console.log(f"[Job] {job_id} - 처리 작업 시작")
    
    # 처리 상태 초기화
    processing_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': '처리 준비 중...',
        'result': None
    }
    
    try:
        # 오디오 프로세서 생성
        processor = AudioProcessor(console_log=console.log, processed_folder=app.config['PROCESSED_FOLDER'])
        
        # 파일 정보 준비
        file_list = []
        for file_info in data['files']:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info['filename'])
            console.log(f"[Process] 파일 경로 구성: {file_info['filename']} -> {file_path}")
            console.log(f"[Process] 파일 존재 여부: {os.path.exists(file_path)}")
            file_list.append({
                'filename': file_path,
                'settings': file_info['settings']
            })
        
        # 출력 파일명 생성
        output_filename = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # 진행률 콜백 함수
        def progress_callback(progress, message):
            processing_jobs[job_id]['progress'] = progress
            processing_jobs[job_id]['message'] = message
            console.log(f"[Job] {job_id} - {progress}% - {message}")
        
        # 오디오 병합 실행
        result = processor.merge_audio_files(
            file_list=file_list,
            global_settings=data['globalSettings'],
            output_path=output_path,
            progress_callback=progress_callback
        )
        
        # 처리 완료
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 100
        processing_jobs[job_id]['message'] = '처리 완료!'
        processing_jobs[job_id]['result'] = result
        
        console.log(f"[Job] {job_id} - 처리 완료: {result}")
        
    except Exception as e:
        # 오류 처리
        console.log(f"[Job] {job_id} - 오류 발생: {str(e)}")
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['message'] = f'오류: {str(e)}'
        

@app.route('/process/status/<job_id>')
def process_status(job_id):
    """처리 작업 상태 확인"""
    if job_id not in processing_jobs:
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    job_info = processing_jobs[job_id]
    
    # 완료된 작업은 정보 제거 (메모리 정리)
    if job_info['status'] == 'completed' and job_info.get('result'):
        result = job_info['result']
        
        # download_url이 없으면 파일명을 기반으로 생성
        if ('new_filename' in result or 'filename' in result) and 'download_url' not in result:
            download_filename = result.get('new_filename') or result.get('filename')
            result['download_url'] = f"/download/{download_filename}"
            console.log(f"[Status] download_url 생성: {result['download_url']} (파일명: {download_filename})")
        
        del processing_jobs[job_id]
        return jsonify({
            'status': 'completed',
            'progress': 100,
            'message': '처리 완료!',
            'result': result
        })
    
    return jsonify(job_info)


@app.route('/files/list')
def list_files():
    """업로드된 파일 목록 확인"""
    console.log("[Route] /files/list - 파일 목록 요청")
    
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        files = []
        
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                if filename.lower().endswith(('.mp3', '.mp4', '.webm', '.m4a', '.wav')):
                    filepath = os.path.join(upload_folder, filename)
                    file_stat = os.stat(filepath)
                    
                    files.append({
                        'filename': filename,
                        'size': file_stat.st_size,
                        'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'is_extracted': any(pattern in filename.lower() for pattern in ['youtube_', '_30s.', '_plus', '_minus'])
                    })
        
        # 최신 파일 순으로 정렬
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        console.log(f"[Files] 총 {len(files)}개 파일 발견")
        
        return jsonify({
            'success': True,
            'files': files,
            'total': len(files)
        })
        
    except Exception as e:
        console.log(f"[Files] 파일 목록 조회 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/status/<job_id>')
def job_status(job_id):
    """모든 작업 상태 확인 (통합 엔드포인트)"""
    console.log(f"[Route] /status/{job_id} - 작업 상태 확인")
    
    if job_id not in processing_jobs:
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    job_info = processing_jobs[job_id]
    
    # 완료된 작업은 정보 제거 (메모리 정리) - 단, 결과를 먼저 반환
    if job_info['status'] in ['completed', 'error']:
        result = job_info.copy()  # 복사본 생성
        # 5초 후에 정리하도록 지연 (클라이언트가 결과를 받을 시간 확보)
        import threading
        def cleanup():
            import time
            time.sleep(5)
            if job_id in processing_jobs:
                del processing_jobs[job_id]
                console.log(f"[Cleanup] 작업 정보 정리: {job_id}")
        
        cleanup_thread = threading.Thread(target=cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        return jsonify(result)
    
    return jsonify(job_info)


@app.route('/extract', methods=['POST'])
def extract_from_link():
    """링크에서 음악 추출"""
    console.log("[Route] /extract - 링크 추출 요청")
    
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL이 필요합니다'}), 400
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # 추출 작업 시작
    thread = threading.Thread(
        target=extract_link_job,
        args=(job_id, url)
    )
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': '링크에서 음악 추출을 시작했습니다'
    })


def extract_link_job(job_id, url):
    """백그라운드 링크 추출 작업"""
    console.log(f"[Extract Job] {job_id} - 추출 시작: {url}")
    
    # 처리 상태 초기화
    processing_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': '링크 분석 중...',
        'result': None
    }
    
    try:
        # 링크 추출기 생성
        extractor = LinkExtractor(console_log=console.log)
        
        # 진행률 콜백 함수
        def progress_callback(progress, message):
            processing_jobs[job_id]['progress'] = progress
            processing_jobs[job_id]['message'] = message
            console.log(f"[Extract Job] {job_id} - {progress}% - {message}")
        
        # 음악 추출 실행
        result = extractor.extract_audio(
            url=url,
            output_folder=app.config['UPLOAD_FOLDER'],
            progress_callback=progress_callback
        )
        
        if result['success']:
            # 추출 완료
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['message'] = '추출 완료!'
            processing_jobs[job_id]['result'] = {
                'type': 'extract',
                'file_info': result['file_info']
            }
            
            console.log(f"[Extract Job] {job_id} - 추출 완료: {result['file_info']['filename']}")
        else:
            # 추출 실패
            processing_jobs[job_id]['status'] = 'error'
            processing_jobs[job_id]['message'] = result['error']
            console.log(f"[Extract Job] {job_id} - 추출 실패: {result['error']}")
        
    except Exception as e:
        # 오류 처리
        console.log(f"[Extract Job] {job_id} - 오류 발생: {str(e)}")
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['message'] = f'오류: {str(e)}'


@app.route('/extract_music', methods=['POST'])
def extract_music():
    """링크에서 음원 추출 (음원 추출 탭용)"""
    console.log("[Route] /extract_music - 음원 추출 요청")
    
    data = request.get_json()
    
    if not data or 'url' not in data:
        console.log("[Extract Music] URL이 없음")
        return jsonify({'error': 'URL이 필요합니다'}), 400
    
    url = data['url']
    
    # 링크 추출기가 없으면 오류 반환
    if not hasattr(app, 'link_extractor'):
        console.log("[Extract Music] LinkExtractor 없음")
        return jsonify({'error': '링크 추출 기능을 사용할 수 없습니다'}), 500
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    console.log(f"[Extract Music] 작업 ID: {job_id}, URL: {url}")
    
    # 백그라운드 작업 시작
    thread = threading.Thread(
        target=extract_music_job,
        args=(job_id, url)
    )
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': '음원 추출을 시작했습니다'
    })


def extract_music_job(job_id, url):
    """백그라운드 음원 추출 작업"""
    console.log(f"[Extract Music Job] {job_id} - 추출 시작: {url}")
    
    # 처리 상태 초기화
    processing_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': '링크 분석 중...',
        'result': None
    }
    
    try:
        # 링크 추출기 생성
        extractor = LinkExtractor(console_log=console.log)
        
        # 진행률 콜백 함수
        def progress_callback(progress, message):
            processing_jobs[job_id]['progress'] = progress
            processing_jobs[job_id]['message'] = message
            console.log(f"[Extract Music Job] {job_id} - {progress}% - {message}")
        
        # 음악 추출 실행
        result = extractor.extract_audio(
            url=url,
            output_folder=app.config['UPLOAD_FOLDER'],
            progress_callback=progress_callback
        )
        
        if result['success']:
            # 추출 완료
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['message'] = '추출 완료!'
            processing_jobs[job_id]['result'] = {
                'type': 'extract',
                'file_info': result['file_info']
            }
            
            console.log(f"[Extract Music Job] {job_id} - 추출 완료: {result['file_info']['filename']}")
        else:
            # 추출 실패
            processing_jobs[job_id]['status'] = 'error'
            processing_jobs[job_id]['message'] = result['error']
            console.log(f"[Extract Music Job] {job_id} - 추출 실패: {result['error']}")
        
    except Exception as e:
        # 오류 처리
        console.log(f"[Extract Music Job] {job_id} - 오류 발생: {str(e)}")
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['message'] = f'오류: {str(e)}'


@app.route('/extract_status/<job_id>')
def extract_status(job_id):
    """음원 추출 상태 확인"""
    if job_id not in processing_jobs:
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    return jsonify(processing_jobs[job_id])


@app.route('/api/get_stream_url', methods=['POST'])
def get_stream_url():
    """SoundCloud 등에서 스트리밍 URL 가져오기 (앱 등록 불필요)"""
    console.log("[Route] /api/get_stream_url - 스트리밍 URL 요청")
    
    data = request.get_json()
    
    if not data or 'url' not in data:
        console.log("[Stream URL] URL이 없음")
        return jsonify({'success': False, 'error': 'URL이 필요합니다'}), 400
    
    url = data['url']
    
    try:
        # LinkExtractor 사용
        extractor = LinkExtractor(console_log=console.log)
        result = extractor.get_stream_url(url)
        
        if result['success']:
            console.log(f"[Stream URL] 스트리밍 URL 추출 성공: {result.get('title', 'Unknown')}")
            return jsonify(result), 200
        else:
            console.log(f"[Stream URL] 스트리밍 URL 추출 실패: {result.get('error', 'Unknown error')}")
            return jsonify(result), 400
            
    except Exception as e:
        console.log(f"[Stream URL] 오류 발생: {str(e)}")
        return jsonify({'success': False, 'error': f'오류: {str(e)}'}), 500


@app.route('/upload_extract_file', methods=['POST'])
def upload_extract_file():
    """음원 추출 탭용 파일 업로드"""
    console.log("[Route] /upload_extract_file - 파일 업로드 요청")
    
    if 'file' not in request.files:
        console.log("[Upload Extract File] 파일이 없음")
        return jsonify({'error': '파일이 없습니다'}), 400
    
    file = request.files['file']
    
    if file and validate_audio_file(file.filename):
        # 파일 데이터 읽기 (중복 체크용)
        file_data = file.read()
        file.seek(0)  # 파일 포인터 초기화
        
        # 안전한 파일명 생성 (중복 체크 포함)
        filename = generate_safe_filename(file.filename, file_data, app.config['UPLOAD_FOLDER'])
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        console.log(f"[Upload Extract File] 파일 저장 경로: {filepath}")
        
        # 중복된 파일이면 저장하지 않고 기존 정보 반환
        if os.path.exists(filepath):
            console.log(f"[Upload Extract File] 중복 파일 발견, 기존 파일 사용: {filename}")
        else:
            # 파일 저장
            file.save(filepath)
            console.log(f"[Upload Extract File] 새 파일 저장 완료: {filename}")
        
        # 오디오 프로세서로 파일 정보 가져오기
        try:
            processor = AudioProcessor(console_log=console.log, processed_folder=app.config['PROCESSED_FOLDER'])
            audio_info = processor.get_audio_info(filepath)
            
            file_info = {
                'filename': filename,
                'original_name': file.filename,
                'filepath': filepath,
                'format': audio_info.get('format', 'unknown'),
                'duration': audio_info.get('duration', 0),
                'duration_str': audio_info.get('duration_str', '0:00'),
                'size_mb': get_file_size_mb(filepath)
            }
            
            return jsonify({
                'success': True,
                'file_info': file_info
            })
            
        except Exception as e:
            console.log(f"[Upload Extract File] 파일 정보 분석 오류: {str(e)}")
            return jsonify({'error': f'파일 분석 중 오류가 발생했습니다: {str(e)}'}), 500
    
    return jsonify({'error': '지원하지 않는 파일 형식입니다'}), 400


@app.route('/trim_audio', methods=['POST'])
def trim_audio():
    """음원 자르기 (30초)"""
    console.log("[Route] /trim_audio - 음원 자르기 요청")
    
    data = request.get_json()
    
    if not data or 'filename' not in data:
        return jsonify({'error': '파일명이 필요합니다'}), 400
    
    filename = data['filename']
    duration = data.get('duration', 30)  # 기본 30초
    
    # 파일 경로 확인
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(input_path):
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
    
    try:
        # 오디오 프로세서로 자르기
        processor = AudioProcessor(console_log=console.log, processed_folder=app.config['PROCESSED_FOLDER'])
        result = processor.trim_audio(input_path, duration)
        
        if result['success']:
            # 파일 정보 업데이트
            audio_info = processor.get_audio_info(result['output_path'])
            
            file_info = {
                'filename': result['filename'],
                'original_name': filename,
                'filepath': result['output_path'],
                'format': audio_info.get('format', 'unknown'),
                'duration': audio_info.get('duration', 0),
                'duration_str': audio_info.get('duration_str', '0:00'),
                'size_mb': get_file_size_mb(result['output_path'])
            }
            
            return jsonify({
                'success': True,
                'file_info': file_info,
                'message': f'음원이 {duration}초로 잘렸습니다'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        console.log(f"[Trim Audio] 오류: {str(e)}")
        return jsonify({'error': f'자르기 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/adjust_audio_pitch', methods=['POST'])
def adjust_audio_pitch():
    """음원 키(피치) 조절"""
    console.log("[Route] /adjust_audio_pitch - 키 조절 요청")
    
    data = request.get_json()
    
    if not data or 'filename' not in data:
        return jsonify({'error': '파일명이 필요합니다'}), 400
    
    filename = data['filename']
    pitch_shift = data.get('pitch_shift', 0)  # 반음 단위
    
    # 파일 경로 확인
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(input_path):
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
    
    try:
        # 오디오 프로세서로 키 조절
        processor = AudioProcessor(console_log=console.log, processed_folder=app.config['PROCESSED_FOLDER'])
        result = processor.adjust_pitch(input_path, pitch_shift)
        
        if result['success']:
            # 파일 정보 업데이트
            audio_info = processor.get_audio_info(result['output_path'])
            
            file_info = {
                'filename': result['filename'],
                'original_name': filename,
                'filepath': result['output_path'],
                'format': audio_info.get('format', 'unknown'),
                'duration': audio_info.get('duration', 0),
                'duration_str': audio_info.get('duration_str', '0:00'),
                'size_mb': get_file_size_mb(result['output_path'])
            }
            
            return jsonify({
                'success': True,
                'file_info': file_info,
                'message': f'키가 {pitch_shift} 반음 조절되었습니다'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        console.log(f"[Adjust Pitch] 오류: {str(e)}")
        return jsonify({'error': f'키 조절 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/download_mp3/<filename>')
def download_mp3(filename):
    """MP3 형식으로 다운로드"""
    console.log(f"[Route] /download_mp3/{filename} - MP3 다운로드 요청")
    
    # 파일 경로 확인
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(input_path):
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
    
    try:
        # 이미 MP3 파일인 경우 바로 다운로드
        if filename.lower().endswith('.mp3'):
            return send_file(input_path, as_attachment=True, download_name=filename)
        
        # MP3로 변환 후 다운로드
        processor = AudioProcessor(console_log=console.log, processed_folder=app.config['PROCESSED_FOLDER'])
        result = processor.convert_to_mp3(input_path)
        
        if result['success']:
            return send_file(result['output_path'], as_attachment=True, 
                           download_name=result['filename'])
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        console.log(f"[Download MP3] 오류: {str(e)}")
        return jsonify({'error': f'MP3 변환 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/trim_file', methods=['POST'])
def trim_file():
    """파일 자르기 (기존 음악 합치기 탭 호환용)"""
    console.log("[Route] /trim_file - 파일 자르기 요청 (호환용)")
    
    data = request.get_json()
    
    if not data or 'filename' not in data:
        return jsonify({'error': '파일명이 필요합니다'}), 400
    
    filename = data['filename']
    duration = data.get('duration', 30)  # 기본 30초
    
    # 파일 경로 확인
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(input_path):
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
    
    try:
        # 오디오 프로세서로 자르기
        processor = AudioProcessor(console_log=console.log, processed_folder=app.config['PROCESSED_FOLDER'])
        result = processor.trim_audio(input_path, duration)
        
        if result['success']:
            # 파일 정보 업데이트
            audio_info = processor.get_audio_info(result['output_path'])
            
            file_info = {
                'filename': result['filename'],
                'original_name': filename,
                'filepath': result['output_path'],
                'format': audio_info.get('format', 'unknown'),
                'duration': audio_info.get('duration', 0),
                'duration_str': audio_info.get('duration_str', '0:00'),
                'size_mb': get_file_size_mb(result['output_path'])
            }
            
            return jsonify({
                'success': True,
                'file_info': file_info,
                'message': f'파일이 {duration}초로 잘렸습니다'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        console.log(f"[Trim File] 오류: {str(e)}")
        return jsonify({'error': f'자르기 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/adjust_pitch', methods=['POST'])
def adjust_pitch():
    """키(피치) 조절 (기존 음악 합치기 탭 호환용)"""
    console.log("[Route] /adjust_pitch - 키 조절 요청 (호환용)")
    
    data = request.get_json()
    
    if not data or 'filename' not in data:
        return jsonify({'error': '파일명이 필요합니다'}), 400
    
    filename = data['filename']
    pitch_shift = data.get('pitch_shift', 0)  # 반음 단위
    
    # 파일 경로 확인
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(input_path):
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
    
    try:
        # 오디오 프로세서로 키 조절
        processor = AudioProcessor(console_log=console.log, processed_folder=app.config['PROCESSED_FOLDER'])
        result = processor.adjust_pitch(input_path, pitch_shift)
        
        if result['success']:
            # 파일 정보 업데이트
            audio_info = processor.get_audio_info(result['output_path'])
            
            file_info = {
                'filename': result['filename'],
                'original_name': filename,
                'filepath': result['output_path'],
                'format': audio_info.get('format', 'unknown'),
                'duration': audio_info.get('duration', 0),
                'duration_str': audio_info.get('duration_str', '0:00'),
                'size_mb': get_file_size_mb(result['output_path'])
            }
            
            return jsonify({
                'success': True,
                'file_info': file_info,
                'message': f'키가 {pitch_shift} 반음 조절되었습니다'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        console.log(f"[Adjust Pitch] 오류: {str(e)}")
        return jsonify({'error': f'키 조절 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/upload_image', methods=['POST'])
def upload_image():
    """이미지 파일 업로드 처리"""
    console.log("[Route] /upload_image - 이미지 업로드 요청")
    
    if 'image' not in request.files:
        console.log("[Upload Image] 이미지 파일이 없음")
        return jsonify({'error': '이미지 파일이 없습니다'}), 400
    
    file = request.files['image']
    
    if file and allowed_image_file(file.filename):
        # 안전한 파일명 생성
        filename = generate_safe_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        console.log(f"[Upload Image] 이미지 저장 경로: {filepath}")
        
        # 파일 저장
        file.save(filepath)
        console.log(f"[Upload Image] 이미지 저장 완료: {filename}")
        
        # 로고 합성 여부 확인
        apply_logo = request.form.get('apply_logo') == 'on'

        # Frame 1.png 합성 처리
        if apply_logo:
            try:
                from PIL import Image
                
                # Frame 1.png 경로
                frame_path = os.path.join(os.path.dirname(__file__), 'app', 'Frame 1.png')
                
                if os.path.exists(frame_path):
                    # 업로드된 이미지 열기
                    uploaded_image = Image.open(filepath)
                    
                    # Frame 이미지 열기 (RGBA 모드로 변환하여 투명도 유지)
                    frame_image = Image.open(frame_path).convert('RGBA')
                    
                    # Frame 이미지 크기를 업로드된 이미지의 30%로 조절
                    img_width, img_height = uploaded_image.size
                    frame_size = min(img_width, img_height) // 4  # 25%
                    frame_image = frame_image.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
                    
                    # 업로드된 이미지를 RGBA 모드로 변환
                    if uploaded_image.mode != 'RGBA':
                        uploaded_image = uploaded_image.convert('RGBA')
                    
                    # Frame 이미지를 업로드된 이미지 중앙에 합성
                    frame_x = (img_width - frame_size) // 2
                    frame_y = (img_height - frame_size) // 2
                    
                    # 합성 (투명도 유지)
                    uploaded_image.paste(frame_image, (frame_x, frame_y), frame_image)
                    
                    # 합성된 이미지를 PNG로 저장
                    uploaded_image.save(filepath, 'PNG')
                    
                    console.log(f"[Upload Image] Frame 1.png 합성 완료: {frame_size}x{frame_size} at ({frame_x}, {frame_y})")
                else:
                    console.log(f"[Upload Image] Frame 1.png 파일을 찾을 수 없음: {frame_path}")
                    
            except Exception as frame_error:
                console.log(f"[Upload Image] Frame 합성 오류: {str(frame_error)}")
                # Frame 합성 실패해도 업로드된 이미지는 유지
        
        # 파일 정보 반환
        file_info = {
            'filename': filename,
            'original_name': file.filename,
            'size': os.path.getsize(filepath),
            'size_mb': get_file_size_mb(filepath),
            'path': filepath
        }
        
        return jsonify({
            'success': True,
            'image': file_info
        })
    else:
        console.log(f"[Upload Image] 허용되지 않은 이미지 파일: {file.filename}")
        return jsonify({
            'success': False,
            'error': f"{file.filename}: 지원하지 않는 이미지 형식입니다"
        }), 400


@app.route('/create_video', methods=['POST'])
def create_video():
    """동영상 생성 요청"""
    console.log("[Route] /create_video - 동영상 생성 요청")
    
    data = request.get_json()
    console.log(f"[Create Video] 받은 데이터: {json.dumps(data, indent=2)}")
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # 동영상 생성 작업 시작
    thread = threading.Thread(
        target=create_video_job,
        args=(job_id, data)
    )
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': '동영상 생성을 시작했습니다'
    })


def create_video_job(job_id, data):
    """백그라운드 동영상 생성 작업"""
    console.log(f"[Video Job] {job_id} - 동영상 생성 시작")
    
    # 처리 상태 초기화
    processing_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': '동영상 생성 준비 중...',
        'result': None
    }
    
    try:
        # 동영상 프로세서 생성
        video_processor = VideoProcessor(console_log=console.log)
        
        # 파일 경로 설정
        audio_filename = data['audio_filename']
        image_filename = data['image_filename']
        
        audio_path = os.path.join(app.config['PROCESSED_FOLDER'], audio_filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        
        console.log(f"[Video Job] 오디오 파일: {audio_path}")
        console.log(f"[Video Job] 이미지 파일: {image_path}")
        console.log(f"[Video Job] 오디오 파일 존재: {os.path.exists(audio_path)}")
        console.log(f"[Video Job] 이미지 파일 존재: {os.path.exists(image_path)}")
        
        # 출력 파일명 생성
        output_filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # 동영상 설정
        video_preset = data.get('preset', 'youtube_hd')
        presets = video_processor.get_video_presets()
        
        if video_preset in presets:
            video_size = presets[video_preset]['size']
            fps = presets[video_preset]['fps']
        else:
            video_size = (1920, 1080)
            fps = 30
        
        # 진행률 콜백 함수
        def progress_callback(progress, message):
            processing_jobs[job_id]['progress'] = progress
            processing_jobs[job_id]['message'] = message
            console.log(f"[Video Job] {job_id} - {progress}% - {message}")
        
        # 동영상 생성 실행
        result = video_processor.create_video_from_audio_image(
            audio_path=audio_path,
            image_path=image_path,
            output_path=output_path,
            video_size=video_size,
            fps=fps,
            progress_callback=progress_callback
        )
        
        # 처리 완료
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 100
        processing_jobs[job_id]['message'] = '동영상 생성 완료!'
        processing_jobs[job_id]['result'] = {
            'type': 'video',
            'video_info': result
        }
        
        console.log(f"[Video Job] {job_id} - 동영상 생성 완료: {result}")
        
    except Exception as e:
        # 오류 처리
        console.log(f"[Video Job] {job_id} - 오류 발생: {str(e)}")
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['message'] = f'오류: {str(e)}'


@app.route('/video_presets')
def get_video_presets():
    """동영상 프리셋 목록 반환"""
    video_processor = VideoProcessor()
    presets = video_processor.get_video_presets()
    
    return jsonify({
        'success': True,
        'presets': presets
    })


@app.route('/download/<filename>')
def download_file(filename):
    """파일 다운로드 (처리된 파일과 업로드된 파일 모두 지원)"""
    mp3_param = request.args.get('mp3', 'true')
    console.log(f"[Route] /download/{filename} - 파일 다운로드 요청 (mp3={mp3_param})")
    
    try:
        # 디버깅: 원본 파일명과 안전 파일명 비교
        safe_filename = secure_filename(filename)
        console.log(f"[Debug] 원본 파일명: '{filename}'")
        console.log(f"[Debug] 안전 파일명: '{safe_filename}'")
        console.log(f"[Debug] 파일명 변경됨: {filename != safe_filename}")
        
        file_path = None
        is_extracted_file = False
        
        # 처리된 파일 폴더에서 먼저 찾기
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], safe_filename)
        console.log(f"[Debug] 처리된 파일 경로 확인: {processed_path}")
        console.log(f"[Debug] 처리된 파일 존재: {os.path.exists(processed_path)}")
        
        if os.path.exists(processed_path):
            console.log(f"[Download] 처리된 파일 다운로드: {processed_path}")
            return send_file(processed_path, as_attachment=True)
        
        # 업로드 폴더에서 찾기 (링크 추출 파일 등)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        console.log(f"[Debug] 업로드 파일 경로 확인: {upload_path}")
        console.log(f"[Debug] 업로드 파일 존재: {os.path.exists(upload_path)}")
        
        # 안전 파일명으로 찾지 못한 경우 원본 파일명으로 다시 시도
        if not os.path.exists(upload_path):
            original_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            console.log(f"[Debug] 원본 파일명으로 재시도: {original_upload_path}")
            console.log(f"[Debug] 원본 파일명 존재: {os.path.exists(original_upload_path)}")
            
            if os.path.exists(original_upload_path):
                upload_path = original_upload_path
                safe_filename = filename  # 원본 파일명 사용
        
        # 여전히 파일이 없으면 유사한 파일명 검색
        if not os.path.exists(upload_path):
            console.log(f"[Debug] 파일 검색 실패, 유사 파일명 검색 시작...")
            upload_folder = app.config['UPLOAD_FOLDER']
            
            # 업로드 폴더의 모든 파일 확인
            try:
                all_files = os.listdir(upload_folder)
                console.log(f"[Debug] 업로드 폴더 파일 개수: {len(all_files)}")
                
                # 요청된 파일명과 유사한 파일 찾기
                target_base = os.path.splitext(filename)[0].lower()
                console.log(f"[Debug] 검색 대상 기본명: '{target_base}'")
                
                for file in all_files:
                    file_base = os.path.splitext(file)[0].lower()
                    # 부분 매칭으로 검색
                    if target_base in file_base or file_base in target_base:
                        potential_path = os.path.join(upload_folder, file)
                        console.log(f"[Debug] 유사 파일 발견: {file}")
                        console.log(f"[Debug] 유사 파일 경로: {potential_path}")
                        
                        if os.path.exists(potential_path):
                            upload_path = potential_path
                            safe_filename = file
                            console.log(f"[Debug] 유사 파일 매칭 성공: {file}")
                            break
                            
            except Exception as e:
                console.log(f"[Debug] 파일 검색 중 오류: {str(e)}")
        
        if os.path.exists(upload_path):
            file_path = upload_path
            # 링크 추출 파일 및 처리된 파일인지 확인 (다양한 패턴 체크)
            filename_lower = safe_filename.lower()
            is_extracted_file = (
                'youtube_' in filename_lower or          # 링크 추출 파일
                '_processed_' in filename_lower or       # 새로운 처리된 파일 패턴
                '_trimmed_' in filename_lower or         # 자른 파일 (레거시)
                '_pitch' in filename_lower or            # 피치 조절 파일
                '_30s.' in filename_lower or             # 30초 자른 파일 (레거시)
                '_30s_' in filename_lower or             # 30초 자른 파일 (다른 패턴)
                '_plus' in filename_lower or             # 키 올린 파일 (레거시)
                '_minus' in filename_lower or            # 키 내린 파일 (레거시)
                any(ext in filename_lower for ext in ['.mp4', '.webm', '.m4a']) and 'youtube' in filename_lower
            )
            console.log(f"[Download] 업로드된 파일 발견: {upload_path}, 추출 파일: {is_extracted_file}")
            console.log(f"[Download] 파일명 분석: {safe_filename}")
        
        if not file_path:
            console.log(f"[Download] 파일을 찾을 수 없음 - 최종 확인")
            console.log(f"[Download] 요청 파일명: '{filename}'")
            console.log(f"[Download] 안전 파일명: '{safe_filename}'")
            console.log(f"[Download] 업로드 폴더: {app.config['UPLOAD_FOLDER']}")
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
        
        # URL 파라미터로 형식 선택 (기본값: MP3 변환)
        force_mp3 = request.args.get('mp3', 'true').lower() == 'true'
        
        # 추출된 파일인 경우 처리
        if is_extracted_file:
            console.log(f"[Download] 추출된 파일 다운로드: {file_path}, MP3 변환: {force_mp3}")
            
            # MP3 변환을 원하지 않는 경우만 원본 다운로드
            if not force_mp3:
                console.log(f"[Download] 원본 파일 다운로드: {file_path}")
                return send_file(file_path, as_attachment=True)
            
            # 이미 MP3인 경우 바로 다운로드
            if file_path.lower().endswith('.mp3'):
                console.log(f"[Download] 이미 MP3 파일: {file_path}")
                return send_file(file_path, as_attachment=True)
            
            # MP3로 변환 (바로 uploads 폴더에)
            console.log(f"[Download] MP3 변환 시작: {file_path}")
            from link_extractor import LinkExtractor
            extractor = LinkExtractor(console_log=console.log)
            
            # uploads 폴더에서 직접 변환
            mp3_path = extractor.convert_to_mp3(file_path, app.config['UPLOAD_FOLDER'])
            
            if mp3_path and os.path.exists(mp3_path):
                console.log(f"[Download] MP3 변환 성공: {mp3_path}")
                
                # 파일 크기 확인
                file_size = os.path.getsize(mp3_path)
                console.log(f"[Download] 변환된 MP3 파일 크기: {file_size} bytes")
                
                if file_size == 0:
                    console.log(f"[Download-Error] MP3 변환 실패 - 파일이 비어있음")
                    return jsonify({'error': 'MP3 변환에 실패했습니다. 파일이 손상되었을 수 있습니다.'}), 500
                
                # MP3 파일명으로 다운로드
                base_name = os.path.splitext(safe_filename)[0]
                mp3_filename = f"{base_name}.mp3"
                
                # 변환된 파일은 이미 uploads 폴더에 있으므로 바로 다운로드
                return send_file(mp3_path, as_attachment=True, download_name=mp3_filename)
            else:
                console.log(f"[Download-Error] MP3 변환 완전 실패: {file_path}")
                return jsonify({'error': 'MP3 변환에 실패했습니다. FFmpeg 오류가 발생했을 수 있습니다.'}), 500
        else:
            # 일반 파일 다운로드
            console.log(f"[Download] 일반 파일 다운로드: {file_path}")
            return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        console.log(f"[Download] 다운로드 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ===========================================
# 음악 분석 및 AI 생성 API 라우팅
# ===========================================

@app.route('/api/music-analysis/status')
def music_analysis_status():
    """음악 분석 서비스 상태 확인"""
    console.log("[Route] /api/music-analysis/status - 서비스 상태 확인")
    
    try:
        # 분석 전용 모드 상태 확인
        return jsonify({
            'overall_status': 'analysis_only',
            'youtube_analyzer': {
                'available': music_analyzer is not None,
                'api_key_set': bool(os.getenv('YOUTUBE_API_KEY')),
                'status': 'ready' if music_analyzer else 'not_configured'
            },
            'lyria_client': {
                'available': False,
                'status': 'disabled',
                'message': 'AI 음악 생성 기능은 현재 비활성화되어 있습니다'
            },
            'features': {
                'analysis': music_analyzer is not None,
                'generation': False
            }
        })
    except Exception as e:
        console.log(f"[Music Analysis] 상태 확인 오류: {str(e)}")
        return jsonify({
            'overall_status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/music-analysis/analyze', methods=['POST'])
def analyze_music():
    """YouTube 음악 분석 (분석만)"""
    console.log("[Route] /api/music-analysis/analyze - 음악 분석 요청")
    
    try:
        if not music_analyzer:
            return jsonify({
                'success': False,
                'error': 'YouTube 분석기가 초기화되지 않았습니다'
            }), 500
        
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'YouTube URL이 필요합니다'
            }), 400
        
        # 작업 ID 생성
        job_id = str(uuid.uuid4())
        
        # 분석 작업 시작
        thread = threading.Thread(
            target=analyze_music_job,
            args=(job_id, url)
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': '음악 분석을 시작했습니다 (분석 전용 모드)'
        })
        
    except Exception as e:
        console.log(f"[Music Analysis] 분석 요청 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/music-analysis/generate', methods=['POST'])
def generate_music():
    """YouTube 음악 분석 후 AI 생성 (현재 비활성화)"""
    console.log("[Route] /api/music-analysis/generate - 음악 생성 요청 (비활성화)")
    
    return jsonify({
        'success': False,
        'error': 'AI 음악 생성 기능은 현재 비활성화되어 있습니다',
        'message': '분석 기능만 사용 가능합니다',
        'available_features': ['analyze'],
        'disabled_features': ['generate']
    }), 503


@app.route('/api/music-analysis/status/<job_id>')
def music_analysis_job_status(job_id):
    """음악 분석 작업 상태 확인"""
    console.log(f"[Route] /api/music-analysis/status/{job_id} - 작업 상태 확인")
    
    if job_id not in music_analysis_jobs:
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    job_info = music_analysis_jobs[job_id]
    
    # 완료된 작업은 정보 제거 (메모리 정리)
    if job_info['status'] == 'completed' and job_info.get('result'):
        result = job_info['result']
        del music_analysis_jobs[job_id]
        return jsonify({
            'status': 'completed',
            'progress': 100,
            'message': '처리 완료!',
            'result': result
        })
    
    return jsonify(job_info)


@app.route('/api/music-analysis/styles')
def get_music_styles():
    """지원하는 음악 스타일 목록"""
    console.log("[Route] /api/music-analysis/styles - 스타일 목록 요청")
    
    try:
        if music_service:
            styles = music_service.get_music_styles()
            return jsonify({
                'success': True,
                'styles': styles
            })
        else:
            return jsonify({
                'success': False,
                'error': '음악 서비스가 초기화되지 않았습니다'
            }), 500
    except Exception as e:
        console.log(f"[Music Analysis] 스타일 목록 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/music-analysis/history')
def get_music_history():
    """음악 분석 이력 조회"""
    console.log("[Route] /api/music-analysis/history - 이력 조회 요청")
    
    try:
        limit = request.args.get('limit', 50, type=int)
        
        if db_manager:
            history = db_manager.get_analysis_history(limit)
            return jsonify({
                'success': True,
                'history': history,
                'count': len(history)
            })
        else:
            return jsonify({
                'success': False,
                'error': '데이터베이스가 초기화되지 않았습니다'
            })
    except Exception as e:
        console.log(f"[Route] 이력 조회 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/database/session/<int:session_id>')
def get_session_details(session_id):
    """특정 세션의 상세 정보 조회 (댓글 포함)"""
    console.log(f"[Route] /api/database/session/{session_id} - 세션 상세 조회")
    
    try:
        if db_manager:
            session_data = db_manager.get_session_details(session_id)
            if session_data:
                return jsonify({
                    'success': True,
                    'session': session_data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '세션을 찾을 수 없습니다'
                }), 404
        else:
            return jsonify({
                'success': False,
                'error': '데이터베이스가 초기화되지 않았습니다'
            })
    except Exception as e:
        console.log(f"[Route] 세션 조회 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/database/search/artist')
def search_by_artist():
    """아티스트로 검색"""
    console.log("[Route] /api/database/search/artist - 아티스트 검색")
    
    try:
        artist = request.args.get('q', '').strip()
        if not artist:
            return jsonify({
                'success': False,
                'error': '검색어를 입력해주세요'
            }), 400
        
        if db_manager:
            results = db_manager.search_by_artist(artist)
            return jsonify({
                'success': True,
                'results': results,
                'count': len(results)
            })
        else:
            return jsonify({
                'success': False,
                'error': '데이터베이스가 초기화되지 않았습니다'
            })
    except Exception as e:
        console.log(f"[Route] 아티스트 검색 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/database/search/genre')
def search_by_genre():
    """장르로 검색"""
    console.log("[Route] /api/database/search/genre - 장르 검색")
    
    try:
        genre = request.args.get('q', '').strip()
        if not genre:
            return jsonify({
                'success': False,
                'error': '검색할 장르를 입력해주세요'
            }), 400
        
        if db_manager:
            results = db_manager.search_by_genre(genre)
            return jsonify({
                'success': True,
                'results': results,
                'count': len(results)
            })
        else:
            return jsonify({
                'success': False,
                'error': '데이터베이스가 초기화되지 않았습니다'
            })
    except Exception as e:
        console.log(f"[Route] 장르 검색 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/database/statistics')
def get_database_statistics():
    """데이터베이스 통계 조회"""
    console.log("[Route] /api/database/statistics - 통계 조회")
    
    try:
        if db_manager:
            stats = db_manager.get_statistics()
            return jsonify({
                'success': True,
                'statistics': stats
            })
        else:
            return jsonify({
                'success': False,
                'error': '데이터베이스가 초기화되지 않았습니다'
            })
    except Exception as e:
        console.log(f"[Route] 통계 조회 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/database/session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """세션 삭제"""
    console.log(f"[Route] DELETE /api/database/session/{session_id} - 세션 삭제")
    
    try:
        if db_manager:
            success = db_manager.delete_session(session_id)
            if success:
                return jsonify({
                    'success': True,
                    'message': '세션이 삭제되었습니다'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '세션 삭제에 실패했습니다'
                })
        else:
            return jsonify({
                'success': False,
                'error': '데이터베이스가 초기화되지 않았습니다'
            })
    except Exception as e:
        console.log(f"[Route] 세션 삭제 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/trends/artist', methods=['POST'])
def get_artist_trends():
    """아티스트 트렌드 분석"""
    console.log("[Route] /api/trends/artist - 아티스트 트렌드 분석")
    
    try:
        if not trends_analyzer:
            return jsonify({
                'success': False,
                'error': '트렌드 분석기가 초기화되지 않았습니다'
            }), 500
        
        data = request.get_json()
        artist = data.get('artist', '').strip()
        timeframe = data.get('timeframe', 'today 3-m')
        geo = data.get('geo', 'KR')
        
        if not artist:
            return jsonify({
                'success': False,
                'error': '아티스트명을 입력해주세요'
            }), 400
        
        result = trends_analyzer.get_artist_trends(artist, timeframe, geo)
        return jsonify(result)
        
    except Exception as e:
        console.log(f"[Route] 아티스트 트렌드 분석 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/trends/compare', methods=['POST'])
def compare_artists_trends():
    """아티스트 비교 트렌드 분석"""
    console.log("[Route] /api/trends/compare - 아티스트 비교 분석")
    
    try:
        if not trends_analyzer:
            return jsonify({
                'success': False,
                'error': '트렌드 분석기가 초기화되지 않았습니다'
            }), 500
        
        data = request.get_json()
        artists = data.get('artists', [])
        timeframe = data.get('timeframe', 'today 3-m')
        geo = data.get('geo', 'KR')
        
        if not artists or len(artists) < 2:
            return jsonify({
                'success': False,
                'error': '비교할 아티스트를 2명 이상 입력해주세요'
            }), 400
        
        result = trends_analyzer.compare_artists(artists, timeframe, geo)
        return jsonify(result)
        
    except Exception as e:
        console.log(f"[Route] 아티스트 비교 분석 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/trends/genres')
def get_genre_trends():
    """음악 장르 트렌드 분석"""
    console.log("[Route] /api/trends/genres - 장르 트렌드 분석")
    
    try:
        if not trends_analyzer:
            return jsonify({
                'success': False,
                'error': '트렌드 분석기가 초기화되지 않았습니다'
            }), 500
        
        timeframe = request.args.get('timeframe', 'today 3-m')
        geo = request.args.get('geo', 'KR')
        genres = request.args.getlist('genres')  # ?genres=케이팝&genres=힙합
        
        if not genres:
            genres = None  # 기본 장르 사용
        
        result = trends_analyzer.get_music_genre_trends(genres, timeframe, geo)
        return jsonify(result)
        
    except Exception as e:
        console.log(f"[Route] 장르 트렌드 분석 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/trends/keywords', methods=['POST'])
def get_keyword_suggestions():
    """키워드 제안 및 관련 검색어"""
    console.log("[Route] /api/trends/keywords - 키워드 제안")
    
    try:
        if not trends_analyzer:
            return jsonify({
                'success': False,
                'error': '트렌드 분석기가 초기화되지 않았습니다'
            }), 500
        
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        geo = data.get('geo', 'KR')
        
        if not keyword:
            return jsonify({
                'success': False,
                'error': '키워드를 입력해주세요'
            }), 400
        
        result = trends_analyzer.get_keyword_suggestions(keyword, geo)
        return jsonify(result)
        
    except Exception as e:
        console.log(f"[Route] 키워드 제안 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })




def analyze_music_job(job_id, url):
    """백그라운드 음악 분석 작업"""
    console.log(f"[Analyze Job] {job_id} - 분석 시작: {url}")
    
    # 처리 상태 초기화
    music_analysis_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': '분석 준비 중...',
        'result': None
    }
    
    try:
        # 진행률 콜백 함수
        def progress_callback(progress, message):
            music_analysis_jobs[job_id]['progress'] = progress
            music_analysis_jobs[job_id]['message'] = message
            console.log(f"[Analyze Job] {job_id} - {progress}% - {message}")
        
        # 음악 분석 실행 (분석 전용 모드)
        result = music_analyzer.analyze_youtube_music(url)
        
        # 프롬프트 생성 추가 (분석 전용 모드에서도 프롬프트 제공)
        if result['success']:
            try:
                from prompt_generator import PromptGenerator
                prompt_generator = PromptGenerator(console_log=console.log)
                prompt_options = prompt_generator.generate_prompt_options(result)
                result['prompt_options'] = prompt_options
                progress_callback(100, "분석 및 프롬프트 생성 완료!")
            except Exception as e:
                console.log(f"[Analyze Job] {job_id} - 프롬프트 생성 실패: {str(e)}")
                progress_callback(100, "분석 완료! (프롬프트 생성 실패)")
        else:
            progress_callback(0, f"분석 실패: {result['error']}")
        
        if result['success']:
            # 데이터베이스에 저장
            if db_manager:
                try:
                    session_id = db_manager.save_analysis_result(result)
                    result['database'] = {
                        'saved': True,
                        'session_id': session_id
                    }
                    console.log(f"[Analyze Job] {job_id} - 데이터베이스 저장 완료: session_id={session_id}")
                except Exception as e:
                    console.log(f"[Analyze Job] {job_id} - 데이터베이스 저장 실패: {str(e)}")
                    result['database'] = {
                        'saved': False,
                        'error': str(e)
                    }
            
            # 분석 완료
            music_analysis_jobs[job_id]['status'] = 'completed'
            music_analysis_jobs[job_id]['progress'] = 100
            music_analysis_jobs[job_id]['message'] = '분석 완료!'
            music_analysis_jobs[job_id]['result'] = result
            
            console.log(f"[Analyze Job] {job_id} - 분석 완료")
        else:
            # 분석 실패
            music_analysis_jobs[job_id]['status'] = 'error'
            music_analysis_jobs[job_id]['message'] = result['error']
            console.log(f"[Analyze Job] {job_id} - 분석 실패: {result['error']}")
        
    except Exception as e:
        # 오류 처리
        console.log(f"[Analyze Job] {job_id} - 오류 발생: {str(e)}")
        music_analysis_jobs[job_id]['status'] = 'error'
        music_analysis_jobs[job_id]['message'] = f'오류: {str(e)}'


def generate_music_job(job_id, url, options):
    """백그라운드 음악 생성 작업"""
    console.log(f"[Generate Job] {job_id} - 생성 시작: {url}")
    
    # 처리 상태 초기화
    music_analysis_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': '생성 준비 중...',
        'result': None
    }
    
    try:
        # 진행률 콜백 함수
        def progress_callback(progress, message):
            music_analysis_jobs[job_id]['progress'] = progress
            music_analysis_jobs[job_id]['message'] = message
            console.log(f"[Generate Job] {job_id} - {progress}% - {message}")
        
        # 출력 폴더 설정
        generation_options = options.copy()
        generation_options['output_folder'] = app.config['PROCESSED_FOLDER']
        
        # 음악 분석 및 생성 실행
        result = music_service.analyze_and_generate(
            url, 
            generation_options, 
            progress_callback
        )
        
        if result['success']:
            # 생성 완료
            music_analysis_jobs[job_id]['status'] = 'completed'
            music_analysis_jobs[job_id]['progress'] = 100
            music_analysis_jobs[job_id]['message'] = '생성 완료!'
            music_analysis_jobs[job_id]['result'] = result
            
            console.log(f"[Generate Job] {job_id} - 생성 완료")
        else:
            # 생성 실패
            music_analysis_jobs[job_id]['status'] = 'error'
            music_analysis_jobs[job_id]['message'] = result['error']
            console.log(f"[Generate Job] {job_id} - 생성 실패: {result['error']}")
        
    except Exception as e:
        # 오류 처리
        console.log(f"[Generate Job] {job_id} - 오류 발생: {str(e)}")
        music_analysis_jobs[job_id]['status'] = 'error'
        music_analysis_jobs[job_id]['message'] = f'오류: {str(e)}'


# ============================================================================
# Music Trend Analyzer V2 API 엔드포인트
# ============================================================================

@app.route('/api/trends/v2/status')
def trend_analyzer_v2_status():
    """Music Trend Analyzer V2 시스템 상태 확인"""
    console.log("[Route] /api/trends/v2/status - V2 시스템 상태 확인")
    
    try:
        if not trend_analyzer_v2:
            return jsonify({
                'success': False,
                'error': 'Music Trend Analyzer V2가 초기화되지 않았습니다'
            }), 500
        
        status = trend_analyzer_v2.get_system_status()
        
        return jsonify({
            'success': True,
            'system_status': status,
            'version': 'v2.0',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        console.log(f"[Route] V2 상태 확인 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/trends/v2/analyze', methods=['POST'])
def trend_analyzer_v2_comprehensive():
    """종합 음악 트렌드 분석"""
    console.log("[Route] /api/trends/v2/analyze - 종합 트렌드 분석")
    
    try:
        if not trend_analyzer_v2:
            return jsonify({
                'success': False,
                'error': 'Music Trend Analyzer V2가 초기화되지 않았습니다'
            }), 500
        
        data = request.get_json() or {}
        
        # 요청 파라미터 추출
        categories = data.get('categories', ['kpop', 'hiphop', 'pop', 'rock', 'ballad'])
        include_reddit = data.get('include_reddit', True)
        include_spotify = data.get('include_spotify', True)
        include_comments = data.get('include_comments', True)
        
        console.log(f"[Route] 분석 카테고리: {categories}")
        
        # 종합 트렌드 분석 실행
        result = trend_analyzer_v2.analyze_current_music_trends(
            categories=categories,
            include_reddit=include_reddit,
            include_spotify=include_spotify,
            include_comments=include_comments
        )
        
        if result.get('success'):
            console.log("[Route] 종합 트렌드 분석 완료")
            return jsonify(result)
        else:
            console.log(f"[Route] 종합 트렌드 분석 실패: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        console.log(f"[Route] 종합 트렌드 분석 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/spotify/charts')
def get_spotify_charts():
    """Spotify 차트 데이터만 가져오기"""
    try:
        if not trend_analyzer_v2:
            return jsonify({'success': False, 'error': 'Music Trend Analyzer V2가 초기화되지 않았습니다'}), 500
        
        # Spotify 차트 데이터만 수집
        chart_data = trend_analyzer_v2._collect_spotify_chart_data()
        
        if chart_data['success']:
            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'chart_data': chart_data,
                'total_tracks': len(chart_data.get('chart_tracks', []))
            })
        else:
            return jsonify({'success': False, 'error': chart_data.get('error', '차트 데이터 수집 실패')}), 500
            
    except Exception as e:
        console.log(f"[API] Spotify 차트 API 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/charts')
def charts_page():
    """Spotify 차트 전용 페이지"""
    # 로그인 체크
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    return render_template('charts.html')

@app.route('/api/melon/charts')
def get_melon_charts():
    """멜론 차트 데이터 가져오기"""
    try:
        if not melon_connector:
            return jsonify({'success': False, 'error': '멜론 커넥터가 초기화되지 않았습니다'}), 500
        
        # 요청 파라미터
        chart_type = request.args.get('type', 'realtime')  # realtime, hot100, week, month
        limit = min(int(request.args.get('limit', 100)), 100)  # 최대 100곡
        
        console.log(f"[API] 멜론 {chart_type} 차트 요청 (limit: {limit})")
        
        # 멜론 차트 데이터 수집
        chart_data = melon_connector.get_chart_data(chart_type, limit)
        
        if chart_data['success']:
            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'chart_type': chart_type,
                'chart_data': chart_data,
                'total_tracks': chart_data.get('total_tracks', 0),
                'source': 'melon'
            })
        else:
            return jsonify({'success': False, 'error': chart_data.get('error', '멜론 차트 데이터 수집 실패')}), 500
            
    except Exception as e:
        console.log(f"[API] 멜론 차트 오류: {str(e)}")
        return jsonify({'success': False, 'error': f'멜론 차트 데이터 수집 중 오류: {str(e)}'}), 500

@app.route('/api/melon/charts/all')
def get_all_melon_charts():
    """모든 멜론 차트 데이터 가져오기"""
    try:
        if not melon_connector:
            return jsonify({'success': False, 'error': '멜론 커넥터가 초기화되지 않았습니다'}), 500
        
        # 요청 파라미터
        limit_per_chart = min(int(request.args.get('limit', 50)), 50)  # 차트별 최대 50곡
        
        console.log(f"[API] 멜론 전체 차트 요청 (차트별 limit: {limit_per_chart})")
        
        # 모든 멜론 차트 데이터 수집
        all_charts = melon_connector.get_all_charts(limit_per_chart)
        
        if all_charts['success']:
            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'charts': all_charts['charts'],
                'total_tracks': all_charts.get('total_tracks', 0),
                'source': 'melon'
            })
        else:
            return jsonify({'success': False, 'error': '멜론 전체 차트 데이터 수집 실패'}), 500
            
    except Exception as e:
        console.log(f"[API] 멜론 전체 차트 오류: {str(e)}")
        return jsonify({'success': False, 'error': f'멜론 전체 차트 수집 중 오류: {str(e)}'}), 500

@app.route('/api/korea-charts/all')
def get_all_korea_charts():
    """국내 주요 음원사 통합 차트 API (개별 API 사용)"""
    console.log("[Route] /api/korea-charts/all - 국내 통합 차트 요청")
    
    try:
        # 파라미터 파싱
        services = request.args.getlist('services') or ['melon', 'bugs', 'genie']
        limit_per_chart = min(int(request.args.get('limit', 50)), 100)
        
        console.log(f"[API] 통합 차트 요청 - 서비스: {services}, 차트별 limit: {limit_per_chart}")
        
        # 개별 커넥터 초기화
        from connectors.korea_music_charts_connector import KoreaMusicChartsConnector
        connector = KoreaMusicChartsConnector(console.log)
        
        # 서비스별 차트 수집
        all_services = {}
        total_tracks = 0
        successful_services = 0
        
        for service in services:
            try:
                chart_result = None
                if service == 'melon':
                    chart_result = connector._get_melon_chart('realtime', limit_per_chart)
                elif service == 'bugs':
                    chart_result = connector._get_bugs_chart('realtime', limit_per_chart)
                elif service == 'genie':
                    chart_result = connector._get_genie_chart('realtime', limit_per_chart)
                elif service == 'vibe':
                    chart_result = connector._get_vibe_chart('chart', limit_per_chart)
                else:
                    continue
                
                # 반환 타입에 따른 처리
                if isinstance(chart_result, dict):
                    # 딕셔너리 형태 (멜론)
                    if chart_result.get('success') and chart_result.get('tracks'):
                        tracks = chart_result['tracks']
                        all_services[service] = {
                            'realtime': {
                                'success': True,
                                'tracks': tracks,
                                'total_tracks': len(tracks)
                            }
                        }
                        total_tracks += len(tracks)
                        successful_services += 1
                        console.log(f"[API] {service} 차트 수집 성공: {len(tracks)}곡")
                    else:
                        all_services[service] = {
                            'realtime': {
                                'success': False,
                                'tracks': [],
                                'total_tracks': 0,
                                'error': chart_result.get('error', f'{service} 차트 수집 실패')
                            }
                        }
                        console.log(f"[API] {service} 차트 수집 실패: {chart_result.get('error', 'Unknown')}")
                elif isinstance(chart_result, list):
                    # 리스트 형태 (기타 서비스)
                    if chart_result and len(chart_result) > 0:
                        all_services[service] = {
                            'realtime': {
                                'success': True,
                                'tracks': chart_result,
                                'total_tracks': len(chart_result)
                            }
                        }
                        total_tracks += len(chart_result)
                        successful_services += 1
                        console.log(f"[API] {service} 차트 수집 성공: {len(chart_result)}곡")
                    else:
                        all_services[service] = {
                            'realtime': {
                                'success': False,
                                'tracks': [],
                                'total_tracks': 0,
                                'error': f'{service} 차트 데이터 없음'
                            }
                        }
                        console.log(f"[API] {service} 차트 수집 실패")
                else:
                    all_services[service] = {
                        'realtime': {
                            'success': False,
                            'tracks': [],
                            'total_tracks': 0,
                            'error': f'{service} 차트 데이터 형식 오류'
                        }
                    }
                    console.log(f"[API] {service} 차트 데이터 형식 오류: {type(chart_result)}")
                    
            except Exception as e:
                all_services[service] = {
                    'realtime': {
                        'success': False,
                        'tracks': [],
                        'total_tracks': 0,
                        'error': str(e)
                    }
                }
                console.log(f"[API] {service} 차트 수집 오류: {str(e)}")
        
        # 성공률 계산
        success_rate = (successful_services / len(services) * 100) if services else 0
        
        # 크로스 플랫폼 분석 (간단한 버전)
        cross_platform_hits = []
        if successful_services >= 2:
            # 공통 트랙 찾기
            all_tracks = {}
            for service, charts in all_services.items():
                if charts.get('realtime', {}).get('success'):
                    for track in charts['realtime']['tracks']:
                        track_key = f"{track.get('title', '').strip()} - {track.get('artist', '').strip()}"
                        if track_key not in all_tracks:
                            all_tracks[track_key] = {
                                'title': track.get('title', ''),
                                'artist': track.get('artist', ''),
                                'services': [],
                                'ranks': []
                            }
                        all_tracks[track_key]['services'].append(service)
                        all_tracks[track_key]['ranks'].append(track.get('rank', 999))
            
            # 2개 이상 서비스에서 등장하는 트랙
            for track_key, track_info in all_tracks.items():
                if len(track_info['services']) >= 2:
                    avg_rank = sum(track_info['ranks']) / len(track_info['ranks'])
                    cross_platform_hits.append({
                        'title': track_info['title'],
                        'artist': track_info['artist'],
                        'services': track_info['services'],
                        'services_count': len(track_info['services']),
                        'avg_rank': round(avg_rank, 1),
                        'cross_platform_score': len(track_info['services']) * 100 - avg_rank
                    })
            
            # 크로스 플랫폼 점수로 정렬
            cross_platform_hits.sort(key=lambda x: x['cross_platform_score'], reverse=True)
            cross_platform_hits = cross_platform_hits[:20]  # 상위 20개만
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'services': all_services,
            'total_tracks': total_tracks,
            'successful_services': successful_services,
            'success_rate': round(success_rate, 1),
            'cross_platform_analysis': {
                'success': len(cross_platform_hits) > 0,
                'cross_platform_hits': cross_platform_hits
            },
            'source': 'individual_connectors'
        })
            
    except Exception as e:
        console.log(f"[API] 국내 통합 차트 오류: {str(e)}")
        return jsonify({'success': False, 'error': f'국내 통합 차트 수집 중 오류: {str(e)}'}), 500

@app.route('/api/korea-charts/cross-analysis')
def get_korea_charts_cross_analysis():
    """국내 차트 크로스 플랫폼 분석만 반환"""
    console.log("[Route] /api/korea-charts/cross-analysis - 크로스 플랫폼 분석")
    
    try:
        if not korea_charts_connector_available:
            return jsonify({'success': False, 'error': '커넥터 사용 불가'}), 500
        
        services = request.args.getlist('services') or ['melon', 'bugs', 'genie']
        limit = min(int(request.args.get('limit', 30)), 50)
        
        korea_connector = KoreaMusicChartsConnector(console.log)
        all_charts = korea_connector.get_all_charts(services=services, limit_per_chart=limit)
        
        if all_charts['success']:
            cross_analysis = korea_connector.get_cross_platform_analysis(all_charts)
            return jsonify(cross_analysis)
        else:
            return jsonify({'success': False, 'error': '차트 데이터 수집 실패'}), 500
            
    except Exception as e:
        console.log(f"[API] 크로스 분석 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/status')
def get_scheduler_status():
    """차트 스케줄러 상태 확인"""
    console.log("[Route] /api/scheduler/status - 스케줄러 상태 확인")
    
    try:
        if not chart_scheduler_available:
            return jsonify({'success': False, 'error': '스케줄러를 사용할 수 없습니다'}), 500
        
        scheduler = get_scheduler()
        status = scheduler.get_status()
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        console.log(f"[API] 스케줄러 상태 확인 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """차트 스케줄러 시작"""
    console.log("[Route] /api/scheduler/start - 스케줄러 시작")
    
    try:
        if not chart_scheduler_available:
            return jsonify({'success': False, 'error': '스케줄러를 사용할 수 없습니다'}), 500
        
        scheduler = start_chart_scheduler()
        
        return jsonify({
            'success': True,
            'message': '차트 스케줄러가 시작되었습니다',
            'status': scheduler.get_status()
        })
        
    except Exception as e:
        console.log(f"[API] 스케줄러 시작 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """차트 스케줄러 중지"""
    console.log("[Route] /api/scheduler/stop - 스케줄러 중지")
    
    try:
        if not chart_scheduler_available:
            return jsonify({'success': False, 'error': '스케줄러를 사용할 수 없습니다'}), 500
        
        stop_chart_scheduler()
        
        return jsonify({
            'success': True,
            'message': '차트 스케줄러가 중지되었습니다'
        })
        
    except Exception as e:
        console.log(f"[API] 스케줄러 중지 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/config', methods=['GET', 'POST'])
def scheduler_config():
    """스케줄러 설정 확인/변경"""
    console.log(f"[Route] /api/scheduler/config - {request.method}")
    
    try:
        if not chart_scheduler_available:
            return jsonify({'success': False, 'error': '스케줄러를 사용할 수 없습니다'}), 500
        
        scheduler = get_scheduler()
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'config': scheduler.schedule_config
            })
        else:  # POST
            data = request.get_json()
            if data:
                scheduler.update_config(data)
                return jsonify({
                    'success': True,
                    'message': '스케줄러 설정이 업데이트되었습니다',
                    'config': scheduler.schedule_config
                })
            else:
                return jsonify({'success': False, 'error': '설정 데이터가 필요합니다'}), 400
        
    except Exception as e:
        console.log(f"[API] 스케줄러 설정 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/charts/analysis')
def analyze_charts():
    """차트 분석 및 비교"""
    console.log("[Route] /api/charts/analysis - 차트 분석")
    
    try:
        if not chart_analyzer_available:
            return jsonify({'success': False, 'error': '차트 분석기를 사용할 수 없습니다'}), 500
        
        if not korea_charts_connector_available:
            return jsonify({'success': False, 'error': '차트 커넥터를 사용할 수 없습니다'}), 500
        
        # 파라미터 파싱
        services = request.args.getlist('services') or ['melon', 'bugs', 'genie']
        limit = min(int(request.args.get('limit', 30)), 50)
        
        console.log(f"[API] 차트 분석 요청 - 서비스: {services}, limit: {limit}")
        
        # 차트 데이터 수집
        korea_connector = KoreaMusicChartsConnector(console.log)
        chart_data = korea_connector.get_all_charts(services=services, limit_per_chart=limit)
        
        if not chart_data['success']:
            return jsonify({'success': False, 'error': '차트 데이터 수집 실패'}), 500
        
        # 차트 분석 실행
        analyzer = ChartAnalyzer(console.log)
        analysis_result = analyzer.analyze_service_differences(chart_data)
        
        if not analysis_result['success']:
            return jsonify({'success': False, 'error': '차트 분석 실패'}), 500
        
        # 인사이트 생성
        insights = analyzer.generate_insights_report(analysis_result)
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis_result['analysis'],
            'insights': insights if insights.get('success') else None,
            'data_source': {
                'services': services,
                'total_tracks': chart_data.get('total_tracks', 0),
                'successful_services': chart_data.get('successful_services', 0)
            }
        })
        
    except Exception as e:
        console.log(f"[API] 차트 분석 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/charts/insights')
def get_chart_insights():
    """차트 인사이트 요약"""
    console.log("[Route] /api/charts/insights - 인사이트 요약")
    
    try:
        if not chart_analyzer_available:
            return jsonify({'success': False, 'error': '차트 분석기를 사용할 수 없습니다'}), 500
        
        # 최신 분석 결과 로드
        analysis_dir = os.path.join(os.path.dirname(__file__), 'chart_analysis')
        latest_file = os.path.join(analysis_dir, 'latest_analysis.json')
        
        if os.path.exists(latest_file):
            with open(latest_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            analyzer = ChartAnalyzer(console.log)
            insights = analyzer.generate_insights_report({'success': True, 'analysis': analysis_data})
            
            return jsonify({
                'success': True,
                'insights': insights['insights'] if insights.get('success') else [],
                'summary': insights.get('summary', {}),
                'analysis_date': analysis_data.get('generated_at'),
                'from_cache': True
            })
        else:
            return jsonify({
                'success': False, 
                'error': '분석 데이터가 없습니다. 먼저 /api/charts/analysis를 호출하세요.'
            }), 404
            
    except Exception as e:
        console.log(f"[API] 인사이트 요약 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/individual-chart/<service>')
def get_individual_chart(service):
    """개별 음원사 차트 API"""
    console.log(f"[Route] /api/individual-chart/{service} - 개별 차트 요청")
    
    try:
        if not korea_charts_connector_available:
            return jsonify({'success': False, 'error': '차트 커넥터를 사용할 수 없습니다'}), 500
        
        # 파라미터 파싱
        chart_type = request.args.get('type', 'realtime')
        limit = min(int(request.args.get('limit', 50)), 100)
        
        console.log(f"[API] {service} {chart_type} 차트 요청 (limit: {limit})")
        
        # 개별 차트 커넥터 초기화
        connector = KoreaMusicChartsConnector(console.log)
        
        # 서비스별 차트 수집
        if service == 'bugs':
            chart_data = connector._get_bugs_chart(chart_type, limit)
        elif service == 'genie':
            chart_data = connector._get_genie_chart(chart_type, limit)
        elif service == 'vibe':
            chart_data = connector._get_vibe_chart(chart_type, limit)
        elif service == 'flo':
            chart_data = connector._get_flo_chart(chart_type, limit)
        else:
            return jsonify({'success': False, 'error': f'지원하지 않는 서비스: {service}'}), 400
        
        if chart_data['success']:
            return jsonify({
                'success': True,
                'service': service,
                'chart_type': chart_type,
                'total_tracks': chart_data.get('total_tracks', 0),
                'tracks': chart_data.get('tracks', []),
                'timestamp': datetime.now().isoformat(),
                'note': chart_data.get('note')  # 샘플 데이터 알림 등
            })
        else:
            return jsonify({
                'success': False, 
                'error': chart_data.get('error', f'{service} 차트 수집 실패'),
                'service': service
            }), 500
            
    except Exception as e:
        console.log(f"[API] {service} 개별 차트 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trends/v2/keywords', methods=['POST'])
def trend_analyzer_v2_keywords():
    """키워드 트렌드 검색 분석"""
    console.log("[Route] /api/trends/v2/keywords - 키워드 트렌드 검색")
    
    try:
        if not trend_analyzer_v2:
            return jsonify({
                'success': False,
                'error': 'Music Trend Analyzer V2가 초기화되지 않았습니다'
            }), 500
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': '검색 키워드(query)가 필요합니다'
            }), 400
        
        query = data['query']
        deep_analysis = data.get('deep_analysis', True)
        
        console.log(f"[Route] 키워드 검색: {query}")
        
        # 키워드 트렌드 분석 실행
        result = trend_analyzer_v2.search_trending_keywords(
            query=query,
            deep_analysis=deep_analysis
        )
        
        if result.get('success'):
            console.log(f"[Route] 키워드 검색 완료: {len(result.get('sources_analyzed', []))}개 소스")
            return jsonify(result)
        else:
            console.log(f"[Route] 키워드 검색 실패: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        console.log(f"[Route] 키워드 검색 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500






@app.route('/trim-audio', methods=['POST'])
def trim_audio_legacy():
    """추출된 음원 30초 자르기"""
    console.log("[Route] /trim-audio - 30초 자르기 요청")
    
    data = request.get_json()
    filename = data.get('filename', '').strip()
    
    if not filename:
        return jsonify({'error': '파일명이 필요합니다'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # 자르기 작업 시작
    thread = threading.Thread(
        target=trim_audio_job,
        args=(job_id, filename)
    )
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': '30초 자르기 작업을 시작했습니다'
    })


@app.route('/trim-audio-download', methods=['POST'])
def trim_audio_download():
    """추출된 음원 30초 자르기 후 바로 다운로드"""
    console.log("[Route] /trim-audio-download - 30초 자르기 후 다운로드 요청")
    
    data = request.get_json()
    filename = data.get('filename', '').strip()
    
    if not filename:
        return jsonify({'error': '파일명이 필요합니다'}), 400
    
    try:
        # 파일 경로 확인
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            console.log(f"[Trim-Download] 파일을 찾을 수 없음: {file_path}")
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
        
        console.log(f"[Trim-Download] 30초 자르기 시작: {file_path}")
        
        # LinkExtractor를 사용하여 30초 자르기
        from link_extractor import LinkExtractor
        extractor = LinkExtractor(console_log=console.log)
        
        # 30초 자른 파일 생성
        trimmed_path = extractor._trim_audio_to_30_seconds(file_path, app.config['UPLOAD_FOLDER'])
        
        if not trimmed_path or not os.path.exists(trimmed_path):
            console.log(f"[Trim-Download] 30초 자르기 실패: {filename}")
            return jsonify({'error': '30초 자르기에 실패했습니다'}), 500
        
        # 파일 크기 검증
        file_size = os.path.getsize(trimmed_path)
        if file_size == 0:
            console.log(f"[Trim-Download] 자른 파일이 비어있음: {trimmed_path}")
            return jsonify({'error': '자른 파일이 비어있습니다'}), 500
        
        console.log(f"[Trim-Download] 30초 자르기 성공: {trimmed_path} ({file_size} bytes)")
        
        # 다운로드 파일명 생성
        base_name = os.path.splitext(filename)[0]
        download_filename = f"{base_name}_30s.mp3"
        
        # 파일을 바로 다운로드로 전송
        return send_file(
            trimmed_path, 
            as_attachment=True, 
            download_name=download_filename,
            mimetype='audio/mpeg'
        )
        
    except Exception as e:
        console.log(f"[Trim-Download] 오류 발생: {str(e)}")
        import traceback
        console.log(f"[Trim-Download] 상세 오류: {traceback.format_exc()}")
        return jsonify({'error': f'30초 자르기 처리 중 오류: {str(e)}'}), 500


@app.route('/api/music-video/upload-audio', methods=['POST'])
def upload_audio_for_video():
    """음원 영상 만들기용 음원 업로드"""
    console.log("[Route] /api/music-video/upload-audio - 음원 업로드 요청")
    
    if 'audio' not in request.files:
        console.log("[Upload Audio] 음원 파일이 없음")
        return jsonify({'error': '음원 파일이 없습니다'}), 400
    
    file = request.files['audio']
    
    if file and allowed_file(file.filename):
        # 안전한 파일명 생성
        filename = generate_safe_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        console.log(f"[Upload Audio] 음원 저장 경로: {filepath}")
        
        # 파일 저장
        file.save(filepath)
        console.log(f"[Upload Audio] 음원 저장 완료: {filename}")
        
        # 음원 파일 검증
        validation = validate_audio_file(filepath)
        
        if validation['valid']:
            # 파일 정보 수집
            file_info = {
                'filename': filename,
                'original_name': file.filename,
                'size': os.path.getsize(filepath),
                'size_mb': get_file_size_mb(filepath),
                'duration': validation['info']['duration'],
                'duration_str': validation['info']['duration_str'],
                'format': validation['info']['format'],
                'path': filepath
            }
            
            console.log(f"[Upload Audio] 검증 통과: {filename}")
            return jsonify({
                'success': True,
                'file_info': file_info
            })
        else:
            # 검증 실패 시 파일 삭제
            os.remove(filepath)
            console.log(f"[Upload Audio] 검증 실패: {validation['error']}")
            return jsonify({
                'success': False,
                'error': f"{file.filename}: {validation['error']}"
            }), 400
    else:
        console.log(f"[Upload Audio] 허용되지 않은 파일: {file.filename}")
        return jsonify({
            'success': False,
            'error': f"{file.filename}: 지원하지 않는 파일 형식입니다"
        }), 400


@app.route('/api/music-video/process-image', methods=['POST'])
def process_image_for_video():
    """음원 영상 만들기용 이미지 처리 (로고 합성 포함)"""
    console.log("[Route] /api/music-video/process-image - 이미지 처리 요청")
    
    if 'image' not in request.files:
        console.log("[Process Image] 이미지 파일이 없음")
        return jsonify({'error': '이미지 파일이 없습니다'}), 400
    
    # 로고 합성 여부 확인
    apply_logo = request.form.get('apply_logo') == 'true'
    console.log(f"[Process Image] 로고 합성: {apply_logo}")
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '파일이 선택되지 않았습니다'}), 400
    
    # 파일 형식 검증
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({'error': '지원하지 않는 이미지 형식입니다'}), 400
    
    try:
        # 원본 이미지를 메모리에서 처리
        from PIL import Image
        import io
        import base64
        
        # 업로드된 이미지 열기
        image = Image.open(file.stream)
        
        # 파일 정보 생성
        file_info = {
            'original_name': file.filename,
            'size_mb': round(len(file.read()) / (1024 * 1024), 2),
            'format': file_ext.upper().replace('.', ''),
            'width': image.width,
            'height': image.height,
            'apply_logo': apply_logo
        }
        
        # 파일 스트림 리셋
        file.stream.seek(0)
        image = Image.open(file.stream)
        
        # 로고 합성 처리
        if apply_logo:
            try:
                # Frame 1.png 경로
                frame_path = os.path.join(os.path.dirname(__file__), 'app', 'Frame 1.png')
                
                if os.path.exists(frame_path):
                    # Frame 이미지 열기
                    frame_image = Image.open(frame_path).convert('RGBA')
                    
                    # Frame 이미지 크기 조절 (25%)
                    img_width, img_height = image.size
                    frame_size = min(img_width, img_height) // 4
                    frame_image = frame_image.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
                    
                    # 업로드된 이미지를 RGBA 모드로 변환
                    if image.mode != 'RGBA':
                        image = image.convert('RGBA')
                    
                    # Frame 이미지를 중앙에 합성
                    frame_x = (img_width - frame_size) // 2
                    frame_y = (img_height - frame_size) // 2
                    
                    # 합성
                    image.paste(frame_image, (frame_x, frame_y), frame_image)
                    
                    console.log(f"[Process Image] 로고 합성 완료: {frame_size}x{frame_size}")
                else:
                    console.log(f"[Process Image] Frame 1.png 파일을 찾을 수 없음")
                    
            except Exception as e:
                console.log(f"[Process Image] 로고 합성 오류: {str(e)}")
        
        # 이미지를 base64로 인코딩하여 반환
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        
        # 임시로 파일도 저장 (영상 생성용)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        image.save(filepath, 'PNG')
        
        file_info['filename'] = filename
        file_info['preview_url'] = f"data:image/png;base64,{img_base64}"
        
        return jsonify({
            'success': True,
            'file_info': file_info
        })
        
    except Exception as e:
        console.log(f"[Process Image] 오류: {str(e)}")
        return jsonify({'error': f'이미지 처리 중 오류: {str(e)}'}), 500


@app.route('/api/music-video/upload-image', methods=['POST'])
def upload_image_for_video():
    """음원 영상 만들기용 이미지 업로드 (기존 호환성)"""
    console.log("[Route] /api/music-video/upload-image - 이미지 업로드 요청")
    
    if 'image' not in request.files:
        console.log("[Upload Image] 이미지 파일이 없음")
        return jsonify({'error': '이미지 파일이 없습니다'}), 400
    
    file = request.files['image']
    
    if file and allowed_image_file(file.filename):
        # 안전한 파일명 생성
        filename = generate_safe_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        console.log(f"[Upload Image] 이미지 저장 경로: {filepath}")
        
        # 파일 저장
        file.save(filepath)
        console.log(f"[Upload Image] 이미지 저장 완료: {filename}")
        
        # 로고 합성 여부 확인
        apply_logo = request.form.get('apply_logo') == 'on'

        # Frame 1.png 합성 처리
        if apply_logo:
            try:
                from PIL import Image
                
                # Frame 1.png 경로
                frame_path = os.path.join(os.path.dirname(__file__), 'app', 'Frame 1.png')
                
                if os.path.exists(frame_path):
                    # 업로드된 이미지 열기
                    uploaded_image = Image.open(filepath)
                    
                    # Frame 이미지 열기 (RGBA 모드로 변환하여 투명도 유지)
                    frame_image = Image.open(frame_path).convert('RGBA')
                    
                    # Frame 이미지 크기를 업로드된 이미지의 30%로 조절
                    img_width, img_height = uploaded_image.size
                    frame_size = min(img_width, img_height) // 4  # 25%
                    frame_image = frame_image.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
                    
                    # 업로드된 이미지를 RGBA 모드로 변환
                    if uploaded_image.mode != 'RGBA':
                        uploaded_image = uploaded_image.convert('RGBA')
                    
                    # Frame 이미지를 업로드된 이미지 중앙에 합성
                    frame_x = (img_width - frame_size) // 2
                    frame_y = (img_height - frame_size) // 2
                    
                    # 합성 (투명도 유지)
                    uploaded_image.paste(frame_image, (frame_x, frame_y), frame_image)
                    
                    # 합성된 이미지를 PNG로 저장
                    uploaded_image.save(filepath, 'PNG')
                    
                    console.log(f"[Upload Image Video] Frame 1.png 합성 완료: {frame_size}x{frame_size} at ({frame_x}, {frame_y})")
                else:
                    console.log(f"[Upload Image Video] Frame 1.png 파일을 찾을 수 없음: {frame_path}")
                    
            except Exception as frame_error:
                console.log(f"[Upload Image Video] Frame 합성 오류: {str(frame_error)}")
                # Frame 합성 실패해도 업로드된 이미지는 유지
        
        # 파일 정보 반환
        file_info = {
            'filename': filename,
            'original_name': file.filename,
            'size': os.path.getsize(filepath),
            'size_mb': get_file_size_mb(filepath),
            'path': filepath
        }
        
        return jsonify({
            'success': True,
            'file_info': file_info
        })
    else:
        console.log(f"[Upload Image] 허용되지 않은 이미지 파일: {file.filename}")
        return jsonify({
            'success': False,
            'error': f"{file.filename}: 지원하지 않는 이미지 형식입니다"
        }), 400


@app.route('/api/music-video/generate-image', methods=['POST'])
def generate_ai_image():
    """OpenAI API를 사용한 AI 이미지 생성"""
    console.log("[Route] /api/music-video/generate-image - AI 이미지 생성 요청")
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        style = data.get('style', 'realistic')
        quality = data.get('quality', 'standard')
        size = data.get('size', '1024x1024')
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': '이미지 설명을 입력해주세요'
            }), 400
        
        # OpenAI API 키 확인
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({
                'success': False,
                'error': 'OpenAI API 키가 설정되지 않았습니다'
            }), 500
        
        # 작업 ID 생성
        job_id = str(uuid.uuid4())
        
        # AI 이미지 생성 작업 시작
        thread = threading.Thread(
            target=generate_ai_image_job,
            args=(job_id, prompt, style, quality, size)
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'AI 이미지 생성을 시작했습니다'
        })
        
    except Exception as e:
        console.log(f"[Generate AI Image] 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/music-video/create-unified', methods=['POST'])
def create_music_video_unified():
    """통합 음원 영상 생성 (파일 업로드 + 영상 생성)"""
    console.log("[Route] /api/music-video/create-unified - 통합 음원 영상 생성 요청")
    
    try:
        # 파일 확인
        if 'audio' not in request.files:
            return jsonify({'error': '음원 파일이 없습니다'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': '음원 파일이 선택되지 않았습니다'}), 400
        
        # 이미지 처리 - 이미 처리된 파일 또는 새 파일
        image_file = request.files.get('image')
        processed_image_filename = request.form.get('processed_image_filename')
        
        # 추가 설정 파라미터
        video_quality = request.form.get('video_quality', 'youtube_hd')
        apply_logo = request.form.get('apply_logo') == 'true'
        add_watermark = request.form.get('add_watermark') == 'true'
        fade_in_out = request.form.get('fade_in_out', 'true') == 'true'
        
        console.log(f"[Unified] 설정 파라미터: video_quality={video_quality}, apply_logo={apply_logo}, add_watermark={add_watermark}, fade_in_out={fade_in_out}")
        console.log(f"[Unified] processed_image_filename: {processed_image_filename}")
        
        # AI 이미지 생성 관련
        ai_prompt = request.form.get('ai_prompt', '').strip()
        ai_style = request.form.get('ai_style', 'realistic')
        ai_size = request.form.get('ai_size', '1024x1024')
        
        # 음원 파일 저장
        audio_filename = secure_filename(audio_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        audio_file.save(audio_path)
        console.log(f"[Unified] 음원 파일 저장: {audio_filename}")
        
        # 이미지 처리
        image_filename = None
        if processed_image_filename:
            # 이미 처리된 이미지 사용
            image_filename = processed_image_filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            
            if os.path.exists(image_path):
                console.log(f"[Unified] 이미 처리된 이미지 사용: {image_filename}")
            else:
                console.log(f"[Unified] 처리된 이미지 파일을 찾을 수 없음: {image_filename}")
                return jsonify({'error': '처리된 이미지 파일을 찾을 수 없습니다'}), 400
                
        elif image_file and image_file.filename:
            # 새로 업로드된 이미지 (실시간 처리 실패 시 폴백)
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)
            console.log(f"[Unified] 새 이미지 파일 저장: {image_filename}")
            
            # 로고 합성 처리 (폴백용)
            if apply_logo:
                try:
                    from PIL import Image
                    
                    # Frame 1.png 경로
                    frame_path = os.path.join(os.path.dirname(__file__), 'app', 'Frame 1.png')
                    
                    if os.path.exists(frame_path):
                        # 업로드된 이미지 열기
                        uploaded_image = Image.open(image_path)
                        
                        # Frame 이미지 열기 (RGBA 모드로 변환하여 투명도 유지)
                        frame_image = Image.open(frame_path).convert('RGBA')
                        
                        # Frame 이미지 크기를 업로드된 이미지의 25%로 조절
                        img_width, img_height = uploaded_image.size
                        frame_size = min(img_width, img_height) // 4  # 25%
                        frame_image = frame_image.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
                        
                        # 업로드된 이미지를 RGBA 모드로 변환
                        if uploaded_image.mode != 'RGBA':
                            uploaded_image = uploaded_image.convert('RGBA')
                        
                        # Frame 이미지를 업로드된 이미지 중앙에 합성
                        frame_x = (img_width - frame_size) // 2
                        frame_y = (img_height - frame_size) // 2
                        
                        # 합성 (투명도 유지)
                        uploaded_image.paste(frame_image, (frame_x, frame_y), frame_image)
                        
                        # 합성된 이미지를 PNG로 저장
                        uploaded_image.save(image_path, 'PNG')
                        
                        console.log(f"[Unified] 폴백 로고 합성 완료: {frame_size}x{frame_size}")
                    else:
                        console.log(f"[Unified] Frame 1.png 파일을 찾을 수 없음")
                        
                except Exception as e:
                    console.log(f"[Unified] 폴백 로고 합성 오류: {str(e)}")
                    
        elif ai_prompt:
            # AI 이미지 생성 요청
            console.log(f"[Unified] AI 이미지 생성 요청: {ai_prompt}")
            # 여기서 AI 이미지 생성 로직 추가 필요
            # 현재는 기본 이미지 사용
            pass
        
        if not image_filename:
            return jsonify({'error': '이미지 파일 또는 AI 프롬프트가 필요합니다'}), 400
        
        # 작업 ID 생성
        job_id = str(uuid.uuid4())
        
        # 옵션 설정
        options = {
            'apply_logo': apply_logo,
            'add_watermark': add_watermark,
            'fade_in_out': fade_in_out
        }
        
        # 영상 생성 작업 시작
        thread = threading.Thread(
            target=create_music_video_job,
            args=(job_id, audio_filename, image_filename, video_quality, options)
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': '음원 영상 생성을 시작했습니다',
            'audio_filename': audio_filename,
            'image_filename': image_filename
        })
        
    except Exception as e:
        console.log(f"[Create Music Video Unified] 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/music-video/create', methods=['POST'])
def create_music_video():
    """음원과 이미지로 영상 생성 (기존 방식)"""
    console.log("[Route] /api/music-video/create - 음원 영상 생성 요청")
    
    try:
        data = request.get_json()
        audio_filename = data.get('audio_filename')
        image_filename = data.get('image_filename')
        video_quality = data.get('video_quality', 'youtube_hd')
        options = data.get('options', {})
        
        if not audio_filename or not image_filename:
            return jsonify({
                'success': False,
                'error': '음원과 이미지 파일이 모두 필요합니다'
            }), 400
        
        # 작업 ID 생성
        job_id = str(uuid.uuid4())
        
        # 영상 생성 작업 시작
        thread = threading.Thread(
            target=create_music_video_job,
            args=(job_id, audio_filename, image_filename, video_quality, options)
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': '음원 영상 생성을 시작했습니다'
        })
        
    except Exception as e:
        console.log(f"[Create Music Video] 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/adjust-pitch', methods=['POST'])
def adjust_pitch_legacy():
    """추출된 음원 키 조절"""
    console.log("[Route] /adjust-pitch - 키 조절 요청")
    
    data = request.get_json()
    filename = data.get('filename', '').strip()
    semitones = data.get('semitones', 0)
    
    if not filename:
        return jsonify({'error': '파일명이 필요합니다'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
    
    # 키 조절 값 검증 (-12 ~ +12 반음)
    try:
        semitones = int(semitones)
        if semitones < -12 or semitones > 12:
            return jsonify({'error': '키 조절은 -12 ~ +12 반음 범위만 가능합니다'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': '올바른 반음 값이 아닙니다'}), 400
    
    if semitones == 0:
        return jsonify({'error': '키 조절이 필요하지 않습니다'}), 400
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # 키 조절 작업 시작
    thread = threading.Thread(
        target=pitch_adjust_job,
        args=(job_id, filename, semitones)
    )
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': f'키 조절 작업을 시작했습니다 ({semitones:+d} 반음)'
    })


def trim_audio_job(job_id, filename):
    """백그라운드 30초 자르기 작업"""
    console.log(f"[Trim Job] {job_id} - 30초 자르기 시작: {filename}")
    
    # 처리 상태 초기화
    processing_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': '30초 자르기 준비 중...',
        'result': None
    }
    
    try:
        # AudioProcessor 사용으로 변경
        processor = AudioProcessor(console_log=console.log, processed_folder=app.config['PROCESSED_FOLDER'])
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 진행률 업데이트
        processing_jobs[job_id]['progress'] = 50
        processing_jobs[job_id]['message'] = '30초 자르기 중...'
        
        # 30초 자르기 실행
        result = processor.trim_audio(file_path, 30)
        
        if result['success']:
            result_path = result['output_path']
        else:
            result_path = None
        
        if result_path and os.path.exists(result_path):
            # 성공
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['message'] = '30초 자르기 완료!'
            processing_jobs[job_id]['result'] = {
                'type': 'trim',
                'original_filename': filename,
                'new_filename': result['filename'],  # AudioProcessor의 올바른 파일명 사용
                'file_info': {
                    'filename': result['filename'],
                    'output_path': result['output_path']
                }
            }
            
            console.log(f"[Trim Job] {job_id} - 완료: {result_path}")
        else:
            # 실패
            processing_jobs[job_id]['status'] = 'error'
            processing_jobs[job_id]['message'] = '30초 자르기 실패'
            console.log(f"[Trim Job] {job_id} - 실패")
        
    except Exception as e:
        console.log(f"[Trim Job] {job_id} - 오류: {str(e)}")
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['message'] = f'오류: {str(e)}'


def generate_ai_image_job(job_id, prompt, style, quality, size):
    """백그라운드 AI 이미지 생성 작업"""
    console.log(f"[AI Image Job] {job_id} - AI 이미지 생성 시작: {prompt}")
    console.log(f"[AI Image Job] {job_id} - 스타일: {style}, 품질: {quality}, 크기: {size}")
    
    # 처리 상태 초기화
    processing_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': 'AI 이미지 생성 중...',
        'result': None
    }
    
    try:
        try:
            from openai import OpenAI
        except ImportError:
            raise Exception("OpenAI 라이브러리가 설치되지 않았습니다. pip install openai를 실행해주세요.")
        
        import requests
        from datetime import datetime
        
        # OpenAI 클라이언트 초기화
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # 프롬프트 길이 검증 및 보완
        if len(prompt.strip()) < 3:
            prompt = "beautiful landscape with vibrant colors"
        
        # 스타일에 따른 프롬프트 조정
        style_prompts = {
            'realistic': f"{prompt}, photorealistic, high quality, detailed, 4k resolution",
            'artistic': f"{prompt}, artistic style, painterly, creative, beautiful art",
            'cartoon': f"{prompt}, cartoon style, animated, colorful, cute illustration"
        }
        
        final_prompt = style_prompts.get(style, style_prompts['realistic'])
        console.log(f"[AI Image Job] 최종 프롬프트: {final_prompt}")
        
        # 진행률 업데이트
        processing_jobs[job_id]['progress'] = 30
        processing_jobs[job_id]['message'] = 'OpenAI API 호출 중...'
        
        # OpenAI DALL-E API 호출 (새로운 방식)
        response = client.images.generate(
            model="dall-e-3",
            prompt=final_prompt,
            size=size,
            quality=quality,
            n=1
        )
        
        processing_jobs[job_id]['progress'] = 70
        processing_jobs[job_id]['message'] = '이미지 다운로드 중...'
        
        # 생성된 이미지 URL 가져오기 (새로운 방식)
        image_url = response.data[0].url
        
        # 이미지 다운로드
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # 파일명 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ai_generated_{timestamp}.png"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # 이미지 저장
            with open(filepath, 'wb') as f:
                f.write(image_response.content)
            
            # Frame 1.png 합성 처리
            try:
                from PIL import Image
                
                processing_jobs[job_id]['progress'] = 80
                processing_jobs[job_id]['message'] = 'Frame 이미지 합성 중...'
                
                # Frame 1.png 경로
                frame_path = os.path.join(os.path.dirname(__file__), 'app', 'Frame 1.png')
                
                if os.path.exists(frame_path):
                    # AI 이미지 열기
                    ai_image = Image.open(filepath)
                    
                    # Frame 이미지 열기 (RGBA 모드로 변환하여 투명도 유지)
                    frame_image = Image.open(frame_path).convert('RGBA')
                    
                    # Frame 이미지 크기를 AI 이미지의 20%로 조절
                    ai_width, ai_height = ai_image.size
                    frame_size = min(ai_width, ai_height) // 5  # 20%
                    frame_image = frame_image.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
                    
                    # AI 이미지를 RGBA 모드로 변환
                    if ai_image.mode != 'RGBA':
                        ai_image = ai_image.convert('RGBA')
                    
                    # Frame 이미지를 AI 이미지 중앙에 합성
                    frame_x = (ai_width - frame_size) // 2
                    frame_y = (ai_height - frame_size) // 2
                    
                    # 합성 (투명도 유지)
                    ai_image.paste(frame_image, (frame_x, frame_y), frame_image)
                    
                    # 합성된 이미지를 PNG로 저장
                    ai_image.save(filepath, 'PNG')
                    
                    console.log(f"[AI Image Job] Frame 1.png 합성 완료: {frame_size}x{frame_size} at ({frame_x}, {frame_y})")
                else:
                    console.log(f"[AI Image Job] Frame 1.png 파일을 찾을 수 없음: {frame_path}")
                    
            except Exception as frame_error:
                console.log(f"[AI Image Job] Frame 합성 오류: {str(frame_error)}")
                # Frame 합성 실패해도 AI 이미지는 유지
            
            # 파일 정보 생성
            file_info = {
                'filename': filename,
                'original_name': f"AI_Generated_{style}.png",
                'size': os.path.getsize(filepath),
                'size_mb': get_file_size_mb(filepath),
                'path': filepath,
                'prompt': prompt,
                'style': style
            }
            
            # 성공
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['message'] = 'AI 이미지 생성 완료!'
            processing_jobs[job_id]['result'] = {
                'type': 'ai_image',
                'file_info': file_info
            }
            
            console.log(f"[AI Image Job] {job_id} - 완료: {filename}")
        else:
            raise Exception("이미지 다운로드 실패")
        
    except Exception as e:
        console.log(f"[AI Image Job] {job_id} - 오류: {str(e)}")
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['message'] = f'오류: {str(e)}'


def create_music_video_job(job_id, audio_filename, image_filename, video_quality, options):
    """백그라운드 음원 영상 생성 작업"""
    console.log(f"[Music Video Job] {job_id} - 음원 영상 생성 시작")
    
    # 처리 상태 초기화
    processing_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': '영상 생성 준비 중...',
        'result': None
    }
    
    try:
        # 동영상 프로세서 생성
        video_processor = VideoProcessor(console_log=console.log)
        
        # 파일 경로 설정
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        
        console.log(f"[Music Video Job] 오디오 파일: {audio_path}")
        console.log(f"[Music Video Job] 이미지 파일: {image_path}")
        
        # 파일 존재 확인
        if not os.path.exists(audio_path):
            raise Exception(f"음원 파일을 찾을 수 없습니다: {audio_filename}")
        if not os.path.exists(image_path):
            raise Exception(f"이미지 파일을 찾을 수 없습니다: {image_filename}")
        
        # 출력 파일명 생성
        output_filename = f"music_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # 영상 품질 설정
        presets = video_processor.get_video_presets()
        if video_quality in presets:
            video_size = presets[video_quality]['size']
            fps = presets[video_quality]['fps']
        else:
            video_size = (1920, 1080)
            fps = 30
        
        # 진행률 콜백 함수
        def progress_callback(progress, message):
            processing_jobs[job_id]['progress'] = progress
            processing_jobs[job_id]['message'] = message
            console.log(f"[Music Video Job] {job_id} - {progress}% - {message}")
        
        # 영상 생성 실행
        result = video_processor.create_video_from_audio_image(
            audio_path=audio_path,
            image_path=image_path,
            output_path=output_path,
            video_size=video_size,
            fps=fps,
            progress_callback=progress_callback
        )
        
        # 처리 완료
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 100
        processing_jobs[job_id]['message'] = '음원 영상 생성 완료!'
        processing_jobs[job_id]['result'] = {
            'type': 'music_video',
            'video_info': result,
            'options': options
        }
        
        console.log(f"[Music Video Job] {job_id} - 영상 생성 완료: {result}")
        
    except Exception as e:
        # 오류 처리
        console.log(f"[Music Video Job] {job_id} - 오류 발생: {str(e)}")
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['message'] = f'오류: {str(e)}'


def pitch_adjust_job(job_id, filename, semitones):
    """백그라운드 키 조절 작업"""
    console.log(f"[Pitch Job] {job_id} - 키 조절 시작: {filename} ({semitones:+d} 반음)")
    
    # 처리 상태 초기화
    processing_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': f'키 조절 준비 중... ({semitones:+d} 반음)',
        'result': None
    }
    
    try:
        # AudioProcessor 사용으로 변경
        processor = AudioProcessor(console_log=console.log, processed_folder=app.config['PROCESSED_FOLDER'])
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 진행률 업데이트
        processing_jobs[job_id]['progress'] = 50
        processing_jobs[job_id]['message'] = f'키 조절 중... ({semitones:+d} 반음)'
        
        # 키 조절 실행
        result = processor.adjust_pitch(file_path, semitones)
        
        if result['success']:
            result_path = result['output_path']
        else:
            result_path = None
        
        if result_path and os.path.exists(result_path):
            # 성공
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['message'] = f'키 조절 완료! ({semitones:+d} 반음)'
            processing_jobs[job_id]['result'] = {
                'type': 'pitch',
                'original_filename': filename,
                'new_filename': result['filename'],  # AudioProcessor의 올바른 파일명 사용
                'semitones': semitones,
                'file_info': {
                    'filename': result['filename'],
                    'output_path': result['output_path']
                }
            }
            
            console.log(f"[Pitch Job] {job_id} - 완료: {result_path}")
        else:
            # 실패
            processing_jobs[job_id]['status'] = 'error'
            processing_jobs[job_id]['message'] = f'키 조절 실패 ({semitones:+d} 반음)'
            console.log(f"[Pitch Job] {job_id} - 실패")
        
    except Exception as e:
        console.log(f"[Pitch Job] {job_id} - 오류: {str(e)}")
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['message'] = f'오류: {str(e)}'


@app.errorhandler(413)
def too_large(e):
    """파일 크기 초과 에러 처리"""
    console.log("[Error] 파일 크기 초과")
    return jsonify({'error': '파일 크기가 너무 큽니다 (최대 500MB)'}), 413


if __name__ == '__main__':
    console.log("=== Music Merger 서버 시작 ===")
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
