#!/usr/bin/env python3
"""
Trends Analyzer - Google Trends 데이터 수집 및 분석 모듈
음악 트렌드, 아티스트 인기도, 키워드 분석
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pytrends.request import TrendReq

class TrendsAnalyzer:
    def __init__(self, console_log=None):
        """
        트렌드 분석기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        
        try:
            # pytrends 초기화 (한국어, 한국 시간대)
            self.pytrends = TrendReq(hl='ko', tz=540)
            self.console_log("[Trends] Google Trends 분석기 초기화 완료")
        except Exception as e:
            self.console_log(f"[Trends] 초기화 오류: {str(e)}")
            self.pytrends = None
    
    def get_artist_trends(self, artist_name: str, timeframe: str = 'today 12-m', geo: str = 'KR') -> Dict:
        """
        아티스트 트렌드 분석
        
        Args:
            artist_name: 아티스트명
            timeframe: 분석 기간 ('today 12-m', 'today 3-m', 'today 1-m' 등)
            geo: 지역 코드 ('KR', 'US', '' 등)
            
        Returns:
            트렌드 분석 결과
        """
        try:
            if not self.pytrends:
                return {'success': False, 'error': '트렌드 분석기가 초기화되지 않았습니다'}
            
            self.console_log(f"[Trends] 아티스트 트렌드 분석: {artist_name}")
            
            # 키워드 빌드
            self.pytrends.build_payload([artist_name], cat=0, timeframe=timeframe, geo=geo)
            
            # 시간별 관심도
            interest_over_time = self.pytrends.interest_over_time()
            
            result = {
                'success': True,
                'artist': artist_name,
                'timeframe': timeframe,
                'geo': geo,
                'analyzed_at': datetime.now().isoformat()
            }
            
            if not interest_over_time.empty:
                # 시간별 데이터
                time_data = []
                for date, row in interest_over_time.iterrows():
                    if artist_name in row:
                        time_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'score': int(row[artist_name])
                        })
                
                result['time_series'] = time_data
                
                # 통계 계산
                scores = [item['score'] for item in time_data]
                result['statistics'] = {
                    'current_score': scores[-1] if scores else 0,
                    'average_score': sum(scores) / len(scores) if scores else 0,
                    'max_score': max(scores) if scores else 0,
                    'min_score': min(scores) if scores else 0,
                    'trend_direction': self._calculate_trend(scores[-4:] if len(scores) >= 4 else scores)
                }
                
                # 지역별 관심도
                try:
                    regional_interest = self.pytrends.interest_by_region(resolution='REGION')
                    if not regional_interest.empty:
                        regions = []
                        for region, row in regional_interest.sort_values(artist_name, ascending=False).head(10).iterrows():
                            regions.append({
                                'region': region,
                                'score': int(row[artist_name])
                            })
                        result['regional_interest'] = regions
                except:
                    result['regional_interest'] = []
                
                # 관련 검색어
                try:
                    related_queries = self.pytrends.related_queries()
                    if artist_name in related_queries:
                        top_queries = related_queries[artist_name]['top']
                        rising_queries = related_queries[artist_name]['rising']
                        
                        result['related_queries'] = {
                            'top': top_queries.to_dict('records') if top_queries is not None else [],
                            'rising': rising_queries.to_dict('records') if rising_queries is not None else []
                        }
                except:
                    result['related_queries'] = {'top': [], 'rising': []}
            else:
                result['time_series'] = []
                result['statistics'] = {
                    'current_score': 0,
                    'average_score': 0,
                    'max_score': 0,
                    'min_score': 0,
                    'trend_direction': 'stable'
                }
                result['regional_interest'] = []
                result['related_queries'] = {'top': [], 'rising': []}
            
            return result
            
        except Exception as e:
            self.console_log(f"[Trends] 아티스트 트렌드 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def compare_artists(self, artists: List[str], timeframe: str = 'today 12-m', geo: str = 'KR') -> Dict:
        """
        여러 아티스트 트렌드 비교
        
        Args:
            artists: 아티스트 목록 (최대 5개)
            timeframe: 분석 기간
            geo: 지역 코드
            
        Returns:
            비교 분석 결과
        """
        try:
            if not self.pytrends:
                return {'success': False, 'error': '트렌드 분석기가 초기화되지 않았습니다'}
            
            if len(artists) > 5:
                artists = artists[:5]  # Google Trends 제한
            
            self.console_log(f"[Trends] 아티스트 비교 분석: {', '.join(artists)}")
            
            # 키워드 빌드
            self.pytrends.build_payload(artists, cat=0, timeframe=timeframe, geo=geo)
            
            # 시간별 관심도
            interest_over_time = self.pytrends.interest_over_time()
            
            result = {
                'success': True,
                'artists': artists,
                'timeframe': timeframe,
                'geo': geo,
                'analyzed_at': datetime.now().isoformat()
            }
            
            if not interest_over_time.empty:
                # 각 아티스트별 데이터
                artists_data = {}
                for artist in artists:
                    if artist in interest_over_time.columns:
                        scores = interest_over_time[artist].tolist()
                        artists_data[artist] = {
                            'current_score': scores[-1] if scores else 0,
                            'average_score': sum(scores) / len(scores) if scores else 0,
                            'max_score': max(scores) if scores else 0,
                            'peak_date': interest_over_time[artist].idxmax().strftime('%Y-%m-%d') if scores else None,
                            'trend_direction': self._calculate_trend(scores[-4:] if len(scores) >= 4 else scores)
                        }
                
                result['artists_data'] = artists_data
                
                # 순위 계산
                current_ranking = sorted(artists_data.items(), key=lambda x: x[1]['current_score'], reverse=True)
                average_ranking = sorted(artists_data.items(), key=lambda x: x[1]['average_score'], reverse=True)
                
                result['rankings'] = {
                    'current': [{'artist': artist, 'score': data['current_score']} for artist, data in current_ranking],
                    'average': [{'artist': artist, 'score': data['average_score']} for artist, data in average_ranking]
                }
                
                # 시계열 데이터
                time_series = []
                for date, row in interest_over_time.iterrows():
                    data_point = {'date': date.strftime('%Y-%m-%d')}
                    for artist in artists:
                        if artist in row:
                            data_point[artist] = int(row[artist])
                    time_series.append(data_point)
                
                result['time_series'] = time_series
            else:
                result['artists_data'] = {}
                result['rankings'] = {'current': [], 'average': []}
                result['time_series'] = []
            
            return result
            
        except Exception as e:
            self.console_log(f"[Trends] 아티스트 비교 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_music_genre_trends(self, genres: List[str] = None, timeframe: str = 'today 12-m', geo: str = 'KR') -> Dict:
        """
        음악 장르 트렌드 분석
        
        Args:
            genres: 장르 목록 (기본값: 주요 장르들)
            timeframe: 분석 기간
            geo: 지역 코드
            
        Returns:
            장르 트렌드 분석 결과
        """
        try:
            if not self.pytrends:
                return {'success': False, 'error': '트렌드 분석기가 초기화되지 않았습니다'}
            
            if genres is None:
                genres = ['케이팝', '힙합', '팝송', '록음악', '발라드']
            
            if len(genres) > 5:
                genres = genres[:5]
            
            self.console_log(f"[Trends] 음악 장르 트렌드 분석: {', '.join(genres)}")
            
            # 키워드 빌드
            self.pytrends.build_payload(genres, cat=0, timeframe=timeframe, geo=geo)
            
            # 시간별 관심도
            interest_over_time = self.pytrends.interest_over_time()
            
            result = {
                'success': True,
                'genres': genres,
                'timeframe': timeframe,
                'geo': geo,
                'analyzed_at': datetime.now().isoformat()
            }
            
            if not interest_over_time.empty:
                # 장르별 통계
                genres_data = {}
                for genre in genres:
                    if genre in interest_over_time.columns:
                        scores = interest_over_time[genre].tolist()
                        genres_data[genre] = {
                            'current_score': scores[-1] if scores else 0,
                            'average_score': sum(scores) / len(scores) if scores else 0,
                            'max_score': max(scores) if scores else 0,
                            'trend_direction': self._calculate_trend(scores[-4:] if len(scores) >= 4 else scores)
                        }
                
                result['genres_data'] = genres_data
                
                # 장르 순위
                ranking = sorted(genres_data.items(), key=lambda x: x[1]['current_score'], reverse=True)
                result['ranking'] = [{'genre': genre, 'score': data['current_score']} for genre, data in ranking]
                
                # 시계열 데이터
                time_series = []
                for date, row in interest_over_time.iterrows():
                    data_point = {'date': date.strftime('%Y-%m-%d')}
                    for genre in genres:
                        if genre in row:
                            data_point[genre] = int(row[genre])
                    time_series.append(data_point)
                
                result['time_series'] = time_series
            else:
                result['genres_data'] = {}
                result['ranking'] = []
                result['time_series'] = []
            
            return result
            
        except Exception as e:
            self.console_log(f"[Trends] 장르 트렌드 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_keyword_suggestions(self, base_keyword: str, geo: str = 'KR') -> Dict:
        """
        키워드 관련 검색어 및 제안
        
        Args:
            base_keyword: 기본 키워드
            geo: 지역 코드
            
        Returns:
            키워드 제안 결과
        """
        try:
            if not self.pytrends:
                return {'success': False, 'error': '트렌드 분석기가 초기화되지 않았습니다'}
            
            self.console_log(f"[Trends] 키워드 제안 분석: {base_keyword}")
            
            # 키워드 빌드
            self.pytrends.build_payload([base_keyword], timeframe='today 3-m', geo=geo)
            
            result = {
                'success': True,
                'base_keyword': base_keyword,
                'geo': geo,
                'analyzed_at': datetime.now().isoformat()
            }
            
            # 관련 검색어
            try:
                related_queries = self.pytrends.related_queries()
                if base_keyword in related_queries:
                    top_queries = related_queries[base_keyword]['top']
                    rising_queries = related_queries[base_keyword]['rising']
                    
                    result['suggestions'] = {
                        'top_queries': top_queries.to_dict('records') if top_queries is not None else [],
                        'rising_queries': rising_queries.to_dict('records') if rising_queries is not None else []
                    }
                else:
                    result['suggestions'] = {'top_queries': [], 'rising_queries': []}
            except:
                result['suggestions'] = {'top_queries': [], 'rising_queries': []}
            
            # 관련 주제
            try:
                related_topics = self.pytrends.related_topics()
                if base_keyword in related_topics:
                    top_topics = related_topics[base_keyword]['top']
                    rising_topics = related_topics[base_keyword]['rising']
                    
                    result['topics'] = {
                        'top_topics': top_topics.to_dict('records') if top_topics is not None else [],
                        'rising_topics': rising_topics.to_dict('records') if rising_topics is not None else []
                    }
                else:
                    result['topics'] = {'top_topics': [], 'rising_topics': []}
            except:
                result['topics'] = {'top_topics': [], 'rising_topics': []}
            
            return result
            
        except Exception as e:
            self.console_log(f"[Trends] 키워드 제안 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_trend(self, scores: List[int]) -> str:
        """
        트렌드 방향 계산
        
        Args:
            scores: 점수 리스트
            
        Returns:
            트렌드 방향 ('rising', 'falling', 'stable')
        """
        if len(scores) < 2:
            return 'stable'
        
        # 최근 데이터와 이전 데이터 비교
        recent_avg = sum(scores[-2:]) / 2 if len(scores) >= 2 else scores[-1]
        earlier_avg = sum(scores[:-2]) / len(scores[:-2]) if len(scores) > 2 else scores[0]
        
        if recent_avg > earlier_avg * 1.1:
            return 'rising'
        elif recent_avg < earlier_avg * 0.9:
            return 'falling'
        else:
            return 'stable'
    
    def save_trends_data(self, data: Dict, filename: str = None) -> bool:
        """
        트렌드 데이터를 파일로 저장
        
        Args:
            data: 저장할 데이터
            filename: 파일명 (기본값: 자동 생성)
            
        Returns:
            저장 성공 여부
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'trends_data_{timestamp}.json'
            
            # trends_data 디렉토리 생성
            os.makedirs('trends_data', exist_ok=True)
            filepath = os.path.join('trends_data', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.console_log(f"[Trends] 트렌드 데이터 저장 완료: {filepath}")
            return True
            
        except Exception as e:
            self.console_log(f"[Trends] 데이터 저장 오류: {str(e)}")
            return False