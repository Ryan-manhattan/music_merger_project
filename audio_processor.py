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
            
            # duration_str 생성
            minutes = int(estimated_duration // 60)
            seconds = int(estimated_duration % 60)
            duration_str = f"{minutes}:{seconds:02d}"
            
            return {
                'duration': estimated_duration,
                'duration_str': duration_str,
                'format': ext.upper().replace('.', ''),
                'channels': 2,
                'sample_rate': 44100,
                'bitrate': 128000
            }
            
        except Exception as e:
            self.log(f"파일 정보 확인 실패: {str(e)}")
            # 최소한의 기본값 반환
            return {
                'duration': 60.0,
                'duration_str': '1:00',
                'format': 'UNKNOWN',
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
    
    def trim_audio(self, input_path, duration_seconds):
        """
        오디오 파일을 지정된 시간으로 자르기
        
        Args:
            input_path: 입력 파일 경로
            duration_seconds: 자를 시간 (초)
        
        Returns:
            {'success': bool, 'output_path': str, 'filename': str, 'error': str}
        """
        self.log(f"오디오 자르기 시작: {input_path} -> {duration_seconds}초")
        
        try:
            # 출력 파일명 생성
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.dirname(input_path)
            output_filename = f"{base_name}_trimmed_{duration_seconds}s.mp3"
            output_path = os.path.join(output_dir, output_filename)
            
            # FFmpeg 명령어
            cmd = [
                FFMPEG_EXE,
                '-i', input_path,
                '-t', str(duration_seconds),  # 자를 시간
                '-codec:a', 'libmp3lame',
                '-b:a', '320k',
                '-ar', '44100',
                '-y',  # 덮어쓰기
                output_path
            ]
            
            self.log(f"FFmpeg 실행: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1분 타임아웃
            )
            
            if result.returncode != 0:
                error_msg = f"오디오 자르기 실패: {result.stderr}"
                self.log(error_msg)
                return {'success': False, 'error': error_msg}
            
            self.log(f"오디오 자르기 완료: {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'filename': output_filename
            }
            
        except Exception as e:
            error_msg = f"오디오 자르기 중 오류: {str(e)}"
            self.log(error_msg)
            return {'success': False, 'error': error_msg}
    
    def adjust_pitch(self, input_path, pitch_shift_semitones):
        """
        오디오 파일의 키(피치) 조절
        
        Args:
            input_path: 입력 파일 경로
            pitch_shift_semitones: 반음 단위 피치 변경 (-12 ~ +12)
        
        Returns:
            {'success': bool, 'output_path': str, 'filename': str, 'error': str}
        """
        self.log(f"키 조절 시작 (속도 유지): {input_path} -> {pitch_shift_semitones} 반음")
        
        try:
            # 출력 파일명 생성
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.dirname(input_path)
            pitch_str = f"+{pitch_shift_semitones}" if pitch_shift_semitones > 0 else str(pitch_shift_semitones)
            output_filename = f"{base_name}_pitch{pitch_str}.mp3"
            output_path = os.path.join(output_dir, output_filename)
            
            # FFmpeg rubberband 필터 사용 (속도 유지하면서 피치만 변경)
            # rubberband가 없는 경우를 대비해 두 가지 방식 시도
            
            # 방법 1: rubberband 필터 (고품질, 속도 유지)
            if pitch_shift_semitones != 0:
                # 피치 변경 비율 계산: 2^(semitones/12)
                pitch_ratio = 2 ** (pitch_shift_semitones / 12.0)
                
                # 먼저 rubberband 필터로 시도
                cmd_rubberband = [
                    FFMPEG_EXE,
                    '-i', input_path,
                    '-filter:a', f'rubberband=pitch={pitch_ratio}',
                    '-codec:a', 'libmp3lame',
                    '-b:a', '320k',
                    '-y',  # 덮어쓰기
                    output_path
                ]
                
                # rubberband 시도
                try:
                    result_rubberband = subprocess.run(
                        cmd_rubberband,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    if result_rubberband.returncode == 0:
                        self.log("rubberband 필터로 키 조절 성공 (속도 유지)")
                        cmd = cmd_rubberband
                    else:
                        raise Exception("rubberband 필터 실패")
                        
                except Exception as e:
                    self.log(f"rubberband 필터 실패, atempo+asetrate 방식 사용: {str(e)}")
                    
                    # 방법 2: asetrate + atempo (속도 보정)
                    # atempo 필터는 0.5~2.0 범위만 지원하므로 여러 단계로 나누어 처리
                    tempo_correction = 1 / pitch_ratio  # 속도 보정 비율
                    
                    # atempo 체인 생성 (0.5~2.0 범위로 제한)
                    atempo_filters = []
                    remaining_tempo = tempo_correction
                    
                    self.log(f"속도 보정 비율: {tempo_correction:.4f}")
                    
                    while remaining_tempo < 0.5:
                        atempo_filters.append("atempo=0.5")
                        remaining_tempo /= 0.5
                    
                    while remaining_tempo > 2.0:
                        atempo_filters.append("atempo=2.0")
                        remaining_tempo /= 2.0
                    
                    if abs(remaining_tempo - 1.0) > 0.001:  # 부동소수점 오차 고려
                        atempo_filters.append(f"atempo={remaining_tempo:.6f}")
                    
                    # 필터 체인 구성
                    if atempo_filters:
                        filter_chain = f'asetrate=44100*{pitch_ratio:.6f},aresample=44100,{",".join(atempo_filters)}'
                        self.log(f"atempo 필터 체인: {atempo_filters}")
                    else:
                        filter_chain = f'asetrate=44100*{pitch_ratio:.6f},aresample=44100'
                    
                    cmd = [
                        FFMPEG_EXE,
                        '-i', input_path,
                        '-filter:a', filter_chain,
                        '-codec:a', 'libmp3lame',
                        '-b:a', '320k',
                        '-y',  # 덮어쓰기
                        output_path
                    ]
            else:
                # 피치 변경 없음 - 단순 복사
                cmd = [
                    FFMPEG_EXE,
                    '-i', input_path,
                    '-codec:a', 'libmp3lame',
                    '-b:a', '320k',
                    '-y',
                    output_path
                ]
            
            self.log(f"FFmpeg 실행: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2분 타임아웃
            )
            
            if result.returncode != 0:
                error_msg = f"키 조절 실패: {result.stderr}"
                self.log(error_msg)
                return {'success': False, 'error': error_msg}
            
            self.log(f"키 조절 완료: {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'filename': output_filename
            }
            
        except Exception as e:
            error_msg = f"키 조절 중 오류: {str(e)}"
            self.log(error_msg)
            return {'success': False, 'error': error_msg}
    
    def convert_to_mp3(self, input_path):
        """
        오디오 파일을 MP3로 변환
        
        Args:
            input_path: 입력 파일 경로
        
        Returns:
            {'success': bool, 'output_path': str, 'filename': str, 'error': str}
        """
        self.log(f"MP3 변환 시작: {input_path}")
        
        try:
            # 출력 파일명 생성
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.dirname(input_path)
            output_filename = f"{base_name}.mp3"
            output_path = os.path.join(output_dir, output_filename)
            
            # 이미 MP3인 경우 원본 반환
            if input_path.lower().endswith('.mp3'):
                return {
                    'success': True,
                    'output_path': input_path,
                    'filename': os.path.basename(input_path)
                }
            
            # FFmpeg 명령어
            cmd = [
                FFMPEG_EXE,
                '-i', input_path,
                '-codec:a', 'libmp3lame',
                '-b:a', '320k',
                '-ar', '44100',
                '-y',  # 덮어쓰기
                output_path
            ]
            
            self.log(f"FFmpeg 실행: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2분 타임아웃
            )
            
            if result.returncode != 0:
                error_msg = f"MP3 변환 실패: {result.stderr}"
                self.log(error_msg)
                return {'success': False, 'error': error_msg}
            
            self.log(f"MP3 변환 완료: {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'filename': output_filename
            }
            
        except Exception as e:
            error_msg = f"MP3 변환 중 오류: {str(e)}"
            self.log(error_msg)
            return {'success': False, 'error': error_msg}