#!/usr/bin/env python3
"""
Music Merger - 최소 기능 테스트용 앱
NumPy 호환성 문제 회피를 위한 간단한 버전
"""

import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import json

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

def allowed_file(filename, allowed_extensions):
    """파일 확장자 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    """메인 페이지"""
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

@app.route('/api/health')
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'status': 'ok',
        'message': 'Music Merger 서버가 정상 작동 중입니다',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/upload-test', methods=['POST'])
def upload_test():
    """파일 업로드 테스트"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '파일이 없습니다'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다'})
    
    if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'message': '파일 업로드 성공',
            'filename': safe_filename,
            'size': os.path.getsize(file_path)
        })
    
    return jsonify({'success': False, 'error': '지원되지 않는 파일 형식입니다'})

if __name__ == '__main__':
    print("🎵 Music Merger 테스트 서버 시작")
    print("📍 http://localhost:5000")
    print("🛑 Ctrl+C로 중지")
    
    debug = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=debug, host='0.0.0.0', port=port)