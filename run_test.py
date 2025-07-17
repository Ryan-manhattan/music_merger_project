#!/usr/bin/env python3
import subprocess
import sys
import os

# 현재 디렉토리를 프로젝트 디렉토리로 변경
os.chdir('/Users/kimjunhyeong/music_merger_project')

# 가상환경 활성화를 포함한 실행 명령
venv_python = '/Users/kimjunhyeong/music_merger_project/venv/bin/python'

# 테스트 앱 실행
subprocess.run([venv_python, 'test_app.py'])
