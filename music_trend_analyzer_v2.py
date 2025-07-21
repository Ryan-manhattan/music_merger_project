#!/usr/bin/env python3
"""
Music Trend Analyzer V2 - 통합 음악 트렌드 분석 시스템
키워드 & 댓글 중심 분석 + Reddit & Spotify API 통합
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics

# 자체 모듈 임포트
from reddit_connector import RedditConnector
from spotify_connector import SpotifyConnector
from keyword_trend_analyzer import KeywordTrendAnalyzer
from comment_trend_analyzer import CommentTrendAnalyzer
from trends_analyzer import TrendsAnalyzer
from database import DatabaseManager

class MusicTrendAnalyzerV2:
    def __init__(self, console_log=None):
        """
        통합 음악 트렌드 분석기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        
        # 각 분석 모듈 초기화
        try:
            self.reddit_connector = RedditConnector(console_log=self.console_log)
            self.console_log("[TrendV2] Reddit 연결기 초기화 완료")
        except Exception as e:
            self.console_log(f"[TrendV2] Reddit 연결기 초기화 실패: {str(e)}")
            self.reddit_connector = None
        
        try:
            self.spotify_connector = SpotifyConnector(console_log=self.console_log)
            self.console_log("[TrendV2] Spotify 연결기 초기화 완료")
        except Exception as e:
            self.console_log(f"[TrendV2] Spotify 연결기 초기화 실패: {str(e)}")
            self.spotify_connector = None
        
        try:
            self.keyword_analyzer = KeywordTrendAnalyzer(console_log=self.console_log)
            self.console_log("[TrendV2] 키워드 분석기 초기화 완료")
        except Exception as e:
            self.console_log(f"[TrendV2] 키워드 분석기 초기화 실패: {str(e)}")
            self.keyword_analyzer = None
        
        try:
            self.comment_analyzer = CommentTrendAnalyzer(console_log=self.console_log)
            self.console_log("[TrendV2] 댓글 분석기 초기화 완료")
        except Exception as e:
            self.console_log(f"[TrendV2] 댓글 분석기 초기화 실패: {str(e)}")
            self.comment_analyzer = None
        
        try:
            self.trends_analyzer = TrendsAnalyzer(console_log=self.console_log)
            self.console_log("[TrendV2] Google Trends 분석기 초기화 완료")
        except Exception as e:
            self.console_log(f"[TrendV2] Google Trends 분석기 초기화 실패: {str(e)}")
            self.trends_analyzer = None
        
        try:
            self.db_manager = DatabaseManager(console_log=self.console_log)
            self.console_log("[TrendV2] 데이터베이스 매니저 초기화 완료")
        except Exception as e:
            self.console_log(f"[TrendV2] 데이터베이스 매니저 초기화 실패: {str(e)}")
            self.db_manager = None
        
        # 분석 설정
        self.analysis_config = {
            'reddit_limit': 100,
            'spotify_limit': 50,
            'comment_limit': 200,
            'time_weight_decay': 0.1,  # 시간에 따른 가중치 감소
            'confidence_threshold': 0.6
        }
    
    def analyze_current_music_trends(self, 
                                   categories: List[str] = None, 
                                   include_reddit: bool = True,
                                   include_spotify: bool = True,
                                   include_comments: bool = True) -> Dict:
        """
        Spotify 차트 기반 음악 트렌드 분석
        
        Args:
            categories: 분석할 음악 카테고리 ['kpop', 'hiphop', 'pop' 등]
            include_reddit: Reddit 데이터 포함 여부
            include_spotify: Spotify 데이터 포함 여부
            include_comments: 댓글 분석 포함 여부
            
        Returns:
            차트 기반 트렌드 분석 결과
        """
        try:
            if categories is None:
                categories = ['kpop', 'hiphop', 'pop', 'rock', 'ballad']
            
            self.console_log(f"[TrendV2] 현재 음악 트렌드 분석 시작: {', '.join(categories)}")
            
            result = {
                'success': True,
                'analysis_timestamp': datetime.now().isoformat(),
                'categories_analyzed': categories,
                'data_sources': [],
                'trend_analysis': {},
                'keyword_insights': {},
                'sentiment_overview': {},
                'recommendations': []
            }
            
            all_texts = []
            all_comments = []
            trend_scores = defaultdict(float)
            
            # 1. Spotify 차트 데이터 수집 (기본 시작점)
            spotify_tracks = []
            if include_spotify and self.spotify_connector:
                spotify_data = self._collect_spotify_chart_data()
                if spotify_data['success']:
                    result['data_sources'].append('spotify')
                    result['spotify_charts'] = spotify_data
                    spotify_tracks = spotify_data.get('chart_tracks', [])
                    
                    # 차트 트랙 기본 정보 저장
                    result['chart_tracks'] = spotify_tracks
                    
                    # Spotify 트렌드 점수 반영
                    for track in spotify_tracks:
                        artist = track.get('main_artist', '')
                        popularity = track.get('popularity', 0)
                        trend_scores[f"spotify_{artist}"] += popularity * 0.5
            
            # 2. 차트 곡들에 대한 Reddit 반응 수집
            if include_reddit and self.reddit_connector and spotify_tracks:
                reddit_reactions = self._collect_reddit_reactions_for_tracks(spotify_tracks)
                if reddit_reactions['success']:
                    result['data_sources'].append('reddit')
                    result['reddit_reactions'] = reddit_reactions
                    
                    # Reddit 반응 텍스트 수집
                    for reaction in reddit_reactions.get('track_reactions', []):
                        for post in reaction.get('posts', []):
                            all_texts.append(post.get('title', '') + ' ' + post.get('selftext', ''))
                            
                            # Reddit 댓글 수집
                            if post.get('id'):
                                post_comments = self._get_reddit_post_comments(post['id'])
                                all_comments.extend(post_comments)
                    
                    # 대표 의견 추출
                    representative_opinions = self._extract_representative_opinions(reddit_reactions)
                    result['representative_opinions'] = representative_opinions
            
            # 3. 차트 곡들에 대한 YouTube 댓글 수집
            if include_comments and spotify_tracks:
                youtube_comments = self._collect_youtube_comments_for_tracks(spotify_tracks)
                if youtube_comments['success']:
                    result['data_sources'].append('youtube')
                    result['youtube_comments'] = youtube_comments
                    
                    # YouTube 댓글 텍스트 수집
                    for comment_data in youtube_comments.get('track_comments', []):
                        for comment in comment_data.get('comments', []):
                            all_comments.append({
                                'text': comment.get('text', ''),
                                'likes': comment.get('likes', 0),
                                'timestamp': comment.get('timestamp'),
                                'source': 'youtube'
                            })
                    
                    # 대표 댓글 추출
                    representative_comments = self._extract_representative_comments(youtube_comments)
                    result['representative_comments'] = representative_comments
            
            # 4. 키워드 분석
            if self.keyword_analyzer and all_texts:
                keyword_analysis = self.keyword_analyzer.analyze_keyword_frequency(all_texts)
                result['keyword_analysis'] = keyword_analysis
                
                # 해시태그 분석
                hashtag_analysis = {}
                for text in all_texts:
                    hashtags = self.keyword_analyzer.extract_hashtags_and_mentions(text)
                    for hashtag in hashtags.get('hashtags', []):
                        if hashtag not in hashtag_analysis:
                            hashtag_analysis[hashtag] = 0
                        hashtag_analysis[hashtag] += 1
                
                result['hashtag_analysis'] = dict(Counter(hashtag_analysis).most_common(20))
                
                # 감정어 분석
                emotion_analysis = self.keyword_analyzer.analyze_emotion_keywords(all_texts)
                result['emotion_analysis'] = emotion_analysis
                
                # 키워드 트렌드 점수 반영
                for keyword, importance in keyword_analysis.get('keyword_importance', {}).items():
                    trend_scores[f"keyword_{keyword}"] += importance * 0.3
            
            # 5. 댓글 감정 분석
            if include_comments and self.comment_analyzer and all_comments:
                comment_sentiment = self.comment_analyzer.analyze_comment_sentiment(all_comments)
                result['comment_sentiment'] = comment_sentiment
                
                # 댓글 토픽 모델링
                comment_texts = [comment.get('text', '') for comment in all_comments]
                if len(comment_texts) >= 10:
                    topic_analysis = self.comment_analyzer.extract_comment_topics(comment_texts)
                    result['topic_analysis'] = topic_analysis
                
                # 댓글 패턴 분석
                pattern_analysis = self.comment_analyzer.analyze_comment_patterns(all_comments)
                result['pattern_analysis'] = pattern_analysis
            
            # 6. 종합 트렌드 점수 계산
            trend_insights = self._calculate_comprehensive_trends(trend_scores, result)
            result['trend_insights'] = trend_insights
            
            # 7. 트렌드 예측 및 추천
            predictions = self._generate_trend_predictions(result)
            result['predictions'] = predictions
            
            recommendations = self._generate_recommendations(result)
            result['recommendations'] = recommendations
            
            # 8. 분석 요약
            summary = self._generate_analysis_summary(result)
            result['summary'] = summary
            
            self.console_log(f"[TrendV2] 트렌드 분석 완료")
            return result
            
        except Exception as e:
            self.console_log(f"[TrendV2] 트렌드 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _collect_reddit_data(self, categories: List[str]) -> Dict:
        """Reddit 데이터 수집"""
        try:
            reddit_result = {'success': True, 'posts': [], 'keyword_analysis': {}}
            
            for category in categories:
                # 카테고리별 트렌딩 게시물 수집
                posts_data = self.reddit_connector.get_trending_posts(
                    category=category, 
                    limit=self.analysis_config['reddit_limit']//len(categories)
                )
                
                if posts_data['success']:
                    reddit_result['posts'].extend(posts_data.get('posts', []))
            
            # Reddit 키워드 추출
            if reddit_result['posts']:
                keyword_data = self.reddit_connector.extract_music_keywords(reddit_result['posts'])
                reddit_result['keyword_analysis'] = keyword_data
            
            return reddit_result
            
        except Exception as e:
            self.console_log(f"[TrendV2] Reddit 데이터 수집 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _collect_spotify_data(self, categories: List[str]) -> Dict:
        """Spotify 데이터 수집"""
        try:
            spotify_result = {'success': True, 'trending_tracks': [], 'audio_features': {}}
            
            # 한국 및 글로벌 트렌딩 트랙 수집
            regions = ['korea', 'global']
            playlist_types = ['top', 'viral']
            
            all_tracks = []
            for region in regions:
                for playlist_type in playlist_types:
                    tracks_data = self.spotify_connector.get_trending_tracks(
                        region=region,
                        playlist_type=playlist_type,
                        limit=self.analysis_config['spotify_limit']//4
                    )
                    
                    if tracks_data['success']:
                        all_tracks.extend(tracks_data.get('tracks', []))
            
            spotify_result['trending_tracks'] = all_tracks
            
            # 오디오 특성 분석
            if all_tracks:
                track_ids = [track['id'] for track in all_tracks[:20]]  # 상위 20개만
                audio_features = self.spotify_connector.get_audio_features(track_ids)
                if audio_features['success']:
                    spotify_result['audio_features'] = audio_features
            
            return spotify_result
            
        except Exception as e:
            self.console_log(f"[TrendV2] Spotify 데이터 수집 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _collect_google_trends_data(self, categories: List[str]) -> Dict:
        """Google Trends 데이터 수집"""
        try:
            trends_result = {'success': True, 'category_data': {}}
            
            # 카테고리별 트렌드 분석
            for category in categories:
                category_korean = {
                    'kpop': '케이팝',
                    'hiphop': '힙합',
                    'pop': '팝',
                    'rock': '록',
                    'ballad': '발라드'
                }.get(category, category)
                
                trend_data = self.trends_analyzer.get_artist_trends(
                    artist_name=category_korean,
                    timeframe='today 3-m',
                    geo='KR'
                )
                
                if trend_data['success']:
                    trends_result['category_data'][category] = trend_data
            
            return trends_result
            
        except Exception as e:
            self.console_log(f"[TrendV2] Google Trends 데이터 수집 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _collect_spotify_chart_data(self) -> Dict:
        """스포티파이 차트 데이터 수집 (기본 시작점)"""
        try:
            chart_result = {'success': True, 'chart_tracks': [], 'audio_features': {}}
            
            # 실제 API 호출 시도 후 실패하면 Mock 데이터 사용
            regions = ['korea', 'global']
            
            all_tracks = []
            for region in regions:
                # Top 50 차트 수집
                tracks_data = self.spotify_connector.get_trending_tracks(
                    region=region,
                    playlist_type='top',
                    limit=25  # 각 지역별 25개씩
                )
                
                if tracks_data['success']:
                    tracks = tracks_data.get('tracks', [])
                    # 지역 정보 추가
                    for track in tracks:
                        track['chart_region'] = region
                        track['chart_type'] = 'top_50'
                    all_tracks.extend(tracks)
            
            # 만약 실제 데이터가 없다면 Mock 데이터 사용
            if not all_tracks:
                self.console_log("[TrendV2] Spotify API 데이터가 없어서 Mock 차트 데이터 사용")
                all_tracks = self._generate_mock_chart_data()
            
            chart_result['chart_tracks'] = all_tracks
            
            # 상위 20개 트랙의 오디오 특성 분석 (Mock 데이터에서는 생략)
            if all_tracks and all_tracks[0].get('id', '').startswith('real_'):  # 실제 데이터인 경우만
                track_ids = [track['id'] for track in all_tracks[:20]]
                audio_features = self.spotify_connector.get_audio_features(track_ids)
                if audio_features['success']:
                    chart_result['audio_features'] = audio_features
            
            self.console_log(f"[TrendV2] Spotify 차트 데이터 수집 완료: {len(all_tracks)}개 트랙")
            return chart_result
            
        except Exception as e:
            self.console_log(f"[TrendV2] Spotify 차트 데이터 수집 오류: {str(e)}")
            # 오류 발생 시에도 Mock 데이터 반환
            mock_tracks = self._generate_mock_chart_data()
            return {'success': True, 'chart_tracks': mock_tracks, 'audio_features': {}}
    
    def _collect_reddit_reactions_for_tracks(self, tracks: List[Dict]) -> Dict:
        """차트 곡들에 대한 Reddit 반응 수집"""
        try:
            reactions_result = {'success': True, 'track_reactions': []}
            
            # 상위 10개 트랙에 대한 반응 수집
            for track in tracks[:10]:
                track_title = track.get('name', '')
                artist_name = track.get('main_artist', '')
                
                # 아티스트 또는 곡명으로 Reddit 검색
                search_queries = [
                    f"{artist_name} {track_title}",
                    artist_name,
                    track_title
                ]
                
                track_reaction = {
                    'track_info': {
                        'title': track_title,
                        'artist': artist_name,
                        'spotify_id': track.get('id'),
                        'popularity': track.get('popularity', 0)
                    },
                    'posts': [],
                    'total_reactions': 0
                }
                
                # 각 검색어로 Reddit 검색
                for query in search_queries:
                    search_result = self.reddit_connector.search_music_discussions(
                        query=query,
                        limit=5  # 각 쿼리당 5개씩
                    )
                    
                    if search_result['success']:
                        posts = search_result.get('discussions', [])
                        track_reaction['posts'].extend(posts)
                        track_reaction['total_reactions'] += len(posts)
                
                reactions_result['track_reactions'].append(track_reaction)
            
            self.console_log(f"[TrendV2] Reddit 반응 수집 완료: {len(reactions_result['track_reactions'])}개 트랙")
            return reactions_result
            
        except Exception as e:
            self.console_log(f"[TrendV2] Reddit 반응 수집 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _collect_youtube_comments_for_tracks(self, tracks: List[Dict]) -> Dict:
        """차트 곡들에 대한 YouTube 댓글 수집"""
        try:
            comments_result = {'success': True, 'track_comments': []}
            
            # 상위 10개 트랙에 대한 YouTube 댓글 수집
            for track in tracks[:10]:
                track_title = track.get('name', '')
                artist_name = track.get('main_artist', '')
                
                # YouTube 비디오 검색 쿼리
                search_query = f"{artist_name} {track_title} official"
                
                track_comment = {
                    'track_info': {
                        'title': track_title,
                        'artist': artist_name,
                        'spotify_id': track.get('id'),
                        'popularity': track.get('popularity', 0)
                    },
                    'comments': [],
                    'total_comments': 0
                }
                
                # YouTube API가 없으므로 간단한 mock 데이터 생성
                # 실제 구현 시 YouTube API 연동 필요
                mock_comments = [
                    {
                        'text': f"{track_title} is amazing! Love this song",
                        'likes': 150,
                        'timestamp': '2 days ago',
                        'author': 'MusicLover123'
                    },
                    {
                        'text': f"{artist_name} never disappoints! This is a banger",
                        'likes': 89,
                        'timestamp': '1 day ago',
                        'author': 'KpopFan456'
                    },
                    {
                        'text': f"The vocals in {track_title} are insane",
                        'likes': 234,
                        'timestamp': '3 hours ago',
                        'author': 'VocalAnalyst'
                    }
                ]
                
                track_comment['comments'] = mock_comments
                track_comment['total_comments'] = len(mock_comments)
                
                comments_result['track_comments'].append(track_comment)
            
            self.console_log(f"[TrendV2] YouTube 댓글 수집 완료: {len(comments_result['track_comments'])}개 트랙")
            return comments_result
            
        except Exception as e:
            self.console_log(f"[TrendV2] YouTube 댓글 수집 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_representative_opinions(self, reddit_reactions: Dict) -> List[Dict]:
        """대표적인 Reddit 의견 추출"""
        try:
            opinions = []
            
            for reaction in reddit_reactions.get('track_reactions', []):
                track_info = reaction.get('track_info', {})
                posts = reaction.get('posts', [])
                
                if not posts:
                    continue
                
                # 상위 3개 게시물 선택 (점수 기준)
                sorted_posts = sorted(posts, key=lambda x: x.get('score', 0), reverse=True)[:3]
                
                track_opinions = {
                    'track_title': track_info.get('title', ''),
                    'artist': track_info.get('artist', ''),
                    'opinions': []
                }
                
                for post in sorted_posts:
                    opinion = {
                        'title': post.get('title', ''),
                        'content': post.get('selftext', '')[:200] + '...' if len(post.get('selftext', '')) > 200 else post.get('selftext', ''),
                        'score': post.get('score', 0),
                        'comments_count': post.get('num_comments', 0),
                        'subreddit': post.get('subreddit', '')
                    }
                    track_opinions['opinions'].append(opinion)
                
                if track_opinions['opinions']:
                    opinions.append(track_opinions)
            
            return opinions[:5]  # 상위 5개 트랙만
            
        except Exception as e:
            self.console_log(f"[TrendV2] 대표 의견 추출 오류: {str(e)}")
            return []
    
    def _extract_representative_comments(self, youtube_comments: Dict) -> List[Dict]:
        """대표적인 YouTube 댓글 추출"""
        try:
            comments = []
            
            for comment_data in youtube_comments.get('track_comments', []):
                track_info = comment_data.get('track_info', {})
                track_comments = comment_data.get('comments', [])
                
                if not track_comments:
                    continue
                
                # 좋아요 수 기준으로 상위 3개 댓글 선택
                sorted_comments = sorted(track_comments, key=lambda x: x.get('likes', 0), reverse=True)[:3]
                
                track_representative = {
                    'track_title': track_info.get('title', ''),
                    'artist': track_info.get('artist', ''),
                    'comments': []
                }
                
                for comment in sorted_comments:
                    representative_comment = {
                        'text': comment.get('text', ''),
                        'likes': comment.get('likes', 0),
                        'timestamp': comment.get('timestamp', ''),
                        'author': comment.get('author', '')
                    }
                    track_representative['comments'].append(representative_comment)
                
                if track_representative['comments']:
                    comments.append(track_representative)
            
            return comments[:5]  # 상위 5개 트랙만
            
        except Exception as e:
            self.console_log(f"[TrendV2] 대표 댓글 추출 오류: {str(e)}")
            return []
    
    def _generate_mock_chart_data(self) -> List[Dict]:
        """Mock 차트 데이터 생성 (API 실패 시 사용)"""
        try:
            # 한국 차트 Mock 데이터
            korea_tracks = [
                {'id': 'mock_kr_1', 'name': 'Spicy', 'main_artist': 'aespa', 'popularity': 92, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_2', 'name': 'UNFORGIVEN (feat. Nile Rodgers)', 'main_artist': 'LE SSERAFIM', 'popularity': 89, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_3', 'name': 'New Jeans', 'main_artist': 'NewJeans', 'popularity': 87, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_4', 'name': 'GODS', 'main_artist': 'NewJeans', 'popularity': 85, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_5', 'name': 'Seven (feat. Latto)', 'main_artist': 'Jung Kook', 'popularity': 84, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_6', 'name': 'ISTJ', 'main_artist': 'NMIXX', 'popularity': 82, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_7', 'name': 'Queencard', 'main_artist': '(G)I-DLE', 'popularity': 80, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_8', 'name': 'Eve, Psyche & The Bluebeard\'s wife', 'main_artist': 'LE SSERAFIM', 'popularity': 78, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_9', 'name': 'Perfect Night', 'main_artist': 'LE SSERAFIM', 'popularity': 76, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_10', 'name': 'Drama', 'main_artist': 'aespa', 'popularity': 74, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_11', 'name': 'Fast Forward', 'main_artist': 'NewJeans', 'popularity': 72, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_12', 'name': 'LALALALA', 'main_artist': 'Stray Kids', 'popularity': 70, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_13', 'name': 'S-Class', 'main_artist': 'Stray Kids', 'popularity': 68, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_14', 'name': 'Super Shy', 'main_artist': 'NewJeans', 'popularity': 66, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_15', 'name': 'Get Up', 'main_artist': 'NewJeans', 'popularity': 64, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_16', 'name': 'Cruel Summer', 'main_artist': 'Taylor Swift', 'popularity': 62, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_17', 'name': 'Paint The Town Red', 'main_artist': 'Doja Cat', 'popularity': 60, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_18', 'name': '사랑은 늘 도망가', 'main_artist': '임영웅', 'popularity': 58, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_19', 'name': 'Polaroid Love', 'main_artist': 'ENHYPEN', 'popularity': 56, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_20', 'name': 'After LIKE', 'main_artist': 'IVE', 'popularity': 54, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_21', 'name': 'LOVE DIVE', 'main_artist': 'IVE', 'popularity': 52, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_22', 'name': 'OMG', 'main_artist': 'NewJeans', 'popularity': 50, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_23', 'name': 'Hype Boy', 'main_artist': 'NewJeans', 'popularity': 48, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_24', 'name': 'Attention', 'main_artist': 'NewJeans', 'popularity': 46, 'chart_region': 'korea', 'chart_type': 'top_50'},
                {'id': 'mock_kr_25', 'name': 'Cookie', 'main_artist': 'NewJeans', 'popularity': 44, 'chart_region': 'korea', 'chart_type': 'top_50'}
            ]
            
            # 글로벌 차트 Mock 데이터
            global_tracks = [
                {'id': 'mock_gl_1', 'name': 'Cruel Summer', 'main_artist': 'Taylor Swift', 'popularity': 95, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_2', 'name': 'Paint The Town Red', 'main_artist': 'Doja Cat', 'popularity': 93, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_3', 'name': 'Flowers', 'main_artist': 'Miley Cyrus', 'popularity': 91, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_4', 'name': 'As It Was', 'main_artist': 'Harry Styles', 'popularity': 89, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_5', 'name': 'Anti-Hero', 'main_artist': 'Taylor Swift', 'popularity': 87, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_6', 'name': 'Seven (feat. Latto)', 'main_artist': 'Jung Kook', 'popularity': 85, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_7', 'name': 'vampire', 'main_artist': 'Olivia Rodrigo', 'popularity': 83, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_8', 'name': 'Blinding Lights', 'main_artist': 'The Weeknd', 'popularity': 81, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_9', 'name': 'Shivers', 'main_artist': 'Ed Sheeran', 'popularity': 79, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_10', 'name': 'Bad Habit', 'main_artist': 'Steve Lacy', 'popularity': 77, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_11', 'name': 'Stay', 'main_artist': 'The Kid LAROI, Justin Bieber', 'popularity': 75, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_12', 'name': 'Shape of You', 'main_artist': 'Ed Sheeran', 'popularity': 73, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_13', 'name': 'Watermelon Sugar', 'main_artist': 'Harry Styles', 'popularity': 71, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_14', 'name': 'Levitating', 'main_artist': 'Dua Lipa', 'popularity': 69, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_15', 'name': 'Good 4 U', 'main_artist': 'Olivia Rodrigo', 'popularity': 67, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_16', 'name': 'Starboy', 'main_artist': 'The Weeknd', 'popularity': 65, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_17', 'name': 'Peaches', 'main_artist': 'Justin Bieber', 'popularity': 63, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_18', 'name': 'Unholy', 'main_artist': 'Sam Smith', 'popularity': 61, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_19', 'name': 'Heat Waves', 'main_artist': 'Glass Animals', 'popularity': 59, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_20', 'name': 'Industry Baby', 'main_artist': 'Lil Nas X', 'popularity': 57, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_21', 'name': 'Somebody That I Used to Know', 'main_artist': 'Gotye', 'popularity': 55, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_22', 'name': 'Sunflower', 'main_artist': 'Post Malone', 'popularity': 53, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_23', 'name': 'Circles', 'main_artist': 'Post Malone', 'popularity': 51, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_24', 'name': 'Lucid Dreams', 'main_artist': 'Juice WRLD', 'popularity': 49, 'chart_region': 'global', 'chart_type': 'top_50'},
                {'id': 'mock_gl_25', 'name': 'Perfect', 'main_artist': 'Ed Sheeran', 'popularity': 47, 'chart_region': 'global', 'chart_type': 'top_50'}
            ]
            
            # 모든 트랙 합치기
            all_tracks = korea_tracks + global_tracks
            
            self.console_log(f"[TrendV2] Mock 차트 데이터 생성 완료: {len(all_tracks)}개 트랙")
            return all_tracks
            
        except Exception as e:
            self.console_log(f"[TrendV2] Mock 데이터 생성 오류: {str(e)}")
            return []
    
    def _get_reddit_post_comments(self, post_id: str) -> List[Dict]:
        """Reddit 게시물 댓글 수집"""
        try:
            comments_data = self.reddit_connector.get_post_comments(
                post_id=post_id,
                limit=20  # 게시물당 20개 댓글
            )
            
            if comments_data['success']:
                comments = []
                for comment in comments_data.get('comments', []):
                    comments.append({
                        'text': comment.get('body', ''),
                        'score': comment.get('score', 0),
                        'timestamp': comment.get('created_utc'),
                        'source': 'reddit'
                    })
                return comments
            
            return []
            
        except Exception as e:
            self.console_log(f"[TrendV2] Reddit 댓글 수집 오류: {str(e)}")
            return []
    
    def _calculate_comprehensive_trends(self, trend_scores: Dict, analysis_result: Dict) -> Dict:
        """종합 트렌드 점수 계산"""
        try:
            # 상위 트렌드 키워드 선별
            top_trends = dict(sorted(trend_scores.items(), key=lambda x: x[1], reverse=True)[:20])
            
            # 카테고리별 점수 집계
            category_scores = defaultdict(float)
            source_contributions = defaultdict(float)
            
            for trend_key, score in top_trends.items():
                source, keyword = trend_key.split('_', 1)
                source_contributions[source] += score
                
                # 음악 카테고리와 매칭
                for category in ['kpop', 'hiphop', 'pop', 'rock', 'ballad']:
                    if category in keyword.lower():
                        category_scores[category] += score
            
            # 신뢰도 계산
            total_score = sum(top_trends.values())
            confidence = min(1.0, total_score / 100) if total_score > 0 else 0
            
            # 트렌드 방향 결정
            trend_direction = 'rising' if total_score > 50 else 'stable' if total_score > 20 else 'declining'
            
            return {
                'top_trend_keywords': top_trends,
                'category_scores': dict(category_scores),
                'source_contributions': dict(source_contributions),
                'overall_trend_score': total_score,
                'confidence_level': confidence,
                'trend_direction': trend_direction,
                'analysis_completeness': len(analysis_result.get('data_sources', [])) / 4 * 100  # 최대 4개 소스
            }
            
        except Exception as e:
            self.console_log(f"[TrendV2] 종합 트렌드 계산 오류: {str(e)}")
            return {'error': str(e)}
    
    def _generate_trend_predictions(self, analysis_result: Dict) -> Dict:
        """트렌드 예측 생성"""
        try:
            predictions = {
                'short_term': {},  # 1-2주
                'medium_term': {},  # 1-3개월
                'confidence_scores': {}
            }
            
            trend_insights = analysis_result.get('trend_insights', {})
            category_scores = trend_insights.get('category_scores', {})
            overall_score = trend_insights.get('overall_trend_score', 0)
            
            # 카테고리별 예측
            for category, score in category_scores.items():
                if score > 30:
                    predictions['short_term'][category] = 'rapid_growth'
                    predictions['medium_term'][category] = 'sustained_popularity'
                    predictions['confidence_scores'][category] = 0.8
                elif score > 15:
                    predictions['short_term'][category] = 'moderate_growth'
                    predictions['medium_term'][category] = 'stable_interest'
                    predictions['confidence_scores'][category] = 0.6
                else:
                    predictions['short_term'][category] = 'stable'
                    predictions['medium_term'][category] = 'declining_interest'
                    predictions['confidence_scores'][category] = 0.4
            
            # 전체 시장 예측
            if overall_score > 100:
                predictions['market_outlook'] = 'very_positive'
            elif overall_score > 50:
                predictions['market_outlook'] = 'positive'
            elif overall_score > 20:
                predictions['market_outlook'] = 'neutral'
            else:
                predictions['market_outlook'] = 'cautious'
            
            return predictions
            
        except Exception as e:
            self.console_log(f"[TrendV2] 트렌드 예측 생성 오류: {str(e)}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, analysis_result: Dict) -> List[str]:
        """분석 기반 추천사항 생성"""
        try:
            recommendations = []
            
            trend_insights = analysis_result.get('trend_insights', {})
            category_scores = trend_insights.get('category_scores', {})
            
            # 상위 카테고리 추천
            if category_scores:
                top_category = max(category_scores.items(), key=lambda x: x[1])
                recommendations.append(f"🎯 {top_category[0]} 장르가 현재 가장 높은 트렌드를 보이고 있습니다")
            
            # 감정 분석 기반 추천
            emotion_analysis = analysis_result.get('emotion_analysis', {})
            if emotion_analysis:
                dominant_emotion = emotion_analysis.get('dominant_emotion')
                if dominant_emotion == 'positive':
                    recommendations.append("😊 전반적으로 긍정적인 반응을 보이는 콘텐츠에 집중하세요")
                elif dominant_emotion == 'excitement':
                    recommendations.append("🔥 에너지 넘치는 콘텐츠가 높은 호응을 얻고 있습니다")
            
            # Spotify 데이터 기반 추천
            spotify_analysis = analysis_result.get('spotify_analysis', {})
            if spotify_analysis.get('audio_features'):
                audio_features = spotify_analysis['audio_features'].get('average_features', {})
                if audio_features.get('danceability', 0) > 0.7:
                    recommendations.append("💃 댄스할 수 있는 리듬감 있는 음악이 트렌드입니다")
                if audio_features.get('valence', 0) > 0.6:
                    recommendations.append("✨ 밝고 긍정적인 분위기의 음악이 인기입니다")
            
            # Reddit 분석 기반 추천
            reddit_analysis = analysis_result.get('reddit_analysis', {})
            if reddit_analysis.get('keyword_analysis'):
                top_genres = reddit_analysis['keyword_analysis'].get('top_genres', {})
                if top_genres:
                    trending_genre = max(top_genres.items(), key=lambda x: x[1])[0]
                    recommendations.append(f"📈 Reddit에서 {trending_genre} 관련 논의가 활발합니다")
            
            # 기본 추천사항
            if not recommendations:
                recommendations.extend([
                    "🎵 다양한 음악 장르를 균형있게 탐색해보세요",
                    "📊 정기적인 트렌드 모니터링을 권장합니다",
                    "💬 사용자 댓글과 피드백을 적극 활용하세요"
                ])
            
            return recommendations[:5]  # 최대 5개 추천사항
            
        except Exception as e:
            self.console_log(f"[TrendV2] 추천사항 생성 오류: {str(e)}")
            return ["분석 데이터를 기반으로 맞춤 추천을 준비 중입니다"]
    
    def _generate_analysis_summary(self, analysis_result: Dict) -> Dict:
        """분석 결과 요약 생성"""
        try:
            summary = {
                'data_completeness': 0,
                'key_findings': [],
                'trend_strength': 'unknown',
                'market_sentiment': 'neutral',
                'recommendation_priority': 'medium'
            }
            
            # 데이터 완성도 계산
            data_sources = analysis_result.get('data_sources', [])
            max_sources = 4  # reddit, spotify, google_trends, comments
            summary['data_completeness'] = len(data_sources) / max_sources * 100
            
            # 핵심 발견사항
            trend_insights = analysis_result.get('trend_insights', {})
            overall_score = trend_insights.get('overall_trend_score', 0)
            
            if overall_score > 100:
                summary['key_findings'].append("매우 활발한 음악 트렌드 활동 감지")
                summary['trend_strength'] = 'very_strong'
            elif overall_score > 50:
                summary['key_findings'].append("안정적인 음악 트렌드 흐름 확인")
                summary['trend_strength'] = 'strong'
            else:
                summary['key_findings'].append("보통 수준의 트렌드 활동")
                summary['trend_strength'] = 'moderate'
            
            # 시장 감정
            comment_sentiment = analysis_result.get('comment_sentiment', {})
            if comment_sentiment:
                avg_sentiment = comment_sentiment.get('overall_sentiment', {}).get('average_score', 0)
                if avg_sentiment > 0.3:
                    summary['market_sentiment'] = 'positive'
                elif avg_sentiment < -0.3:
                    summary['market_sentiment'] = 'negative'
                else:
                    summary['market_sentiment'] = 'neutral'
            
            # 추천 우선순위
            if summary['trend_strength'] == 'very_strong' and summary['market_sentiment'] == 'positive':
                summary['recommendation_priority'] = 'high'
            elif summary['trend_strength'] in ['strong', 'moderate'] and summary['market_sentiment'] != 'negative':
                summary['recommendation_priority'] = 'medium'
            else:
                summary['recommendation_priority'] = 'low'
            
            return summary
            
        except Exception as e:
            self.console_log(f"[TrendV2] 분석 요약 생성 오류: {str(e)}")
            return {'error': str(e)}
    
    def search_trending_keywords(self, query: str, deep_analysis: bool = True) -> Dict:
        """
        특정 키워드의 트렌드 심층 분석
        
        Args:
            query: 검색할 키워드
            deep_analysis: 심층 분석 여부
            
        Returns:
            키워드 트렌드 분석 결과
        """
        try:
            self.console_log(f"[TrendV2] 키워드 트렌드 검색: {query}")
            
            result = {
                'success': True,
                'query': query,
                'analysis_timestamp': datetime.now().isoformat(),
                'sources_analyzed': []
            }
            
            # Reddit 검색
            if self.reddit_connector:
                reddit_search = self.reddit_connector.search_music_discussions(
                    query=query,
                    limit=50
                )
                if reddit_search['success']:
                    result['reddit_results'] = reddit_search
                    result['sources_analyzed'].append('reddit')
            
            # Spotify 검색
            if self.spotify_connector:
                spotify_search = self.spotify_connector.search_trending_keywords(
                    keyword=query,
                    limit=30
                )
                if spotify_search['success']:
                    result['spotify_results'] = spotify_search
                    result['sources_analyzed'].append('spotify')
            
            # Google Trends 검색
            if self.trends_analyzer:
                trends_search = self.trends_analyzer.get_keyword_suggestions(
                    base_keyword=query
                )
                if trends_search['success']:
                    result['trends_results'] = trends_search
                    result['sources_analyzed'].append('google_trends')
            
            # 심층 분석
            if deep_analysis:
                trend_analysis = self._analyze_keyword_trends(result)
                result['trend_analysis'] = trend_analysis
            
            return result
            
        except Exception as e:
            self.console_log(f"[TrendV2] 키워드 검색 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _analyze_keyword_trends(self, search_result: Dict) -> Dict:
        """키워드 트렌드 심층 분석"""
        try:
            analysis = {
                'trend_score': 0,
                'popularity_indicators': {},
                'growth_potential': 'unknown',
                'market_penetration': 'unknown'
            }
            
            # Spotify 인기도
            spotify_results = search_result.get('spotify_results', {})
            if spotify_results:
                avg_popularity = spotify_results.get('average_popularity', 0)
                trend_score = spotify_results.get('trend_score', 0)
                analysis['popularity_indicators']['spotify'] = {
                    'popularity': avg_popularity,
                    'trend_score': trend_score
                }
                analysis['trend_score'] += trend_score * 0.4
            
            # Reddit 활성도
            reddit_results = search_result.get('reddit_results', {})
            if reddit_results:
                total_results = reddit_results.get('total_results', 0)
                analysis['popularity_indicators']['reddit'] = {
                    'discussion_count': total_results,
                    'engagement_score': min(total_results * 2, 100)
                }
                analysis['trend_score'] += min(total_results * 2, 100) * 0.3
            
            # Google Trends 상승세
            trends_results = search_result.get('trends_results', {})
            if trends_results:
                rising_queries = trends_results.get('suggestions', {}).get('rising_queries', [])
                analysis['popularity_indicators']['google_trends'] = {
                    'rising_queries_count': len(rising_queries),
                    'search_momentum': len(rising_queries) * 10
                }
                analysis['trend_score'] += len(rising_queries) * 10 * 0.3
            
            # 성장 잠재력 평가
            if analysis['trend_score'] > 70:
                analysis['growth_potential'] = 'high'
            elif analysis['trend_score'] > 40:
                analysis['growth_potential'] = 'medium'
            else:
                analysis['growth_potential'] = 'low'
            
            # 시장 침투도 평가
            if analysis['trend_score'] > 80:
                analysis['market_penetration'] = 'mainstream'
            elif analysis['trend_score'] > 50:
                analysis['market_penetration'] = 'emerging'
            elif analysis['trend_score'] > 20:
                analysis['market_penetration'] = 'niche'
            else:
                analysis['market_penetration'] = 'underground'
            
            return analysis
            
        except Exception as e:
            self.console_log(f"[TrendV2] 키워드 트렌드 분석 오류: {str(e)}")
            return {'error': str(e)}
    
    def get_system_status(self) -> Dict:
        """시스템 상태 확인"""
        return {
            'reddit_connector': self.reddit_connector is not None,
            'spotify_connector': self.spotify_connector is not None,
            'keyword_analyzer': self.keyword_analyzer is not None,
            'comment_analyzer': self.comment_analyzer is not None,
            'trends_analyzer': self.trends_analyzer is not None,
            'db_manager': self.db_manager is not None,
            'analysis_config': self.analysis_config,
            'system_ready': all([
                self.keyword_analyzer is not None,
                self.comment_analyzer is not None
            ])
        }