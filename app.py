#!/usr/bin/env python3
"""
Music Merger - 음악 파일 이어붙이기 웹 서비스
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

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import threading
import uuid
from utils import validate_audio_file, generate_safe_filename, get_file_size_mb
from audio_processor import AudioProcessor
from link_extractor import LinkExtractor
from video_processor import VideoProcessor
from music_service import MusicService
from database import DatabaseManager
from trends_analyzer import TrendsAnalyzer
from market_analyzer import MusicMarketAnalyzer
from emotion_playlist_generator import EmotionPlaylistGenerator

# Flask 앱 초기화 (Windows 경로 대응)
app = Flask(__name__, 
           template_folder='app/templates', 
           static_folder='app/static')
CORS(app)

# 설정
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB 제한
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'app', 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.path.dirname(__file__), 'app', 'processed')
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'm4a', 'flac', 'mp4', 'webm'}
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'bmp', 'gif'}

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

try:
    # 프로젝트 루트의 기본 DB 파일 사용
    db_path = os.path.join(os.path.dirname(__file__), 'music_analysis.db')
    db_manager = DatabaseManager(db_path=db_path, console_log=lambda msg: console.log(msg))
    console.log("데이터베이스 매니저 초기화 완료")
except Exception as e:
    console.log(f"데이터베이스 매니저 초기화 실패: {str(e)}")

try:
    trends_analyzer = TrendsAnalyzer(console_log=lambda msg: console.log(msg))
    console.log("트렌드 분석기 초기화 완료")
except Exception as e:
    trends_analyzer = None
    console.log(f"트렌드 분석기 초기화 실패: {str(e)}")

try:
    market_analyzer = MusicMarketAnalyzer(console_log=lambda msg: console.log(msg))
    console.log("시장 분석기 초기화 완료")
except Exception as e:
    market_analyzer = None
    console.log(f"시장 분석기 초기화 실패: {str(e)}")

# Music Trend Analyzer V2 초기화
try:
    from music_trend_analyzer_v2 import MusicTrendAnalyzerV2
    trend_analyzer_v2 = MusicTrendAnalyzerV2(console_log=lambda msg: console.log(msg))
    console.log("Music Trend Analyzer V2 초기화 완료")
except Exception as e:
    trend_analyzer_v2 = None
    console.log(f"Music Trend Analyzer V2 초기화 실패: {str(e)}")

# 감정 플레이리스트 생성기 초기화
try:
    emotion_playlist_generator = EmotionPlaylistGenerator(console_log=lambda msg: console.log(msg))
    console.log("감정 플레이리스트 생성기 초기화 완료")
except Exception as e:
    emotion_playlist_generator = None
    console.log(f"감정 플레이리스트 생성기 초기화 실패: {str(e)}")

# 음악 분석 작업 저장소
music_analysis_jobs = {}


def allowed_file(filename):
    """파일 확장자 검증"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def allowed_image_file(filename):
    """이미지 파일 확장자 검증"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_IMAGE_EXTENSIONS']


# cleanup 함수 제거 - 파일 자동 삭제 방지


@app.route('/')
def index():
    """메인 페이지"""
    print("[Route] / - 메인 페이지 요청")
    return render_template('index.html')


@app.route('/music-analysis')
def music_analysis():
    """음악 분석 페이지"""
    console.log("[Route] /music-analysis - 음악 분석 페이지 요청")
    return render_template('music_analysis.html')


@app.route('/emotion-playlist')
def emotion_playlist():
    """감정 플레이리스트 페이지"""
    console.log("[Route] /emotion-playlist - 감정 플레이리스트 페이지 요청")
    return render_template('emotion_playlist.html')


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
        processor = AudioProcessor(console_log=console.log)
        
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
            # 링크 추출 파일인지 확인 (다양한 패턴 체크)
            filename_lower = safe_filename.lower()
            is_extracted_file = (
                'youtube_' in filename_lower or  # 링크 추출 파일
                '_30s.' in filename_lower or     # 30초 자른 파일
                '_30s_' in filename_lower or     # 30초 자른 파일 (다른 패턴)
                '_plus' in filename_lower or     # 키 올린 파일
                '_minus' in filename_lower or    # 키 내린 파일
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


# ===========================================
# 시장 분석 API 라우팅
# ===========================================

@app.route('/api/market/analyze/<genre>')
def analyze_genre_market(genre):
    """특정 장르의 시장 분석"""
    console.log(f"[Route] /api/market/analyze/{genre} - 장르 시장 분석")
    
    try:
        if not market_analyzer:
            return jsonify({
                'success': False,
                'error': '시장 분석기가 초기화되지 않았습니다'
            }), 500
        
        timeframe = request.args.get('timeframe', 'today 12-m')
        geo = request.args.get('geo', 'KR')
        
        result = market_analyzer.analyze_genre_market(genre, timeframe, geo)
        return jsonify(result)
        
    except Exception as e:
        console.log(f"[Route] 장르 시장 분석 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/market/compare', methods=['POST'])
def compare_genre_markets():
    """여러 장르의 시장 비교 분석"""
    console.log("[Route] /api/market/compare - 장르 시장 비교")
    
    try:
        if not market_analyzer:
            return jsonify({
                'success': False,
                'error': '시장 분석기가 초기화되지 않았습니다'
            }), 500
        
        data = request.get_json()
        genres = data.get('genres', [])
        timeframe = data.get('timeframe', 'today 12-m')
        geo = data.get('geo', 'KR')
        
        if not genres or len(genres) < 2:
            return jsonify({
                'success': False,
                'error': '비교할 장르를 2개 이상 입력해주세요'
            }), 400
        
        result = market_analyzer.compare_genre_markets(genres, timeframe, geo)
        return jsonify(result)
        
    except Exception as e:
        console.log(f"[Route] 장르 시장 비교 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/market/overview')
def get_market_overview():
    """전체 음악 시장 개관"""
    console.log("[Route] /api/market/overview - 전체 시장 개관")
    
    try:
        if not market_analyzer:
            return jsonify({
                'success': False,
                'error': '시장 분석기가 초기화되지 않았습니다'
            }), 500
        
        timeframe = request.args.get('timeframe', 'today 12-m')
        geo = request.args.get('geo', 'KR')
        
        result = market_analyzer.get_market_overview(timeframe, geo)
        return jsonify(result)
        
    except Exception as e:
        console.log(f"[Route] 시장 개관 분석 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/market/genres')
def get_supported_genres():
    """지원되는 장르 목록"""
    console.log("[Route] /api/market/genres - 지원 장르 목록")
    
    try:
        if not market_analyzer:
            return jsonify({
                'success': False,
                'error': '시장 분석기가 초기화되지 않았습니다'
            }), 500
        
        genres = market_analyzer.genre_mapping
        genre_list = []
        
        for genre_id, genre_info in genres.items():
            genre_list.append({
                'id': genre_id,
                'korean': genre_info['ko'],
                'english': genre_info['en'],
                'category': genre_info['category']
            })
        
        return jsonify({
            'success': True,
            'genres': genre_list,
            'count': len(genre_list)
        })
        
    except Exception as e:
        console.log(f"[Route] 장르 목록 조회 오류: {str(e)}")
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
    return render_template('charts.html')

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


# === 감정 플레이리스트 API 엔드포인트 ===

@app.route('/api/emotion-playlist/status')
def emotion_playlist_status():
    """감정 플레이리스트 생성기 상태 확인"""
    console.log("[Route] /api/emotion-playlist/status - 상태 확인")
    
    try:
        if not emotion_playlist_generator:
            return jsonify({
                'success': False,
                'error': '감정 플레이리스트 생성기가 초기화되지 않았습니다'
            }), 500
        
        status = emotion_playlist_generator.get_api_status()
        return jsonify({
            'success': True,
            'status': status,
            'available_emotions': list(emotion_playlist_generator.emotion_categories.keys())
        })
        
    except Exception as e:
        console.log(f"[Route] 감정 플레이리스트 상태 확인 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/emotion-playlist/generate', methods=['POST'])
def generate_emotion_playlist():
    """감정별 플레이리스트 생성"""
    console.log("[Route] /api/emotion-playlist/generate - 플레이리스트 생성")
    
    try:
        if not emotion_playlist_generator:
            return jsonify({
                'success': False,
                'error': '감정 플레이리스트 생성기가 초기화되지 않았습니다'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '요청 데이터가 없습니다'
            }), 400
        
        emotion_type = data.get('emotion_type')
        if not emotion_type:
            return jsonify({
                'success': False,
                'error': '감정 타입을 지정해주세요'
            }), 400
        
        limit = data.get('limit', 30)
        include_reddit = data.get('include_reddit', True)
        include_spotify = data.get('include_spotify', True)
        include_youtube = data.get('include_youtube', True)
        
        console.log(f"[Route] 감정 플레이리스트 생성: {emotion_type} ({limit}곡)")
        
        # 플레이리스트 생성
        result = emotion_playlist_generator.generate_emotion_playlist(
            emotion_type=emotion_type,
            limit=limit,
            include_reddit=include_reddit,
            include_spotify=include_spotify,
            include_youtube=include_youtube
        )
        
        if result.get('success'):
            console.log(f"[Route] 감정 플레이리스트 생성 완료: {result.get('total_tracks', 0)}곡")
            return jsonify(result)
        else:
            console.log(f"[Route] 감정 플레이리스트 생성 실패: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        console.log(f"[Route] 감정 플레이리스트 생성 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/emotion-playlist/all')
def get_all_emotion_playlists():
    """모든 감정별 플레이리스트 생성"""
    console.log("[Route] /api/emotion-playlist/all - 전체 플레이리스트 생성")
    
    try:
        if not emotion_playlist_generator:
            return jsonify({
                'success': False,
                'error': '감정 플레이리스트 생성기가 초기화되지 않았습니다'
            }), 500
        
        limit_per_emotion = request.args.get('limit', 20, type=int)
        
        console.log(f"[Route] 전체 감정 플레이리스트 생성: 감정당 {limit_per_emotion}곡")
        
        # 모든 감정 플레이리스트 생성
        result = emotion_playlist_generator.get_all_emotion_playlists(limit_per_emotion)
        
        if result.get('success'):
            console.log(f"[Route] 전체 감정 플레이리스트 생성 완료: {result.get('total_playlists', 0)}개")
            return jsonify(result)
        else:
            console.log(f"[Route] 전체 감정 플레이리스트 생성 실패: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        console.log(f"[Route] 전체 감정 플레이리스트 생성 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/emotion-playlist/categories')
def get_emotion_categories():
    """감정 카테고리 목록 및 설명"""
    console.log("[Route] /api/emotion-playlist/categories - 카테고리 목록")
    
    try:
        if not emotion_playlist_generator:
            return jsonify({
                'success': False,
                'error': '감정 플레이리스트 생성기가 초기화되지 않았습니다'
            }), 500
        
        categories = {}
        for emotion_type, config in emotion_playlist_generator.emotion_categories.items():
            categories[emotion_type] = {
                'name': config['name'],
                'description': config['description'],
                'keywords': config['keywords'][:5],  # 상위 5개 키워드만
                'comment_prompt': config['comment_prompt']
            }
        
        return jsonify({
            'success': True,
            'categories': categories,
            'total_categories': len(categories)
        })
        
    except Exception as e:
        console.log(f"[Route] 감정 카테고리 목록 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500




@app.route('/trim-audio', methods=['POST'])
def trim_audio():
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


@app.route('/adjust-pitch', methods=['POST'])
def adjust_pitch():
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
        # LinkExtractor 사용
        extractor = LinkExtractor(console_log=console.log)
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 진행률 업데이트
        processing_jobs[job_id]['progress'] = 50
        processing_jobs[job_id]['message'] = '30초 자르기 중...'
        
        # 30초 자르기 실행
        result_path = extractor._trim_audio_to_30_seconds(file_path, app.config['UPLOAD_FOLDER'])
        
        if result_path and os.path.exists(result_path):
            # 성공
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['message'] = '30초 자르기 완료!'
            processing_jobs[job_id]['result'] = {
                'type': 'trim',
                'original_filename': filename,
                'new_filename': os.path.basename(result_path)
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
        # LinkExtractor 사용
        extractor = LinkExtractor(console_log=console.log)
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 진행률 업데이트
        processing_jobs[job_id]['progress'] = 50
        processing_jobs[job_id]['message'] = f'키 조절 중... ({semitones:+d} 반음)'
        
        # 키 조절 실행
        result_path = extractor.adjust_pitch(file_path, app.config['UPLOAD_FOLDER'], semitones)
        
        if result_path and os.path.exists(result_path):
            # 성공
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['message'] = f'키 조절 완료! ({semitones:+d} 반음)'
            processing_jobs[job_id]['result'] = {
                'type': 'pitch',
                'original_filename': filename,
                'new_filename': os.path.basename(result_path),
                'semitones': semitones
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
