#!/usr/bin/env python3
"""
Flask 서버 실행 스크립트
"""

import subprocess
import sys
import os
import time

def run_server():
    """Flask 서버 실행"""
    # 현재 디렉토리를 프로젝트 루트로 변경
    os.chdir('/Users/kimjunhyeong/music_merger_project')
    
    # 가상환경의 Python 경로
    venv_python = '/Users/kimjunhyeong/music_merger_project/venv/bin/python'
    
    try:
        # Flask 앱 실행
        print("Flask 서버 시작 중...")
        process = subprocess.Popen([
            venv_python, 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 서버가 시작될 때까지 잠시 대기
        time.sleep(3)
        
        print("Flask 서버가 시작되었습니다: http://localhost:5000")
        print("서버를 중지하려면 Ctrl+C를 누르세요.")
        
        # 서버 출력 모니터링
        for line in iter(process.stdout.readline, ''):
            print(line.strip())
            
    except KeyboardInterrupt:
        print("\n서버를 종료합니다...")
        process.terminate()
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    run_server()
