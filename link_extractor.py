#!/usr/bin/env python3
"""
Link Extractor - YouTube/음악 링크에서 오디오 추출
yt-dlp를 사용한 오디오 다운로드 및 변환
"""

import os
import yt_dlp
import tempfile
import subprocess
from datetime import datetime
from utils import generate_safe_filename, validate_audio_file, get_file_size_mb

class LinkExtractor:
    def __init__(self, console_log=None):
        self.console_log = console_log or print
        # FFmpeg 경로 설정
        ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg-master-latest-win64-gpl', 'bin')
        self.ffmpeg_exe = os.path.join(ffmpeg_path, 'ffmpeg.exe') if os.path.exists(ffmpeg_path) else 'ffmpeg'
        
    def extract_audio(self, url, output_folder, progress_callback=None):
        """URL에서 오디오 추출"""
        try:
            # 다운로드를 output_folder에 직접 저장 (temp 폴더 사용 안함)
            download_folder = output_folder
            self.console_log(f"[Extract] 다운로드 폴더: {download_folder}")
            
            # 먼저 비디오 정보를 가져와서 기존 파일 확인
            if progress_callback:
                progress_callback(5, "비디오 정보 확인 중...")
            
            video_info = self.get_video_info(url)
            if video_info['success']:
                title = video_info['title']
                # 안전한 파일명 생성 (제목 기반)
                import re
                safe_title = re.sub(r'[^\w\s-]', '', title).strip()
                safe_title = re.sub(r'[-\s]+', '_', safe_title)[:50]
                
                # 기존 파일 확인 (제목으로 검색)
                self.console_log(f"[Extract] 기존 파일 확인 중... 제목: {title}")
                existing_files = []
                
                # 폴더의 모든 파일 확인 (원본 파일만)
                for filename in os.listdir(download_folder):
                    if filename.endswith(('.mp4', '.webm', '.m4a', '.mp3')):
                        # 가공된 파일은 제외 (30초 자른 파일, 키 조절된 파일)
                        if ('_30s.' in filename or '_plus' in filename or '_minus' in filename):
                            self.console_log(f"[Extract] 가공된 파일 제외: {filename}")
                            continue
                            
                        # 파일명에서 제목 부분 추출하여 비교
                        name_without_ext = os.path.splitext(filename)[0]
                        if safe_title in name_without_ext or name_without_ext in safe_title:
                            file_path = os.path.join(download_folder, filename)
                            existing_files.append(file_path)
                            self.console_log(f"[Extract] 제목 매칭 파일 발견: {filename}")
                
                # 가장 최근 파일 선택
                if existing_files:
                    latest_file = max(existing_files, key=os.path.getctime)
                    self.console_log(f"[Extract] 기존 파일 재사용: {latest_file}")
                    
                    # 기존 파일 정보 반환
                    file_info = {
                        'filename': os.path.basename(latest_file),
                        'original_name': title,
                        'size': os.path.getsize(latest_file),
                        'size_mb': get_file_size_mb(latest_file),
                        'duration': video_info.get('duration', 0),
                        'duration_str': self._format_duration(video_info.get('duration', 0)),
                        'format': os.path.splitext(latest_file)[1].upper().replace('.', ''),
                        'path': latest_file,
                        'source': 'link_extract'
                    }
                    
                    if progress_callback:
                        progress_callback(100, "기존 파일 사용!")
                    
                    return {
                        'success': True,
                        'file_info': file_info,
                        'message': '기존 파일을 재사용했습니다'
                    }
                
                # 새 파일명 생성
                safe_filename = f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_title}"
            else:
                # 비디오 정보 가져오기 실패 시 기본 파일명 사용
                safe_filename = f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 진행률 콜백
            def progress_hook(d):
                if progress_callback and d['status'] == 'downloading':
                    if 'total_bytes' in d:
                        percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        progress_callback(int(percent), f"다운로드 중... {percent:.1f}%")
            
            # yt-dlp 설정 (output_folder에 직접 다운로드)
            ydl_opts = {
                'format': 'worst[ext=mp4]/worst',
                'outtmpl': os.path.join(download_folder, f'{safe_filename}_%(title)s.%(ext)s'),
                'noplaylist': True,
                'progress_hooks': [progress_hook],
                'keepvideo': True,  # 파일 유지
                'writethumbnail': False,  # 썸네일 다운로드 안함
                'writeinfojson': False,  # JSON 정보 파일 생성 안함
                'no_post_overwrites': True,  # 파일 덮어쓰기 방지
                'cookiefile': None,  # 쿠키 파일 사용 안함
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            }
            
            self.console_log(f"[Extract] 다운로드 폴더: {download_folder}")
            self.console_log(f"[Extract] 최종 저장 폴더: {output_folder}")
            self.console_log(f"[Extract] 파일명 패턴: {safe_filename}_%(title)s.%(ext)s")
            
            
            # 임시 제목 설정 (나중에 파일명에서 추출)
            title = f"YouTube_Video_{datetime.now().strftime('%H%M%S')}"
            duration = 0
            
            self.console_log(f"[Extract] 바로 다운로드 진행 (제목은 파일명에서 추출 예정)")
            
            # 진행률 업데이트
            if progress_callback:
                progress_callback(10, "다운로드 준비 중...")
            
            # 다운로드 시도
            self.console_log("[Extract] yt-dlp 다운로드 시작...")
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    self.console_log(f"[Extract] 다운로드 URL: {url}")
                    self.console_log(f"[Extract] 출력 경로: {ydl_opts['outtmpl']}")
                    ydl.download([url])
                    self.console_log("[Extract] yt-dlp 다운로드 완료")
            except Exception as e:
                self.console_log(f"[Extract] 다운로드 오류: {str(e)}")
                return {'success': False, 'error': f'다운로드 실패: {str(e)}'}
            
            # 파일 시스템 동기화를 위한 잠시 대기
            import time
            time.sleep(1)
            
            # 다운로드 폴더에서 다운로드된 파일 찾기
            self.console_log(f"[Extract] 다운로드 폴더 확인: {download_folder}")
            self.console_log(f"[Extract] 다운로드 폴더 내 파일 목록:")
            
            downloaded_files = []
            all_files = os.listdir(download_folder)
            
            # 파일명 패턴으로 찾기 (youtube_로 시작하는 파일)
            pattern_files = [f for f in all_files if f.startswith(safe_filename)]
            self.console_log(f"[Extract] 패턴 매칭 파일 ({safe_filename}*): {pattern_files}")
            
            # 패턴 매칭 파일이 있으면 우선 선택
            if pattern_files:
                for filename in pattern_files:
                    if filename.endswith(('.mp3', '.m4a', '.mp4', '.webm')):
                        file_path = os.path.join(download_folder, filename)
                        downloaded_files.append(file_path)
                        self.console_log(f"    [O] 패턴 매칭 파일 선택: {file_path}")
            else:
                # 패턴 매칭 실패 시 최근 생성된 파일 찾기
                self.console_log("[Extract] 패턴 매칭 실패, 최근 파일 검색")
                for filename in all_files:
                    self.console_log(f"  - {filename}")
                    if filename.endswith(('.mp3', '.m4a', '.mp4', '.webm')):
                        file_path = os.path.join(download_folder, filename)
                        file_time = os.path.getctime(file_path)
                        time_diff = datetime.now().timestamp() - file_time
                        self.console_log(f"    파일 시간 차이: {time_diff}초")
                        if time_diff < 60:  # 1분 이내로 단축
                            downloaded_files.append(file_path)
                            self.console_log(f"    [O] 최근 파일로 선택: {file_path}")
            
            self.console_log(f"[Extract] 총 {len(downloaded_files)}개 파일 발견")
            
            if not downloaded_files:
                return {'success': False, 'error': 'yt-dlp 다운로드가 완료되지 않았습니다. 네트워크나 URL을 확인해주세요.'}
            
            # 가장 최근 파일 선택
            latest_file = max(downloaded_files, key=os.path.getctime)
            
            # 진행률 업데이트
            if progress_callback:
                progress_callback(90, "파일 검증 중...")
            
            # 오디오 파일 검증
            validation = validate_audio_file(latest_file)
            if not validation['valid']:
                self.console_log(f"[Extract] 검증 실패하지만 파일 유지: {validation['error']}")
                # MP4 파일도 사용할 수 있도록 파일 삭제하지 않음
                # return {'success': False, 'error': f'다운로드된 파일 검증 실패: {validation["error"]}'}
                
                # 기본 정보로 처리
                file_size = os.path.getsize(latest_file)
                estimated_duration = max(file_size / (1024 * 1024) * 60, 30)
                
                validation = {
                    'valid': True,
                    'info': {
                        'duration': estimated_duration,
                        'duration_str': self._format_duration(estimated_duration),
                        'format': 'MP4'
                    }
                }
            
            # 파일이 이미 목적지에 있으므로 이동 불필요
            safe_filepath = latest_file
            safe_filename = os.path.basename(safe_filepath)
            self.console_log(f"[Extract] 최종 파일 경로: {safe_filepath}")
            self.console_log(f"[Extract] 최종 파일명: {safe_filename}")
            

            # 진행률 완료
            if progress_callback:
                progress_callback(100, "추출 완료!")
            
            # 다운로드된 파일명에서 제목 추출 시도
            original_filename = os.path.basename(latest_file)
            name_without_ext = os.path.splitext(original_filename)[0]
            
            self.console_log(f"[Extract] 원본 파일명: {original_filename}")
            self.console_log(f"[Extract] 확장자 제거: {name_without_ext}")
            
            # youtube_날짜시간_ 패턴 제거하여 실제 제목 추출
            if name_without_ext.startswith('youtube_') and '_' in name_without_ext:
                # youtube_20241216_095923_Something in the Way 형태에서 제목 부분만 추출
                parts = name_without_ext.split('_', 3)  # 최대 3번 분할
                if len(parts) >= 4:
                    # 4번째 부분이 실제 제목
                    title = parts[3].replace('_', ' ').strip()
                    self.console_log(f"[Extract] 패턴 매칭으로 추출한 제목: {title}")
                else:
                    # 패턴이 맞지 않으면 전체를 제목으로 사용
                    title = name_without_ext.replace('_', ' ').strip()
                    self.console_log(f"[Extract] 전체 파일명을 제목으로 사용: {title}")
            else:
                # youtube_ 패턴이 아니면 전체를 제목으로 사용
                title = name_without_ext.replace('_', ' ').strip()
                self.console_log(f"[Extract] 일반 파일명에서 제목 추출: {title}")
            
            # 제목 길이 제한 및 정리
            if len(title) > 60:
                title = title[:60] + '...'
            elif len(title) < 3:
                title = f"음악_{datetime.now().strftime('%H%M%S')}"
                
            self.console_log(f"[Extract] 최종 제목: {title}")
            
            # 파일 정보 반환
            file_info = {
                'filename': safe_filename,
                'original_name': title,
                'size': os.path.getsize(safe_filepath),
                'size_mb': get_file_size_mb(safe_filepath),
                'duration': validation['info']['duration'],
                'duration_str': validation['info']['duration_str'],
                'format': validation['info']['format'],
                'path': safe_filepath,
                'source': 'link_extract'
            }
            
            self.console_log(f"[Extract] 성공: {safe_filename}")
            
            return {
                'success': True,
                'file_info': file_info,
                'message': '링크에서 음악을 성공적으로 추출했습니다'
            }
            
        except Exception as e:
            self.console_log(f"[Extract] 오류: {str(e)}")
            return {'success': False, 'error': f'추출 중 오류 발생: {str(e)}'}
    
    def get_video_info(self, url):
        """링크에서 비디오 정보만 가져오기"""
        try:
            ydl_opts = {
                'quiet': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'success': True,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'thumbnail': info.get('thumbnail', '')
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _format_duration(self, seconds):
        """초를 mm:ss 형식으로 변환"""
        if seconds < 0:
            return "00:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _trim_audio_to_30_seconds(self, input_path, output_folder):
        """오디오 파일의 앞에서 30초만 자르기"""
        try:
            input_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(output_folder, f"{input_name}_30s.mp3")
            
            # 기존 파일이 있는지 확인
            if os.path.exists(output_path):
                self.console_log(f"[Trim] 기존 30초 파일 재사용: {output_path}")
                return output_path
            
            self.console_log(f"[Trim] 30초 자르기 시작: {input_path}")
            self.console_log(f"[Trim] 출력 경로: {output_path}")
            
            # FFmpeg 명령어로 앞에서 30초 자르기
            cmd = [
                self.ffmpeg_exe,
                '-i', input_path,
                '-t', '30',  # 앞에서 30초만
                '-acodec', 'libmp3lame',
                '-ab', '192k',
                '-y',  # 덮어쓰기 허용
                output_path
            ]
            
            self.console_log(f"[Trim] FFmpeg 명령어: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                self.console_log(f"[Trim] 30초 자르기 성공: {output_path}")
                return output_path
            else:
                self.console_log(f"[Trim] FFmpeg 오류: {result.stderr}")
                return None
                
        except Exception as e:
            self.console_log(f"[Trim] 30초 자르기 실패: {str(e)}")
            return None
    
    def adjust_pitch(self, input_path, output_folder, semitones=0):
        """음성 키 조절 (반음 단위)"""
        try:
            if semitones == 0:
                return input_path  # 키 조절이 필요없으면 원본 반환
                
            input_name = os.path.splitext(os.path.basename(input_path))[0]
            pitch_str = f"plus{semitones}" if semitones > 0 else f"minus{abs(semitones)}"
            output_path = os.path.join(output_folder, f"{input_name}_{pitch_str}.mp3")
            
            # 기존 파일이 있는지 확인
            if os.path.exists(output_path):
                self.console_log(f"[Pitch] 기존 키 조절 파일 재사용: {output_path}")
                return output_path
            
            self.console_log(f"[Pitch] 키 조절 시작: {input_path}")
            self.console_log(f"[Pitch] 반음 조절: {semitones}")
            self.console_log(f"[Pitch] 출력 경로: {output_path}")
            
            # 반음을 주파수 비율로 변환 (2^(semitones/12))
            pitch_ratio = 2 ** (semitones / 12.0)
            
            # FFmpeg 명령어로 키 조절 (pitch shift)
            cmd = [
                self.ffmpeg_exe,
                '-i', input_path,
                '-filter:a', f'asetrate=44100*{pitch_ratio},aresample=44100',
                '-acodec', 'libmp3lame',
                '-ab', '192k',
                '-y',  # 덮어쓰기 허용
                output_path
            ]
            
            self.console_log(f"[Pitch] FFmpeg 명령어: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and os.path.exists(output_path):
                self.console_log(f"[Pitch] 키 조절 성공: {output_path}")
                return output_path
            else:
                self.console_log(f"[Pitch] FFmpeg 오류: {result.stderr}")
                return None
                
        except Exception as e:
            self.console_log(f"[Pitch] 키 조절 실패: {str(e)}")
            return None
    
    def convert_to_mp3(self, input_path, output_folder):
        """오디오 파일을 MP3로 변환"""
        try:
            # 디버깅: 상세 입력 정보
            self.console_log(f"[Convert-Debug] ====== MP3 변환 시작 ======")
            self.console_log(f"[Convert-Debug] 입력 파일: {input_path}")
            self.console_log(f"[Convert-Debug] 출력 폴더: {output_folder}")
            self.console_log(f"[Convert-Debug] FFmpeg 경로: {self.ffmpeg_exe}")
            
            # 입력 파일 검증
            if not os.path.exists(input_path):
                self.console_log(f"[Convert-Error] 입력 파일이 존재하지 않음: {input_path}")
                return None
            
            input_size = os.path.getsize(input_path)
            if input_size == 0:
                self.console_log(f"[Convert-Error] 입력 파일이 비어있음: {input_path}")
                return None
            
            # 파일 정보 상세 로깅
            import time
            file_mtime = os.path.getmtime(input_path)
            file_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_mtime))
            self.console_log(f"[Convert-Debug] 파일 크기: {input_size:,} bytes ({input_size/1024/1024:.2f} MB)")
            self.console_log(f"[Convert-Debug] 파일 수정 시간: {file_time}")
            
            input_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(output_folder, f"{input_name}.mp3")
            
            # 출력 폴더 확인
            if not os.path.exists(output_folder):
                self.console_log(f"[Convert-Debug] 출력 폴더 생성: {output_folder}")
                os.makedirs(output_folder, exist_ok=True)
            
            # 이미 변환된 파일 확인
            if os.path.exists(output_path):
                existing_size = os.path.getsize(output_path)
                self.console_log(f"[Convert-Debug] 기존 MP3 파일 발견: {output_path} ({existing_size} bytes)")
                if existing_size > 0:
                    self.console_log(f"[Convert] 기존 MP3 파일 재사용: {output_path}")
                    return output_path
                else:
                    self.console_log(f"[Convert-Debug] 기존 파일이 비어있어 재변환")
            
            # 이미 MP3인 경우 원본 반환
            if input_path.lower().endswith('.mp3'):
                self.console_log(f"[Convert] 이미 MP3 파일: {input_path}")
                return input_path
            
            self.console_log(f"[Convert] MP3 변환 시작: {input_path} ({input_size} bytes)")
            self.console_log(f"[Convert] 출력 경로: {output_path}")
            
            # FFmpeg 존재 여부 확인
            try:
                ffmpeg_check = subprocess.run([self.ffmpeg_exe, '-version'], 
                                            capture_output=True, text=True, timeout=10)
                if ffmpeg_check.returncode == 0:
                    self.console_log(f"[Convert-Debug] FFmpeg 사용 가능")
                    # FFmpeg 버전 정보 첫 줄만 출력
                    version_line = ffmpeg_check.stdout.split('\n')[0] if ffmpeg_check.stdout else "버전 정보 없음"
                    self.console_log(f"[Convert-Debug] FFmpeg 버전: {version_line}")
                else:
                    self.console_log(f"[Convert-Error] FFmpeg 실행 실패 (return code: {ffmpeg_check.returncode})")
                    return None
            except Exception as e:
                self.console_log(f"[Convert-Error] FFmpeg 확인 실패: {str(e)}")
                return None
            
            # FFmpeg 명령어로 MP3 변환 (더 안전한 옵션)
            cmd = [
                self.ffmpeg_exe,
                '-i', input_path,
                '-vn',  # 비디오 스트림 무시 (오디오만)
                '-acodec', 'libmp3lame',
                '-b:a', '192k',  # 비트레이트
                '-ar', '44100',  # 샘플레이트
                '-ac', '2',      # 스테레오
                '-f', 'mp3',     # 출력 포맷 명시
                '-y',            # 덮어쓰기 허용
                output_path
            ]
            
            self.console_log(f"[Convert-Debug] FFmpeg 명령어: {' '.join(cmd)}")
            
            # FFmpeg 실행 시간 측정
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            end_time = time.time()
            conversion_time = end_time - start_time
            
            self.console_log(f"[Convert-Debug] 변환 소요 시간: {conversion_time:.2f}초")
            self.console_log(f"[Convert-Debug] FFmpeg return code: {result.returncode}")
            
            # FFmpeg 출력 분석
            if result.stdout:
                stdout_lines = result.stdout.strip().split('\n')
                self.console_log(f"[Convert-Debug] FFmpeg stdout 줄 수: {len(stdout_lines)}")
                # 중요한 정보만 출력 (마지막 몇 줄)
                for line in stdout_lines[-3:]:
                    if line.strip():
                        self.console_log(f"[Convert-Stdout] {line.strip()}")
            
            if result.stderr:
                stderr_lines = result.stderr.strip().split('\n')
                self.console_log(f"[Convert-Debug] FFmpeg stderr 줄 수: {len(stderr_lines)}")
                # 오류와 경고만 출력
                for line in stderr_lines:
                    if any(keyword in line.lower() for keyword in ['error', 'failed', 'warning']):
                        self.console_log(f"[Convert-Stderr] {line.strip()}")
            
            # 결과 검증
            if result.returncode == 0 and os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                self.console_log(f"[Convert-Debug] 출력 파일 크기: {output_size:,} bytes ({output_size/1024/1024:.2f} MB)")
                
                if output_size > 0:
                    # 압축률 계산
                    compression_ratio = (input_size - output_size) / input_size * 100
                    self.console_log(f"[Convert-Debug] 압축률: {compression_ratio:.1f}%")
                    self.console_log(f"[Convert] MP3 변환 성공: {output_path} ({output_size} bytes)")
                    return output_path
                else:
                    self.console_log(f"[Convert-Error] 변환된 파일이 비어있음: {output_path}")
                    # 빈 파일 삭제
                    try:
                        os.remove(output_path)
                        self.console_log(f"[Convert-Debug] 빈 파일 삭제됨")
                    except:
                        pass
                    return None
            else:
                self.console_log(f"[Convert-Error] FFmpeg 변환 실패 (return code: {result.returncode})")
                if not os.path.exists(output_path):
                    self.console_log(f"[Convert-Error] 출력 파일이 생성되지 않음: {output_path}")
                return None
                
        except subprocess.TimeoutExpired:
            self.console_log(f"[Convert-Error] FFmpeg 변환 시간 초과 (180초)")
            return None
        except Exception as e:
            self.console_log(f"[Convert-Error] MP3 변환 실패: {str(e)}")
            import traceback
            self.console_log(f"[Convert-Error] 상세 오류: {traceback.format_exc()}")
            return None
        finally:
            self.console_log(f"[Convert-Debug] ====== MP3 변환 종료 ======")