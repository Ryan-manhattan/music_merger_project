#!/usr/bin/env python3
"""
Music Analyzer - YouTube 음악 분석 및 특성 추출 모듈
YouTube Data API v3를 사용한 음악 메타데이터 분석
"""

import re
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

# Google API Client
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Text Processing
from textblob import TextBlob
import nltk

class MusicAnalyzer:
    def __init__(self, api_key: str, console_log=None, enable_db=True):
        """
        YouTube Music Analyzer 초기화
        
        Args:
            api_key: YouTube Data API v3 키
            console_log: 로그 출력 함수
            enable_db: 데이터베이스 저장 활성화 여부
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.console_log = console_log or print
        
        # 데이터베이스 초기화
        self.db_manager = None
        if enable_db:
            try:
                from database import DatabaseManager
                # 프로젝트 루트의 기본 DB 파일 사용
                db_path = os.path.join(os.getcwd(), 'music_analysis.db')
                self.db_manager = DatabaseManager(db_path=db_path, console_log=self.console_log)
                self.console_log("[Music Analyzer] 데이터베이스 연결 완료")
            except Exception as e:
                self.console_log(f"[Music Analyzer] 데이터베이스 연결 실패: {str(e)}")
                self.db_manager = None
        
        # 음악 관련 키워드 사전
        self.music_genres = {
            'pop': ['pop', 'popular', 'mainstream', 'chart', 'hit'],
            'rock': ['rock', 'metal', 'punk', 'alternative', 'indie'],
            'hip_hop': ['hip hop', 'rap', 'trap', 'hiphop', 'rapper'],
            'electronic': ['electronic', 'edm', 'techno', 'house', 'dubstep', 'synth'],
            'jazz': ['jazz', 'blues', 'swing', 'bebop', 'fusion'],
            'classical': ['classical', 'orchestra', 'symphony', 'piano', 'violin'],
            'country': ['country', 'folk', 'bluegrass', 'americana'],
            'reggae': ['reggae', 'ska', 'dub', 'dancehall'],
            'latin': ['latin', 'salsa', 'bachata', 'reggaeton', 'bossa nova'],
            'r&b': ['r&b', 'soul', 'funk', 'motown', 'rnb'],
            'ballad': ['ballad', 'slow', 'romantic', 'love song'],
            'dance': ['dance', 'disco', 'club', 'party', 'upbeat']
        }
        
        self.mood_keywords = {
            'happy': ['happy', 'joy', 'cheerful', 'upbeat', 'positive', 'energetic'],
            'sad': ['sad', 'melancholic', 'depressing', 'emotional', 'tearful'],
            'calm': ['calm', 'peaceful', 'relaxing', 'soothing', 'ambient'],
            'energetic': ['energetic', 'pumping', 'intense', 'powerful', 'dynamic'],
            'romantic': ['romantic', 'love', 'passion', 'intimate', 'tender'],
            'nostalgic': ['nostalgic', 'memories', 'vintage', 'classic', 'retro'],
            'dark': ['dark', 'gothic', 'mysterious', 'haunting', 'eerie'],
            'uplifting': ['uplifting', 'inspiring', 'motivational', 'hopeful']
        }
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        YouTube URL에서 비디오 ID 추출
        
        Args:
            url: YouTube URL
            
        Returns:
            비디오 ID 또는 None
        """
        try:
            parsed_url = urlparse(url)
            
            # youtu.be 형태
            if parsed_url.hostname == 'youtu.be':
                return parsed_url.path[1:]
            
            # youtube.com 형태
            elif parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
                if parsed_url.path == '/watch':
                    return parse_qs(parsed_url.query).get('v', [None])[0]
                elif parsed_url.path.startswith('/embed/'):
                    return parsed_url.path.split('/')[2]
                elif parsed_url.path.startswith('/v/'):
                    return parsed_url.path.split('/')[2]
            
            return None
            
        except Exception as e:
            self.console_log(f"[Music Analyzer] URL 파싱 오류: {str(e)}")
            return None
    
    def get_video_details(self, video_id: str) -> Dict:
        """
        비디오 상세 정보 가져오기
        
        Args:
            video_id: YouTube 비디오 ID
            
        Returns:
            비디오 정보 딕셔너리
        """
        try:
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            
            if not response['items']:
                return {'success': False, 'error': '비디오를 찾을 수 없습니다'}
            
            video = response['items'][0]
            snippet = video['snippet']
            statistics = video['statistics']
            content_details = video['contentDetails']
            
            return {
                'success': True,
                'video_id': video_id,
                'title': snippet['title'],
                'description': snippet['description'],
                'channel_title': snippet['channelTitle'],
                'channel_id': snippet['channelId'],
                'published_at': snippet['publishedAt'],
                'tags': snippet.get('tags', []),
                'category_id': snippet['categoryId'],
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'duration': content_details['duration'],
                'thumbnail': snippet['thumbnails']['high']['url']
            }
            
        except HttpError as e:
            self.console_log(f"[Music Analyzer] YouTube API 오류: {str(e)}")
            return {'success': False, 'error': f'YouTube API 오류: {str(e)}'}
        except Exception as e:
            self.console_log(f"[Music Analyzer] 비디오 정보 가져오기 오류: {str(e)}")
            return {'success': False, 'error': f'오류: {str(e)}'}
    
    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict]:
        """
        비디오 댓글 가져오기
        
        Args:
            video_id: YouTube 비디오 ID
            max_results: 최대 댓글 수
            
        Returns:
            댓글 리스트
        """
        try:
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=max_results,
                order='relevance'
            )
            response = request.execute()
            
            comments = []
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'published_at': comment['publishedAt'],
                    'like_count': comment.get('likeCount', 0)
                })
            
            return comments
            
        except HttpError as e:
            self.console_log(f"[Music Analyzer] 댓글 가져오기 오류: {str(e)}")
            return []
        except Exception as e:
            self.console_log(f"[Music Analyzer] 댓글 처리 오류: {str(e)}")
            return []
    
    def analyze_genre(self, title: str, description: str, tags: List[str]) -> Dict:
        """
        제목, 설명, 태그를 분석하여 장르 추정
        
        Args:
            title: 비디오 제목
            description: 비디오 설명
            tags: 비디오 태그
            
        Returns:
            장르 분석 결과
        """
        text = f"{title} {description} {' '.join(tags)}".lower()
        
        genre_scores = {}
        for genre, keywords in self.music_genres.items():
            score = 0
            for keyword in keywords:
                score += text.count(keyword)
            genre_scores[genre] = score
        
        # 점수가 높은 장르 3개 선택
        top_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        predicted_genres = [genre for genre, score in top_genres if score > 0]
        
        return {
            'predicted_genres': predicted_genres,
            'genre_scores': genre_scores,
            'primary_genre': predicted_genres[0] if predicted_genres else 'unknown'
        }
    
    def analyze_mood(self, title: str, description: str, comments: List[Dict]) -> Dict:
        """
        제목, 설명, 댓글을 분석하여 분위기 추정
        
        Args:
            title: 비디오 제목
            description: 비디오 설명
            comments: 댓글 리스트
            
        Returns:
            분위기 분석 결과
        """
        # 제목과 설명에서 키워드 분석
        text = f"{title} {description}".lower()
        
        mood_scores = {}
        for mood, keywords in self.mood_keywords.items():
            score = 0
            for keyword in keywords:
                score += text.count(keyword)
            mood_scores[mood] = score
        
        # 댓글 감성 분석
        if comments:
            comment_sentiments = []
            for comment in comments[:10]:  # 상위 10개 댓글만 분석
                try:
                    blob = TextBlob(comment['text'])
                    sentiment = blob.sentiment.polarity
                    comment_sentiments.append(sentiment)
                except:
                    continue
            
            if comment_sentiments:
                avg_sentiment = sum(comment_sentiments) / len(comment_sentiments)
                
                # 감성 점수를 분위기에 반영
                if avg_sentiment > 0.3:
                    mood_scores['happy'] += 2
                    mood_scores['uplifting'] += 1
                elif avg_sentiment < -0.3:
                    mood_scores['sad'] += 2
                else:
                    mood_scores['calm'] += 1
        
        # 상위 분위기 3개 선택
        top_moods = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        predicted_moods = [mood for mood, score in top_moods if score > 0]
        
        return {
            'predicted_moods': predicted_moods,
            'mood_scores': mood_scores,
            'primary_mood': predicted_moods[0] if predicted_moods else 'neutral',
            'sentiment_score': avg_sentiment if 'avg_sentiment' in locals() else 0
        }
    
    def parse_duration(self, duration_str: str) -> int:
        """
        ISO 8601 duration을 초로 변환
        
        Args:
            duration_str: PT4M13S 형태의 duration
            
        Returns:
            초 단위 duration
        """
        import re
        
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def extract_artist_info(self, title: str, channel_title: str) -> Dict:
        """
        제목과 채널명에서 아티스트 정보 추출
        
        Args:
            title: 비디오 제목
            channel_title: 채널명
            
        Returns:
            아티스트 정보
        """
        # 일반적인 패턴들
        patterns = [
            r'(.+?)\s*-\s*(.+)',  # Artist - Song
            r'(.+?)\s*:\s*(.+)',  # Artist : Song
            r'(.+?)\s*\|\s*(.+)', # Artist | Song
            r'(.+?)\s*by\s*(.+)', # Song by Artist
        ]
        
        artist = None
        song = None
        
        for pattern in patterns:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                if 'by' in pattern:
                    song, artist = match.groups()
                else:
                    artist, song = match.groups()
                break
        
        if not artist:
            # 채널명을 아티스트로 사용
            artist = channel_title
            song = title
        
        return {
            'artist': artist.strip() if artist else 'Unknown',
            'song': song.strip() if song else title,
            'channel': channel_title
        }
    
    def analyze_youtube_music(self, url: str) -> Dict:
        """
        YouTube 음악 URL을 분석하여 음악 특성 추출
        
        Args:
            url: YouTube URL
            
        Returns:
            음악 분석 결과
        """
        self.console_log(f"[Music Analyzer] 음악 분석 시작: {url}")
        
        try:
            # 비디오 ID 추출
            video_id = self.extract_video_id(url)
            if not video_id:
                return {'success': False, 'error': '올바른 YouTube URL이 아닙니다'}
            
            # 비디오 정보 가져오기
            video_details = self.get_video_details(video_id)
            if not video_details['success']:
                return video_details
            
            # 댓글 가져오기
            comments = self.get_video_comments(video_id)
            
            # 장르 분석
            genre_analysis = self.analyze_genre(
                video_details['title'],
                video_details['description'],
                video_details['tags']
            )
            
            # 분위기 분석
            mood_analysis = self.analyze_mood(
                video_details['title'],
                video_details['description'],
                comments
            )
            
            # 아티스트 정보 추출
            artist_info = self.extract_artist_info(
                video_details['title'],
                video_details['channel_title']
            )
            
            # Duration 파싱
            duration_seconds = self.parse_duration(video_details['duration'])
            
            # 분석 결과 종합
            analysis_result = {
                'success': True,
                'video_info': {
                    'video_id': video_id,
                    'url': url,
                    'title': video_details['title'],
                    'channel': video_details['channel_title'],
                    'duration': duration_seconds,
                    'duration_str': self._format_duration(duration_seconds),
                    'view_count': video_details['view_count'],
                    'like_count': video_details['like_count'],
                    'thumbnail': video_details['thumbnail'],
                    'published_at': video_details['published_at']
                },
                'music_analysis': {
                    'artist': artist_info['artist'],
                    'song': artist_info['song'],
                    'genre': genre_analysis,
                    'mood': mood_analysis,
                    'tags': video_details['tags'],
                    'estimated_bpm': self._estimate_bpm(genre_analysis['primary_genre']),
                    'estimated_key': self._estimate_key(mood_analysis['primary_mood']),
                    'energy_level': self._estimate_energy(mood_analysis['primary_mood'])
                },
                'comments_data': {
                    'comments': comments,
                    'comment_count': len(comments),
                    'sentiment_analysis': {
                        'average_sentiment': mood_analysis.get('sentiment_score', 0),
                        'positive_comments': len([c for c in comments if self._get_comment_sentiment(c['text']) > 0.1]),
                        'negative_comments': len([c for c in comments if self._get_comment_sentiment(c['text']) < -0.1]),
                        'neutral_comments': len([c for c in comments if -0.1 <= self._get_comment_sentiment(c['text']) <= 0.1])
                    }
                },
                'analysis_metadata': {
                    'analyzed_at': datetime.now().isoformat(),
                    'comment_count': len(comments),
                    'api_version': 'v3'
                }
            }
            
            self.console_log(f"[Music Analyzer] 분석 완료: {artist_info['artist']} - {artist_info['song']}")
            self.console_log(f"[Music Analyzer] 장르: {genre_analysis['primary_genre']}, 분위기: {mood_analysis['primary_mood']}")
            
            # 데이터베이스에 저장
            if self.db_manager:
                try:
                    session_id = self.db_manager.save_analysis_result(analysis_result)
                    analysis_result['database'] = {
                        'saved': True,
                        'session_id': session_id
                    }
                    self.console_log(f"[Music Analyzer] 데이터베이스 저장 완료: session_id={session_id}")
                except Exception as e:
                    self.console_log(f"[Music Analyzer] 데이터베이스 저장 실패: {str(e)}")
                    analysis_result['database'] = {
                        'saved': False,
                        'error': str(e)
                    }
            else:
                analysis_result['database'] = {
                    'saved': False,
                    'error': 'Database not initialized'
                }
            
            return analysis_result
            
        except Exception as e:
            self.console_log(f"[Music Analyzer] 분석 중 오류: {str(e)}")
            return {'success': False, 'error': f'분석 중 오류 발생: {str(e)}'}
    
    def _format_duration(self, seconds: int) -> str:
        """초를 mm:ss 형식으로 변환"""
        if seconds < 0:
            return "00:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _estimate_bpm(self, genre: str) -> int:
        """장르를 기반으로 BPM 추정"""
        bpm_ranges = {
            'ballad': 60,
            'pop': 120,
            'rock': 140,
            'hip_hop': 85,
            'electronic': 128,
            'dance': 130,
            'jazz': 120,
            'classical': 100,
            'country': 110,
            'reggae': 90,
            'latin': 120,
            'r&b': 100
        }
        return bpm_ranges.get(genre, 120)
    
    def _estimate_key(self, mood: str) -> str:
        """분위기를 기반으로 키 추정"""
        key_mapping = {
            'happy': 'C Major',
            'sad': 'D Minor',
            'calm': 'A Minor',
            'energetic': 'E Major',
            'romantic': 'F Major',
            'nostalgic': 'G Major',
            'dark': 'B Minor',
            'uplifting': 'G Major'
        }
        return key_mapping.get(mood, 'C Major')
    
    def _estimate_energy(self, mood: str) -> str:
        """분위기를 기반으로 에너지 레벨 추정"""
        energy_mapping = {
            'happy': 'High',
            'sad': 'Low',
            'calm': 'Low',
            'energetic': 'Very High',
            'romantic': 'Medium',
            'nostalgic': 'Medium',
            'dark': 'Medium',
            'uplifting': 'High'
        }
        return energy_mapping.get(mood, 'Medium')
    
    def _get_comment_sentiment(self, text: str) -> float:
        """개별 댓글의 감성 점수 계산"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except:
            return 0.0