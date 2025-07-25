#!/usr/bin/env python3
"""
Billboard Connector - Billboard 차트 데이터 수집
billboard.py 라이브러리 대신 직접 웹 스크래핑으로 구현
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import hashlib

class BillboardConnector:
    def __init__(self, console_log=None):
        """
        Billboard 연결기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        self.base_url = 'https://www.billboard.com'
        self.session = requests.Session()
        
        # User-Agent 설정 (봇 차단 방지)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 차트 URL 매핑
        self.chart_urls = {
            'hot-100': '/charts/hot-100',
            'billboard-200': '/charts/billboard-200',
            'artist-100': '/charts/artist-100',
            'global-200': '/charts/billboard-global-200',
            'global-excl-us': '/charts/billboard-global-excl-us',
            'streaming-songs': '/charts/streaming-songs',
            'radio-songs': '/charts/radio-songs',
            'digital-song-sales': '/charts/digital-song-sales'
        }
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # 1초 대기
        self.last_request_time = 0
        
        self.console_log("[Billboard] Billboard 차트 수집기 초기화 완료")
    
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """웹 페이지 요청 및 파싱"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - time_since_last)
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            self.last_request_time = time.time()
            
            # BeautifulSoup이 없는 경우 기본 텍스트 파싱
            try:
                from bs4 import BeautifulSoup
                return BeautifulSoup(response.text, 'html.parser')
            except ImportError:
                # BeautifulSoup 없이 간단한 파싱
                return self._simple_html_parse(response.text)
            
        except requests.exceptions.RequestException as e:
            self.console_log(f"[Billboard] 네트워크 오류: {str(e)}")
            return None
        except Exception as e:
            self.console_log(f"[Billboard] 페이지 파싱 오류: {str(e)}")
            return None
    
    def _simple_html_parse(self, html_text: str) -> Dict:
        """BeautifulSoup 없이 간단한 HTML 파싱"""
        # 간단한 정규식을 사용한 파싱 (제한적)
        chart_items = []
        
        # 차트 항목 패턴 찾기 (매우 기본적인 구현)
        # 실제로는 더 정교한 파싱이 필요함
        title_pattern = r'<h3[^>]*class="[^"]*chart-element__title[^"]*"[^>]*>([^<]+)</h3>'
        artist_pattern = r'<p[^>]*class="[^"]*chart-element__artist[^"]*"[^>]*>([^<]+)</p>'
        
        titles = re.findall(title_pattern, html_text, re.IGNORECASE)
        artists = re.findall(artist_pattern, html_text, re.IGNORECASE)
        
        return {
            'titles': titles,
            'artists': artists,
            'raw_html': html_text[:1000]  # 디버깅용 첫 1000자
        }
    
    def get_hot_100(self, date: str = None) -> Dict:
        """
        Billboard Hot 100 차트 수집
        
        Args:
            date: 차트 날짜 (YYYY-MM-DD 형식, None이면 최신)
            
        Returns:
            Hot 100 차트 데이터
        """
        try:
            self.console_log("[Billboard] Hot 100 차트 수집 시작")
            
            # URL 구성
            chart_url = urljoin(self.base_url, self.chart_urls['hot-100'])
            if date:
                chart_url += f'/{date}'
            
            # 페이지 요청
            soup = self._make_request(chart_url)
            if not soup:
                return {
                    'success': False,
                    'error': 'Billboard 페이지에 접근할 수 없습니다',
                    'tracks': []
                }
            
            # 차트 데이터 추출
            tracks_data = []
            
            # BeautifulSoup 객체인지 확인
            if hasattr(soup, 'find_all'):
                # BeautifulSoup 사용 가능
                chart_items = soup.find_all('li', class_='chart-list__element')
                
                for idx, item in enumerate(chart_items[:100]):  # Hot 100이므로 최대 100개
                    try:
                        # 순위
                        rank_elem = item.find('span', class_='chart-element__rank__number')
                        rank = int(rank_elem.text.strip()) if rank_elem else idx + 1
                        
                        # 곡명
                        title_elem = item.find('h3', class_='chart-element__title')
                        title = title_elem.text.strip() if title_elem else f"Track {rank}"
                        
                        # 아티스트
                        artist_elem = item.find('p', class_='chart-element__artist')
                        artist = artist_elem.text.strip() if artist_elem else "Unknown Artist"
                        
                        # 추가 정보 (있는 경우)
                        last_week_elem = item.find('span', class_='chart-element__last-week')
                        last_week = last_week_elem.text.strip() if last_week_elem else None
                        
                        peak_elem = item.find('span', class_='chart-element__peak')
                        peak = peak_elem.text.strip() if peak_elem else None
                        
                        weeks_elem = item.find('span', class_='chart-element__weeks-on-chart')
                        weeks_on_chart = weeks_elem.text.strip() if weeks_elem else None
                        
                        track_data = {
                            'rank': rank,
                            'id': f"bb_hot100_{hashlib.md5((title + artist).encode()).hexdigest()[:16]}",
                            'title': title,
                            'artist': artist,
                            'last_week': last_week,
                            'peak_position': peak,
                            'weeks_on_chart': weeks_on_chart,
                            'chart_type': 'hot-100',
                            'chart_date': date or datetime.now().strftime('%Y-%m-%d'),
                            'source': 'billboard'
                        }
                        
                        # 인기도 점수 (순위 기반, 1위=100점)
                        track_data['popularity'] = max(1, 101 - rank)
                        
                        tracks_data.append(track_data)
                        
                    except Exception as e:
                        self.console_log(f"[Billboard] 트랙 파싱 오류 (순위 {idx+1}): {str(e)}")
                        continue
            else:
                # 간단한 파싱 결과 처리
                titles = soup.get('titles', [])
                artists = soup.get('artists', [])
                
                for idx, (title, artist) in enumerate(zip(titles, artists)):
                    track_data = {
                        'rank': idx + 1,
                        'id': f"bb_hot100_{hashlib.md5((title + artist).encode()).hexdigest()[:16]}",
                        'title': title.strip(),
                        'artist': artist.strip(),
                        'chart_type': 'hot-100',
                        'chart_date': date or datetime.now().strftime('%Y-%m-%d'),
                        'popularity': max(1, 101 - (idx + 1)),
                        'source': 'billboard'
                    }
                    tracks_data.append(track_data)
            
            result = {
                'success': True,
                'chart_type': 'hot-100',
                'chart_date': date or datetime.now().strftime('%Y-%m-%d'),
                'total_tracks': len(tracks_data),
                'tracks': tracks_data,
                'source': 'billboard',
                'collected_at': datetime.now().isoformat()
            }
            
            self.console_log(f"[Billboard] Hot 100 차트 {len(tracks_data)}곡 수집 완료")
            return result
            
        except Exception as e:
            error_msg = f"Billboard Hot 100 수집 오류: {str(e)}"
            self.console_log(f"[Billboard] {error_msg}")
            return {'success': False, 'error': error_msg, 'tracks': []}
    
    def get_billboard_200(self, date: str = None) -> Dict:
        """
        Billboard 200 앨범 차트 수집
        
        Args:
            date: 차트 날짜 (YYYY-MM-DD 형식, None이면 최신)
            
        Returns:
            Billboard 200 차트 데이터
        """
        try:
            self.console_log("[Billboard] Billboard 200 앨범 차트 수집 시작")
            
            chart_url = urljoin(self.base_url, self.chart_urls['billboard-200'])
            if date:
                chart_url += f'/{date}'
            
            soup = self._make_request(chart_url)
            if not soup:
                return {'success': False, 'error': 'Billboard 200 페이지에 접근할 수 없습니다'}
            
            albums_data = []
            
            if hasattr(soup, 'find_all'):
                chart_items = soup.find_all('li', class_='chart-list__element')
                
                for idx, item in enumerate(chart_items[:200]):
                    try:
                        rank_elem = item.find('span', class_='chart-element__rank__number')
                        rank = int(rank_elem.text.strip()) if rank_elem else idx + 1
                        
                        title_elem = item.find('h3', class_='chart-element__title')
                        album_title = title_elem.text.strip() if title_elem else f"Album {rank}"
                        
                        artist_elem = item.find('p', class_='chart-element__artist')
                        artist = artist_elem.text.strip() if artist_elem else "Unknown Artist"
                        
                        album_data = {
                            'rank': rank,
                            'id': f"bb_200_{hashlib.md5((album_title + artist).encode()).hexdigest()[:16]}",
                            'album_title': album_title,
                            'artist': artist,
                            'chart_type': 'billboard-200',
                            'chart_date': date or datetime.now().strftime('%Y-%m-%d'),
                            'popularity': max(1, 201 - rank),
                            'source': 'billboard'
                        }
                        
                        albums_data.append(album_data)
                        
                    except Exception as e:
                        self.console_log(f"[Billboard] 앨범 파싱 오류 (순위 {idx+1}): {str(e)}")
                        continue
            
            result = {
                'success': True,
                'chart_type': 'billboard-200',
                'chart_date': date or datetime.now().strftime('%Y-%m-%d'),
                'total_albums': len(albums_data),
                'albums': albums_data,
                'source': 'billboard',
                'collected_at': datetime.now().isoformat()
            }
            
            self.console_log(f"[Billboard] Billboard 200 앨범 {len(albums_data)}개 수집 완료")
            return result
            
        except Exception as e:
            error_msg = f"Billboard 200 수집 오류: {str(e)}"
            self.console_log(f"[Billboard] {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_global_200(self, date: str = None) -> Dict:
        """
        Billboard Global 200 차트 수집
        
        Args:
            date: 차트 날짜 (YYYY-MM-DD 형식, None이면 최신)
            
        Returns:
            Global 200 차트 데이터
        """
        try:
            self.console_log("[Billboard] Global 200 차트 수집 시작")
            
            chart_url = urljoin(self.base_url, self.chart_urls['global-200'])
            if date:
                chart_url += f'/{date}'
            
            soup = self._make_request(chart_url)
            if not soup:
                return {'success': False, 'error': 'Global 200 페이지에 접근할 수 없습니다'}
            
            tracks_data = []
            
            if hasattr(soup, 'find_all'):
                chart_items = soup.find_all('li', class_='chart-list__element')
                
                for idx, item in enumerate(chart_items[:200]):
                    try:
                        rank_elem = item.find('span', class_='chart-element__rank__number')
                        rank = int(rank_elem.text.strip()) if rank_elem else idx + 1
                        
                        title_elem = item.find('h3', class_='chart-element__title')
                        title = title_elem.text.strip() if title_elem else f"Track {rank}"
                        
                        artist_elem = item.find('p', class_='chart-element__artist')
                        artist = artist_elem.text.strip() if artist_elem else "Unknown Artist"
                        
                        track_data = {
                            'rank': rank,
                            'id': f"bb_global200_{hashlib.md5((title + artist).encode()).hexdigest()[:16]}",
                            'title': title,
                            'artist': artist,
                            'chart_type': 'global-200',
                            'chart_date': date or datetime.now().strftime('%Y-%m-%d'),
                            'popularity': max(1, 201 - rank),
                            'source': 'billboard'
                        }
                        
                        tracks_data.append(track_data)
                        
                    except Exception as e:
                        self.console_log(f"[Billboard] Global 트랙 파싱 오류 (순위 {idx+1}): {str(e)}")
                        continue
            
            result = {
                'success': True,
                'chart_type': 'global-200',
                'chart_date': date or datetime.now().strftime('%Y-%m-%d'),
                'total_tracks': len(tracks_data),
                'tracks': tracks_data,
                'source': 'billboard',
                'collected_at': datetime.now().isoformat()
            }
            
            self.console_log(f"[Billboard] Global 200 차트 {len(tracks_data)}곡 수집 완료")
            return result
            
        except Exception as e:
            error_msg = f"Billboard Global 200 수집 오류: {str(e)}"
            self.console_log(f"[Billboard] {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def search_chart_history(self, artist: str, track: str = None) -> Dict:
        """
        아티스트/트랙의 차트 히스토리 검색 (제한적 구현)
        
        Args:
            artist: 아티스트명
            track: 트랙명 (선택사항)
            
        Returns:
            차트 히스토리 데이터
        """
        try:
            # 현재 차트에서 해당 아티스트/트랙 찾기
            current_charts = []
            
            # Hot 100에서 검색
            hot100 = self.get_hot_100()
            if hot100['success']:
                matching_tracks = []
                for track_data in hot100['tracks']:
                    if artist.lower() in track_data['artist'].lower():
                        if not track or track.lower() in track_data['title'].lower():
                            matching_tracks.append(track_data)
                
                if matching_tracks:
                    current_charts.append({
                        'chart_type': 'hot-100',
                        'matches': matching_tracks
                    })
            
            result = {
                'success': True,
                'artist': artist,
                'track': track,
                'current_chart_positions': current_charts,
                'searched_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            error_msg = f"차트 히스토리 검색 오류: {str(e)}"
            self.console_log(f"[Billboard] {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_available_charts(self) -> Dict:
        """사용 가능한 차트 목록 반환"""
        return {
            'success': True,
            'available_charts': list(self.chart_urls.keys()),
            'chart_descriptions': {
                'hot-100': 'Billboard Hot 100 - 가장 인기 있는 곡 100곡',
                'billboard-200': 'Billboard 200 - 가장 인기 있는 앨범 200개',
                'artist-100': 'Artist 100 - 가장 인기 있는 아티스트 100명',
                'global-200': 'Global 200 - 글로벌 인기 곡 200곡',
                'global-excl-us': 'Global Excl. US - 미국 제외 글로벌 차트',
                'streaming-songs': 'Streaming Songs - 스트리밍 차트',
                'radio-songs': 'Radio Songs - 라디오 방송 차트',
                'digital-song-sales': 'Digital Song Sales - 디지털 판매 차트'
            }
        }
    
    def get_api_status(self) -> Dict:
        """Billboard 연결 상태 확인"""
        return {
            'base_url': self.base_url,
            'available_charts': len(self.chart_urls),
            'rate_limit_delay': self.rate_limit_delay,
            'session_configured': bool(self.session),
            'charts_supported': list(self.chart_urls.keys())
        }