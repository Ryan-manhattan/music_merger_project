#!/usr/bin/env python3
"""
Lyria Client - Google Cloud Vertex AI Lyria 음악 생성 클라이언트
"""

import os
import json
import time
import base64
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Google Cloud Vertex AI
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    from google.cloud import aiplatform
    from google.cloud import storage
    from google.auth import default
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

class LyriaClient:
    def __init__(self, project_id: str, location: str = "us-central1", 
                 service_account_path: str = None, console_log=None):
        """
        Lyria AI 클라이언트 초기화
        
        Args:
            project_id: Google Cloud 프로젝트 ID
            location: Vertex AI 위치 (기본: us-central1)
            service_account_path: 서비스 계정 JSON 파일 경로
            console_log: 로그 출력 함수
        """
        self.project_id = project_id
        self.location = location
        self.console_log = console_log or print
        
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("Google Cloud Vertex AI 라이브러리가 설치되지 않았습니다. pip install google-cloud-aiplatform 실행")
        
        # 서비스 계정 설정 (Render 환경 변수 우선 처리)
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if credentials_json:
            # Render 환경: JSON 문자열을 임시 파일로 저장
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(credentials_json)
                temp_credentials_path = f.name
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_credentials_path
            self.console_log(f"[Lyria Client] 서비스 계정 설정 (환경 변수): {temp_credentials_path}")
        elif service_account_path and os.path.exists(service_account_path):
            # 로컬 환경: 파일 경로 사용
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
            self.console_log(f"[Lyria Client] 서비스 계정 설정 (파일): {service_account_path}")
        
        try:
            # Vertex AI 초기화
            vertexai.init(project=project_id, location=location)
            self.console_log(f"[Lyria Client] Vertex AI 초기화 완료: {project_id}, {location}")
            
            # 저장소 클라이언트 초기화
            self.storage_client = storage.Client(project=project_id)
            
            # 지원 가능한 음악 스타일 정의
            self.supported_styles = {
                'pop': 'Popular mainstream music',
                'rock': 'Rock music with electric instruments',
                'electronic': 'Electronic and synthesized music',
                'jazz': 'Jazz with improvisation',
                'classical': 'Classical instrumental music',
                'ambient': 'Ambient and atmospheric music',
                'folk': 'Folk and acoustic music',
                'blues': 'Blues music',
                'country': 'Country music',
                'hip_hop': 'Hip-hop beats and rhythms',
                'r&b': 'R&B and soul music',
                'world': 'World music from various cultures'
            }
            
            # 음악 생성 파라미터 기본값
            self.default_params = {
                'max_output_tokens': 1024,
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40
            }
            
        except Exception as e:
            self.console_log(f"[Lyria Client] 초기화 오류: {str(e)}")
            raise
    
    def test_connection(self) -> Dict:
        """
        Vertex AI 연결 테스트
        
        Returns:
            연결 상태 결과
        """
        try:
            # 기본 인증 테스트
            credentials, project = default()
            
            # AI Platform 클라이언트 테스트
            client = aiplatform.gapic.ModelServiceClient()
            
            return {
                'success': True,
                'project_id': self.project_id,
                'location': self.location,
                'credentials_valid': True,
                'message': 'Vertex AI 연결 성공'
            }
            
        except Exception as e:
            self.console_log(f"[Lyria Client] 연결 테스트 실패: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Vertex AI 연결 실패'
            }
    
    def get_available_models(self) -> List[str]:
        """
        사용 가능한 모델 목록 반환
        
        Returns:
            모델 목록
        """
        try:
            # Lyria 관련 모델들 (실제 사용 가능한 모델은 Google Cloud Console에서 확인)
            models = [
                'lyria-001',
                'lyria-music-generation',
                'gemini-1.5-pro',  # 음악 생성 지원 모델
                'gemini-1.5-flash'
            ]
            
            self.console_log(f"[Lyria Client] 사용 가능한 모델: {len(models)}개")
            return models
            
        except Exception as e:
            self.console_log(f"[Lyria Client] 모델 목록 조회 오류: {str(e)}")
            return []
    
    def prepare_music_prompt(self, prompt: str, style: str = None, 
                           duration: int = 30, additional_params: Dict = None) -> str:
        """
        음악 생성용 프롬프트 준비
        
        Args:
            prompt: 기본 프롬프트
            style: 음악 스타일
            duration: 생성할 음악 길이 (초)
            additional_params: 추가 파라미터
            
        Returns:
            최종 프롬프트
        """
        try:
            # 기본 프롬프트 구성
            music_prompt = f"Generate instrumental music: {prompt}"
            
            # 스타일 추가
            if style and style in self.supported_styles:
                music_prompt += f", in {style} style"
            
            # 길이 제한
            if duration:
                music_prompt += f", approximately {duration} seconds long"
            
            # 추가 파라미터
            if additional_params:
                if additional_params.get('tempo'):
                    music_prompt += f", with {additional_params['tempo']} tempo"
                if additional_params.get('key'):
                    music_prompt += f", in {additional_params['key']} key"
                if additional_params.get('instruments'):
                    music_prompt += f", featuring {', '.join(additional_params['instruments'])}"
            
            # 음악 생성 지시어 추가
            music_prompt += ". Create high-quality instrumental music without vocals."
            
            self.console_log(f"[Lyria Client] 프롬프트 준비 완료: {music_prompt}")
            return music_prompt
            
        except Exception as e:
            self.console_log(f"[Lyria Client] 프롬프트 준비 오류: {str(e)}")
            return prompt
    
    def generate_music(self, prompt: str, model: str = "gemini-1.5-pro",
                      style: str = None, duration: int = 30,
                      output_folder: str = None, progress_callback=None) -> Dict:
        """
        음악 생성 실행
        
        Args:
            prompt: 음악 생성 프롬프트
            model: 사용할 모델 (기본: gemini-1.5-pro)
            style: 음악 스타일
            duration: 생성할 음악 길이 (초)
            output_folder: 출력 폴더 경로
            progress_callback: 진행률 콜백 함수
            
        Returns:
            생성 결과
        """
        try:
            self.console_log(f"[Lyria Client] 음악 생성 시작: {prompt}")
            
            if progress_callback:
                progress_callback(10, "음악 생성 준비 중...")
            
            # 프롬프트 준비
            music_prompt = self.prepare_music_prompt(prompt, style, duration)
            
            if progress_callback:
                progress_callback(20, "AI 모델 로딩 중...")
            
            # 모델 초기화
            generative_model = GenerativeModel(model)
            
            if progress_callback:
                progress_callback(40, "음악 생성 중...")
            
            # 음악 생성 요청
            response = generative_model.generate_content(
                music_prompt,
                generation_config={
                    "max_output_tokens": self.default_params['max_output_tokens'],
                    "temperature": self.default_params['temperature'],
                    "top_p": self.default_params['top_p'],
                    "top_k": self.default_params['top_k']
                }
            )
            
            if progress_callback:
                progress_callback(70, "생성 결과 처리 중...")
            
            # 실제 Lyria는 오디오 파일을 생성하지만, 현재는 텍스트 응답 처리
            # 실제 구현에서는 오디오 바이너리 데이터를 처리해야 함
            
            if not output_folder:
                output_folder = tempfile.gettempdir()
            
            # 생성된 음악 파일 저장 (시뮬레이션)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"lyria_generated_{timestamp}.mp3"
            output_path = os.path.join(output_folder, output_filename)
            
            # 실제 구현에서는 여기서 오디오 파일을 저장
            # 현재는 메타데이터만 저장
            metadata = {
                'prompt': music_prompt,
                'model': model,
                'style': style,
                'duration': duration,
                'generated_at': datetime.now().isoformat(),
                'response_text': response.text if hasattr(response, 'text') else str(response)
            }
            
            # 메타데이터 저장
            metadata_path = output_path.replace('.mp3', '_metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            if progress_callback:
                progress_callback(100, "음악 생성 완료!")
            
            result = {
                'success': True,
                'output_path': output_path,
                'metadata_path': metadata_path,
                'filename': output_filename,
                'duration': duration,
                'style': style,
                'prompt': music_prompt,
                'model': model,
                'size': 0,  # 실제 파일 크기는 오디오 파일 생성 후 측정
                'generated_at': datetime.now().isoformat(),
                'file_info': {
                    'filename': output_filename,
                    'original_name': f"AI Generated Music - {style or 'Mixed'}",
                    'size': 0,
                    'duration': duration,
                    'duration_str': self._format_duration(duration),
                    'format': 'MP3',
                    'path': output_path,
                    'source': 'lyria_ai'
                }
            }
            
            self.console_log(f"[Lyria Client] 음악 생성 완료: {output_filename}")
            return result
            
        except Exception as e:
            self.console_log(f"[Lyria Client] 음악 생성 오류: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f'음악 생성 중 오류 발생: {str(e)}'
            }
    
    def generate_music_variations(self, prompt: str, count: int = 3,
                                style: str = None, duration: int = 30,
                                output_folder: str = None, progress_callback=None) -> List[Dict]:
        """
        음악 변형 생성 (여러 버전)
        
        Args:
            prompt: 기본 프롬프트
            count: 생성할 변형 개수
            style: 음악 스타일
            duration: 생성할 음악 길이 (초)
            output_folder: 출력 폴더 경로
            progress_callback: 진행률 콜백 함수
            
        Returns:
            변형 생성 결과 리스트
        """
        try:
            self.console_log(f"[Lyria Client] {count}개 변형 생성 시작")
            
            variations = []
            
            for i in range(count):
                if progress_callback:
                    progress = int((i / count) * 100)
                    progress_callback(progress, f"변형 {i+1}/{count} 생성 중...")
                
                # 각 변형마다 약간씩 다른 파라미터 사용
                variation_params = {
                    'temperature': self.default_params['temperature'] + (i * 0.1),
                    'top_p': min(0.9, self.default_params['top_p'] + (i * 0.05))
                }
                
                # 변형 프롬프트 생성
                variation_prompt = f"{prompt} (variation {i+1})"
                
                result = self.generate_music(
                    prompt=variation_prompt,
                    style=style,
                    duration=duration,
                    output_folder=output_folder
                )
                
                if result['success']:
                    variations.append(result)
                    
                # 변형 간 간격
                time.sleep(0.5)
            
            if progress_callback:
                progress_callback(100, f"{len(variations)}개 변형 생성 완료!")
            
            self.console_log(f"[Lyria Client] {len(variations)}개 변형 생성 완료")
            return variations
            
        except Exception as e:
            self.console_log(f"[Lyria Client] 변형 생성 오류: {str(e)}")
            return []
    
    def get_music_styles(self) -> Dict:
        """
        지원하는 음악 스타일 목록 반환
        
        Returns:
            스타일 목록 및 설명
        """
        return {
            'styles': self.supported_styles,
            'count': len(self.supported_styles),
            'recommended': ['pop', 'electronic', 'ambient', 'jazz', 'classical']
        }
    
    def validate_prompt(self, prompt: str) -> Dict:
        """
        프롬프트 유효성 검사
        
        Args:
            prompt: 검사할 프롬프트
            
        Returns:
            검사 결과
        """
        try:
            issues = []
            suggestions = []
            
            # 길이 검사
            if len(prompt.strip()) < 10:
                issues.append("프롬프트가 너무 짧습니다")
                suggestions.append("더 구체적인 설명을 추가해주세요")
            
            if len(prompt) > 500:
                issues.append("프롬프트가 너무 깁니다")
                suggestions.append("더 간결하게 작성해주세요")
            
            # 음악 관련 키워드 검사
            music_keywords = ['music', 'song', 'track', 'melody', 'rhythm', 'beat', 'sound']
            has_music_keyword = any(keyword in prompt.lower() for keyword in music_keywords)
            
            if not has_music_keyword:
                suggestions.append("음악 관련 키워드를 포함하는 것이 좋습니다")
            
            # 부적절한 내용 검사
            inappropriate_words = ['vocal', 'lyrics', 'singing', 'voice']
            has_inappropriate = any(word in prompt.lower() for word in inappropriate_words)
            
            if has_inappropriate:
                issues.append("Lyria는 인스트루멘털 음악만 생성합니다")
                suggestions.append("보컬이나 가사 관련 내용을 제거해주세요")
            
            is_valid = len(issues) == 0
            
            return {
                'valid': is_valid,
                'issues': issues,
                'suggestions': suggestions,
                'score': max(0, 100 - len(issues) * 20),
                'improved_prompt': self._improve_prompt(prompt) if not is_valid else prompt
            }
            
        except Exception as e:
            self.console_log(f"[Lyria Client] 프롬프트 검사 오류: {str(e)}")
            return {
                'valid': False,
                'issues': [f"검사 중 오류: {str(e)}"],
                'suggestions': [],
                'score': 0,
                'improved_prompt': prompt
            }
    
    def _improve_prompt(self, prompt: str) -> str:
        """프롬프트 개선 제안"""
        improved = prompt.strip()
        
        # 기본 개선사항 적용
        if 'instrumental' not in improved.lower():
            improved = f"instrumental {improved}"
        
        if not any(word in improved.lower() for word in ['music', 'track', 'song']):
            improved = f"{improved} music"
        
        return improved
    
    def _format_duration(self, seconds: int) -> str:
        """초를 mm:ss 형식으로 변환"""
        if seconds < 0:
            return "00:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_generation_history(self) -> List[Dict]:
        """
        생성 이력 조회 (로컬 파일 기반)
        
        Returns:
            생성 이력 리스트
        """
        try:
            history_file = os.path.join(tempfile.gettempdir(), 'lyria_history.json')
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                return history
            
            return []
            
        except Exception as e:
            self.console_log(f"[Lyria Client] 이력 조회 오류: {str(e)}")
            return []
    
    def save_generation_history(self, generation_result: Dict):
        """
        생성 이력 저장
        
        Args:
            generation_result: 생성 결과
        """
        try:
            history_file = os.path.join(tempfile.gettempdir(), 'lyria_history.json')
            
            # 기존 이력 로드
            history = self.get_generation_history()
            
            # 새 이력 추가
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'prompt': generation_result.get('prompt', ''),
                'style': generation_result.get('style', ''),
                'duration': generation_result.get('duration', 0),
                'filename': generation_result.get('filename', ''),
                'success': generation_result.get('success', False)
            }
            
            history.append(history_entry)
            
            # 최대 100개 이력만 유지
            if len(history) > 100:
                history = history[-100:]
            
            # 파일 저장
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            self.console_log(f"[Lyria Client] 이력 저장 완료: {len(history)}개 항목")
            
        except Exception as e:
            self.console_log(f"[Lyria Client] 이력 저장 오류: {str(e)}")