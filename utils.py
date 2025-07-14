"""
Music Merger - 유틸리티 함수들
"""

import os
import subprocess
import json
from datetime import datetime, timedelta

# FFmpeg 경로 설정
ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg-master-latest-win64-gpl', 'bin')
FFMPEG_EXE = os.path.join(ffmpeg_path, 'ffmpeg.exe') if os.path.exists(ffmpeg_path) else 'ffmpeg'
FFPROBE_EXE = os.path.join(ffmpeg_path, 'ffprobe.exe') if os.path.exists(ffmpeg_path) else 'ffprobe'

# 허용된 MIME 타입
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.webm'}

def validate_audio_file(filepath):
    """
    오디오 파일 유효성 검증 (확장자만 검사)
    Args:
        filepath: 검증할 파일 경로
    Returns:
        dict: 유효성 검증 결과 및 파일 정보
    """
    console_log = lambda msg: print(f"[Validate] {msg}")
    result = {
        'valid': False,
        'error': None,
        'info': {}
    }
    try:
        # 파일 존재 확인
        console_log(f"파일 경로 확인: {filepath}")
        console_log(f"파일 존재 여부: {os.path.exists(filepath)}")
        
        if not os.path.exists(filepath):
            result['error'] = f'파일이 존재하지 않습니다: {filepath}'
            return result
        # 확장자 검사
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            result['error'] = f'지원하지 않는 파일 확장자입니다: {ext}'
            return result
        # 기본 정보로 검증 (ffprobe 없이)
        try:
            console_log(f"파일 기본 정보 확인: {filepath}")
            
            # 파일 크기로 대략적인 지속시간 추정
            file_size = os.path.getsize(filepath)
            console_log(f"파일 크기: {file_size} bytes")
            
            # 대략적인 추정 (파일 크기 기반)
            if ext == '.mp3':
                # MP3: 1MB당 약 1분 (128kbps 기준)
                estimated_duration = max(file_size / (1024 * 1024) * 60, 10)
            elif ext == '.wav':
                # WAV: 1MB당 약 6초 (16bit, 44.1kHz 스테레오 기준)
                estimated_duration = max(file_size / (1024 * 1024) * 6, 10)
            else:
                # 기타 포맷
                estimated_duration = max(file_size / (1024 * 1024) * 30, 10)
            
            # 최대 30분 제한
            if estimated_duration > 1800:
                result['error'] = f'파일이 너무 큽니다 (추정: {estimated_duration/60:.1f}분, 최대: 30분)'
                return result
            
            # 기본 오디오 정보 설정
            result['info'] = {
                'duration': estimated_duration,
                'duration_str': format_duration(estimated_duration),
                'channels': 2,
                'frame_rate': 44100,
                'sample_width': 2,
                'bitrate': 128000,
                'format': ext[1:].upper()
            }
            
            console_log(f"추정 오디오 정보: {result['info']}")
            result['valid'] = True
        except Exception as e:
            result['error'] = f'오디오 파일 읽기 실패: {str(e)}'
            console_log(f"오디오 읽기 오류: {e}")
    except Exception as e:
        result['error'] = f'파일 검증 실패: {str(e)}'
        console_log(f"검증 오류: {e}")
    return result


def format_duration(seconds):
    """
    초를 mm:ss 형식으로 변환
    """
    if seconds < 0:
        return "00:00"
    
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def cleanup_old_files(folder_path, hours=1):
    """
    오래된 임시 파일 정리
    
    Args:
        folder_path: 정리할 폴더 경로
        hours: 파일 보관 시간 (기본 1시간)
    """
    console_log = lambda msg: print(f"[Cleanup] {msg}")
    
    try:
        now = datetime.now()
        cutoff_time = now - timedelta(hours=hours)
        
        for filename in os.listdir(folder_path):
            if filename.startswith('.'):
                continue
                
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_modified < cutoff_time:
                    os.remove(filepath)
                    console_log(f"삭제됨: {filename}")
                    
    except Exception as e:
        console_log(f"정리 중 오류: {e}")


def generate_safe_filename(original_filename):
    """
    안전한 파일명 생성
    """
    from werkzeug.utils import secure_filename
    import uuid
    
    # 기본 secure_filename 적용
    safe_name = secure_filename(original_filename)
    
    # 확장자 분리
    name, ext = os.path.splitext(safe_name)
    
    # UUID 추가하여 중복 방지
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"{timestamp}_{name}_{unique_id}{ext}"


def get_file_size_mb(filepath):
    """
    파일 크기를 MB 단위로 반환
    """
    size_bytes = os.path.getsize(filepath)
    return round(size_bytes / (1024 * 1024), 2)
