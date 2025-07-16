"""
Music Merger - 오디오 처리 엔진 (FFmpeg 기반)
"""

import os
import subprocess
import json
import tempfile
from datetime import datetime

# FFmpeg 경로 설정
ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg-master-latest-win64-gpl', 'bin')
FFMPEG_EXE = os.path.join(ffmpeg_path, 'ffmpeg.exe') if os.path.exists(ffmpeg_path) else 'ffmpeg'
FFPROBE_EXE = os.path.join(ffmpeg_path, 'ffprobe.exe') if os.path.exists(ffmpeg_path) else 'ffprobe'

class AudioProcessor:
    """FFmpeg 기반 오디오 파일 처리 클래스"""
    
    def __init__(self, console_log=None):
        self.console_log = console_log or print
        
    def log(self, message):
        """로그 메시지 출력"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.console_log(f"[{timestamp}] [AudioProcessor] {message}")
        
    def get_audio_info(self, filepath):
        """오디오 파일 정보 가져오기 (기본값 사용)"""
        self.log(f"파일 정보 확인: {filepath}")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")
        
        try:
            # 파일 크기 기반 추정
            file_size = os.path.getsize(filepath)
            ext = os.path.splitext(filepath)[1].lower()
            
            # 대략적인 지속시간 추정
            if ext == '.mp3':
                estimated_duration = max(file_size / (1024 * 1024) * 60, 10)
            elif ext == '.wav':
                estimated_duration = max(file_size / (1024 * 1024) * 6, 10)
            else:
                estimated_duration = max(file_size / (1024 * 1024) * 30, 10)
            
            self.log(f"파일 크기: {file_size} bytes, 추정 길이: {estimated_duration:.1f}초")
            
            return {
                'duration': estimated_duration,
                'channels': 2,
                'sample_rate': 44100,
                'bitrate': 128000
            }
            
        except Exception as e:
            self.log(f"파일 정보 확인 실패: {str(e)}")
            # 최소한의 기본값 반환
            return {
                'duration': 60.0,
                'channels': 2,
                'sample_rate': 44100,
                'bitrate': 128000
            }
            
    def merge_audio_files(self, file_list, global_settings, output_path, progress_callback=None):
        """
        여러 오디오 파일 병합 (FFmpeg 기반)
        
        Args:
            file_list: [{filename, settings}] 형태의 파일 목록
            global_settings: 전체 설정 (normalizeVolume, crossfade)
            output_path: 출력 파일 경로
            progress_callback: 진행률 콜백 함수
        """
        self.log(f"병합 시작: {len(file_list)}개 파일")
        
        # 모든 파일 존재 여부 사전 확인
        missing_files = []
        for file_info in file_list:
            filename = file_info['filename']
            if not os.path.exists(filename):
                missing_files.append(filename)
                self.log(f"파일 없음: {filename}")
        
        if missing_files:
            error_msg = f"다음 파일들을 찾을 수 없습니다: {', '.join([os.path.basename(f) for f in missing_files])}"
            self.log(f"병합 실패: {error_msg}")
            raise FileNotFoundError(error_msg)
        
        try:
            # 임시 파일 목록 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                filelist_path = f.name
                
                for file_info in file_list:
                    filename = file_info['filename']
                    # Windows 경로 처리
                    filename = os.path.abspath(filename).replace('\\', '/')
                    f.write(f"file '{filename}'\n")
            
            if progress_callback:
                progress_callback(20, "파일 목록 생성 완료")
            
            # FFmpeg concat 명령어로 병합
            cmd = [
                FFMPEG_EXE,
                '-f', 'concat',
                '-safe', '0',
                '-i', filelist_path,
                '-vn',  # 비디오 스트림 제거
                '-acodec', 'libmp3lame',  # MP3 인코딩
                '-ab', '320k',  # 비트레이트 설정
                '-ar', '44100',  # 샘플레이트 설정
                '-y',  # 덮어쓰기
                output_path
            ]
            
            if progress_callback:
                progress_callback(50, "오디오 병합 중...")
            
            self.log(f"FFmpeg 실행: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5분 타임아웃
            )
            
            # 임시 파일 정리
            try:
                os.unlink(filelist_path)
            except:
                pass
            
            if result.returncode != 0:
                self.log(f"FFmpeg 오류: {result.stderr}")
                raise Exception(f"오디오 병합 실패: {result.stderr}")
            
            if progress_callback:
                progress_callback(90, "품질 최적화 중...")
            
            # 출력 파일이 너무 큰 경우 재인코딩
            if os.path.exists(output_path):
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                if file_size_mb > 50:  # 50MB 이상인 경우
                    self.log("파일 크기가 큰 관계로 재인코딩 수행")
                    self._reencode_audio(output_path, output_path + "_temp")
                    if os.path.exists(output_path + "_temp"):
                        os.replace(output_path + "_temp", output_path)
            
            if progress_callback:
                progress_callback(100, "완료!")
            
            self.log(f"병합 완료: {output_path}")
            
            # 결과 정보 반환
            audio_info = self.get_audio_info(output_path)
            
            return {
                'success': True,
                'filename': os.path.basename(output_path),
                'duration': audio_info['duration'],
                'size': os.path.getsize(output_path)
            }
            
        except Exception as e:
            self.log(f"병합 실패: {str(e)}")
            # 임시 파일 정리
            try:
                os.unlink(filelist_path)
            except:
                pass
            raise
    
    def _reencode_audio(self, input_path, output_path):
        """오디오 재인코딩 (품질 최적화)"""
        cmd = [
            FFMPEG_EXE,
            '-i', input_path,
            '-codec:a', 'mp3',
            '-b:a', '320k',
            '-ar', '44100',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            self.log(f"재인코딩 실패: {result.stderr}")
            raise Exception(f"재인코딩 실패: {result.stderr}")
        
        self.log("재인코딩 완료")
        
    def estimate_processing_time(self, file_count, total_duration):
        """
        예상 처리 시간 계산
        
        Args:
            file_count: 파일 개수
            total_duration: 총 재생 시간 (초)
        
        Returns:
            예상 처리 시간 (초)
        """
        # FFmpeg는 빠르므로 재생 시간의 5% + 파일당 1초
        base_time = total_duration * 0.05
        per_file_time = file_count * 1
        return max(base_time + per_file_time, 10)  # 최소 10초