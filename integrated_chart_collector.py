#!/usr/bin/env python3
"""
Integrated Chart Collector - 통합 차트 데이터 수집기
Last.fm, Billboard, Spotify, YouTube 차트를 통합하여 수집
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics

# 차트 연결기들 임포트
from lastfm_connector import LastfmConnector
from billboard_connector import BillboardConnector
from spotify_connector import SpotifyConnector
from youtube_chart_collector import YouTubeChartCollector

class IntegratedChartCollector:
    def __init__(self, console_log=None):
        """
        통합 차트 수집기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        
        # 각 차트 API 연결기 초기화
        try:
            self.lastfm = LastfmConnector(console_log=self.console_log)
            self.console_log("[IntegratedChart] Last.fm 연결기 초기화 완료")
        except Exception as e:
            self.console_log(f"[IntegratedChart] Last.fm 연결기 초기화 실패: {str(e)}")
            self.lastfm = None
        
        try:
            self.billboard = BillboardConnector(console_log=self.console_log)
            self.console_log("[IntegratedChart] Billboard 연결기 초기화 완료")
        except Exception as e:
            self.console_log(f"[IntegratedChart] Billboard 연결기 초기화 실패: {str(e)}")
            self.billboard = None
        
        try:
            self.spotify = SpotifyConnector(console_log=self.console_log)
            self.console_log("[IntegratedChart] Spotify 연결기 초기화 완료")
        except Exception as e:
            self.console_log(f"[IntegratedChart] Spotify 연결기 초기화 실패: {str(e)}")
            self.spotify = None
        
        try:
            self.youtube = YouTubeChartCollector(console_log=self.console_log)
            self.console_log("[IntegratedChart] YouTube 연결기 초기화 완료")
        except Exception as e:
            self.console_log(f"[IntegratedChart] YouTube 연결기 초기화 실패: {str(e)}")
            self.youtube = None
        
        # 차트 가중치 설정
        self.chart_weights = {
            'billboard': 0.3,     # 공식 차트, 높은 신뢰도
            'spotify': 0.25,      # 스트리밍 기반, 현재 트렌드
            'lastfm': 0.25,       # 실제 사용자 데이터, 글로벌
            'youtube': 0.2        # 조회수 기반, 바이럴
        }
        
        # 지역별 설정
        self.regions = ['korea', 'global']
        
    def collect_all_charts(self, region: str = 'korea', limit: int = 50) -> Dict:
        """
        모든 차트 API에서 데이터 수집 후 통합
        
        Args:
            region: 지역 ('korea', 'global')
            limit: 수집할 트랙 수
            
        Returns:
            통합 차트 데이터
        """
        try:
            self.console_log(f"[IntegratedChart] {region} 지역 통합 차트 수집 시작")
            
            all_chart_data = {}
            collection_status = {}
            
            # 1. Last.fm 글로벌 차트 수집
            if self.lastfm:
                try:
                    lastfm_data = self.lastfm.get_top_tracks(period='7day', limit=limit)
                    if lastfm_data['success']:
                        all_chart_data['lastfm'] = lastfm_data
                        collection_status['lastfm'] = 'success'
                        self.console_log(f"[IntegratedChart] Last.fm 차트 수집 성공: {len(lastfm_data['tracks'])}곡")
                    else:
                        collection_status['lastfm'] = f"failed: {lastfm_data.get('error', 'Unknown')}"
                except Exception as e:
                    collection_status['lastfm'] = f"error: {str(e)}"
                    self.console_log(f"[IntegratedChart] Last.fm 수집 오류: {str(e)}")
            else:
                collection_status['lastfm'] = 'not_available'
            
            # 2. Billboard 차트 수집
            if self.billboard:
                try:
                    # Hot 100 수집
                    billboard_data = self.billboard.get_hot_100()
                    if billboard_data['success']:
                        all_chart_data['billboard'] = billboard_data
                        collection_status['billboard'] = 'success'
                        self.console_log(f"[IntegratedChart] Billboard Hot 100 수집 성공: {len(billboard_data['tracks'])}곡")
                    else:
                        collection_status['billboard'] = f"failed: {billboard_data.get('error', 'Unknown')}"
                except Exception as e:
                    collection_status['billboard'] = f"error: {str(e)}"
                    self.console_log(f"[IntegratedChart] Billboard 수집 오류: {str(e)}")
            else:
                collection_status['billboard'] = 'not_available'
            
            # 3. Spotify 차트 수집
            if self.spotify:
                try:
                    playlist_type = 'top' if region == 'korea' else 'top'
                    spotify_data = self.spotify.get_trending_tracks(region=region, playlist_type=playlist_type, limit=limit)
                    if spotify_data['success']:
                        all_chart_data['spotify'] = spotify_data
                        collection_status['spotify'] = 'success'
                        self.console_log(f"[IntegratedChart] Spotify 차트 수집 성공: {len(spotify_data['tracks'])}곡")
                    else:
                        collection_status['spotify'] = f"failed: {spotify_data.get('error', 'Unknown')}"
                except Exception as e:
                    collection_status['spotify'] = f"error: {str(e)}"
                    self.console_log(f"[IntegratedChart] Spotify 수집 오류: {str(e)}")
            else:
                collection_status['spotify'] = 'not_available'
            
            # 4. YouTube 차트 수집
            if self.youtube:
                try:
                    youtube_data = self.youtube.collect_chart_data(region=region, max_results=limit)
                    if youtube_data['success']:
                        all_chart_data['youtube'] = youtube_data
                        collection_status['youtube'] = 'success'
                        self.console_log(f"[IntegratedChart] YouTube 차트 수집 성공: {len(youtube_data['chart_tracks'])}곡")
                    else:
                        collection_status['youtube'] = f"failed: {youtube_data.get('error', 'Unknown')}"
                except Exception as e:
                    collection_status['youtube'] = f"error: {str(e)}"
                    self.console_log(f"[IntegratedChart] YouTube 수집 오류: {str(e)}")
            else:
                collection_status['youtube'] = 'not_available'
            
            # 5. 통합 차트 생성
            integrated_chart = self._create_integrated_chart(all_chart_data, region, limit)
            
            result = {
                'success': True,
                'region': region,
                'collection_status': collection_status,
                'raw_chart_data': all_chart_data,
                'integrated_chart': integrated_chart,
                'total_sources': len([k for k, v in collection_status.items() if v == 'success']),
                'collected_at': datetime.now().isoformat()
            }
            
            self.console_log(f"[IntegratedChart] {region} 통합 차트 생성 완료: {len(integrated_chart['tracks'])}곡")
            return result
            
        except Exception as e:
            error_msg = f"통합 차트 수집 오류: {str(e)}"
            self.console_log(f"[IntegratedChart] {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def _create_integrated_chart(self, all_data: Dict, region: str, limit: int) -> Dict:
        """
        수집된 차트 데이터를 통합하여 하나의 차트 생성
        
        Args:
            all_data: 모든 차트 API에서 수집된 데이터
            region: 지역
            limit: 결과 트랙 수 제한
            
        Returns:
            통합 차트 데이터
        """
        try:
            track_scores = defaultdict(float)
            track_info = {}
            
            # 각 차트 소스별로 점수 계산
            for source, data in all_data.items():
                if not data.get('success'):
                    continue
                
                source_weight = self.chart_weights.get(source, 0.1)
                tracks = []
                
                # 소스별 트랙 데이터 추출
                if source == 'lastfm':
                    tracks = data.get('tracks', [])
                elif source == 'billboard':
                    tracks = data.get('tracks', [])
                elif source == 'spotify':
                    tracks = data.get('tracks', [])
                elif source == 'youtube':
                    tracks = data.get('chart_tracks', [])
                
                # 각 트랙의 점수 계산
                for track in tracks:
                    track_key = self._generate_track_key(track, source)
                    
                    # 순위 기반 점수 (1위=100점, 순위가 낮을수록 점수 감소)
                    rank = track.get('rank', track.get('position', 999))
                    if rank == 999:  # rank 정보가 없는 경우
                        rank = tracks.index(track) + 1
                    
                    rank_score = max(1, 101 - rank)
                    
                    # 인기도 점수
                    popularity = track.get('popularity', 50)
                    
                    # 조회수/재생수 점수 (정규화)
                    play_count = track.get('view_count', track.get('playcount', track.get('listeners', 0)))
                    play_score = min(50, play_count / 1000000) if play_count else 0
                    
                    # 최종 점수 계산
                    final_score = (rank_score * 0.5 + popularity * 0.3 + play_score * 0.2) * source_weight
                    track_scores[track_key] += final_score
                    
                    # 트랙 정보 저장 (가장 상세한 정보로 업데이트)
                    if track_key not in track_info or len(str(track)) > len(str(track_info[track_key])):
                        track_info[track_key] = {
                            'title': track.get('name', track.get('title', 'Unknown')),
                            'artist': track.get('main_artist', track.get('artist', 'Unknown')),
                            'popularity': popularity,
                            'sources': [],
                            'source_ranks': {},
                            'source_data': {}
                        }
                    
                    # 소스 정보 추가
                    track_info[track_key]['sources'].append(source)
                    track_info[track_key]['source_ranks'][source] = rank
                    track_info[track_key]['source_data'][source] = track
            
            # 점수순으로 정렬
            sorted_tracks = sorted(track_scores.items(), key=lambda x: x[1], reverse=True)
            
            # 최종 통합 차트 생성
            integrated_tracks = []
            for idx, (track_key, score) in enumerate(sorted_tracks[:limit]):
                track_data = track_info[track_key]
                
                integrated_track = {
                    'rank': idx + 1,
                    'id': f"integrated_{region}_{track_key}",
                    'title': track_data['title'],
                    'artist': track_data['artist'],
                    'integrated_score': round(score, 2),
                    'popularity': track_data['popularity'],
                    'source_count': len(set(track_data['sources'])),
                    'sources': list(set(track_data['sources'])),
                    'source_ranks': track_data['source_ranks'],
                    'trend_strength': self._calculate_trend_strength(track_data),
                    'consistency': self._calculate_consistency(track_data['source_ranks'])
                }
                
                integrated_tracks.append(integrated_track)
            
            # 통계 계산
            source_stats = {}
            for source in ['lastfm', 'billboard', 'spotify', 'youtube']:
                contributing_tracks = [t for t in integrated_tracks if source in t['sources']]
                source_stats[source] = {
                    'contributing_tracks': len(contributing_tracks),
                    'weight': self.chart_weights.get(source, 0),
                    'avg_rank_contribution': statistics.mean([t['source_ranks'].get(source, 999) for t in contributing_tracks]) if contributing_tracks else 0
                }
            
            return {
                'tracks': integrated_tracks,
                'total_tracks': len(integrated_tracks),
                'source_statistics': source_stats,
                'region': region,
                'integration_method': 'weighted_scoring',
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.console_log(f"[IntegratedChart] 통합 차트 생성 오류: {str(e)}")
            return {'tracks': [], 'error': str(e)}
    
    def _generate_track_key(self, track: Dict, source: str) -> str:
        """트랙의 고유 키 생성 (중복 제거용)"""
        title = track.get('name', track.get('title', '')).lower().strip()
        artist = track.get('main_artist', track.get('artist', '')).lower().strip()
        
        # 특수문자 제거 및 정규화
        import re
        title = re.sub(r'[^\w\s]', '', title).strip()
        artist = re.sub(r'[^\w\s]', '', artist).strip()
        
        return f"{artist}_{title}"
    
    def _calculate_trend_strength(self, track_data: Dict) -> str:
        """트렌드 강도 계산"""
        source_count = len(set(track_data['sources']))
        avg_rank = statistics.mean(track_data['source_ranks'].values()) if track_data['source_ranks'] else 50
        
        if source_count >= 3 and avg_rank <= 20:
            return 'Very Strong'
        elif source_count >= 2 and avg_rank <= 30:
            return 'Strong'
        elif source_count >= 2 or avg_rank <= 50:
            return 'Moderate'
        else:
            return 'Weak'
    
    def _calculate_consistency(self, source_ranks: Dict) -> float:
        """차트 간 순위 일관성 계산 (0-1, 1이 가장 일관적)"""
        if len(source_ranks) < 2:
            return 1.0
        
        ranks = list(source_ranks.values())
        rank_variance = statistics.variance(ranks) if len(ranks) > 1 else 0
        
        # 분산이 낮을수록 일관성이 높음 (최대 분산 10000으로 정규화)
        consistency = max(0, 1 - (rank_variance / 10000))
        return round(consistency, 3)
    
    def get_chart_comparison(self, region: str = 'korea') -> Dict:
        """
        차트 간 비교 분석
        
        Args:
            region: 분석할 지역
            
        Returns:
            차트 비교 분석 결과
        """
        try:
            all_charts = self.collect_all_charts(region=region, limit=100)
            
            if not all_charts['success']:
                return {'success': False, 'error': 'Failed to collect charts for comparison'}
            
            raw_data = all_charts['raw_chart_data']
            comparison = {}
            
            # 각 차트별 특성 분석
            for source, data in raw_data.items():
                if not data.get('success'):
                    continue
                
                tracks = data.get('tracks', data.get('chart_tracks', []))
                if not tracks:
                    continue
                
                # 상위 10곡 분석
                top10 = tracks[:10]
                
                comparison[source] = {
                    'total_tracks': len(tracks),
                    'top10_artists': [t.get('main_artist', t.get('artist', 'Unknown')) for t in top10],
                    'avg_popularity': statistics.mean([t.get('popularity', 50) for t in top10]),
                    'unique_characteristics': self._identify_chart_characteristics(tracks, source)
                }
            
            # 교집합 분석
            overlap_analysis = self._analyze_chart_overlaps(raw_data)
            
            result = {
                'success': True,
                'region': region,
                'chart_characteristics': comparison,
                'overlap_analysis': overlap_analysis,
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            error_msg = f"차트 비교 분석 오류: {str(e)}"
            self.console_log(f"[IntegratedChart] {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def _identify_chart_characteristics(self, tracks: List[Dict], source: str) -> Dict:
        """차트별 고유 특성 식별"""
        characteristics = {}
        
        if source == 'billboard':
            characteristics['focus'] = 'Commercial success in US market'
            characteristics['update_frequency'] = 'Weekly'
            characteristics['data_basis'] = 'Sales + Radio + Streaming'
        elif source == 'spotify':
            characteristics['focus'] = 'Streaming popularity'
            characteristics['update_frequency'] = 'Daily'
            characteristics['data_basis'] = 'Spotify streaming data'
        elif source == 'lastfm':
            characteristics['focus'] = 'Global user listening habits'
            characteristics['update_frequency'] = 'Real-time'
            characteristics['data_basis'] = 'User scrobbling data'
        elif source == 'youtube':
            characteristics['focus'] = 'Video popularity and discovery'
            characteristics['update_frequency'] = 'Dynamic'
            characteristics['data_basis'] = 'View count + engagement'
        
        return characteristics
    
    def _analyze_chart_overlaps(self, raw_data: Dict) -> Dict:
        """차트 간 겹치는 트랙 분석"""
        try:
            # 모든 차트의 트랙을 정규화된 키로 변환
            chart_tracks = {}
            for source, data in raw_data.items():
                if not data.get('success'):
                    continue
                
                tracks = data.get('tracks', data.get('chart_tracks', []))
                chart_tracks[source] = set()
                
                for track in tracks[:50]:  # 상위 50곡만 비교
                    track_key = self._generate_track_key(track, source)
                    chart_tracks[source].add(track_key)
            
            # 교집합 계산
            overlaps = {}
            chart_names = list(chart_tracks.keys())
            
            for i, chart1 in enumerate(chart_names):
                for chart2 in chart_names[i+1:]:
                    overlap = chart_tracks[chart1] & chart_tracks[chart2]
                    overlap_percentage = len(overlap) / min(len(chart_tracks[chart1]), len(chart_tracks[chart2])) * 100
                    
                    overlaps[f"{chart1}_vs_{chart2}"] = {
                        'common_tracks': len(overlap),
                        'overlap_percentage': round(overlap_percentage, 1),
                        'chart1_size': len(chart_tracks[chart1]),
                        'chart2_size': len(chart_tracks[chart2])
                    }
            
            return overlaps
            
        except Exception as e:
            self.console_log(f"[IntegratedChart] 차트 겹침 분석 오류: {str(e)}")
            return {}
    
    def get_api_status(self) -> Dict:
        """모든 차트 API 상태 확인"""
        status = {}
        
        if self.lastfm:
            status['lastfm'] = self.lastfm.get_api_status()
        else:
            status['lastfm'] = {'status': 'not_initialized'}
        
        if self.billboard:
            status['billboard'] = self.billboard.get_api_status()
        else:
            status['billboard'] = {'status': 'not_initialized'}
        
        if self.spotify:
            status['spotify'] = self.spotify.get_api_status()
        else:
            status['spotify'] = {'status': 'not_initialized'}
        
        if self.youtube:
            status['youtube'] = {'status': 'initialized' if self.youtube else 'not_initialized'}
        else:
            status['youtube'] = {'status': 'not_initialized'}
        
        return {
            'overall_status': 'operational',
            'individual_apis': status,
            'chart_weights': self.chart_weights,
            'supported_regions': self.regions
        }