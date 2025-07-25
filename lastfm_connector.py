#!/usr/bin/env python3
"""
Last.fm Connector - Last.fm API를 통한 실시간 음악 트렌드 데이터 수집
글로벌 스크로블링 데이터 기반 차트 및 트렌드 분석
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter
import hashlib

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class LastfmConnector:
    def __init__(self, console_log=None):
        """
        Last.fm 연결기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        self.api_key = os.getenv('LASTFM_API_KEY')
        self.api_secret = os.getenv('LASTFM_API_SECRET')
        self.base_url = 'http://ws.audioscrobbler.com/2.0/'
        self.session = requests.Session()
        
        # API 호출 제한 (초당 5회)
        self.rate_limit_delay = 0.2
        self.last_request_time = 0
        
        if self.api_key:
            self.console_log("[Last.fm] Last.fm API 연결기 초기화 완료")
        else:
            self.console_log("[Last.fm] 경고: Last.fm API 키가 설정되지 않았습니다")
            self.console_log("[Last.fm] 환경변수 LASTFM_API_KEY 설정 필요")
    
    def _make_request(self, method: str, params: Dict = None) -> Optional[Dict]:
        """Last.fm API 요청 실행"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - time_since_last)
            
            # 기본 파라미터
            request_params = {
                'method': method,
                'api_key': self.api_key,
                'format': 'json'
            }
            
            if params:
                request_params.update(params)
            
            response = self.session.get(self.base_url, params=request_params, timeout=10)
            response.raise_for_status()
            
            self.last_request_time = time.time()
            
            data = response.json()
            if 'error' in data:
                self.console_log(f"[Last.fm] API 오류: {data.get('message', 'Unknown error')}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.console_log(f"[Last.fm] 네트워크 오류: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.console_log(f"[Last.fm] JSON 파싱 오류: {str(e)}")
            return None
        except Exception as e:
            self.console_log(f"[Last.fm] API 요청 오류: {str(e)}")
            return None
    
    def get_top_tracks(self, period: str = '7day', limit: int = 50) -> Dict:
        """
        글로벌 Top 트랙 차트 수집
        
        Args:
            period: 기간 ('overall', '7day', '1month', '3month', '6month', '12month')
            limit: 수집할 트랙 수 (최대 1000)
            
        Returns:
            Top 트랙 차트 데이터
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Last.fm API 키가 설정되지 않았습니다',
                    'tracks': []
                }
            
            self.console_log(f"[Last.fm] 글로벌 Top 트랙 수집: {period} ({limit}곡)")
            
            data = self._make_request('chart.gettoptracks', {
                'period': period,
                'limit': min(limit, 1000)
            })
            
            if not data or 'tracks' not in data:
                return {
                    'success': False,
                    'error': 'Last.fm에서 트랙 데이터를 가져올 수 없습니다',
                    'tracks': []
                }
            
            tracks_data = []
            for idx, track in enumerate(data['tracks']['track']):
                track_info = {
                    'rank': idx + 1,
                    'id': f"lastfm_{hashlib.md5((track['name'] + track['artist']['name']).encode()).hexdigest()[:16]}",
                    'name': track['name'],
                    'artist': track['artist']['name'],
                    'playcount': int(track['playcount']),
                    'listeners': int(track['listeners']),
                    'url': track['url'],
                    'chart_period': period,
                    'source': 'lastfm_global'
                }
                
                # 인기도 점수 계산 (0-100)
                # playcount와 listeners 조합으로 계산
                max_playcount = int(data['tracks']['track'][0]['playcount']) if data['tracks']['track'] else 1
                popularity = min(100, int((track_info['playcount'] / max_playcount) * 100))
                track_info['popularity'] = max(1, popularity)
                
                tracks_data.append(track_info)
            
            result = {
                'success': True,
                'period': period,
                'total_tracks': len(tracks_data),
                'tracks': tracks_data,
                'source': 'lastfm',
                'collected_at': datetime.now().isoformat()
            }
            
            self.console_log(f"[Last.fm] 글로벌 Top 트랙 {len(tracks_data)}곡 수집 완료")
            return result
            
        except Exception as e:
            error_msg = f"Last.fm Top 트랙 수집 오류: {str(e)}"
            self.console_log(f"[Last.fm] {error_msg}")
            return {'success': False, 'error': error_msg, 'tracks': []}
    
    def get_top_artists(self, period: str = '7day', limit: int = 50) -> Dict:
        """
        글로벌 Top 아티스트 차트 수집
        
        Args:
            period: 기간 ('overall', '7day', '1month', '3month', '6month', '12month')
            limit: 수집할 아티스트 수 (최대 1000)
            
        Returns:
            Top 아티스트 차트 데이터
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Last.fm API 키가 설정되지 않았습니다'}
            
            self.console_log(f"[Last.fm] 글로벌 Top 아티스트 수집: {period} ({limit}명)")
            
            data = self._make_request('chart.gettopartists', {
                'period': period,
                'limit': min(limit, 1000)
            })
            
            if not data or 'artists' not in data:
                return {'success': False, 'error': 'Last.fm에서 아티스트 데이터를 가져올 수 없습니다'}
            
            artists_data = []
            for idx, artist in enumerate(data['artists']['artist']):
                artist_info = {
                    'rank': idx + 1,
                    'name': artist['name'],
                    'playcount': int(artist['playcount']),
                    'listeners': int(artist['listeners']),
                    'url': artist['url'],
                    'chart_period': period
                }
                artists_data.append(artist_info)
            
            result = {
                'success': True,
                'period': period,
                'total_artists': len(artists_data),
                'artists': artists_data,
                'collected_at': datetime.now().isoformat()
            }
            
            self.console_log(f"[Last.fm] 글로벌 Top 아티스트 {len(artists_data)}명 수집 완료")
            return result
            
        except Exception as e:
            error_msg = f"Last.fm Top 아티스트 수집 오류: {str(e)}"
            self.console_log(f"[Last.fm] {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_track_info(self, artist: str, track: str) -> Dict:
        """
        특정 트랙 상세 정보 조회
        
        Args:
            artist: 아티스트명
            track: 트랙명
            
        Returns:
            트랙 상세 정보
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Last.fm API 키가 설정되지 않았습니다'}
            
            data = self._make_request('track.getInfo', {
                'artist': artist,
                'track': track
            })
            
            if not data or 'track' not in data:
                return {'success': False, 'error': f'트랙 정보를 찾을 수 없습니다: {artist} - {track}'}
            
            track_data = data['track']
            
            # 태그 정보 추출
            tags = []
            if 'toptags' in track_data and 'tag' in track_data['toptags']:
                for tag in track_data['toptags']['tag']:
                    tags.append(tag['name'])
            
            result = {
                'success': True,
                'name': track_data['name'],
                'artist': track_data['artist']['name'],
                'playcount': int(track_data.get('playcount', 0)),
                'listeners': int(track_data.get('listeners', 0)),
                'url': track_data['url'],
                'tags': tags[:10],  # 상위 10개 태그만
                'wiki_summary': track_data.get('wiki', {}).get('summary', ''),
                'duration': int(track_data.get('duration', 0)),
                'retrieved_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            error_msg = f"트랙 정보 조회 오류: {str(e)}"
            self.console_log(f"[Last.fm] {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def search_tracks(self, query: str, limit: int = 30) -> Dict:
        """
        트랙 검색
        
        Args:
            query: 검색 쿼리
            limit: 결과 수 제한
            
        Returns:
            검색 결과
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Last.fm API 키가 설정되지 않았습니다'}
            
            self.console_log(f"[Last.fm] 트랙 검색: {query}")
            
            data = self._make_request('track.search', {
                'track': query,
                'limit': min(limit, 50)
            })
            
            if not data or 'results' not in data:
                return {'success': False, 'error': f'검색 결과가 없습니다: {query}'}
            
            search_results = []
            if 'trackmatches' in data['results'] and 'track' in data['results']['trackmatches']:
                for track in data['results']['trackmatches']['track']:
                    track_info = {
                        'name': track['name'],
                        'artist': track['artist'],
                        'url': track['url'],
                        'listeners': int(track.get('listeners', 0)),
                        'query': query
                    }
                    search_results.append(track_info)
            
            result = {
                'success': True,
                'query': query,
                'total_results': len(search_results),
                'tracks': search_results,
                'searched_at': datetime.now().isoformat()
            }
            
            self.console_log(f"[Last.fm] 트랙 검색 완료: {len(search_results)}개 결과")
            return result
            
        except Exception as e:
            error_msg = f"트랙 검색 오류: {str(e)}"
            self.console_log(f"[Last.fm] {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_trending_tags(self, limit: int = 50) -> Dict:
        """
        트렌딩 태그 수집 (장르/스타일 분석용)
        
        Args:
            limit: 수집할 태그 수
            
        Returns:
            트렌딩 태그 데이터
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Last.fm API 키가 설정되지 않았습니다'}
            
            self.console_log(f"[Last.fm] 트렌딩 태그 수집: {limit}개")
            
            data = self._make_request('chart.gettoptags', {
                'limit': min(limit, 1000)
            })
            
            if not data or 'tags' not in data:
                return {'success': False, 'error': 'Last.fm에서 태그 데이터를 가져올 수 없습니다'}
            
            tags_data = []
            for idx, tag in enumerate(data['tags']['tag']):
                tag_info = {
                    'rank': idx + 1,
                    'name': tag['name'],
                    'count': int(tag['count']),
                    'url': tag['url']
                }
                tags_data.append(tag_info)
            
            result = {
                'success': True,
                'total_tags': len(tags_data),
                'tags': tags_data,
                'collected_at': datetime.now().isoformat()
            }
            
            self.console_log(f"[Last.fm] 트렌딩 태그 {len(tags_data)}개 수집 완료")
            return result
            
        except Exception as e:
            error_msg = f"트렌딩 태그 수집 오류: {str(e)}"
            self.console_log(f"[Last.fm] {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_api_status(self) -> Dict:
        """Last.fm API 연결 상태 확인"""
        return {
            'api_key_configured': bool(self.api_key),
            'api_secret_configured': bool(self.api_secret),
            'base_url': self.base_url,
            'rate_limit_delay': self.rate_limit_delay,
            'available_periods': ['overall', '7day', '1month', '3month', '6month', '12month']
        }