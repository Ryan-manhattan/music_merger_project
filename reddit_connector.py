#!/usr/bin/env python3
"""
Reddit Connector - Reddit API를 통한 음악 관련 데이터 수집
음악 서브레딧에서 트렌드, 키워드, 댓글 데이터 수집
"""

import os
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    print("PRAW 라이브러리가 설치되지 않았습니다. 'pip install praw' 실행")

class RedditConnector:
    def __init__(self, console_log=None):
        """
        Reddit 연결기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        self.reddit = None
        
        if PRAW_AVAILABLE:
            self._initialize_reddit()
        
        # 음악 관련 서브레딧 목록
        self.music_subreddits = {
            'general': ['Music', 'WeAreTheMusicMakers', 'listentothis'],
            'kpop': ['kpop', 'bangtan', 'TWICE', 'BlackPink'],
            'hiphop': ['hiphopheads', 'KoreanHipHop'],
            'electronic': ['electronicmusic', 'trap', 'dubstep'],
            'discussion': ['LetsTalkMusic', 'musictheory', 'MusicRecommendations']
        }
        
        # 트렌드 키워드 패턴
        self.trend_keywords = [
            'trending', 'viral', 'hot', 'popular', 'chart', 'billboard',
            '인기', '트렌드', '핫', '바이럴', '차트', '순위'
        ]
    
    def _initialize_reddit(self):
        """Reddit API 초기화"""
        try:
            # 환경변수에서 Reddit API 크리덴셜 읽기
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'MusicTrendAnalyzer/1.0')
            
            if not client_id or not client_secret:
                self.console_log("[Reddit] API 크리덴셜이 설정되지 않았습니다")
                self.console_log("[Reddit] 환경변수 REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET 설정 필요")
                return
            
            # Reddit 인스턴스 생성
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                read_only=True
            )
            
            # 연결 테스트
            self.reddit.user.me()
            self.console_log("[Reddit] API 연결 성공")
            
        except Exception as e:
            self.console_log(f"[Reddit] API 초기화 오류: {str(e)}")
            self.reddit = None
    
    def get_trending_posts(self, category: str = 'general', limit: int = 50, time_filter: str = 'week') -> Dict:
        """
        트렌딩 게시물 수집
        
        Args:
            category: 음악 카테고리 ('general', 'kpop', 'hiphop' 등)
            limit: 수집할 게시물 수
            time_filter: 시간 필터 ('day', 'week', 'month', 'year')
            
        Returns:
            트렌딩 게시물 데이터
        """
        try:
            if not self.reddit:
                return {'success': False, 'error': 'Reddit API가 초기화되지 않았습니다'}
            
            subreddits = self.music_subreddits.get(category, self.music_subreddits['general'])
            all_posts = []
            
            self.console_log(f"[Reddit] 트렌딩 게시물 수집: {category} ({limit}개)")
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Hot 게시물 수집
                    for post in subreddit.hot(limit=limit//len(subreddits)):
                        post_data = {
                            'id': post.id,
                            'title': post.title,
                            'subreddit': subreddit_name,
                            'score': post.score,
                            'upvote_ratio': post.upvote_ratio,
                            'num_comments': post.num_comments,
                            'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                            'url': post.url,
                            'selftext': post.selftext,
                            'is_video': post.is_video,
                            'permalink': f"https://reddit.com{post.permalink}"
                        }
                        
                        # 플레어 정보
                        if hasattr(post, 'link_flair_text') and post.link_flair_text:
                            post_data['flair'] = post.link_flair_text
                        
                        all_posts.append(post_data)
                        
                    time.sleep(0.1)  # API 호출 제한 고려
                    
                except Exception as e:
                    self.console_log(f"[Reddit] {subreddit_name} 수집 오류: {str(e)}")
                    continue
            
            # 점수순 정렬
            all_posts.sort(key=lambda x: x['score'], reverse=True)
            
            result = {
                'success': True,
                'category': category,
                'time_filter': time_filter,
                'collected_at': datetime.now().isoformat(),
                'total_posts': len(all_posts),
                'posts': all_posts[:limit],
                'subreddits_searched': subreddits
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Reddit] 트렌딩 게시물 수집 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_post_comments(self, post_id: str, limit: int = 100) -> Dict:
        """
        특정 게시물의 댓글 수집
        
        Args:
            post_id: Reddit 게시물 ID
            limit: 수집할 댓글 수
            
        Returns:
            댓글 데이터
        """
        try:
            if not self.reddit:
                return {'success': False, 'error': 'Reddit API가 초기화되지 않았습니다'}
            
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # "more comments" 링크 확장
            
            comments = []
            for comment in submission.comments.list()[:limit]:
                if hasattr(comment, 'body') and comment.body != '[deleted]':
                    comment_data = {
                        'id': comment.id,
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat(),
                        'parent_id': comment.parent_id,
                        'is_submitter': comment.is_submitter,
                        'depth': comment.depth if hasattr(comment, 'depth') else 0
                    }
                    comments.append(comment_data)
            
            result = {
                'success': True,
                'post_id': post_id,
                'post_title': submission.title,
                'post_score': submission.score,
                'total_comments': len(comments),
                'comments': comments,
                'collected_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Reddit] 댓글 수집 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_music_keywords(self, posts: List[Dict]) -> Dict:
        """
        게시물에서 음악 관련 키워드 추출
        
        Args:
            posts: Reddit 게시물 리스트
            
        Returns:
            키워드 분석 결과
        """
        try:
            all_text = []
            artist_mentions = Counter()
            genre_mentions = Counter()
            trend_mentions = Counter()
            
            # 장르 패턴 정의
            genre_patterns = {
                'kpop': r'\bk-?pop\b|\bkpop\b|케이?팝|아이돌',
                'hiphop': r'\bhip-?hop\b|\brap\b|힙합|랩',
                'rock': r'\brock\b|\bmetal\b|록|메탈',
                'pop': r'\bpop\b(?!.*k-?pop)|팝(?!.*케이)',
                'electronic': r'\bedm\b|\belectronic\b|\bdubstep\b|\btrap\b|일렉트로닉',
                'ballad': r'\bballad\b|발라드',
                'jazz': r'\bjazz\b|재즈',
                'classical': r'\bclassical\b|\borchestra\b|클래식|오케스트라'
            }
            
            for post in posts:
                text = f"{post['title']} {post.get('selftext', '')}"
                all_text.append(text.lower())
                
                # 장르 언급 카운트
                for genre, pattern in genre_patterns.items():
                    matches = len(re.findall(pattern, text, re.IGNORECASE))
                    if matches > 0:
                        genre_mentions[genre] += matches
                
                # 트렌드 키워드 카운트
                for keyword in self.trend_keywords:
                    if keyword.lower() in text.lower():
                        trend_mentions[keyword] += 1
                
                # 아티스트명 추출 (간단한 패턴)
                # 제목에서 따옴표나 대괄호 안의 내용 추출
                artist_patterns = [
                    r'\"([^\"]+)\"',  # "아티스트명"
                    r'\[([^\]]+)\]',  # [아티스트명]
                    r'by\s+([A-Za-z\s]+)',  # by 아티스트명
                ]
                
                for pattern in artist_patterns:
                    matches = re.findall(pattern, post['title'], re.IGNORECASE)
                    for match in matches:
                        if len(match.strip()) > 1 and len(match.strip()) < 50:
                            artist_mentions[match.strip()] += 1
            
            # 결과 정리
            result = {
                'success': True,
                'analyzed_posts': len(posts),
                'top_genres': dict(genre_mentions.most_common(10)),
                'top_artists': dict(artist_mentions.most_common(20)),
                'trend_keywords': dict(trend_mentions.most_common()),
                'total_text_analyzed': len(' '.join(all_text)),
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Reddit] 키워드 추출 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_subreddit_stats(self, subreddit_name: str) -> Dict:
        """
        서브레딧 통계 정보
        
        Args:
            subreddit_name: 서브레딧 이름
            
        Returns:
            서브레딧 통계
        """
        try:
            if not self.reddit:
                return {'success': False, 'error': 'Reddit API가 초기화되지 않았습니다'}
            
            subreddit = self.reddit.subreddit(subreddit_name)
            
            result = {
                'success': True,
                'name': subreddit.display_name,
                'title': subreddit.title,
                'description': subreddit.public_description,
                'subscribers': subreddit.subscribers,
                'active_users': subreddit.active_user_count,
                'created_utc': datetime.fromtimestamp(subreddit.created_utc).isoformat(),
                'over18': subreddit.over18,
                'lang': subreddit.lang,
                'collected_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Reddit] 서브레딧 통계 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def search_music_discussions(self, query: str, subreddit_category: str = 'general', 
                                sort: str = 'hot', time_filter: str = 'week', limit: int = 25) -> Dict:
        """
        음악 관련 토론 검색
        
        Args:
            query: 검색 쿼리
            subreddit_category: 서브레딧 카테고리
            sort: 정렬 방식 ('hot', 'new', 'top', 'relevance')
            time_filter: 시간 필터
            limit: 결과 수 제한
            
        Returns:
            검색 결과
        """
        try:
            if not self.reddit:
                return {'success': False, 'error': 'Reddit API가 초기화되지 않았습니다'}
            
            subreddits = self.music_subreddits.get(subreddit_category, ['Music'])
            search_results = []
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # 검색 실행
                    submissions = subreddit.search(
                        query, 
                        sort=sort, 
                        time_filter=time_filter, 
                        limit=limit//len(subreddits)
                    )
                    
                    for submission in submissions:
                        result_data = {
                            'id': submission.id,
                            'title': submission.title,
                            'subreddit': subreddit_name,
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                            'url': submission.url,
                            'permalink': f"https://reddit.com{submission.permalink}",
                            'relevance_score': self._calculate_relevance(submission.title, query)
                        }
                        search_results.append(result_data)
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.console_log(f"[Reddit] {subreddit_name} 검색 오류: {str(e)}")
                    continue
            
            # 관련성 점수로 정렬
            search_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            result = {
                'success': True,
                'query': query,
                'category': subreddit_category,
                'sort': sort,
                'time_filter': time_filter,
                'total_results': len(search_results),
                'results': search_results[:limit],
                'searched_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Reddit] 검색 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_relevance(self, text: str, query: str) -> float:
        """텍스트와 쿼리의 관련성 점수 계산"""
        text_lower = text.lower()
        query_lower = query.lower()
        
        # 정확한 매치
        if query_lower in text_lower:
            return 1.0
        
        # 단어별 매치
        query_words = query_lower.split()
        text_words = text_lower.split()
        
        matches = sum(1 for word in query_words if word in text_words)
        return matches / len(query_words) if query_words else 0
    
    def get_api_status(self) -> Dict:
        """Reddit API 연결 상태 확인"""
        return {
            'reddit_available': PRAW_AVAILABLE,
            'reddit_connected': self.reddit is not None,
            'subreddits_configured': len(sum(self.music_subreddits.values(), [])),
            'categories': list(self.music_subreddits.keys())
        }