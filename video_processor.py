"""
Music Merger - 동영상 처리 엔진 (MoviePy 기반)
오디오 파일과 이미지를 결합하여 유튜브 업로드용 동영상 생성
"""

import os
import tempfile
from datetime import datetime
from PIL import Image
from moviepy import AudioFileClip, ImageClip

class VideoProcessor:
    """MoviePy 기반 동영상 파일 처리 클래스"""
    
    def __init__(self, console_log=None):
        self.console_log = console_log or print
        
    def log(self, message):
        """로그 메시지 출력"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.console_log(f"[{timestamp}] [VideoProcessor] {message}")
        
    def create_video_from_audio_image(self, audio_path, image_path, output_path, 
                                    video_size=(1920, 1080), fps=30, 
                                    progress_callback=None):
        """
        오디오 파일과 이미지를 결합하여 동영상 생성
        
        Args:
            audio_path: 오디오 파일 경로 (.mp3, .wav 등)
            image_path: 이미지 파일 경로 (.jpg, .png 등)
            output_path: 출력 동영상 파일 경로 (.mp4)
            video_size: 동영상 해상도 (width, height)
            fps: 프레임 레이트
            progress_callback: 진행률 콜백 함수
            
        Returns:
            dict: 생성 결과 정보
        """
        self.log(f"동영상 생성 시작: {os.path.basename(audio_path)} + {os.path.basename(image_path)}")
        
        # 파일 존재 여부 확인
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            
        try:
            if progress_callback:
                progress_callback(10, "오디오 파일 로딩 중...")
                
            # 오디오 클립 로드
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            self.log(f"오디오 길이: {audio_duration:.2f}초")
            
            if progress_callback:
                progress_callback(30, "이미지 처리 중...")
                
            # 이미지 전처리 (크기 조정)
            processed_image_path = self._resize_image(image_path, video_size)
            
            if progress_callback:
                progress_callback(50, "이미지 클립 생성 중...")
                
            # 이미지 클립 생성 (오디오 길이만큼)
            image_clip = ImageClip(processed_image_path, duration=audio_duration)
            image_clip = image_clip.with_fps(fps)
            
            if progress_callback:
                progress_callback(70, "오디오-비디오 결합 중...")
                
            # 오디오와 이미지 결합
            final_clip = image_clip.with_audio(audio_clip)
            
            if progress_callback:
                progress_callback(80, "동영상 파일 생성 중...")
                
            # 동영상 파일로 출력 (유튜브 최적화 설정)
            final_clip.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                preset='medium',  # 품질과 속도 균형
                ffmpeg_params=[
                    '-crf', '23',  # 품질 설정 (낮을수록 고품질)
                    '-movflags', '+faststart'  # 웹 스트리밍 최적화
                ]
            )
            
            # 메모리 정리
            audio_clip.close()
            image_clip.close()
            final_clip.close()
            
            # 임시 이미지 파일 정리 (약간의 지연 후)
            if processed_image_path != image_path:
                try:
                    import time
                    time.sleep(0.5)  # 파일 핸들이 완전히 해제될 때까지 대기
                    os.unlink(processed_image_path)
                except Exception as e:
                    self.log(f"임시 파일 삭제 실패 (무시됨): {str(e)}")
            
            if progress_callback:
                progress_callback(100, "완료!")
                
            # 결과 정보
            output_size = os.path.getsize(output_path)
            self.log(f"동영상 생성 완료: {output_path} ({output_size / (1024*1024):.1f}MB)")
            
            return {
                'success': True,
                'filename': os.path.basename(output_path),
                'duration': audio_duration,
                'size': output_size,
                'resolution': f"{video_size[0]}x{video_size[1]}",
                'fps': fps
            }
            
        except Exception as e:
            self.log(f"동영상 생성 실패: {str(e)}")
            raise
            
    def _resize_image(self, image_path, target_size):
        """이미지 크기 조정 및 최적화"""
        self.log(f"이미지 크기 조정: {target_size}")
        
        try:
            with Image.open(image_path) as img:
                # RGBA를 RGB로 변환 (필요시)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (0, 0, 0))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 비율 유지하면서 크기 조정
                img_ratio = img.width / img.height
                target_ratio = target_size[0] / target_size[1]
                
                if img_ratio > target_ratio:
                    # 이미지가 더 넓음 - 높이 맞춤
                    new_height = target_size[1]
                    new_width = int(new_height * img_ratio)
                else:
                    # 이미지가 더 높음 - 너비 맞춤  
                    new_width = target_size[0]
                    new_height = int(new_width / img_ratio)
                
                # 리사이즈
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 중앙 크롭
                left = (new_width - target_size[0]) // 2
                top = (new_height - target_size[1]) // 2
                right = left + target_size[0]
                bottom = top + target_size[1]
                
                img = img.crop((left, top, right, bottom))
                
                # 임시 파일로 저장
                temp_dir = os.path.dirname(image_path)
                temp_filename = f"temp_resized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                temp_path = os.path.join(temp_dir, temp_filename)
                
                img.save(temp_path, 'JPEG', quality=95, optimize=True)
                
                self.log(f"이미지 처리 완료: {temp_path}")
                return temp_path
                
        except Exception as e:
            self.log(f"이미지 처리 실패: {str(e)}")
            # 원본 이미지 반환
            return image_path
            
    def get_video_presets(self):
        """유튜브 업로드용 동영상 프리셋"""
        return {
            'youtube_hd': {
                'size': (1920, 1080),
                'fps': 30,
                'description': '유튜브 HD (1080p)'
            },
            'youtube_hd_60': {
                'size': (1920, 1080), 
                'fps': 60,
                'description': '유튜브 HD 60fps (1080p)'
            },
            'youtube_standard': {
                'size': (1280, 720),
                'fps': 30,
                'description': '유튜브 표준 (720p)'
            },
            'youtube_mobile': {
                'size': (1280, 720),
                'fps': 30,
                'description': '모바일 최적화 (720p)'
            }
        }
        
    def estimate_processing_time(self, audio_duration):
        """
        예상 처리 시간 계산
        
        Args:
            audio_duration: 오디오 길이 (초)
            
        Returns:
            예상 처리 시간 (초)
        """
        # MoviePy는 실시간의 1.5-2배 정도 소요
        return max(audio_duration * 1.8, 30)  # 최소 30초