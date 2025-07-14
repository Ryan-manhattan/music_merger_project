"""
Music Merger - 유틸리티 함수들
"""

import os
# import magic  # magic 모듈 주석 처리
from pydub import AudioSegment
from datetime import datetime, timedelta

# FFmpeg 경로 설정
ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg-master-latest-win64-gpl', 'bin')
if os.path.exists(ffmpeg_path):
    AudioSegment.converter = os.path.join(ffmpeg_path, 'ffmpeg.exe')
    AudioSegment.ffmpeg = os.path.join(ffmpeg_path, 'ffmpeg.exe')
    AudioSegment.ffprobe = os.path.join(ffmpeg_path, 'ffprobe.exe')

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
        # pydub으로 오디오 정보 추출 (FFmpeg 없이 기본 포맷만)
        try:
            console_log(f"pydub으로 파일 읽기 시도: {filepath}")
            # MP3/MP4 파일인 경우 FFmpeg 없이 처리 시도
            if ext in ['.mp3', '.mp4']:
                try:
                    # FFmpeg 없이 처리 어려우므로 기본값 반환
                    console_log(f"{ext.upper()} 파일 - 기본 정보로 처리")
                    file_size = os.path.getsize(filepath)
                    # 대략적인 추정 (1MB당 약 1분)
                    estimated_duration = max(file_size / (1024 * 1024) * 60, 30)
                    
                    format_name = 'MP3' if ext == '.mp3' else 'MP4'
                    
                    result['info'] = {
                        'duration': estimated_duration,
                        'duration_str': format_duration(estimated_duration),
                        'channels': 2,
                        'frame_rate': 44100,
                        'sample_width': 2,
                        'bitrate': 128000,
                        'format': format_name
                    }
                    result['valid'] = True
                    return result
                except Exception:
                    pass
            
            audio = AudioSegment.from_file(filepath)
            # 오디오 정보 수집
            result['info'] = {
                'duration': len(audio) / 1000.0,  # 초 단위
                'duration_str': format_duration(len(audio) / 1000.0),
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'bitrate': audio.frame_rate * audio.frame_width * 8,
                'format': ext[1:].upper()
            }
            console_log(f"오디오 정보: {result['info']}")
            # 최대 길이 체크 (30분)
            if result['info']['duration'] > 1800:
                result['error'] = '파일 길이가 너무 깁니다 (최대 30분)'
                return result
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
