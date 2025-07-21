#!/usr/bin/env python3
"""
Emotion-Based Playlist Generator - 감정 기반 플레이리스트 생성기
Reddit, Spotify, YouTube 데이터를 통합하여 감정별 플레이리스트 생성
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics

# 자체 모듈 임포트 (순환 참조 방지)
try:
    from reddit_connector import RedditConnector
except ImportError:
    RedditConnector = None

try:
    from spotify_connector import SpotifyConnector
except ImportError:
    SpotifyConnector = None

try:
    from keyword_trend_analyzer import KeywordTrendAnalyzer
except ImportError:
    KeywordTrendAnalyzer = None

try:
    from comment_trend_analyzer import CommentTrendAnalyzer
except ImportError:
    CommentTrendAnalyzer = None

try:
    from music_analyzer import MusicAnalyzer
except ImportError:
    MusicAnalyzer = None

class EmotionPlaylistGenerator:
    def __init__(self, console_log=None):
        """
        감정 기반 플레이리스트 생성기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        
        # 각 분석 모듈 초기화 (안전한 초기화)
        self.reddit_connector = None
        self.spotify_connector = None
        self.keyword_analyzer = None
        self.comment_analyzer = None
        self.youtube_analyzer = None
        
        try:
            if RedditConnector:
                self.reddit_connector = RedditConnector(console_log=self.console_log)
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] Reddit 연결기 초기화 오류: {str(e)}")
        
        try:
            if SpotifyConnector:
                self.spotify_connector = SpotifyConnector(console_log=self.console_log)
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] Spotify 연결기 초기화 오류: {str(e)}")
        
        try:
            if KeywordTrendAnalyzer:
                self.keyword_analyzer = KeywordTrendAnalyzer(console_log=self.console_log)
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] 키워드 분석기 초기화 오류: {str(e)}")
        
        try:
            if CommentTrendAnalyzer:
                self.comment_analyzer = CommentTrendAnalyzer(console_log=self.console_log)
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] 댓글 분석기 초기화 오류: {str(e)}")
        
        # YouTube 분석기 초기화 (API 키 필요)
        try:
            youtube_api_key = os.getenv('YOUTUBE_API_KEY')
            if youtube_api_key and MusicAnalyzer:
                self.youtube_analyzer = MusicAnalyzer(youtube_api_key, console_log=self.console_log)
            else:
                self.console_log("[EmotionPlaylist] YouTube API 키가 설정되지 않았습니다")
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] YouTube 분석기 초기화 오류: {str(e)}")
        
        # 감정 카테고리 정의
        self.emotion_categories = {
            'energetic': {
                'name': '🔥 에너지 플레이리스트',
                'description': '신나고 역동적인 곡들로 구성된 플레이리스트',
                'keywords': ['신나다', '에너지', '파워풀', '역동적', '흥겨워', 'energetic', 'pump', 'hype'],
                'spotify_criteria': {
                    'energy_min': 0.7,
                    'danceability_min': 0.6,
                    'valence_min': 0.5
                },
                'comment_prompt': '이 곡 들으면 어떤 에너지가 느껴지세요?'
            },
            'romantic': {
                'name': '💝 로맨틱 플레이리스트',
                'description': '사랑과 로맨스를 느낄 수 있는 감성적인 곡들',
                'keywords': ['로맨틱', '사랑', '설레다', '감성적', '달콤', 'romantic', 'love', 'sweet'],
                'spotify_criteria': {
                    'valence_min': 0.4,
                    'acousticness_min': 0.3,
                    'energy_max': 0.7
                },
                'comment_prompt': '이 곡을 들으면 어떤 사람이 생각나세요?'
            },
            'melancholic': {
                'name': '😢 감성 플레이리스트',
                'description': '깊은 감정과 여운을 남기는 곡들',
                'keywords': ['슬프다', '감성', '여운', '깊다', '눈물', 'sad', 'melancholic', 'emotional'],
                'spotify_criteria': {
                    'valence_max': 0.4,
                    'energy_max': 0.5,
                    'acousticness_min': 0.2
                },
                'comment_prompt': '이 곡이 주는 감정을 한 단어로 표현하면?'
            },
            'peaceful': {
                'name': '🧘 힐링 플레이리스트',
                'description': '마음이 평온해지는 차분하고 안정적인 곡들',
                'keywords': ['힐링', '편안', '차분', '평온', '안정', 'peaceful', 'calm', 'healing'],
                'spotify_criteria': {
                    'energy_max': 0.4,
                    'valence_min': 0.4,
                    'acousticness_min': 0.4
                },
                'comment_prompt': '이 곡을 들으면 어떤 순간이 떠오르세요?'
            },
            'party': {
                'name': '🎉 파티 플레이리스트',
                'description': '클럽이나 파티에서 즐길 수 있는 댄스 곡들',
                'keywords': ['파티', '클럽', '댄스', '신나다', '춤', 'party', 'club', 'dance'],
                'spotify_criteria': {
                    'danceability_min': 0.8,
                    'energy_min': 0.8,
                    'valence_min': 0.6
                },
                'comment_prompt': '이 곡으로 어떤 춤을 추고 싶으세요?'
            }
        }
        
        # 감정 가중치 설정
        self.emotion_weights = {
            'reddit': 0.3,      # Reddit 감정 키워드
            'spotify': 0.4,     # Spotify 오디오 특성
            'youtube': 0.3      # YouTube 댓글 분석
        }
    
    def generate_emotion_playlist(self, 
                                emotion_type: str, 
                                limit: int = 30,
                                include_reddit: bool = True,
                                include_spotify: bool = True,
                                include_youtube: bool = True) -> Dict:
        """
        감정별 플레이리스트 생성
        
        Args:
            emotion_type: 감정 타입 ('energetic', 'romantic', 'melancholic', 'peaceful', 'party')
            limit: 플레이리스트 곡 수
            include_reddit: Reddit 데이터 포함 여부
            include_spotify: Spotify 데이터 포함 여부
            include_youtube: YouTube 데이터 포함 여부
            
        Returns:
            감정별 플레이리스트 데이터
        """
        try:
            if emotion_type not in self.emotion_categories:
                return {'success': False, 'error': f'지원하지 않는 감정 타입: {emotion_type}'}
            
            emotion_config = self.emotion_categories[emotion_type]
            self.console_log(f"[EmotionPlaylist] {emotion_config['name']} 생성 시작")
            
            result = {
                'success': True,
                'emotion_type': emotion_type,
                'playlist_name': emotion_config['name'],
                'description': emotion_config['description'],
                'generated_at': datetime.now().isoformat(),
                'tracks': [],
                'emotion_analysis': {},
                'comment_prompts': []
            }
            
            # 1. 곡 후보 수집
            candidate_tracks = self._collect_candidate_tracks(emotion_type, limit * 2)
            self.console_log(f"[EmotionPlaylist] 후보 곡 수집: {len(candidate_tracks)}곡")
            
            # 2. 감정 점수 계산
            scored_tracks = []
            for track in candidate_tracks:
                emotion_score = self._calculate_emotion_score(track, emotion_type)
                self.console_log(f"[EmotionPlaylist] 곡: {track.get('title', 'Unknown')} - 점수: {emotion_score}")
                if emotion_score > 0.2:  # 임계값 더 낮춤 (API 제한 고려)
                    track['emotion_score'] = emotion_score
                    scored_tracks.append(track)
            
            self.console_log(f"[EmotionPlaylist] 필터링 후 곡 수: {len(scored_tracks)}곡")
            
            # 3. 점수순 정렬 및 상위 곡 선택
            scored_tracks.sort(key=lambda x: x['emotion_score'], reverse=True)
            selected_tracks = scored_tracks[:limit]
            
            # 4. 플레이리스트 구성
            result['tracks'] = selected_tracks
            result['total_tracks'] = len(selected_tracks)
            result['average_emotion_score'] = statistics.mean([t['emotion_score'] for t in selected_tracks]) if selected_tracks else 0
            
            # 5. 댓글 유도 문구 생성
            result['comment_prompts'] = self._generate_comment_prompts(emotion_type, selected_tracks)
            
            # 6. 감정 분석 요약
            result['emotion_analysis'] = self._analyze_playlist_emotions(selected_tracks)
            
            self.console_log(f"[EmotionPlaylist] {emotion_config['name']} 생성 완료: {len(selected_tracks)}곡")
            
            return result
            
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] 플레이리스트 생성 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _collect_candidate_tracks(self, emotion_type: str, limit: int) -> List[Dict]:
        """곡 후보 수집"""
        candidate_tracks = []
        
        # API 연결 상태 확인 후 데이터 수집
        if not self.spotify_connector or not hasattr(self.spotify_connector, 'spotify') or not self.spotify_connector.spotify:
            self.console_log("[EmotionPlaylist] Spotify 연결 안됨, 샘플 데이터 사용")
            return self._get_sample_tracks(emotion_type, limit)
        
        # Spotify에서 감정 키워드 기반 트랙 검색
        if self.spotify_connector and self.spotify_connector.spotify:
            try:
                emotion_config = self.emotion_categories[emotion_type]
                keywords = emotion_config.get('keywords', [])
                
                # 키워드 기반 검색
                spotify_tracks = self.spotify_connector.search_popular_tracks_by_keywords(keywords, limit)
                if spotify_tracks and spotify_tracks.get('success') and spotify_tracks.get('tracks'):
                    for track in spotify_tracks['tracks']:
                        candidate_tracks.append({
                            'source': 'spotify_search',
                            'spotify_data': track,
                            'title': track.get('name', ''),
                            'artist': track.get('main_artist', ''),
                            'id': track.get('id', ''),
                            'popularity': track.get('popularity', 0)
                        })
            except Exception as e:
                self.console_log(f"[EmotionPlaylist] Spotify 데이터 수집 오류: {str(e)}")
        
        # Reddit에서 언급된 곡 수집
        if self.reddit_connector and self.reddit_connector.reddit:
            try:
                reddit_posts = self.reddit_connector.get_trending_posts('general', limit//3)
                if reddit_posts and reddit_posts.get('success') and reddit_posts.get('posts'):
                    for post in reddit_posts['posts']:
                        # 제목에서 곡 정보 추출
                        song_info = self._extract_song_from_title(post.get('title', ''))
                        if song_info:
                            candidate_tracks.append({
                                'source': 'reddit',
                                'reddit_data': post,
                                'title': song_info.get('title', ''),
                                'artist': song_info.get('artist', ''),
                                'reddit_score': post.get('score', 0)
                            })
            except Exception as e:
                self.console_log(f"[EmotionPlaylist] Reddit 데이터 수집 오류: {str(e)}")
        
        return candidate_tracks
    
    def _get_sample_tracks(self, emotion_type: str, limit: int) -> List[Dict]:
        """API 연결 실패시 샘플 데이터 제공"""
        sample_tracks = {
            'energetic': [
                {'title': 'Dynamite', 'artist': 'BTS', 'emotion_score': 0.95},
                {'title': 'How You Like That', 'artist': 'BLACKPINK', 'emotion_score': 0.92},
                {'title': 'Next Level', 'artist': 'aespa', 'emotion_score': 0.88},
                {'title': 'Savage', 'artist': 'aespa', 'emotion_score': 0.85},
                {'title': 'Permission to Dance', 'artist': 'BTS', 'emotion_score': 0.90},
                {'title': 'DALLA DALLA', 'artist': 'ITZY', 'emotion_score': 0.87},
                {'title': 'Not Shy', 'artist': 'ITZY', 'emotion_score': 0.84},
                {'title': 'God\'s Menu', 'artist': 'Stray Kids', 'emotion_score': 0.89},
                {'title': 'Thunderous', 'artist': 'Stray Kids', 'emotion_score': 0.86},
                {'title': 'WANNABE', 'artist': 'ITZY', 'emotion_score': 0.83},
            ],
            'romantic': [
                {'title': 'Spring Day', 'artist': 'BTS', 'emotion_score': 0.93},
                {'title': 'Through the Night', 'artist': 'IU', 'emotion_score': 0.89},
                {'title': 'Stay', 'artist': 'BLACKPINK', 'emotion_score': 0.86},
                {'title': 'Eight', 'artist': 'IU ft. Suga', 'emotion_score': 0.91},
                {'title': 'Lovesick Girls', 'artist': 'BLACKPINK', 'emotion_score': 0.88},
                {'title': 'Celebrity', 'artist': 'IU', 'emotion_score': 0.87},
                {'title': 'My Universe', 'artist': 'Coldplay & BTS', 'emotion_score': 0.85},
                {'title': 'Butter', 'artist': 'BTS', 'emotion_score': 0.84},
                {'title': 'Dear Name', 'artist': 'IU', 'emotion_score': 0.82},
                {'title': 'Love Dive', 'artist': 'IVE', 'emotion_score': 0.83},
            ],
            'melancholic': [
                {'title': 'Blue & Grey', 'artist': 'BTS', 'emotion_score': 0.94},
                {'title': 'Palette', 'artist': 'IU', 'emotion_score': 0.87},
                {'title': 'Breathe', 'artist': 'Lee Hi', 'emotion_score': 0.92},
                {'title': 'Dear Name', 'artist': 'IU', 'emotion_score': 0.85},
                {'title': 'Winter Flower', 'artist': 'Younha', 'emotion_score': 0.89},
                {'title': 'Lost in the Woods', 'artist': 'IU', 'emotion_score': 0.83},
                {'title': 'Epiphany', 'artist': 'BTS (Jin)', 'emotion_score': 0.88},
                {'title': 'Lonely', 'artist': 'Lee Hi', 'emotion_score': 0.86},
                {'title': 'Rain', 'artist': 'BTS (Jin)', 'emotion_score': 0.84},
                {'title': 'Goodbye', 'artist': 'Taemin', 'emotion_score': 0.82},
            ],
            'peaceful': [
                {'title': 'Butterfly', 'artist': 'BTS', 'emotion_score': 0.91},
                {'title': 'Serendipity', 'artist': 'BTS (Jimin)', 'emotion_score': 0.88},
                {'title': 'Euphoria', 'artist': 'BTS (Jungkook)', 'emotion_score': 0.85},
                {'title': 'Lilac', 'artist': 'IU', 'emotion_score': 0.87},
                {'title': 'Blueming', 'artist': 'IU', 'emotion_score': 0.84},
                {'title': 'Moon', 'artist': 'BTS (Jin)', 'emotion_score': 0.86},
                {'title': 'Inner Child', 'artist': 'BTS (V)', 'emotion_score': 0.83},
                {'title': 'Filter', 'artist': 'BTS (Jimin)', 'emotion_score': 0.82},
                {'title': 'Sing for You', 'artist': 'EXO', 'emotion_score': 0.81},
                {'title': 'Holo', 'artist': 'Lee Hi', 'emotion_score': 0.80},
            ],
            'party': [
                {'title': 'Gangnam Style', 'artist': 'PSY', 'emotion_score': 0.96},
                {'title': 'DDU-DU DDU-DU', 'artist': 'BLACKPINK', 'emotion_score': 0.93},
                {'title': 'Mic Drop', 'artist': 'BTS', 'emotion_score': 0.90},
                {'title': 'Kill This Love', 'artist': 'BLACKPINK', 'emotion_score': 0.89},
                {'title': 'Fire', 'artist': 'BTS', 'emotion_score': 0.87},
                {'title': 'ICY', 'artist': 'ITZY', 'emotion_score': 0.85},
                {'title': 'Boombayah', 'artist': 'BLACKPINK', 'emotion_score': 0.84},
                {'title': 'DNA', 'artist': 'BTS', 'emotion_score': 0.86},
                {'title': 'Fancy', 'artist': 'TWICE', 'emotion_score': 0.83},
                {'title': 'What Is Love?', 'artist': 'TWICE', 'emotion_score': 0.82},
            ]
        }
        
        tracks = sample_tracks.get(emotion_type, sample_tracks['energetic'])
        result = []
        
        for i, track in enumerate(tracks[:limit]):
            result.append({
                'source': 'sample',
                'title': track['title'],
                'artist': track['artist'],
                'emotion_score': track['emotion_score'],
                'id': f"sample_{i}"
            })
        
        return result
    
    def _calculate_emotion_score(self, track: Dict, emotion_type: str) -> float:
        """감정 점수 계산"""
        try:
            # 샘플 데이터인 경우 미리 계산된 점수 사용
            if track.get('source') == 'sample':
                return track.get('emotion_score', 0.7)
            
            emotion_config = self.emotion_categories[emotion_type]
            total_score = 0.0
            weight_sum = 0.0
            
            # 1. Spotify 오디오 특성 점수
            if 'spotify_data' in track:
                spotify_score = self._calculate_spotify_emotion_score(track['spotify_data'], emotion_config)
                total_score += spotify_score * self.emotion_weights['spotify']
                weight_sum += self.emotion_weights['spotify']
            
            # 2. Reddit 키워드 점수
            if 'reddit_data' in track:
                reddit_score = self._calculate_reddit_emotion_score(track['reddit_data'], emotion_config)
                total_score += reddit_score * self.emotion_weights['reddit']
                weight_sum += self.emotion_weights['reddit']
            
            # 3. YouTube 댓글 점수 (구현 예정)
            # youtube_score = self._calculate_youtube_emotion_score(track, emotion_config)
            # total_score += youtube_score * self.emotion_weights['youtube']
            # weight_sum += self.emotion_weights['youtube']
            
            # 가중 평균 계산
            if weight_sum > 0:
                return total_score / weight_sum
            else:
                return 0.5  # 기본값
                
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] 감정 점수 계산 오류: {str(e)}")
            return 0.5
    
    def _calculate_spotify_emotion_score(self, track_data: Dict, emotion_config: Dict) -> float:
        """Spotify 오디오 특성 기반 감정 점수"""
        try:
            # 오디오 특성 가져오기
            track_id = track_data.get('id')
            if not track_id:
                # 오디오 특성을 사용할 수 없는 경우 인기도와 키워드 기반 점수 계산
                return self._calculate_fallback_spotify_score(track_data, emotion_config)
            
            audio_features = self.spotify_connector.get_audio_features([track_id])
            if not audio_features or not audio_features.get('success') or not audio_features.get('individual_features'):
                # 오디오 특성 실패시 대체 점수 계산
                return self._calculate_fallback_spotify_score(track_data, emotion_config)
            
            features = audio_features['individual_features'][0]
            if not features:
                return self._calculate_fallback_spotify_score(track_data, emotion_config)
                
            criteria = emotion_config['spotify_criteria']
            
            score = 0.0
            criteria_count = 0
            
            # 각 조건 확인
            for key, value in criteria.items():
                if key.endswith('_min'):
                    feature_key = key.replace('_min', '')
                    if features.get(feature_key, 0) >= value:
                        score += 1.0
                    criteria_count += 1
                elif key.endswith('_max'):
                    feature_key = key.replace('_max', '')
                    if features.get(feature_key, 0) <= value:
                        score += 1.0
                    criteria_count += 1
            
            return score / criteria_count if criteria_count > 0 else 0.5
            
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] Spotify 감정 점수 계산 오류: {str(e)}")
            return self._calculate_fallback_spotify_score(track_data, emotion_config)
    
    def _calculate_fallback_spotify_score(self, track_data: Dict, emotion_config: Dict) -> float:
        """오디오 특성을 사용할 수 없을 때 대체 점수 계산"""
        try:
            score = 0.0
            
            # 1. 인기도 기반 점수 (높을수록 좋음)
            popularity = track_data.get('popularity', 0)
            popularity_score = min(popularity / 100, 1.0)
            score += popularity_score * 0.4
            
            # 2. 키워드 매칭 점수
            title = track_data.get('name', '').lower()
            artist = track_data.get('main_artist', '').lower()
            keywords = emotion_config.get('keywords', [])
            
            keyword_matches = 0
            for keyword in keywords:
                if keyword.lower() in title or keyword.lower() in artist:
                    keyword_matches += 1
            
            keyword_score = min(keyword_matches / max(len(keywords), 1), 1.0)
            score += keyword_score * 0.6
            
            return min(score, 1.0)
            
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] 대체 점수 계산 오류: {str(e)}")
            return 0.5
    
    def _calculate_reddit_emotion_score(self, reddit_data: Dict, emotion_config: Dict) -> float:
        """Reddit 키워드 기반 감정 점수"""
        try:
            text = f"{reddit_data.get('title', '')} {reddit_data.get('selftext', '')}"
            keywords = emotion_config['keywords']
            
            score = 0.0
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    score += 1.0
            
            # 정규화 (0-1 범위)
            return min(score / len(keywords), 1.0)
            
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] Reddit 감정 점수 계산 오류: {str(e)}")
            return 0.0
    
    def _extract_song_from_title(self, title: str) -> Optional[Dict]:
        """게시물 제목에서 곡 정보 추출"""
        import re
        
        # 패턴들
        patterns = [
            r'\[([^\]]+)\s*-\s*([^\]]+)\]',  # [Artist - Song]
            r'\"([^\"]+)\s*-\s*([^\"]+)\"',  # "Artist - Song"
            r'([A-Za-z\s]+)\s*-\s*([A-Za-z\s]+)',  # Artist - Song
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return {
                    'artist': match.group(1).strip(),
                    'title': match.group(2).strip()
                }
        
        return None
    
    def _generate_comment_prompts(self, emotion_type: str, tracks: List[Dict]) -> List[Dict]:
        """댓글 유도 문구 생성"""
        emotion_config = self.emotion_categories[emotion_type]
        base_prompt = emotion_config['comment_prompt']
        
        prompts = []
        for i, track in enumerate(tracks[:5]):  # 상위 5곡에 대해
            prompts.append({
                'track_title': track['title'],
                'track_artist': track['artist'],
                'prompt': base_prompt,
                'hashtags': [f"#{emotion_type}", f"#{track['title'].replace(' ', '')}", "#감정공유"]
            })
        
        return prompts
    
    def _analyze_playlist_emotions(self, tracks: List[Dict]) -> Dict:
        """플레이리스트 감정 분석 요약"""
        analysis = {
            'total_tracks': len(tracks),
            'average_emotion_score': 0.0,
            'emotion_distribution': {},
            'top_sources': Counter(),
            'recommendations': []
        }
        
        if tracks:
            # 평균 감정 점수
            scores = [t.get('emotion_score', 0) for t in tracks]
            analysis['average_emotion_score'] = statistics.mean(scores)
            
            # 소스별 분포
            for track in tracks:
                source = track.get('source', 'unknown')
                analysis['top_sources'][source] += 1
            
            # 추천사항
            if analysis['average_emotion_score'] > 0.8:
                analysis['recommendations'].append('매우 높은 감정 일치도를 보이는 완성도 높은 플레이리스트입니다.')
            elif analysis['average_emotion_score'] > 0.6:
                analysis['recommendations'].append('감정에 잘 맞는 곡들로 구성되어 있습니다.')
            else:
                analysis['recommendations'].append('감정 일치도를 높이기 위해 곡 선별을 조정하는 것을 권장합니다.')
        
        return analysis
    
    def get_all_emotion_playlists(self, limit_per_emotion: int = 20) -> Dict:
        """모든 감정별 플레이리스트 생성"""
        try:
            all_playlists = {}
            
            for emotion_type in self.emotion_categories.keys():
                playlist = self.generate_emotion_playlist(emotion_type, limit_per_emotion)
                if playlist['success']:
                    all_playlists[emotion_type] = playlist
            
            result = {
                'success': True,
                'generated_at': datetime.now().isoformat(),
                'total_playlists': len(all_playlists),
                'playlists': all_playlists,
                'emotion_categories': list(self.emotion_categories.keys())
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[EmotionPlaylist] 전체 플레이리스트 생성 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_api_status(self) -> Dict:
        """API 연결 상태 확인"""
        return {
            'reddit_connected': self.reddit_connector.reddit is not None,
            'spotify_connected': self.spotify_connector.spotify is not None,
            'youtube_connected': self.youtube_analyzer is not None,
            'emotion_categories': list(self.emotion_categories.keys()),
            'total_categories': len(self.emotion_categories)
        }