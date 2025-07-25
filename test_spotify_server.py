#!/usr/bin/env python3
"""
Spotify 차트 기능 테스트용 간단한 서버
"""

import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime
from spotify_connector import SpotifyConnector

# Flask 앱 초기화
app = Flask(__name__, 
           template_folder='app/templates', 
           static_folder='app/static')
CORS(app)

# 콘솔 로그 함수
class console:
    @staticmethod
    def log(message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")

# Spotify 연결기 초기화
try:
    spotify_connector = SpotifyConnector(console_log=lambda msg: console.log(msg))
    console.log("Spotify 연결기 초기화 완료")
except Exception as e:
    spotify_connector = None
    console.log(f"Spotify 연결기 초기화 실패: {str(e)}")

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('music_analysis.html')

@app.route('/api/spotify/status')
def spotify_status():
    """Spotify API 연결 상태 확인"""
    console.log("[Route] /api/spotify/status - Spotify 상태 확인")
    
    try:
        if spotify_connector:
            status = spotify_connector.get_api_status()
            return jsonify({
                'success': True,
                'status': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Spotify 연결기가 초기화되지 않았습니다'
            })
    except Exception as e:
        console.log(f"[Route] Spotify 상태 확인 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/spotify/charts/<region>/<playlist_type>')
def get_spotify_charts(region, playlist_type):
    """Spotify 차트 데이터 가져오기"""
    console.log(f"[Route] /api/spotify/charts/{region}/{playlist_type} - 차트 요청")
    
    try:
        if not spotify_connector:
            return jsonify({
                'success': False,
                'error': 'Spotify 연결기가 초기화되지 않았습니다'
            }), 500
        
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 50)  # 최대 50개로 제한
        
        result = spotify_connector.get_trending_tracks(
            region=region,
            playlist_type=playlist_type,
            limit=limit
        )
        
        return jsonify(result)
        
    except Exception as e:
        console.log(f"[Route] Spotify 차트 요청 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    console.log("=== Spotify 차트 테스트 서버 시작 ===")
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)