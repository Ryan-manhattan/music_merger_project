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

# 음악 서비스 초기화 (환경 변수 설정 후)
music_service = None
try:
    music_service = MusicService(console_log=lambda msg: console.log(msg))
    console.log("음악 서비스 초기화 완료")
except Exception as e:
    console.log(f"음악 서비스 초기화 실패: {str(e)}")

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
    """처리된 파일 다운로드"""
    console.log(f"[Route] /download/{filename} - 파일 다운로드 요청")
    
    filepath = os.path.join(app.config['PROCESSED_FOLDER'], secure_filename(filename))
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404


# ===========================================
# 음악 분석 및 AI 생성 API 라우팅
# ===========================================

@app.route('/api/music-analysis/status')
def music_analysis_status():
    """음악 분석 서비스 상태 확인"""
    console.log("[Route] /api/music-analysis/status - 서비스 상태 확인")
    
    try:
        if music_service:
            status = music_service.check_service_status()
            return jsonify(status)
        else:
            return jsonify({
                'overall_status': 'error',
                'error': '음악 서비스가 초기화되지 않았습니다'
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
        if not music_service:
            return jsonify({
                'success': False,
                'error': '음악 서비스가 초기화되지 않았습니다'
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
            'message': '음악 분석을 시작했습니다'
        })
        
    except Exception as e:
        console.log(f"[Music Analysis] 분석 요청 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/music-analysis/generate', methods=['POST'])
def generate_music():
    """YouTube 음악 분석 후 AI 생성"""
    console.log("[Route] /api/music-analysis/generate - 음악 생성 요청")
    
    try:
        if not music_service:
            return jsonify({
                'success': False,
                'error': '음악 서비스가 초기화되지 않았습니다'
            }), 500
        
        data = request.get_json()
        url = data.get('url', '').strip()
        options = data.get('options', {})
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'YouTube URL이 필요합니다'
            }), 400
        
        # 작업 ID 생성
        job_id = str(uuid.uuid4())
        
        # 생성 작업 시작
        thread = threading.Thread(
            target=generate_music_job,
            args=(job_id, url, options)
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': '음악 분석 및 생성을 시작했습니다'
        })
        
    except Exception as e:
        console.log(f"[Music Analysis] 생성 요청 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
    """음악 생성 이력 조회"""
    console.log("[Route] /api/music-analysis/history - 이력 조회 요청")
    
    try:
        if music_service:
            history = music_service.get_generation_history()
            return jsonify({
                'success': True,
                'history': history
            })
        else:
            return jsonify({
                'success': False,
                'error': '음악 서비스가 초기화되지 않았습니다'
            }), 500
    except Exception as e:
        console.log(f"[Music Analysis] 이력 조회 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        
        # 음악 분석 실행
        result = music_service.analyze_only(url, progress_callback)
        
        if result['success']:
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
