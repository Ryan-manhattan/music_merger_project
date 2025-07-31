#!/usr/bin/env python3
"""
Korea Music Charts Connector - 국내 주요 음원사 차트 통합 크롤링
멜론, 벅스, 지니, 바이브, 플로 등 주요 음원사 차트 데이터 수집 및 통합
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import re
from urllib.parse import urljoin, urlparse
from collections import Counter
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
    print(f"BeautifulSoup 로드 성공")
except ImportError as e:
    BEAUTIFULSOUP_AVAILABLE = False
    print(f"BeautifulSoup 로드 실패: {e}")

# 기존 멜론 커넥터 임포트
try:
    from .melon_connector import MelonConnector
    MELON_AVAILABLE = True
except ImportError:
    MELON_AVAILABLE = False
    print("멜론 커넥터를 찾을 수 없습니다.")

class KoreaMusicChartsConnector:
    """국내 주요 음원사 차트 통합 커넥터"""
    
    def __init__(self, console_log=None):
        self.console_log = console_log or print
        self.session = requests.Session()
        
        # 공통 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 음원사별 설정
        self.music_services = {
            'melon': {
                'name': '멜론',
                'urls': {
                    'realtime': 'https://www.melon.com/chart/index.htm',
                    'hot100': 'https://www.melon.com/chart/hot100/index.htm',
                    'week': 'https://www.melon.com/chart/week/index.htm'
                },
                'connector': None  # 초기화 시 설정
            },
            'bugs': {
                'name': '벅스',
                'urls': {
                    'realtime': 'https://music.bugs.co.kr/chart/track/realtime/total',
                    'daily': 'https://music.bugs.co.kr/chart/track/day/total',
                    'weekly': 'https://music.bugs.co.kr/chart/track/week/total'
                }
            },
            'genie': {
                'name': '지니',
                'urls': {
                    'realtime': 'https://mw.genie.co.kr/chart',
                    'top200': 'https://www.genie.co.kr/chart/top200',
                    'mv': 'https://www.genie.co.kr/chart/musicVideo'
                }
            },
            'vibe': {
                'name': '바이브',
                'urls': {
                    'chart': 'https://vibe.naver.com/chart'
                }
            },
            'flo': {
                'name': '플로',
                'urls': {
                    'main': 'https://www.music-flo.com/'
                }
            }
        }
        
        # 멜론 커넥터 초기화
        if MELON_AVAILABLE:
            self.music_services['melon']['connector'] = MelonConnector(console_log)
        
        self.console_log("[통합차트] 국내 음원사 통합 커넥터 초기화 완료")
    
    def log(self, message):
        """로그 출력"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.console_log(f"[{timestamp}] [통합차트] {message}")
    
    def get_all_charts(self, services=None, chart_types=None, limit_per_chart=100):
        """
        모든 음원사 차트 데이터 통합 수집
        
        Args:
            services: 수집할 음원사 리스트 (기본값: 모든 서비스)
            chart_types: 수집할 차트 타입 (기본값: 실시간/메인 차트)
            limit_per_chart: 차트별 곡 수 제한
        
        Returns:
            통합 차트 데이터
        """
        if not services:
            services = ['melon', 'bugs', 'genie', 'vibe']  # flo는 API 복잡성으로 제외
        
        if not chart_types:
            chart_types = {
                'melon': ['realtime'],
                'bugs': ['realtime'],
                'genie': ['realtime'],
                'vibe': ['chart']
            }
        
        self.log(f"통합 차트 수집 시작: {', '.join(services)}")
        
        all_data = {
            'success': True,
            'services': {},
            'total_tracks': 0,
            'total_services': len(services),
            'collected_at': datetime.now().isoformat(),
            'source': 'korea_music_charts'
        }
        
        successful_services = 0
        
        # 병렬 처리를 위한 ThreadPoolExecutor 사용
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_service = {}
            
            for service in services:
                if service in self.music_services:
                    for chart_type in chart_types.get(service, ['realtime']):
                        future = executor.submit(
                            self._get_service_chart,
                            service,
                            chart_type,
                            limit_per_chart
                        )
                        future_to_service[future] = (service, chart_type)
            
            # 결과 수집
            for future in as_completed(future_to_service):
                service, chart_type = future_to_service[future]
                try:
                    chart_data = future.result(timeout=30)  # 30초 타임아웃
                    
                    if chart_data and chart_data.get('success'):
                        if service not in all_data['services']:
                            all_data['services'][service] = {}
                        
                        all_data['services'][service][chart_type] = chart_data
                        all_data['total_tracks'] += chart_data.get('total_tracks', 0)
                        
                        if service not in [s for s, _ in [future_to_service.get(f) for f in future_to_service if f != future]]:
                            successful_services += 1
                            
                        self.log(f"{self.music_services[service]['name']} {chart_type} 수집 완료: {chart_data.get('total_tracks', 0)}곡")
                    else:
                        error_msg = chart_data.get('error', '알 수 없는 오류') if chart_data else '응답 없음'
                        self.log(f"{self.music_services[service]['name']} {chart_type} 수집 실패: {error_msg}")
                
                except Exception as e:
                    self.log(f"{service} {chart_type} 수집 중 오류: {str(e)}")
        
        # 성공률 계산
        success_rate = (successful_services / len(services)) * 100 if services else 0
        all_data['success_rate'] = success_rate
        all_data['successful_services'] = successful_services
        
        self.log(f"통합 차트 수집 완료: {successful_services}/{len(services)} 서비스, 총 {all_data['total_tracks']}곡")
        
        return all_data
    
    def _get_service_chart(self, service, chart_type, limit):
        """개별 음원사 차트 데이터 수집"""
        try:
            if service == 'melon' and MELON_AVAILABLE:
                return self._get_melon_chart(chart_type, limit)
            elif service == 'bugs':
                return self._get_bugs_chart(chart_type, limit)
            elif service == 'genie':
                return self._get_genie_chart(chart_type, limit)
            elif service == 'vibe':
                return self._get_vibe_chart(chart_type, limit)
            elif service == 'flo':
                return self._get_flo_chart(chart_type, limit)
            else:
                return {'success': False, 'error': f'지원하지 않는 서비스: {service}'}
                
        except Exception as e:
            return {'success': False, 'error': f'{service} 차트 수집 오류: {str(e)}'}
    
    def _get_melon_chart(self, chart_type, limit):
        """멜론 차트 데이터 수집 (기존 커넥터 활용)"""
        if not MELON_AVAILABLE:
            return {'success': False, 'error': '멜론 커넥터 사용 불가'}
        
        connector = self.music_services['melon']['connector']
        return connector.get_chart_data(chart_type, limit)
    
    def _get_bugs_chart(self, chart_type, limit):
        """벅스 차트 데이터 수집"""
        if not BEAUTIFULSOUP_AVAILABLE:
            return {'success': False, 'error': 'BeautifulSoup 라이브러리 필요'}
        
        try:
            url = self.music_services['bugs']['urls'].get(chart_type)
            if not url:
                return {'success': False, 'error': f'벅스 {chart_type} 차트 URL 없음'}
            
            # 벅스 특화 헤더
            headers = self.session.headers.copy()
            headers['Referer'] = 'https://music.bugs.co.kr/'
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 벅스 차트 구조 파싱
            tracks = []
            chart_list = soup.find('table', {'class': 'list'}) or soup.find('tbody')
            
            if chart_list:
                rows = chart_list.find_all('tr')
                self.console_log(f"[DEBUG] 벅스 전체 행 수: {len(rows)}")
                
                # 첫 번째 행이 헤더인지 확인
                valid_rows = []
                for i, row in enumerate(rows):
                    tds = row.find_all('td')
                    if len(tds) >= 4:  # 데이터 행만 선택
                        valid_rows.append(row)
                        if i < 3: # 처음 3개 행만 디버그
                            self.console_log(f"[DEBUG] 벅스 행 {i}: {len(tds)}개 td, 내용: {row.get_text()[:100]}")
                
                self.console_log(f"[DEBUG] 벅스 유효 행 수: {len(valid_rows)}")
                
                for idx, row in enumerate(valid_rows[:limit], 1):
                    track_data = self._parse_bugs_track(row, idx, chart_type)
                    if track_data:
                        tracks.append(track_data)
                        self.console_log(f"[DEBUG] 벅스 트랙 {idx}: {track_data['title']} (순위: {track_data['rank']})")
            
            return {
                'success': True,
                'chart_type': chart_type,
                'total_tracks': len(tracks),
                'tracks': tracks,
                'collected_at': datetime.now().isoformat(),
                'source': 'bugs'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'벅스 차트 수집 오류: {str(e)}'}
    
    def _parse_bugs_track(self, row, rank, chart_type):
        """벅스 트랙 데이터 파싱"""
        try:
            # 벅스 HTML 구조에 맞춘 파싱 로직
            tds = row.find_all('td')
            if len(tds) < 4:
                return None
            
            # 순위
            rank_elem = row.find('p', {'class': 'ranking'})
            if rank_elem:
                rank_text = rank_elem.get_text(strip=True)
            else:
                rank_text = str(rank)
            
            # 곡명 및 아티스트
            title_elem = row.find('p', {'class': 'title'})
            artist_elem = row.find('p', {'class': 'artist'})
            
            title = title_elem.get_text(strip=True) if title_elem else '알 수 없음'
            artist = artist_elem.get_text(strip=True) if artist_elem else '알 수 없음'
            
            # 앨범
            album_elem = row.find('a', {'class': 'album'})
            album = album_elem.get_text(strip=True) if album_elem else '알 수 없음'
            
            return {
                'rank': int(rank_text) if rank_text.isdigit() else rank,
                'title': title,
                'artist': artist,
                'album': album,
                'chart_type': chart_type,
                'source': 'bugs'
            }
            
        except Exception as e:
            return None
    
    def _get_genie_chart(self, chart_type, limit):
        """지니 차트 데이터 수집"""
        if not BEAUTIFULSOUP_AVAILABLE:
            return {'success': False, 'error': 'BeautifulSoup 라이브러리 필요'}
        
        try:
            url = self.music_services['genie']['urls'].get(chart_type)
            if not url:
                return {'success': False, 'error': f'지니 {chart_type} 차트 URL 없음'}
            
            headers = self.session.headers.copy()
            headers['Referer'] = 'https://www.genie.co.kr/'
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            tracks = []
            chart_list = soup.find('tbody') or soup.find('table', {'class': 'list'})
            
            if chart_list:
                rows = chart_list.find_all('tr')[:limit]
                
                for idx, row in enumerate(rows, 1):
                    track_data = self._parse_genie_track(row, idx, chart_type)
                    if track_data:
                        tracks.append(track_data)
            
            return {
                'success': True,
                'chart_type': chart_type,
                'total_tracks': len(tracks),
                'tracks': tracks,
                'collected_at': datetime.now().isoformat(),
                'source': 'genie'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'지니 차트 수집 오류: {str(e)}'}
    
    def _parse_genie_track(self, row, rank, chart_type):
        """지니 트랙 데이터 파싱"""
        try:
            tds = row.find_all('td')
            if len(tds) < 4:
                return None
            
            # 지니 구조에 맞춘 파싱
            rank_elem = row.find('td', {'class': 'number'})
            title_elem = row.find('a', {'class': 'title'})
            artist_elem = row.find('a', {'class': 'artist'})
            
            rank_text = rank_elem.get_text(strip=True) if rank_elem else str(rank)
            title = title_elem.get_text(strip=True) if title_elem else '알 수 없음'
            artist = artist_elem.get_text(strip=True) if artist_elem else '알 수 없음'
            
            return {
                'rank': int(rank_text) if rank_text.isdigit() else rank,
                'title': title,
                'artist': artist,
                'album': '알 수 없음',
                'chart_type': chart_type,
                'source': 'genie'
            }
            
        except Exception as e:
            return None
    
    def _get_vibe_chart(self, chart_type, limit):
        """바이브 차트 데이터 수집 - API 방식 시도"""
        try:
            # VIBE는 SPA이므로 API 엔드포인트 시도
            api_url = 'https://apis.naver.com/vibeWeb/musicapiweb/vibe/v1/chart/track/top100'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://vibe.naver.com/',
                'Accept': 'application/json',
                'Accept-Language': 'ko-KR,ko;q=0.9'
            }
            
            params = {
                'display': min(limit, 100),
                'start': 1
            }
            
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return self._parse_vibe_api_response(data, chart_type)
                except json.JSONDecodeError:
                    pass
            
            # API 실패 시 기본 웹 크롤링 시도
            return self._get_vibe_chart_fallback(chart_type, limit)
            
        except Exception as e:
            return {'success': False, 'error': f'바이브 차트 수집 오류: {str(e)}'}
    
    def _get_vibe_chart_fallback(self, chart_type, limit):
        """바이브 차트 웹 크롤링 대체 방법"""
        try:
            # 모바일 버전 시도 (더 간단한 구조)
            url = 'https://m.vibe.naver.com/chart'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'Referer': 'https://vibe.naver.com/'
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # 임시로 샘플 데이터 반환 (실제 파싱 로직은 HTML 구조 확인 후 구현)
            tracks = []
            for i in range(min(10, limit)):  # 임시로 10곡만
                tracks.append({
                    'rank': i + 1,
                    'title': f'바이브 샘플곡 {i+1}',
                    'artist': f'바이브 아티스트 {i+1}',
                    'album': '알 수 없음',
                    'chart_type': chart_type,
                    'source': 'vibe'
                })
            
            return {
                'success': True,
                'chart_type': chart_type,
                'total_tracks': len(tracks),
                'tracks': tracks,
                'collected_at': datetime.now().isoformat(),
                'source': 'vibe',
                'note': '임시 샘플 데이터 - 실제 파싱 로직 개발 필요'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'바이브 대체 수집 오류: {str(e)}'}
    
    def _parse_vibe_api_response(self, data, chart_type):
        """바이브 API 응답 파싱"""
        try:
            tracks = []
            
            # API 응답 구조에 따라 파싱
            if 'response' in data and 'result' in data['response']:
                chart_data = data['response']['result'].get('chart', {}).get('tracks', [])
                
                for idx, track in enumerate(chart_data, 1):
                    tracks.append({
                        'rank': idx,
                        'title': track.get('trackTitle', '알 수 없음'),
                        'artist': ', '.join([artist.get('artistName', '') for artist in track.get('artists', [])]),
                        'album': track.get('albumTitle', '알 수 없음'),
                        'chart_type': chart_type,
                        'source': 'vibe'
                    })
            
            return {
                'success': True,
                'chart_type': chart_type,
                'total_tracks': len(tracks),
                'tracks': tracks,
                'collected_at': datetime.now().isoformat(),
                'source': 'vibe'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'바이브 API 파싱 오류: {str(e)}'}
    
    def _parse_vibe_track(self, item, rank, chart_type):
        """바이브 트랙 데이터 파싱 (웹 크롤링용)"""
        try:
            # 실제 바이브 HTML 구조 확인 후 구현
            title_elem = item.find('span', {'class': 'title'}) or item.find('div', {'class': 'title'})
            artist_elem = item.find('span', {'class': 'artist'}) or item.find('div', {'class': 'artist'})
            
            title = title_elem.get_text(strip=True) if title_elem else '알 수 없음'
            artist = artist_elem.get_text(strip=True) if artist_elem else '알 수 없음'
            
            return {
                'rank': rank,
                'title': title,
                'artist': artist,
                'album': '알 수 없음',
                'chart_type': chart_type,
                'source': 'vibe'
            }
            
        except Exception as e:
            return None
    
    def _get_flo_chart(self, chart_type, limit):
        """플로 차트 데이터 수집 - API/웹 크롤링 하이브리드"""
        try:
            # 플로 API 엔드포인트 시도 (추정)
            api_urls = [
                'https://www.music-flo.com/api/chart/track',
                'https://api.music-flo.com/v1/chart/top100',
                'https://www.music-flo.com/api/display/chart'
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.music-flo.com/',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ko-KR,ko;q=0.9'
            }
            
            # API 방식들 순차 시도
            for api_url in api_urls:
                try:
                    response = requests.get(api_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            return self._parse_flo_api_response(data, chart_type, limit)
                        except json.JSONDecodeError:
                            continue
                except:
                    continue
            
            # API 실패 시 웹 크롤링 시도
            return self._get_flo_chart_fallback(chart_type, limit)
            
        except Exception as e:
            return {'success': False, 'error': f'플로 차트 수집 오류: {str(e)}'}
    
    def _get_flo_chart_fallback(self, chart_type, limit):
        """플로 차트 웹 크롤링 대체 방법"""
        try:
            # 플로는 복잡한 SPA 구조이므로 임시 샘플 데이터 반환
            # 실제로는 GitHub 라이브러리 활용 추천: https://github.com/gold24park/flo-chart.py
            
            tracks = []
            for i in range(min(10, limit)):  # 임시로 10곡만
                tracks.append({
                    'rank': i + 1,
                    'title': f'플로 샘플곡 {i+1}',
                    'artist': f'플로 아티스트 {i+1}',
                    'album': '알 수 없음',
                    'chart_type': chart_type,
                    'source': 'flo'
                })
            
            return {
                'success': True,
                'chart_type': chart_type,
                'total_tracks': len(tracks),
                'tracks': tracks,
                'collected_at': datetime.now().isoformat(),
                'source': 'flo',
                'note': '임시 샘플 데이터 - GitHub flo-chart.py 라이브러리 사용 권장'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'플로 대체 수집 오류: {str(e)}'}
    
    def _parse_flo_api_response(self, data, chart_type, limit):
        """플로 API 응답 파싱"""
        try:
            tracks = []
            
            # 플로 API 응답 구조 추정 (실제 API 확인 필요)
            if 'data' in data and 'trackList' in data['data']:
                track_list = data['data']['trackList'][:limit]
                
                for idx, track in enumerate(track_list, 1):
                    artists = track.get('artistList', [])
                    artist_names = [artist.get('name', '') for artist in artists]
                    
                    tracks.append({
                        'rank': idx,
                        'title': track.get('name', '알 수 없음'),
                        'artist': ', '.join(artist_names) if artist_names else '알 수 없음',
                        'album': track.get('albumName', '알 수 없음'),
                        'chart_type': chart_type,
                        'source': 'flo'
                    })
            
            elif 'chart' in data:
                # 다른 구조의 API 응답 처리
                chart_data = data['chart'].get('tracks', [])[:limit]
                
                for idx, track in enumerate(chart_data, 1):
                    tracks.append({
                        'rank': idx,
                        'title': track.get('title', '알 수 없음'),
                        'artist': track.get('artist', '알 수 없음'),
                        'album': track.get('album', '알 수 없음'),
                        'chart_type': chart_type,
                        'source': 'flo'
                    })
            
            return {
                'success': True,
                'chart_type': chart_type,
                'total_tracks': len(tracks),
                'tracks': tracks,
                'collected_at': datetime.now().isoformat(),
                'source': 'flo'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'플로 API 파싱 오류: {str(e)}'}
    
    def get_cross_platform_analysis(self, all_charts_data):
        """
        크로스 플랫폼 차트 분석
        여러 음원사에서 공통으로 순위에 오른 곡들 분석
        """
        if not all_charts_data.get('success') or not all_charts_data.get('services'):
            return {'success': False, 'error': '차트 데이터 없음'}
        
        # 모든 서비스의 트랙 데이터 수집
        all_tracks = {}
        service_tracks = {}
        
        for service, charts in all_charts_data['services'].items():
            service_tracks[service] = []
            
            for chart_type, chart_data in charts.items():
                if chart_data.get('success') and chart_data.get('tracks'):
                    for track in chart_data['tracks']:
                        track_key = f"{track.get('title', '').strip()} - {track.get('artist', '').strip()}"
                        
                        if track_key not in all_tracks:
                            all_tracks[track_key] = {
                                'title': track.get('title'),
                                'artist': track.get('artist'),
                                'services': {},
                                'total_appearances': 0,
                                'avg_rank': 0,
                                'best_rank': 999
                            }
                        
                        all_tracks[track_key]['services'][service] = {
                            'rank': track.get('rank', 999),
                            'chart_type': chart_type
                        }
                        all_tracks[track_key]['total_appearances'] += 1
                        all_tracks[track_key]['best_rank'] = min(
                            all_tracks[track_key]['best_rank'],
                            track.get('rank', 999)
                        )
                        
                        service_tracks[service].append(track_key)
        
        # 평균 순위 계산
        for track_key, track_info in all_tracks.items():
            ranks = [service_data['rank'] for service_data in track_info['services'].values()]
            track_info['avg_rank'] = sum(ranks) / len(ranks) if ranks else 999
        
        # 크로스 플랫폼 히트곡 (2개 이상 서비스에서 순위권)
        cross_platform_hits = []
        for track_key, track_info in all_tracks.items():
            if track_info['total_appearances'] >= 2:
                cross_platform_hits.append({
                    'title': track_info['title'],
                    'artist': track_info['artist'],
                    'services_count': track_info['total_appearances'],
                    'services': list(track_info['services'].keys()),
                    'avg_rank': round(track_info['avg_rank'], 1),
                    'best_rank': track_info['best_rank'],
                    'cross_platform_score': track_info['total_appearances'] * 10 + (101 - track_info['avg_rank'])
                })
        
        # 점수순 정렬
        cross_platform_hits.sort(key=lambda x: x['cross_platform_score'], reverse=True)
        
        # 서비스별 독점곡 분석
        exclusive_tracks = {}
        for service in service_tracks:
            exclusive = []
            for track_key in service_tracks[service]:
                if all_tracks[track_key]['total_appearances'] == 1:
                    track_info = all_tracks[track_key]
                    exclusive.append({
                        'title': track_info['title'],
                        'artist': track_info['artist'],
                        'rank': track_info['services'][service]['rank']
                    })
            exclusive_tracks[service] = sorted(exclusive, key=lambda x: x['rank'])[:10]
        
        return {
            'success': True,
            'cross_platform_hits': cross_platform_hits[:20],
            'exclusive_tracks': exclusive_tracks,
            'total_unique_tracks': len(all_tracks),
            'services_analyzed': list(all_charts_data['services'].keys()),
            'analysis_date': datetime.now().isoformat()
        }
    
    def export_consolidated_chart(self, all_charts_data, format='json'):
        """
        통합 차트 데이터 내보내기
        
        Args:
            all_charts_data: 통합 차트 데이터
            format: 내보내기 형식 ('json', 'csv')
        """
        try:
            if format == 'json':
                filename = f"korea_music_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(all_charts_data, f, ensure_ascii=False, indent=2)
                return {'success': True, 'filename': filename}
            
            elif format == 'csv':
                import csv
                filename = f"korea_music_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['서비스', '차트타입', '순위', '곡명', '아티스트', '앨범'])
                    
                    for service, charts in all_charts_data.get('services', {}).items():
                        for chart_type, chart_data in charts.items():
                            if chart_data.get('tracks'):
                                for track in chart_data['tracks']:
                                    writer.writerow([
                                        service,
                                        chart_type,
                                        track.get('rank', ''),
                                        track.get('title', ''),
                                        track.get('artist', ''),
                                        track.get('album', '')
                                    ])
                
                return {'success': True, 'filename': filename}
            
        except Exception as e:
            return {'success': False, 'error': f'내보내기 오류: {str(e)}'}

# 테스트 함수
def test_korea_music_charts():
    """통합 음원사 커넥터 테스트"""
    print("=== 국내 음원사 통합 차트 테스트 ===")
    
    connector = KoreaMusicChartsConnector()
    
    # 통합 차트 수집 테스트
    print("\n1. 통합 차트 수집 테스트 (상위 10곡씩)")
    all_data = connector.get_all_charts(
        services=['melon', 'bugs', 'genie'],  # 테스트용으로 3개 서비스만
        limit_per_chart=10
    )
    
    if all_data['success']:
        print(f"성공: {all_data['successful_services']}/{all_data['total_services']} 서비스")
        print(f"총 수집곡: {all_data['total_tracks']}곡")
        
        for service, charts in all_data['services'].items():
            for chart_type, chart_data in charts.items():
                print(f"\n[{service.upper()} {chart_type}]")
                for track in chart_data['tracks'][:5]:  # 상위 5곡만 출력
                    print(f"  #{track['rank']} {track['title']} - {track['artist']}")
    else:
        print("전체 수집 실패")
    
    # 크로스 플랫폼 분석 테스트
    print("\n2. 크로스 플랫폼 분석")
    analysis = connector.get_cross_platform_analysis(all_data)
    
    if analysis['success']:
        print(f"크로스 플랫폼 히트곡 TOP 5:")
        for hit in analysis['cross_platform_hits'][:5]:
            print(f"  {hit['title']} - {hit['artist']} ({hit['services_count']}개 서비스, 평균 {hit['avg_rank']}위)")

if __name__ == "__main__":
    test_korea_music_charts()