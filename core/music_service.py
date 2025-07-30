#!/usr/bin/env python3
"""
Music Service - 음악 분석 및 AI 생성 통합 서비스
YouTube 분석 → Lyria AI 생성 전체 워크플로우
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

from analyzers.music_analyzer import MusicAnalyzer
from connectors.lyria_client import LyriaClient
#from prompt_generator import PromptGenerator

# 환경 변수 로드
load_dotenv()

class MusicService:
    def __init__(self, console_log=None):
        """
        음악 서비스 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        
        # 환경 변수에서 API 키 및 설정 로드
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.google_project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        self.google_location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        self.service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # 기본 설정
        self.default_duration = int(os.getenv('DEFAULT_MUSIC_DURATION', '30'))
        self.max_duration = int(os.getenv('MAX_MUSIC_DURATION', '300'))
        self.lyria_model = os.getenv('LYRIA_MODEL', 'gemini-1.5-pro')
        
        # 모듈 초기화
        try:
            if self.youtube_api_key:
                self.analyzer = MusicAnalyzer(self.youtube_api_key, console_log=self.console_log)
                self.console_log("[Music Service] YouTube 분석기 초기화 완료")
            else:
                self.analyzer = None
                self.console_log("[Music Service] YouTube API 키가 없습니다")
            
            if self.google_project_id:
                self.lyria_client = LyriaClient(
                    project_id=self.google_project_id,
                    location=self.google_location,
                    service_account_path=self.service_account_path,
                    console_log=self.console_log
                )
                self.console_log("[Music Service] Lyria 클라이언트 초기화 완료")
            else:
                self.lyria_client = None
                self.console_log("[Music Service] Google Cloud 프로젝트 ID가 없습니다")
            
            #self.prompt_generator = PromptGenerator(console_log=self.console_log)
            #self.console_log("[Music Service] 프롬프트 생성기 초기화 완료")
            
        except Exception as e:
            self.console_log(f"[Music Service] 초기화 오류: {str(e)}")
            raise
    
    def check_service_status(self) -> Dict:
        """
        서비스 상태 확인
        
        Returns:
            서비스 상태 정보
        """
        try:
            status = {
                'youtube_analyzer': {
                    'available': self.analyzer is not None,
                    'api_key_set': bool(self.youtube_api_key),
                    'status': 'ready' if self.analyzer else 'not_configured'
                },
                'lyria_client': {
                    'available': self.lyria_client is not None,
                    'project_id_set': bool(self.google_project_id),
                    'status': 'ready' if self.lyria_client else 'not_configured'
                },
                'prompt_generator': {
                    'available': self.prompt_generator is not None,
                    'status': 'ready'
                },
                'overall_status': 'ready' if (self.analyzer and self.lyria_client) else 'partial'
            }
            
            # Lyria 연결 테스트
            if self.lyria_client:
                try:
                    connection_test = self.lyria_client.test_connection()
                    status['lyria_client']['connection_test'] = connection_test
                except Exception as e:
                    status['lyria_client']['connection_error'] = str(e)
            
            return status
            
        except Exception as e:
            self.console_log(f"[Music Service] 상태 확인 오류: {str(e)}")
            return {
                'error': str(e),
                'overall_status': 'error'
            }
    
    def analyze_and_generate(self, youtube_url: str, generation_options: Dict = None,
                           progress_callback=None) -> Dict:
        """
        YouTube 음악 분석 후 AI 음악 생성
        
        Args:
            youtube_url: YouTube URL
            generation_options: 생성 옵션 (style, duration, variations 등)
            progress_callback: 진행률 콜백 함수
            
        Returns:
            분석 및 생성 결과
        """
        try:
            self.console_log(f"[Music Service] 분석 및 생성 시작: {youtube_url}")
            
            if not self.analyzer:
                return {'success': False, 'error': 'YouTube 분석기가 초기화되지 않았습니다'}
            
            if not self.lyria_client:
                return {'success': False, 'error': 'Lyria 클라이언트가 초기화되지 않았습니다'}
            
            # 기본 생성 옵션 설정
            if generation_options is None:
                generation_options = {}
            
            duration = generation_options.get('duration', self.default_duration)
            style = generation_options.get('style', None)
            variations = generation_options.get('variations', 1)
            output_folder = generation_options.get('output_folder', None)
            
            # 1단계: YouTube 음악 분석
            if progress_callback:
                progress_callback(10, "YouTube 음악 분석 중...")
            
            analysis_result = self.analyzer.analyze_youtube_music(youtube_url)
            
            if not analysis_result['success']:
                return {
                    'success': False,
                    'error': f"음악 분석 실패: {analysis_result['error']}"
                }
            
            # 2단계: 프롬프트 생성
            if progress_callback:
                progress_callback(30, "AI 프롬프트 생성 중...")
            
            prompt_options = self.prompt_generator.generate_prompt_options(analysis_result)
            
            # 사용자 옵션에 따라 프롬프트 선택
            if generation_options.get('prompt_type') == 'detailed':
                selected_prompt = prompt_options['detailed']
            elif generation_options.get('prompt_type') == 'custom':
                selected_prompt = self.prompt_generator.create_custom_prompt(
                    analysis_result, 
                    generation_options.get('custom_params', {})
                )
            else:
                selected_prompt = prompt_options['basic']
            
            # 스타일 자동 결정 (분석 결과 기반)
            if not style:
                style = analysis_result['music_analysis']['genre']['primary_genre']
            
            # 3단계: AI 음악 생성
            if progress_callback:
                progress_callback(50, "AI 음악 생성 중...")
            
            generation_results = []
            
            if variations > 1:
                # 여러 변형 생성
                results = self.lyria_client.generate_music_variations(
                    prompt=selected_prompt,
                    count=variations,
                    style=style,
                    duration=duration,
                    output_folder=output_folder,
                    progress_callback=lambda p, m: progress_callback(50 + (p * 0.4), m) if progress_callback else None
                )
                generation_results.extend(results)
            else:
                # 단일 생성
                result = self.lyria_client.generate_music(
                    prompt=selected_prompt,
                    style=style,
                    duration=duration,
                    output_folder=output_folder,
                    progress_callback=lambda p, m: progress_callback(50 + (p * 0.4), m) if progress_callback else None
                )
                if result['success']:
                    generation_results.append(result)
            
            if progress_callback:
                progress_callback(95, "결과 정리 중...")
            
            # 4단계: 결과 종합
            final_result = {
                'success': True,
                'analysis': analysis_result,
                'prompt_options': prompt_options,
                'selected_prompt': selected_prompt,
                'generation_results': generation_results,
                'generation_count': len(generation_results),
                'workflow_metadata': {
                    'youtube_url': youtube_url,
                    'generation_options': generation_options,
                    'processed_at': datetime.now().isoformat(),
                    'duration': duration,
                    'style': style,
                    'variations': variations
                }
            }
            
            # 생성 이력 저장
            for result in generation_results:
                self.lyria_client.save_generation_history(result)
            
            if progress_callback:
                progress_callback(100, "분석 및 생성 완료!")
            
            self.console_log(f"[Music Service] 분석 및 생성 완료: {len(generation_results)}개 생성")
            return final_result
            
        except Exception as e:
            self.console_log(f"[Music Service] 분석 및 생성 오류: {str(e)}")
            return {
                'success': False,
                'error': f'분석 및 생성 중 오류 발생: {str(e)}'
            }
    
    def analyze_only(self, youtube_url: str, progress_callback=None) -> Dict:
        """
        YouTube 음악 분석만 수행
        
        Args:
            youtube_url: YouTube URL
            progress_callback: 진행률 콜백 함수
            
        Returns:
            분석 결과
        """
        try:
            if not self.analyzer:
                return {'success': False, 'error': 'YouTube 분석기가 초기화되지 않았습니다'}
            
            if progress_callback:
                progress_callback(20, "YouTube 음악 분석 중...")
            
            analysis_result = self.analyzer.analyze_youtube_music(youtube_url)
            
            if not analysis_result['success']:
                return analysis_result
            
            if progress_callback:
                progress_callback(80, "프롬프트 생성 중...")
            
            # 프롬프트 옵션 생성
            prompt_options = self.prompt_generator.generate_prompt_options(analysis_result)
            
            if progress_callback:
                progress_callback(100, "분석 완료!")
            
            return {
                'success': True,
                'analysis': analysis_result,
                'prompt_options': prompt_options
            }
            
        except Exception as e:
            self.console_log(f"[Music Service] 분석 오류: {str(e)}")
            return {
                'success': False,
                'error': f'분석 중 오류 발생: {str(e)}'
            }
    
    def generate_from_prompt(self, prompt: str, generation_options: Dict = None,
                           progress_callback=None) -> Dict:
        """
        프롬프트에서 직접 음악 생성
        
        Args:
            prompt: 음악 생성 프롬프트
            generation_options: 생성 옵션
            progress_callback: 진행률 콜백 함수
            
        Returns:
            생성 결과
        """
        try:
            if not self.lyria_client:
                return {'success': False, 'error': 'Lyria 클라이언트가 초기화되지 않았습니다'}
            
            if generation_options is None:
                generation_options = {}
            
            # 프롬프트 검증
            if progress_callback:
                progress_callback(10, "프롬프트 검증 중...")
            
            validation = self.lyria_client.validate_prompt(prompt)
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': f"프롬프트 검증 실패: {', '.join(validation['issues'])}",
                    'validation': validation
                }
            
            # 생성 옵션 설정
            duration = generation_options.get('duration', self.default_duration)
            style = generation_options.get('style', None)
            variations = generation_options.get('variations', 1)
            output_folder = generation_options.get('output_folder', None)
            
            if progress_callback:
                progress_callback(20, "AI 음악 생성 중...")
            
            # 음악 생성
            generation_results = []
            
            if variations > 1:
                results = self.lyria_client.generate_music_variations(
                    prompt=prompt,
                    count=variations,
                    style=style,
                    duration=duration,
                    output_folder=output_folder,
                    progress_callback=lambda p, m: progress_callback(20 + (p * 0.7), m) if progress_callback else None
                )
                generation_results.extend(results)
            else:
                result = self.lyria_client.generate_music(
                    prompt=prompt,
                    style=style,
                    duration=duration,
                    output_folder=output_folder,
                    progress_callback=lambda p, m: progress_callback(20 + (p * 0.7), m) if progress_callback else None
                )
                if result['success']:
                    generation_results.append(result)
            
            if progress_callback:
                progress_callback(100, "생성 완료!")
            
            # 생성 이력 저장
            for result in generation_results:
                self.lyria_client.save_generation_history(result)
            
            return {
                'success': True,
                'generation_results': generation_results,
                'generation_count': len(generation_results),
                'prompt': prompt,
                'validation': validation,
                'generation_options': generation_options
            }
            
        except Exception as e:
            self.console_log(f"[Music Service] 프롬프트 생성 오류: {str(e)}")
            return {
                'success': False,
                'error': f'프롬프트 생성 중 오류 발생: {str(e)}'
            }
    
    def get_music_styles(self) -> Dict:
        """
        지원하는 음악 스타일 목록 반환
        
        Returns:
            스타일 목록
        """
        try:
            if self.lyria_client:
                return self.lyria_client.get_music_styles()
            else:
                return {'error': 'Lyria 클라이언트가 초기화되지 않았습니다'}
                
        except Exception as e:
            self.console_log(f"[Music Service] 스타일 목록 조회 오류: {str(e)}")
            return {'error': str(e)}
    
    def get_generation_history(self) -> List[Dict]:
        """
        생성 이력 조회
        
        Returns:
            생성 이력 리스트
        """
        try:
            if self.lyria_client:
                return self.lyria_client.get_generation_history()
            else:
                return []
                
        except Exception as e:
            self.console_log(f"[Music Service] 이력 조회 오류: {str(e)}")
            return []
    
    def explain_workflow(self, youtube_url: str = None) -> str:
        """
        워크플로우 설명 생성
        
        Args:
            youtube_url: YouTube URL (옵션)
            
        Returns:
            워크플로우 설명
        """
        try:
            explanation = """
🎵 음악 분석 및 AI 생성 워크플로우

1. YouTube 음악 분석
   - YouTube Data API로 비디오 메타데이터 수집
   - 제목, 설명, 태그에서 장르/분위기 분석
   - 댓글 감성 분석으로 분위기 보정
   - BPM, 키, 에너지 레벨 추정

2. AI 프롬프트 생성
   - 분석 결과를 Lyria AI 입력 프롬프트로 변환
   - 장르 → 스타일 지시어
   - 분위기 → 감정 표현 지시어
   - 음악적 특성 → 구체적 지시어

3. AI 음악 생성
   - Google Cloud Vertex AI Lyria 모델 사용
   - 프롬프트 기반 인스트루멘털 음악 생성
   - 다양한 스타일 변형 지원

4. 결과 통합
   - 분석 결과와 생성 음악 연결
   - 메타데이터 저장 및 이력 관리
   - 기존 음악 병합 시스템과 연동 가능
"""
            
            if youtube_url and self.analyzer:
                try:
                    # 실제 분석 예시 추가
                    analysis_result = self.analyzer.analyze_youtube_music(youtube_url)
                    if analysis_result['success']:
                        prompt_options = self.prompt_generator.generate_prompt_options(analysis_result)
                        
                        explanation += f"""

📊 분석 예시 ({youtube_url}):
- 제목: {analysis_result['video_info']['title']}
- 추정 장르: {analysis_result['music_analysis']['genre']['primary_genre']}
- 추정 분위기: {analysis_result['music_analysis']['mood']['primary_mood']}
- 생성 프롬프트: {prompt_options['basic']}
"""
                except:
                    pass
            
            return explanation
            
        except Exception as e:
            self.console_log(f"[Music Service] 워크플로우 설명 오류: {str(e)}")
            return f"워크플로우 설명 생성 중 오류: {str(e)}"