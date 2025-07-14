"""
Music Merger - 오디오 처리 엔진
"""

from pydub import AudioSegment
from pydub.effects import normalize
from pydub.utils import which
import os
import numpy as np
from datetime import datetime

# FFmpeg 경로 설정
ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg-master-latest-win64-gpl', 'bin')
if os.path.exists(ffmpeg_path):
    AudioSegment.converter = os.path.join(ffmpeg_path, 'ffmpeg.exe')
    AudioSegment.ffmpeg = os.path.join(ffmpeg_path, 'ffmpeg.exe')
    AudioSegment.ffprobe = os.path.join(ffmpeg_path, 'ffprobe.exe')

class AudioProcessor:
    """오디오 파일 처리 클래스"""
    
    def __init__(self, console_log=None):
        self.console_log = console_log or print
        
    def log(self, message):
        """로그 메시지 출력"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.console_log(f"[{timestamp}] [AudioProcessor] {message}")
        
    def load_audio(self, filepath):
        """오디오 파일 로드"""
        self.log(f"파일 로드 중: {filepath}")
        
        # 파일 존재 확인
        self.log(f"파일 경로 확인: {repr(filepath)}")
        self.log(f"경로 타입: {type(filepath)}")
        self.log(f"파일 존재 여부: {os.path.exists(filepath)}")
        
        if not os.path.exists(filepath):
            # 상위 폴더 확인
            parent_dir = os.path.dirname(filepath)
            self.log(f"상위 폴더: {parent_dir}")
            self.log(f"상위 폴더 존재: {os.path.exists(parent_dir)}")
            if os.path.exists(parent_dir):
                self.log(f"폴더 내 파일들: {os.listdir(parent_dir)[:5]}")  # 첫 5개만
            
            self.log(f"파일이 존재하지 않습니다: {filepath}")
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")
        
        # 파일 크기 확인
        file_size = os.path.getsize(filepath)
        self.log(f"파일 크기: {file_size} bytes")
        
        try:
            # Windows 한글 경로 문제 해결을 위한 처리
            filepath = os.path.abspath(filepath)
            
            # MP3 파일인 경우 FFmpeg 없이 처리 시도
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.mp3':
                try:
                    # MP3은 pydub이 기본적으로 지원
                    audio = AudioSegment.from_mp3(filepath)
                    self.log(f"MP3 로드 완료: {len(audio)}ms")
                    return audio
                except Exception as mp3_error:
                    self.log(f"MP3 로드 실패: {str(mp3_error)}")
                    # 일반 방법으로 재시도
            
            audio = AudioSegment.from_file(filepath)
            self.log(f"로드 완료: {len(audio)}ms")
            return audio
        except Exception as e:
            self.log(f"로드 실패: {str(e)}")
            self.log(f"시도한 경로: {repr(filepath)}")
            raise
            
    def apply_fade_in(self, audio, duration_ms):
        """페이드인 효과 적용"""
        if duration_ms <= 0:
            return audio
        self.log(f"페이드인 적용: {duration_ms}ms")
        return audio.fade_in(duration_ms)
        
    def apply_fade_out(self, audio, duration_ms):
        """페이드아웃 효과 적용"""
        if duration_ms <= 0:
            return audio
        self.log(f"페이드아웃 적용: {duration_ms}ms")
        return audio.fade_out(duration_ms)
        
    def adjust_volume(self, audio, db_change):
        """볼륨 조절"""
        if db_change == 0:
            return audio
        self.log(f"볼륨 조절: {db_change:+}dB")
        return audio + db_change
        
    def add_silence(self, duration_ms):
        """무음 구간 생성"""
        if duration_ms <= 0:
            return AudioSegment.empty()
        self.log(f"무음 추가: {duration_ms}ms")
        return AudioSegment.silent(duration=duration_ms)
        
    def process_single_file(self, filepath, settings):
        """
        단일 파일 처리
        
        Args:
            filepath: 오디오 파일 경로
            settings: {
                'fadeIn': 페이드인 시간 (초),
                'fadeOut': 페이드아웃 시간 (초),
                'volume': 볼륨 조절 (dB),
                'gap': 뒤에 추가할 무음 시간 (초)
            }
        """
        self.log(f"파일 처리 시작: {os.path.basename(filepath)}")
        
        # 오디오 로드
        audio = self.load_audio(filepath)
        
        # 페이드인 적용
        fade_in_ms = int(settings.get('fadeIn', 0) * 1000)
        audio = self.apply_fade_in(audio, fade_in_ms)
        
        # 페이드아웃 적용
        fade_out_ms = int(settings.get('fadeOut', 0) * 1000)
        audio = self.apply_fade_out(audio, fade_out_ms)
        
        # 볼륨 조절
        volume_db = settings.get('volume', 0)
        audio = self.adjust_volume(audio, volume_db)
        
        # 무음 추가
        gap_ms = int(settings.get('gap', 0) * 1000)
        silence = self.add_silence(gap_ms)
        
        # 오디오와 무음 결합
        if len(silence) > 0:
            audio = audio + silence
            
        self.log(f"파일 처리 완료: {len(audio)}ms")
        return audio
        
    def merge_audio_files(self, file_list, global_settings, output_path, progress_callback=None):
        """
        여러 오디오 파일 병합
        
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
        
        # 결과 오디오 초기화
        merged_audio = AudioSegment.empty()
        total_files = len(file_list)
        
        # 각 파일 처리 및 병합
        for idx, file_info in enumerate(file_list):
            filename = file_info['filename']
            settings = file_info['settings']
            
            # 진행률 업데이트
            if progress_callback:
                progress = int((idx / total_files) * 80)  # 80%까지는 개별 파일 처리
                progress_callback(progress, f"처리 중: {filename}")
            
            # 파일 처리
            processed_audio = self.process_single_file(filename, settings)
            
            # 크로스페이드 적용
            if global_settings.get('crossfade') and idx > 0 and len(merged_audio) > 0:
                # 이전 오디오의 마지막 1초와 현재 오디오의 첫 1초를 크로스페이드
                crossfade_duration = 1000  # 1초
                merged_audio = merged_audio.append(processed_audio, crossfade=crossfade_duration)
                self.log(f"크로스페이드 적용: {crossfade_duration}ms")
            else:
                # 단순 연결
                merged_audio = merged_audio + processed_audio
            
            self.log(f"병합 진행: {idx+1}/{total_files}")
        
        # 볼륨 정규화
        if global_settings.get('normalizeVolume'):
            if progress_callback:
                progress_callback(90, "볼륨 정규화 중...")
            self.log("볼륨 정규화 적용")
            merged_audio = normalize(merged_audio)
        
        # 파일 저장
        if progress_callback:
            progress_callback(95, "파일 저장 중...")
        
        self.log(f"파일 저장: {output_path}")
        output_format = os.path.splitext(output_path)[1][1:] or 'mp3'
        
        # 출력 파라미터 설정
        export_params = {
            'format': output_format,
            'bitrate': '192k',
            'parameters': ['-q:a', '0']  # 최고 품질
        }
        
        merged_audio.export(output_path, **export_params)
        
        if progress_callback:
            progress_callback(100, "완료!")
        
        self.log(f"병합 완료: {output_path}")
        
        # 결과 정보 반환
        return {
            'success': True,
            'filename': os.path.basename(output_path),
            'duration': len(merged_audio) / 1000.0,
            'size': os.path.getsize(output_path)
        }
        
    def estimate_processing_time(self, file_count, total_duration):
        """
        예상 처리 시간 계산
        
        Args:
            file_count: 파일 개수
            total_duration: 총 재생 시간 (초)
        
        Returns:
            예상 처리 시간 (초)
        """
        # 대략적인 예상: 재생 시간의 10% + 파일당 2초
        base_time = total_duration * 0.1
        per_file_time = file_count * 2
        return base_time + per_file_time
