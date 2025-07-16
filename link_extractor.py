#!/usr/bin/env python3
"""
Link Extractor - YouTube/음악 링크에서 오디오 추출
yt-dlp를 사용한 오디오 다운로드 및 변환
"""

import os
import yt_dlp
import tempfile
from datetime import datetime
from utils import generate_safe_filename, validate_audio_file, get_file_size_mb

class LinkExtractor:
    def __init__(self, console_log=None):
        self.console_log = console_log or print
        
    def extract_audio(self, url, output_folder, progress_callback=None):
        """URL에서 오디오 추출"""
        try:
            # 임시 다운로드 폴더 생성 (cleanup 함수의 영향을 받지 않도록)
            temp_download_folder = os.path.join(os.path.dirname(output_folder), 'temp_downloads')
            os.makedirs(temp_download_folder, exist_ok=True)
            self.console_log(f"[Extract] 임시 다운로드 폴더: {temp_download_folder}")
            # 진행률 콜백
            def progress_hook(d):
                if progress_callback and d['status'] == 'downloading':
                    if 'total_bytes' in d:
                        percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        progress_callback(int(percent), f"다운로드 중... {percent:.1f}%")
                    
            # 안전한 파일명 생성  
            safe_filename = f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # yt-dlp 설정 (임시 폴더에 다운로드)
            ydl_opts = {
                'format': 'worst[ext=mp4]/worst',
                'outtmpl': os.path.join(temp_download_folder, f'{safe_filename}_%(title)s.%(ext)s'),
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
            
            self.console_log(f"[Extract] 임시 다운로드 폴더: {temp_download_folder}")
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
            
            # 임시 폴더에서 다운로드된 파일 찾기
            self.console_log(f"[Extract] 임시 폴더 확인: {temp_download_folder}")
            self.console_log(f"[Extract] 임시 폴더 내 파일 목록:")
            
            downloaded_files = []
            all_files = os.listdir(temp_download_folder)
            
            # 파일명 패턴으로 찾기 (youtube_로 시작하는 파일)
            pattern_files = [f for f in all_files if f.startswith(safe_filename)]
            self.console_log(f"[Extract] 패턴 매칭 파일 ({safe_filename}*): {pattern_files}")
            
            # 패턴 매칭 파일이 있으면 우선 선택
            if pattern_files:
                for filename in pattern_files:
                    if filename.endswith(('.mp3', '.m4a', '.mp4', '.webm')):
                        file_path = os.path.join(temp_download_folder, filename)
                        downloaded_files.append(file_path)
                        self.console_log(f"    [O] 패턴 매칭 파일 선택: {file_path}")
            else:
                # 패턴 매칭 실패 시 최근 생성된 파일 찾기
                self.console_log("[Extract] 패턴 매칭 실패, 최근 파일 검색")
                for filename in all_files:
                    self.console_log(f"  - {filename}")
                    if filename.endswith(('.mp3', '.m4a', '.mp4', '.webm')):
                        file_path = os.path.join(temp_download_folder, filename)
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
            
            # 파일을 최종 목적지로 이동
            import shutil
            final_filename = os.path.basename(latest_file)
            safe_filepath = os.path.join(output_folder, final_filename)
            
            self.console_log(f"[Extract] 파일 이동: {latest_file} -> {safe_filepath}")
            shutil.move(latest_file, safe_filepath)
            
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