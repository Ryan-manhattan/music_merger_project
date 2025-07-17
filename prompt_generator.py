#!/usr/bin/env python3
"""
Prompt Generator - 음악 분석 결과를 Lyria AI 프롬프트로 변환
"""

import json
from typing import Dict, List, Optional
from datetime import datetime

class PromptGenerator:
    def __init__(self, console_log=None):
        """
        프롬프트 생성기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        
        # 장르별 음악적 특성 정의
        self.genre_characteristics = {
            'pop': {
                'instruments': ['piano', 'guitar', 'drums', 'bass', 'synthesizer'],
                'style': 'catchy and accessible',
                'tempo': 'moderate',
                'description': 'mainstream pop with memorable melody'
            },
            'rock': {
                'instruments': ['electric guitar', 'bass', 'drums', 'vocals'],
                'style': 'powerful and energetic',
                'tempo': 'upbeat',
                'description': 'rock music with strong guitar riffs'
            },
            'hip_hop': {
                'instruments': ['drums', 'bass', 'synthesizer', 'samples'],
                'style': 'rhythmic and urban',
                'tempo': 'moderate',
                'description': 'hip-hop beat with strong rhythm'
            },
            'electronic': {
                'instruments': ['synthesizer', 'electronic drums', 'bass', 'pad'],
                'style': 'synthetic and modern',
                'tempo': 'variable',
                'description': 'electronic music with synthesized sounds'
            },
            'jazz': {
                'instruments': ['piano', 'saxophone', 'trumpet', 'bass', 'drums'],
                'style': 'sophisticated and improvisational',
                'tempo': 'variable',
                'description': 'jazz with improvisation and swing'
            },
            'classical': {
                'instruments': ['piano', 'violin', 'cello', 'orchestra'],
                'style': 'elegant and refined',
                'tempo': 'variable',
                'description': 'classical instrumental music'
            },
            'ballad': {
                'instruments': ['piano', 'guitar', 'strings', 'vocals'],
                'style': 'emotional and expressive',
                'tempo': 'slow',
                'description': 'slow ballad with emotional depth'
            },
            'dance': {
                'instruments': ['electronic drums', 'bass', 'synthesizer', 'vocoder'],
                'style': 'energetic and rhythmic',
                'tempo': 'fast',
                'description': 'dance music with driving beat'
            },
            'country': {
                'instruments': ['acoustic guitar', 'banjo', 'harmonica', 'fiddle'],
                'style': 'rustic and authentic',
                'tempo': 'moderate',
                'description': 'country music with folk elements'
            },
            'reggae': {
                'instruments': ['guitar', 'bass', 'drums', 'keyboard'],
                'style': 'relaxed and rhythmic',
                'tempo': 'moderate',
                'description': 'reggae with characteristic off-beat rhythm'
            },
            'latin': {
                'instruments': ['guitar', 'percussion', 'brass', 'piano'],
                'style': 'passionate and rhythmic',
                'tempo': 'moderate to fast',
                'description': 'latin music with vibrant rhythms'
            },
            'r&b': {
                'instruments': ['piano', 'bass', 'drums', 'horn section'],
                'style': 'soulful and groove-oriented',
                'tempo': 'moderate',
                'description': 'R&B with soul and funk elements'
            }
        }
        
        # 분위기별 형용사 정의
        self.mood_descriptors = {
            'happy': ['upbeat', 'joyful', 'cheerful', 'bright', 'optimistic'],
            'sad': ['melancholic', 'somber', 'emotional', 'tragic', 'mournful'],
            'calm': ['peaceful', 'serene', 'relaxing', 'gentle', 'ambient'],
            'energetic': ['energetic', 'powerful', 'intense', 'driving', 'dynamic'],
            'romantic': ['romantic', 'tender', 'intimate', 'passionate', 'loving'],
            'nostalgic': ['nostalgic', 'wistful', 'reflective', 'vintage', 'dreamy'],
            'dark': ['dark', 'mysterious', 'haunting', 'brooding', 'gothic'],
            'uplifting': ['uplifting', 'inspiring', 'hopeful', 'motivational', 'triumphant']
        }
        
        # 에너지 레벨별 템포 설명
        self.energy_tempo = {
            'Very High': 'very fast and intense',
            'High': 'fast and energetic',
            'Medium': 'moderate tempo',
            'Low': 'slow and gentle'
        }
        
        # BPM 범위별 템포 설명
        self.bpm_description = {
            (0, 70): 'very slow',
            (70, 90): 'slow',
            (90, 120): 'moderate',
            (120, 140): 'upbeat',
            (140, 180): 'fast',
            (180, 999): 'very fast'
        }
    
    def get_tempo_description(self, bpm: int) -> str:
        """BPM을 기반으로 템포 설명 생성"""
        for (min_bpm, max_bpm), description in self.bpm_description.items():
            if min_bpm <= bpm < max_bpm:
                return description
        return 'moderate'
    
    def create_basic_prompt(self, analysis_result: Dict) -> str:
        """
        기본 프롬프트 생성
        
        Args:
            analysis_result: 음악 분석 결과
            
        Returns:
            Lyria AI용 기본 프롬프트
        """
        try:
            music_analysis = analysis_result['music_analysis']
            
            # 기본 구성 요소 추출
            primary_genre = music_analysis['genre']['primary_genre']
            primary_mood = music_analysis['mood']['primary_mood']
            bpm = music_analysis['estimated_bpm']
            energy = music_analysis['energy_level']
            
            # 장르 특성 가져오기
            genre_info = self.genre_characteristics.get(primary_genre, {
                'instruments': ['piano', 'guitar', 'drums'],
                'style': 'melodic',
                'description': 'instrumental music'
            })
            
            # 분위기 형용사 가져오기
            mood_words = self.mood_descriptors.get(primary_mood, ['melodic'])
            
            # 템포 설명 생성
            tempo_desc = self.get_tempo_description(bpm)
            
            # 기본 프롬프트 구성
            prompt_parts = [
                f"Create a {tempo_desc} {primary_genre} track",
                f"with {mood_words[0]} and {mood_words[1] if len(mood_words) > 1 else 'expressive'} mood",
                f"featuring {', '.join(genre_info['instruments'][:3])}",
                f"in {genre_info['style']} style"
            ]
            
            basic_prompt = ", ".join(prompt_parts)
            
            self.console_log(f"[Prompt Generator] 기본 프롬프트 생성: {basic_prompt}")
            return basic_prompt
            
        except Exception as e:
            self.console_log(f"[Prompt Generator] 기본 프롬프트 생성 오류: {str(e)}")
            return "Create an instrumental music track with moderate tempo and melodic style"
    
    def create_detailed_prompt(self, analysis_result: Dict) -> str:
        """
        상세 프롬프트 생성
        
        Args:
            analysis_result: 음악 분석 결과
            
        Returns:
            Lyria AI용 상세 프롬프트
        """
        try:
            music_analysis = analysis_result['music_analysis']
            video_info = analysis_result['video_info']
            
            # 기본 정보
            primary_genre = music_analysis['genre']['primary_genre']
            predicted_genres = music_analysis['genre']['predicted_genres']
            primary_mood = music_analysis['mood']['primary_mood']
            predicted_moods = music_analysis['mood']['predicted_moods']
            bpm = music_analysis['estimated_bpm']
            energy = music_analysis['energy_level']
            key = music_analysis['estimated_key']
            
            # 장르 조합 (최대 2개)
            genre_blend = predicted_genres[:2] if len(predicted_genres) > 1 else [primary_genre]
            genre_desc = f"{genre_blend[0]}"
            if len(genre_blend) > 1:
                genre_desc += f" with {genre_blend[1]} influences"
            
            # 분위기 조합 (최대 2개)
            mood_blend = predicted_moods[:2] if len(predicted_moods) > 1 else [primary_mood]
            mood_descriptors = []
            for mood in mood_blend:
                mood_descriptors.extend(self.mood_descriptors.get(mood, [mood])[:2])
            
            # 악기 선택 (장르 기반)
            instruments = []
            for genre in genre_blend:
                genre_instruments = self.genre_characteristics.get(genre, {}).get('instruments', [])
                instruments.extend(genre_instruments)
            
            # 중복 제거 및 최대 4개 선택
            unique_instruments = list(dict.fromkeys(instruments))[:4]
            
            # 템포 및 리듬 설명
            tempo_desc = self.get_tempo_description(bpm)
            rhythm_desc = self.energy_tempo.get(energy, 'moderate tempo')
            
            # 곡 길이 고려
            duration = video_info['duration']
            if duration < 120:  # 2분 미만
                length_desc = "short and concise"
            elif duration < 240:  # 4분 미만
                length_desc = "standard length"
            else:  # 4분 이상
                length_desc = "extended"
            
            # 상세 프롬프트 구성
            prompt_parts = [
                f"Create a {length_desc} {genre_desc} instrumental track",
                f"with {', '.join(mood_descriptors[:3])} atmosphere",
                f"featuring {', '.join(unique_instruments)}",
                f"in {key.split()[0]} {key.split()[1].lower() if len(key.split()) > 1 else 'major'}",
                f"with {rhythm_desc} and {tempo_desc} pace"
            ]
            
            # 특별한 특성 추가
            if 'electronic' in genre_blend:
                prompt_parts.append("with modern synthesized sounds")
            if 'jazz' in genre_blend:
                prompt_parts.append("with improvisational elements")
            if 'classical' in genre_blend:
                prompt_parts.append("with orchestral arrangement")
            
            detailed_prompt = ", ".join(prompt_parts)
            
            self.console_log(f"[Prompt Generator] 상세 프롬프트 생성: {detailed_prompt}")
            return detailed_prompt
            
        except Exception as e:
            self.console_log(f"[Prompt Generator] 상세 프롬프트 생성 오류: {str(e)}")
            return self.create_basic_prompt(analysis_result)
    
    def create_style_variant_prompts(self, analysis_result: Dict) -> List[str]:
        """
        스타일 변형 프롬프트들 생성
        
        Args:
            analysis_result: 음악 분석 결과
            
        Returns:
            다양한 스타일의 프롬프트 리스트
        """
        try:
            music_analysis = analysis_result['music_analysis']
            primary_genre = music_analysis['genre']['primary_genre']
            primary_mood = music_analysis['mood']['primary_mood']
            
            base_prompt = self.create_basic_prompt(analysis_result)
            
            # 스타일 변형 목록
            style_variants = [
                f"{base_prompt} with minimalist arrangement",
                f"{base_prompt} with rich orchestration",
                f"{base_prompt} with ambient textures",
                f"{base_prompt} with rhythmic emphasis",
                f"{base_prompt} with melodic focus"
            ]
            
            self.console_log(f"[Prompt Generator] {len(style_variants)}개 스타일 변형 생성")
            return style_variants
            
        except Exception as e:
            self.console_log(f"[Prompt Generator] 스타일 변형 생성 오류: {str(e)}")
            return [self.create_basic_prompt(analysis_result)]
    
    def create_custom_prompt(self, analysis_result: Dict, user_preferences: Dict) -> str:
        """
        사용자 선호도를 반영한 커스텀 프롬프트 생성
        
        Args:
            analysis_result: 음악 분석 결과
            user_preferences: 사용자 선호도 (instruments, mood, tempo 등)
            
        Returns:
            커스텀 프롬프트
        """
        try:
            # 기본 프롬프트 생성
            base_prompt = self.create_basic_prompt(analysis_result)
            
            # 사용자 선호도 반영
            custom_parts = []
            
            if user_preferences.get('instruments'):
                custom_parts.append(f"featuring {', '.join(user_preferences['instruments'])}")
            
            if user_preferences.get('mood'):
                custom_parts.append(f"with {user_preferences['mood']} mood")
            
            if user_preferences.get('tempo'):
                custom_parts.append(f"in {user_preferences['tempo']} tempo")
            
            if user_preferences.get('style'):
                custom_parts.append(f"with {user_preferences['style']} style")
            
            if custom_parts:
                custom_prompt = f"{base_prompt}, {', '.join(custom_parts)}"
            else:
                custom_prompt = base_prompt
            
            self.console_log(f"[Prompt Generator] 커스텀 프롬프트 생성: {custom_prompt}")
            return custom_prompt
            
        except Exception as e:
            self.console_log(f"[Prompt Generator] 커스텀 프롬프트 생성 오류: {str(e)}")
            return self.create_basic_prompt(analysis_result)
    
    def generate_prompt_options(self, analysis_result: Dict) -> Dict:
        """
        다양한 프롬프트 옵션 생성
        
        Args:
            analysis_result: 음악 분석 결과
            
        Returns:
            프롬프트 옵션들
        """
        try:
            options = {
                'basic': self.create_basic_prompt(analysis_result),
                'detailed': self.create_detailed_prompt(analysis_result),
                'variants': self.create_style_variant_prompts(analysis_result),
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'source_analysis': {
                        'video_id': analysis_result['video_info']['video_id'],
                        'title': analysis_result['video_info']['title'],
                        'genre': analysis_result['music_analysis']['genre']['primary_genre'],
                        'mood': analysis_result['music_analysis']['mood']['primary_mood']
                    }
                }
            }
            
            self.console_log(f"[Prompt Generator] 프롬프트 옵션 생성 완료")
            return options
            
        except Exception as e:
            self.console_log(f"[Prompt Generator] 프롬프트 옵션 생성 오류: {str(e)}")
            return {
                'basic': "Create an instrumental music track with moderate tempo",
                'detailed': "Create an instrumental music track with moderate tempo and melodic style",
                'variants': ["Create an instrumental music track with moderate tempo"],
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'error': str(e)
                }
            }
    
    def explain_prompt_generation(self, analysis_result: Dict) -> str:
        """
        프롬프트 생성 과정 설명
        
        Args:
            analysis_result: 음악 분석 결과
            
        Returns:
            프롬프트 생성 과정 설명
        """
        try:
            music_analysis = analysis_result['music_analysis']
            video_info = analysis_result['video_info']
            
            explanation = f"""
프롬프트 생성 과정:

1. 원본 음악 분석:
   - 제목: {video_info['title']}
   - 아티스트: {music_analysis['artist']}
   - 주 장르: {music_analysis['genre']['primary_genre']}
   - 주 분위기: {music_analysis['mood']['primary_mood']}

2. 음악적 특성 추출:
   - 예상 BPM: {music_analysis['estimated_bpm']}
   - 예상 키: {music_analysis['estimated_key']}
   - 에너지 레벨: {music_analysis['energy_level']}

3. AI 프롬프트 변환:
   - 장르 → 스타일 지시어
   - 분위기 → 감정 표현 지시어
   - 템포 → 리듬 지시어
   - 악기 → 사운드 지시어

4. 최종 프롬프트:
   - 기본: {self.create_basic_prompt(analysis_result)}
   - 상세: {self.create_detailed_prompt(analysis_result)}
"""
            
            return explanation
            
        except Exception as e:
            self.console_log(f"[Prompt Generator] 설명 생성 오류: {str(e)}")
            return f"프롬프트 생성 과정 설명 중 오류 발생: {str(e)}"