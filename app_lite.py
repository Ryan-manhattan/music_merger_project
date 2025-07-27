#!/usr/bin/env python3
"""
Music Merger Lite - 경량 버전
의존성 최소화로 빠른 실행 가능
"""

import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import threading
import uuid

# Flask 앱 초기화
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

# 백그라운드 작업 관리
background_jobs = {}

def console_log(message):
    """간단한 콘솔 로그"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def allowed_file(filename, allowed_extensions):
    """파일 확장자 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_safe_filename(filename):
    """안전한 파일명 생성"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    safe_name = secure_filename(name)
    random_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{safe_name}_{random_id}{ext}"

def get_file_size_mb(file_path):
    """파일 크기를 MB 단위로 반환"""
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)

# ===========================================
# 기본 라우트들
# ===========================================

@app.route('/')
def index():
    """메인 페이지 - 음악 병합"""
    return render_template('index.html')

@app.route('/music-analysis')
def music_analysis():
    """AI 음악 생성 페이지"""
    return render_template('music_analysis.html')

@app.route('/music-video')
def music_video():
    """음원 영상 만들기 페이지"""
    return render_template('music_video.html')

@app.route('/charts')
def charts():
    """차트 분석 페이지"""
    return render_template('charts.html')

# ===========================================
# API 엔드포인트들
# ===========================================

@app.route('/api/health')
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'status': 'ok',
        'message': 'Music Merger Lite 서버가 정상 작동 중입니다',
        'version': 'lite',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """파일 업로드"""
    console_log("[API] 파일 업로드 요청")
    
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'})
    
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'})
    
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            safe_filename = generate_safe_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            file.save(file_path)
            
            file_info = {
                'filename': safe_filename,
                'original_name': file.filename,
                'size_mb': get_file_size_mb(file_path),
                'format': file.filename.rsplit('.', 1)[1].lower()
            }
            uploaded_files.append(file_info)
            console_log(f"[Upload] 파일 업로드 완료: {file.filename}")
    
    return jsonify({
        'success': True,
        'files': uploaded_files,
        'count': len(uploaded_files)
    })

@app.route('/api/music-video/upload-audio', methods=['POST'])
def upload_audio_for_video():
    """음원 영상 만들기용 음원 업로드"""
    console_log("[API] 음원 영상용 오디오 업로드")
    
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': '음원 파일이 없습니다'})
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다'})
    
    if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        safe_filename = generate_safe_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        
        file_info = {
            'filename': safe_filename,
            'original_name': file.filename,
            'size_mb': get_file_size_mb(file_path),
            'format': file.filename.rsplit('.', 1)[1].lower(),
            'duration_str': '알 수 없음'  # 실제 분석은 무거운 라이브러리 필요
        }
        
        return jsonify({'success': True, 'file_info': file_info})
    
    return jsonify({'success': False, 'error': '지원되지 않는 파일 형식입니다'})

@app.route('/api/music-video/upload-image', methods=['POST'])
def upload_image_for_video():
    """음원 영상 만들기용 이미지 업로드"""
    console_log("[API] 음원 영상용 이미지 업로드")
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '이미지 파일이 없습니다'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다'})
    
    if file and allowed_file(file.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
        safe_filename = generate_safe_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        
        file_info = {
            'filename': safe_filename,
            'original_name': file.filename,
            'size_mb': get_file_size_mb(file_path)
        }
        
        return jsonify({'success': True, 'file_info': file_info})
    
    return jsonify({'success': False, 'error': '지원되지 않는 이미지 형식입니다'})

@app.route('/api/music-video/generate-image', methods=['POST'])
def generate_ai_image():
    """OpenAI API를 사용한 AI 이미지 생성 - Lite 버전에서는 비활성화"""
    return jsonify({
        'success': False, 
        'error': 'Lite 버전에서는 AI 이미지 생성 기능이 비활성화되어 있습니다. 이미지를 직접 업로드해주세요.'
    })

@app.route('/download/<filename>')
def download_file(filename):
    """파일 다운로드"""
    # 업로드 폴더에서 먼저 찾기
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(upload_path):
        return send_file(upload_path, as_attachment=True)
    
    # 처리된 폴더에서 찾기
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    if os.path.exists(processed_path):
        return send_file(processed_path, as_attachment=True)
    
    return jsonify({'error': '파일을 찾을 수 없습니다'}), 404

@app.route('/status/<job_id>')
def job_status(job_id):
    """작업 상태 확인"""
    if job_id not in background_jobs:
        return jsonify({'status': 'not_found', 'message': '작업을 찾을 수 없습니다'})
    
    job = background_jobs[job_id]
    return jsonify({
        'status': job.get('status', 'unknown'),
        'progress': job.get('progress', 0),
        'message': job.get('message', '처리 중...'),
        'result': job.get('result', None)
    })

# ===========================================
# 에러 핸들러
# ===========================================

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': '파일 크기가 너무 큽니다. 500MB 이하의 파일을 업로드해주세요.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': '요청한 리소스를 찾을 수 없습니다.'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': '서버 내부 오류가 발생했습니다.'}), 500

if __name__ == '__main__':
    console_log("=== Music Merger Lite 서버 시작 ===")
    console_log("🎵 경량 버전으로 실행 중")
    console_log("📍 http://localhost:5000")
    console_log("🛑 Ctrl+C로 중지")
    
    debug = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=debug, host='0.0.0.0', port=port)