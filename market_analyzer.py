#!/usr/bin/env python3
"""
Market Analyzer - 장르별 음악 시장 분석 모듈
Google Trends, YouTube 데이터, 댓글 감성 분석을 통한 종합 음악 시장 분석
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from trends_analyzer import TrendsAnalyzer
from database import DatabaseManager

class MusicMarketAnalyzer:
    def __init__(self, console_log=None):
        """
        음악 시장 분석기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        
        # 트렌드 분석기 초기화
        try:
            self.trends_analyzer = TrendsAnalyzer(console_log=self.console_log)
            self.console_log("[Market] 트렌드 분석기 연결 완료")
        except Exception as e:
            self.console_log(f"[Market] 트렌드 분석기 연결 실패: {str(e)}")
            self.trends_analyzer = None
        
        # 데이터베이스 연결
        try:
            self.db_manager = DatabaseManager(console_log=self.console_log)
            self.console_log("[Market] 데이터베이스 연결 완료")
        except Exception as e:
            self.console_log(f"[Market] 데이터베이스 연결 실패: {str(e)}")
            self.db_manager = None
        
        # 음악 장르 정의 (한국어/영어)
        self.genre_mapping = {
            'kpop': {'ko': '케이팝', 'en': 'K-pop', 'category': 'Asian Pop'},
            'pop': {'ko': '팝', 'en': 'Pop', 'category': 'Mainstream'},
            'hiphop': {'ko': '힙합', 'en': 'Hip Hop', 'category': 'Urban'},
            'rock': {'ko': '록', 'en': 'Rock', 'category': 'Alternative'},
            'ballad': {'ko': '발라드', 'en': 'Ballad', 'category': 'Emotional'},
            'electronic': {'ko': '일렉트로닉', 'en': 'Electronic', 'category': 'Dance'},
            'rnb': {'ko': 'R&B', 'en': 'R&B', 'category': 'Soul'},
            'indie': {'ko': '인디', 'en': 'Indie', 'category': 'Independent'},
            'jazz': {'ko': '재즈', 'en': 'Jazz', 'category': 'Traditional'},
            'classical': {'ko': '클래식', 'en': 'Classical', 'category': 'Academic'}
        }
    
    def analyze_genre_market(self, genre: str, timeframe: str = 'today 12-m', geo: str = 'KR') -> Dict:
        """
        특정 장르의 시장 분석
        
        Args:
            genre: 분석할 장르
            timeframe: 분석 기간
            geo: 지역 코드
            
        Returns:
            장르 시장 분석 결과
        """
        try:
            self.console_log(f"[Market] 장르 시장 분석 시작: {genre}")
            
            result = {
                'success': True,
                'genre': genre,
                'timeframe': timeframe,
                'geo': geo,
                'analyzed_at': datetime.now().isoformat()
            }
            
            # 1. 트렌드 데이터 수집
            if self.trends_analyzer:
                genre_kr = self.genre_mapping.get(genre.lower(), {}).get('ko', genre)
                trends_result = self.trends_analyzer.get_artist_trends(genre_kr, timeframe, geo)
                
                if trends_result['success']:
                    result['trends_data'] = {
                        'current_score': trends_result['statistics']['current_score'],
                        'average_score': trends_result['statistics']['average_score'],
                        'trend_direction': trends_result['statistics']['trend_direction'],
                        'regional_interest': trends_result.get('regional_interest', [])
                    }
                else:
                    result['trends_data'] = None
            else:
                result['trends_data'] = None
            
            # 2. YouTube 데이터 분석 (DB에서)
            youtube_analysis = self._analyze_youtube_data_by_genre(genre)
            result['youtube_analysis'] = youtube_analysis
            
            # 3. 댓글 감성 분석
            sentiment_analysis = self._analyze_genre_sentiment(genre)
            result['sentiment_analysis'] = sentiment_analysis
            
            # 4. 시장 지표 계산
            market_metrics = self._calculate_market_metrics(result)
            result['market_metrics'] = market_metrics
            
            # 5. 시장 예측
            market_forecast = self._generate_market_forecast(result)
            result['market_forecast'] = market_forecast
            
            self.console_log(f"[Market] 장르 시장 분석 완료: {genre}")
            return result
            
        except Exception as e:
            self.console_log(f"[Market] 장르 시장 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def compare_genre_markets(self, genres: List[str], timeframe: str = 'today 12-m', geo: str = 'KR') -> Dict:
        """
        여러 장르의 시장 비교 분석
        
        Args:
            genres: 비교할 장르 목록
            timeframe: 분석 기간
            geo: 지역 코드
            
        Returns:
            장르별 시장 비교 결과
        """
        try:
            self.console_log(f"[Market] 장르 시장 비교 분석: {', '.join(genres)}")
            
            result = {
                'success': True,
                'genres': genres,
                'timeframe': timeframe,
                'geo': geo,
                'analyzed_at': datetime.now().isoformat(),
                'genre_analyses': {}
            }
            
            # 각 장르별 분석
            for genre in genres:
                genre_analysis = self.analyze_genre_market(genre, timeframe, geo)
                if genre_analysis['success']:
                    result['genre_analyses'][genre] = genre_analysis
            
            # 장르별 비교 지표
            comparison_metrics = self._calculate_comparison_metrics(result['genre_analyses'])
            result['comparison_metrics'] = comparison_metrics
            
            # 시장 순위
            market_ranking = self._calculate_market_ranking(result['genre_analyses'])
            result['market_ranking'] = market_ranking
            
            # 성장률 분석
            growth_analysis = self._analyze_growth_rates(result['genre_analyses'])
            result['growth_analysis'] = growth_analysis
            
            self.console_log(f"[Market] 장르 시장 비교 완료")
            return result
            
        except Exception as e:
            self.console_log(f"[Market] 장르 시장 비교 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_market_overview(self, timeframe: str = 'today 12-m', geo: str = 'KR') -> Dict:
        """
        전체 음악 시장 개관
        
        Args:
            timeframe: 분석 기간
            geo: 지역 코드
            
        Returns:
            전체 시장 개관
        """
        try:
            self.console_log("[Market] 전체 음악 시장 개관 분석")
            
            # 주요 장르들 분석
            main_genres = ['kpop', 'pop', 'hiphop', 'rock', 'ballad']
            comparison_result = self.compare_genre_markets(main_genres, timeframe, geo)
            
            if not comparison_result['success']:
                return comparison_result
            
            result = {
                'success': True,
                'timeframe': timeframe,
                'geo': geo,
                'analyzed_at': datetime.now().isoformat()
            }
            
            # 시장 요약
            result['market_summary'] = {
                'total_genres_analyzed': len(main_genres),
                'dominant_genre': comparison_result['market_ranking']['trends_ranking'][0] if comparison_result['market_ranking']['trends_ranking'] else None,
                'fastest_growing': comparison_result['growth_analysis']['fastest_growing'] if comparison_result['growth_analysis'] else None,
                'most_engaging': comparison_result['market_ranking']['engagement_ranking'][0] if comparison_result['market_ranking']['engagement_ranking'] else None
            }
            
            # 장르별 상세 데이터
            result['genre_details'] = comparison_result['genre_analyses']
            result['comparison_metrics'] = comparison_result['comparison_metrics']
            result['market_ranking'] = comparison_result['market_ranking']
            result['growth_analysis'] = comparison_result['growth_analysis']
            
            # 시장 인사이트 생성
            insights = self._generate_market_insights(result)
            result['market_insights'] = insights
            
            # 추천사항
            recommendations = self._generate_recommendations(result)
            result['recommendations'] = recommendations
            
            return result
            
        except Exception as e:
            self.console_log(f"[Market] 시장 개관 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _analyze_youtube_data_by_genre(self, genre: str) -> Dict:
        """데이터베이스에서 장르별 YouTube 데이터 분석"""
        try:
            if not self.db_manager:
                return {'error': '데이터베이스 연결 없음'}
            
            conn = sqlite3.connect(self.db_manager.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 장르별 세션 조회
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_videos,
                    AVG(view_count) as avg_views,
                    AVG(like_count) as avg_likes,
                    AVG(sentiment_score) as avg_sentiment,
                    SUM(view_count) as total_views,
                    SUM(like_count) as total_likes
                FROM analysis_sessions 
                WHERE primary_genre = ?
            ''', (genre,))
            
            stats = cursor.fetchone()
            
            # 최근 트렌드 (최근 30일)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute('''
                SELECT 
                    COUNT(*) as recent_videos,
                    AVG(view_count) as recent_avg_views,
                    AVG(sentiment_score) as recent_sentiment
                FROM analysis_sessions 
                WHERE primary_genre = ? AND analyzed_at > ?
            ''', (genre, thirty_days_ago))
            
            recent_stats = cursor.fetchone()
            
            # 댓글 분석
            cursor.execute('''
                SELECT 
                    COUNT(c.id) as total_comments,
                    AVG(c.sentiment_score) as comment_sentiment,
                    COUNT(CASE WHEN c.sentiment_score > 0.1 THEN 1 END) as positive_comments,
                    COUNT(CASE WHEN c.sentiment_score < -0.1 THEN 1 END) as negative_comments
                FROM analysis_sessions s
                JOIN comments c ON s.id = c.session_id
                WHERE s.primary_genre = ?
            ''', (genre,))
            
            comment_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_videos': stats['total_videos'] or 0,
                'avg_views': stats['avg_views'] or 0,
                'avg_likes': stats['avg_likes'] or 0,
                'avg_sentiment': stats['avg_sentiment'] or 0,
                'total_engagement': (stats['total_views'] or 0) + (stats['total_likes'] or 0) * 10,
                'recent_activity': {
                    'recent_videos': recent_stats['recent_videos'] or 0,
                    'recent_avg_views': recent_stats['recent_avg_views'] or 0,
                    'recent_sentiment': recent_stats['recent_sentiment'] or 0
                },
                'comment_analysis': {
                    'total_comments': comment_stats['total_comments'] or 0,
                    'comment_sentiment': comment_stats['comment_sentiment'] or 0,
                    'positive_ratio': (comment_stats['positive_comments'] or 0) / max(comment_stats['total_comments'] or 1, 1),
                    'negative_ratio': (comment_stats['negative_comments'] or 0) / max(comment_stats['total_comments'] or 1, 1)
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_genre_sentiment(self, genre: str) -> Dict:
        """장르별 감성 분석"""
        try:
            if not self.db_manager:
                return {'error': '데이터베이스 연결 없음'}
            
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            # 장르별 감성 분포
            cursor.execute('''
                SELECT 
                    AVG(c.sentiment_score) as avg_sentiment,
                    COUNT(CASE WHEN c.sentiment_score > 0.3 THEN 1 END) as very_positive,
                    COUNT(CASE WHEN c.sentiment_score BETWEEN 0.1 AND 0.3 THEN 1 END) as positive,
                    COUNT(CASE WHEN c.sentiment_score BETWEEN -0.1 AND 0.1 THEN 1 END) as neutral,
                    COUNT(CASE WHEN c.sentiment_score BETWEEN -0.3 AND -0.1 THEN 1 END) as negative,
                    COUNT(CASE WHEN c.sentiment_score < -0.3 THEN 1 END) as very_negative,
                    COUNT(*) as total_comments
                FROM analysis_sessions s
                JOIN comments c ON s.id = c.session_id
                WHERE s.primary_genre = ?
            ''', (genre,))
            
            sentiment_data = cursor.fetchone()
            
            conn.close()
            
            total = sentiment_data[6] or 1  # total_comments
            
            return {
                'average_sentiment': sentiment_data[0] or 0,
                'sentiment_distribution': {
                    'very_positive': {'count': sentiment_data[1] or 0, 'percentage': (sentiment_data[1] or 0) / total * 100},
                    'positive': {'count': sentiment_data[2] or 0, 'percentage': (sentiment_data[2] or 0) / total * 100},
                    'neutral': {'count': sentiment_data[3] or 0, 'percentage': (sentiment_data[3] or 0) / total * 100},
                    'negative': {'count': sentiment_data[4] or 0, 'percentage': (sentiment_data[4] or 0) / total * 100},
                    'very_negative': {'count': sentiment_data[5] or 0, 'percentage': (sentiment_data[5] or 0) / total * 100}
                },
                'total_analyzed': total,
                'positivity_score': ((sentiment_data[1] or 0) + (sentiment_data[2] or 0)) / total * 100,
                'negativity_score': ((sentiment_data[4] or 0) + (sentiment_data[5] or 0)) / total * 100
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_market_metrics(self, genre_data: Dict) -> Dict:
        """시장 지표 계산"""
        try:
            metrics = {}
            
            # 트렌드 지표
            if genre_data.get('trends_data'):
                trends = genre_data['trends_data']
                metrics['trend_score'] = trends['current_score']
                metrics['trend_momentum'] = trends['trend_direction']
                metrics['trend_stability'] = trends['average_score']
            
            # YouTube 지표
            if genre_data.get('youtube_analysis'):
                youtube = genre_data['youtube_analysis']
                metrics['content_volume'] = youtube.get('total_videos', 0)
                metrics['average_engagement'] = youtube.get('avg_views', 0) + youtube.get('avg_likes', 0) * 10
                metrics['content_quality'] = youtube.get('avg_sentiment', 0)
            
            # 감성 지표
            if genre_data.get('sentiment_analysis'):
                sentiment = genre_data['sentiment_analysis']
                metrics['audience_satisfaction'] = sentiment.get('positivity_score', 0)
                metrics['controversy_level'] = sentiment.get('negativity_score', 0)
                metrics['emotional_impact'] = abs(sentiment.get('average_sentiment', 0)) * 100
            
            # 종합 시장 점수 (0-100)
            trend_weight = 0.4
            engagement_weight = 0.3
            sentiment_weight = 0.3
            
            normalized_trend = min(metrics.get('trend_score', 0), 100) / 100
            normalized_engagement = min(metrics.get('average_engagement', 0) / 1000000, 1)  # 100만 기준
            normalized_sentiment = (metrics.get('audience_satisfaction', 0)) / 100
            
            metrics['market_score'] = (
                normalized_trend * trend_weight +
                normalized_engagement * engagement_weight +
                normalized_sentiment * sentiment_weight
            ) * 100
            
            # 시장 등급
            if metrics['market_score'] >= 80:
                metrics['market_grade'] = 'A+'
            elif metrics['market_score'] >= 70:
                metrics['market_grade'] = 'A'
            elif metrics['market_score'] >= 60:
                metrics['market_grade'] = 'B+'
            elif metrics['market_score'] >= 50:
                metrics['market_grade'] = 'B'
            elif metrics['market_score'] >= 40:
                metrics['market_grade'] = 'C+'
            else:
                metrics['market_grade'] = 'C'
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_market_forecast(self, genre_data: Dict) -> Dict:
        """시장 예측 생성"""
        try:
            forecast = {}
            
            # 단기 예측 (1-3개월)
            if genre_data.get('trends_data'):
                trend_direction = genre_data['trends_data']['trend_direction']
                current_score = genre_data['trends_data']['current_score']
                
                if trend_direction == 'rising':
                    forecast['short_term'] = {
                        'direction': '상승',
                        'confidence': 'high',
                        'predicted_change': '+15-25%',
                        'key_factors': ['트렌드 상승세', '검색량 증가']
                    }
                elif trend_direction == 'falling':
                    forecast['short_term'] = {
                        'direction': '하락',
                        'confidence': 'medium',
                        'predicted_change': '-10-20%',
                        'key_factors': ['트렌드 하락세', '관심도 감소']
                    }
                else:
                    forecast['short_term'] = {
                        'direction': '안정',
                        'confidence': 'medium',
                        'predicted_change': '±5%',
                        'key_factors': ['안정적 트렌드', '꾸준한 관심']
                    }
            
            # 장기 예측 (6-12개월)
            market_metrics = genre_data.get('market_metrics', {})
            market_score = market_metrics.get('market_score', 50)
            
            if market_score >= 70:
                forecast['long_term'] = {
                    'outlook': '매우 긍정적',
                    'growth_potential': 'high',
                    'investment_recommendation': '적극 투자',
                    'risk_level': 'low'
                }
            elif market_score >= 50:
                forecast['long_term'] = {
                    'outlook': '긍정적',
                    'growth_potential': 'medium',
                    'investment_recommendation': '선택적 투자',
                    'risk_level': 'medium'
                }
            else:
                forecast['long_term'] = {
                    'outlook': '신중 관망',
                    'growth_potential': 'low',
                    'investment_recommendation': '투자 보류',
                    'risk_level': 'high'
                }
            
            return forecast
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_comparison_metrics(self, genre_analyses: Dict) -> Dict:
        """장르별 비교 지표 계산"""
        metrics = {}
        
        # 각 지표별 점수 수집
        trend_scores = {}
        market_scores = {}
        engagement_scores = {}
        sentiment_scores = {}
        
        for genre, analysis in genre_analyses.items():
            if analysis.get('market_metrics'):
                metrics_data = analysis['market_metrics']
                trend_scores[genre] = metrics_data.get('trend_score', 0)
                market_scores[genre] = metrics_data.get('market_score', 0)
                engagement_scores[genre] = metrics_data.get('average_engagement', 0)
                sentiment_scores[genre] = metrics_data.get('audience_satisfaction', 0)
        
        metrics['trend_scores'] = trend_scores
        metrics['market_scores'] = market_scores
        metrics['engagement_scores'] = engagement_scores
        metrics['sentiment_scores'] = sentiment_scores
        
        return metrics
    
    def _calculate_market_ranking(self, genre_analyses: Dict) -> Dict:
        """시장 순위 계산"""
        rankings = {}
        
        # 트렌드 순위
        trend_ranking = []
        market_ranking = []
        engagement_ranking = []
        sentiment_ranking = []
        
        for genre, analysis in genre_analyses.items():
            if analysis.get('market_metrics'):
                metrics = analysis['market_metrics']
                trend_ranking.append((genre, metrics.get('trend_score', 0)))
                market_ranking.append((genre, metrics.get('market_score', 0)))
                engagement_ranking.append((genre, metrics.get('average_engagement', 0)))
                sentiment_ranking.append((genre, metrics.get('audience_satisfaction', 0)))
        
        rankings['trends_ranking'] = [genre for genre, score in sorted(trend_ranking, key=lambda x: x[1], reverse=True)]
        rankings['market_ranking'] = [genre for genre, score in sorted(market_ranking, key=lambda x: x[1], reverse=True)]
        rankings['engagement_ranking'] = [genre for genre, score in sorted(engagement_ranking, key=lambda x: x[1], reverse=True)]
        rankings['sentiment_ranking'] = [genre for genre, score in sorted(sentiment_ranking, key=lambda x: x[1], reverse=True)]
        
        return rankings
    
    def _analyze_growth_rates(self, genre_analyses: Dict) -> Dict:
        """성장률 분석"""
        growth_data = {}
        
        rising_genres = []
        stable_genres = []
        declining_genres = []
        
        for genre, analysis in genre_analyses.items():
            if analysis.get('trends_data'):
                direction = analysis['trends_data']['trend_direction']
                if direction == 'rising':
                    rising_genres.append(genre)
                elif direction == 'falling':
                    declining_genres.append(genre)
                else:
                    stable_genres.append(genre)
        
        growth_data['rising_genres'] = rising_genres
        growth_data['stable_genres'] = stable_genres
        growth_data['declining_genres'] = declining_genres
        growth_data['fastest_growing'] = rising_genres[0] if rising_genres else None
        growth_data['most_declining'] = declining_genres[0] if declining_genres else None
        
        return growth_data
    
    def _generate_market_insights(self, market_data: Dict) -> List[str]:
        """시장 인사이트 생성"""
        insights = []
        
        # 지배적 장르
        if market_data.get('market_summary', {}).get('dominant_genre'):
            dominant = market_data['market_summary']['dominant_genre']
            insights.append(f"현재 {dominant} 장르가 검색 트렌드를 주도하고 있습니다.")
        
        # 성장 장르
        if market_data.get('growth_analysis', {}).get('fastest_growing'):
            fastest = market_data['growth_analysis']['fastest_growing']
            insights.append(f"{fastest} 장르가 가장 빠른 성장세를 보이고 있습니다.")
        
        # 참여도 높은 장르
        if market_data.get('market_summary', {}).get('most_engaging'):
            engaging = market_data['market_summary']['most_engaging']
            insights.append(f"{engaging} 장르가 가장 높은 사용자 참여도를 기록하고 있습니다.")
        
        # 시장 다양성
        total_genres = market_data.get('market_summary', {}).get('total_genres_analyzed', 0)
        if total_genres >= 5:
            insights.append("음악 시장의 장르 다양성이 높아 여러 세그먼트에서 기회가 존재합니다.")
        
        return insights
    
    def _generate_recommendations(self, market_data: Dict) -> List[str]:
        """추천사항 생성"""
        recommendations = []
        
        # 투자 추천
        if market_data.get('market_ranking', {}).get('market_ranking'):
            top_genre = market_data['market_ranking']['market_ranking'][0]
            recommendations.append(f"{top_genre} 장르에 우선 투자를 고려하세요.")
        
        # 성장 추천
        if market_data.get('growth_analysis', {}).get('rising_genres'):
            rising = market_data['growth_analysis']['rising_genres']
            if rising:
                recommendations.append(f"성장 잠재력이 높은 {', '.join(rising[:2])} 장르를 주목하세요.")
        
        # 참여도 추천
        if market_data.get('market_ranking', {}).get('engagement_ranking'):
            engaging = market_data['market_ranking']['engagement_ranking'][0]
            recommendations.append(f"{engaging} 장르는 높은 참여도로 마케팅 효과가 클 것으로 예상됩니다.")
        
        # 다각화 추천
        recommendations.append("리스크 분산을 위해 여러 장르에 포트폴리오를 구성하는 것을 권장합니다.")
        
        return recommendations