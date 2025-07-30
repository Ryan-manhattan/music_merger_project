#!/usr/bin/env python3
"""
Melon Connector - 멜론 차트 크롤링을 통한 한국 음악 차트 데이터 수집
실시간 차트, TOP100, 장르별 차트 데이터 수집 및 분석
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
from urllib.parse import urljoin, urlparse
from collections import Counter

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
    print(f"BeautifulSoup 로드 성공")
except ImportError as e:
    BEAUTIFULSOUP_AVAILABLE = False
    print(f"BeautifulSoup 로드 실패: {e}")

class MelonConnector:
    """멜론 차트 데이터 크롤링 클래스"""
    
    def __init__(self, console_log=None):
        self.console_log = console_log or print
        self.session = requests.Session()
        
        # 멜론 크롤링을 위한 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.melon.com/'
        })
        
        # 멜론 차트 URL들
        self.chart_urls = {
            'realtime': 'https://www.melon.com/chart/index.htm',  # 실시간 차트
            'hot100': 'https://www.melon.com/chart/hot100/index.htm',  # HOT100
            'week': 'https://www.melon.com/chart/week/index.htm',  # 주간 차트
            'month': 'https://www.melon.com/chart/month/index.htm',  # 월간 차트
        }
        
        # 장르별 차트 URL
        self.genre_urls = {
            'kpop': 'https://www.melon.com/genre/song_list.htm?gnr_code=GN0100',
            'ballad': 'https://www.melon.com/genre/song_list.htm?gnr_code=GN0200',
            'dance': 'https://www.melon.com/genre/song_list.htm?gnr_code=GN0300',
            'hiphop': 'https://www.melon.com/genre/song_list.htm?gnr_code=GN0400',
            'rb': 'https://www.melon.com/genre/song_list.htm?gnr_code=GN0500',
            'rock': 'https://www.melon.com/genre/song_list.htm?gnr_code=GN0600',
            'trot': 'https://www.melon.com/genre/song_list.htm?gnr_code=GN0700'
        }
        
        self.console_log("[Melon] 멜론 커넥터 초기화 완료")
    
    def log(self, message):
        """로그 출력"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.console_log(f"[{timestamp}] [Melon] {message}")
    
    def get_chart_data(self, chart_type='realtime', limit=100):
        """
        멜론 차트 데이터 크롤링
        
        Args:
            chart_type: 차트 유형 ('realtime', 'hot100', 'week', 'month')
            limit: 가져올 곡 수 (기본값: 100)
        
        Returns:
            차트 데이터 딕셔너리
        """
        if not BEAUTIFULSOUP_AVAILABLE:
            self.log("BeautifulSoup이 설치되지 않아 크롤링할 수 없습니다.")
            return {'success': False, 'error': 'BeautifulSoup 라이브러리 필요'}
        
        self.log(f"멜론 {chart_type} 차트 크롤링 시작 (상위 {limit}곡)")
        
        try:
            url = self.chart_urls.get(chart_type, self.chart_urls['realtime'])
            
            # 페이지 요청
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 차트 데이터는 tbody에 있음
            tbody = soup.find('tbody')
            if not tbody:
                self.log("차트 tbody를 찾을 수 없습니다.")
                return {'success': False, 'error': '차트 데이터를 찾을 수 없음'}
            
            tracks = []
            rows = tbody.find_all('tr')[:limit]
            
            for idx, row in enumerate(rows, 1):
                try:
                    track_data = self._parse_track_row(row, idx, chart_type)
                    if track_data:
                        tracks.append(track_data)
                        
                        # 로그 출력 (처음 10곡만)
                        if idx <= 10:
                            self.log(f"#{idx:2d} {track_data['title']} - {track_data['artist']}")
                
                except Exception as e:
                    self.log(f"트랙 파싱 오류 (순위 {idx}): {str(e)}")
                    continue
            
            self.log(f"멜론 {chart_type} 차트 크롤링 완료: {len(tracks)}곡")
            
            return {
                'success': True,
                'chart_type': chart_type,
                'total_tracks': len(tracks),
                'tracks': tracks,
                'collected_at': datetime.now().isoformat(),
                'source': 'melon'
            }
            
        except requests.RequestException as e:
            error_msg = f"멜론 차트 요청 실패: {str(e)}"
            self.log(error_msg)
            return {'success': False, 'error': error_msg}
        
        except Exception as e:
            error_msg = f"멜론 차트 크롤링 오류: {str(e)}"
            self.log(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _parse_track_row(self, row, rank, chart_type):
        """차트 행 파싱 - 멜론 실제 HTML 구조에 맞게 수정"""
        try:
            tds = row.find_all('td')
            if len(tds) < 6:
                return None
            
            # 순위 (두 번째 td에서)
            rank_elem = tds[1].find('span', {'class': 'rank'})
            if rank_elem:
                rank_text = rank_elem.get_text(strip=True)
            else:
                rank_text = str(rank)
            
            # 곡 ID (tr 태그의 data-song-no 속성에서)
            song_id = row.get('data-song-no', None)
            
            # 곡명과 아티스트 (6번째 td에 wrap_song_info가 있음)
            song_info_td = tds[5] if len(tds) > 5 else None
            if not song_info_td:
                return None
            
            # 곡명 추출
            title_elem = song_info_td.find('div', {'class': 'ellipsis rank01'})
            title = None
            if title_elem:
                title_link = title_elem.find('a')
                if title_link:
                    title = title_link.get_text(strip=True)
                else:
                    title = title_elem.get_text(strip=True)
            
            if not title:
                return None
            
            # 아티스트 추출
            artist_elem = song_info_td.find('div', {'class': 'ellipsis rank02'})
            artist = '알 수 없음'
            if artist_elem:
                artist_links = artist_elem.find_all('a')
                if artist_links:
                    artists = [link.get_text(strip=True) for link in artist_links]
                    artist = ', '.join(artists)
                else:
                    artist = artist_elem.get_text(strip=True)
            
            # 앨범 추출
            album_elem = song_info_td.find('div', {'class': 'ellipsis rank03'})
            album = '알 수 없음'
            if album_elem:
                album_link = album_elem.find('a')
                if album_link:
                    album = album_link.get_text(strip=True)
                else:
                    album = album_elem.get_text(strip=True)
            
            # 썸네일 이미지 (4번째 td)
            thumbnail = None
            if len(tds) > 3:
                img_elem = tds[3].find('img')
                if img_elem and 'src' in img_elem.attrs:
                    thumbnail = img_elem['src']
            
            # 좋아요 수 (추후 추가 가능)
            like_count = 0
            
            return {
                'rank': int(rank_text) if rank_text.isdigit() else rank,
                'song_id': song_id,
                'title': title,
                'artist': artist,
                'album': album,
                'like_count': like_count,
                'thumbnail': thumbnail,
                'chart_type': chart_type,
                'source': 'melon',
                'url': f"https://www.melon.com/song/detail.htm?songId={song_id}" if song_id else None
            }
            
        except Exception as e:
            self.log(f"트랙 행 파싱 오류: {str(e)}")
            return None
    
    def get_genre_chart(self, genre='kpop', limit=50):
        """
        장르별 차트 데이터 크롤링
        
        Args:
            genre: 장르 ('kpop', 'ballad', 'dance', 'hiphop', 'rb', 'rock', 'trot')
            limit: 가져올 곡 수
        
        Returns:
            장르별 차트 데이터
        """
        if not BEAUTIFULSOUP_AVAILABLE:
            return {'success': False, 'error': 'BeautifulSoup 라이브러리 필요'}
        
        self.log(f"멜론 {genre} 장르 차트 크롤링 시작")
        
        try:
            url = self.genre_urls.get(genre)
            if not url:
                return {'success': False, 'error': f'지원하지 않는 장르: {genre}'}
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 장르별 페이지는 다른 구조를 가질 수 있음
            song_list = soup.find('table', {'class': 'list_table_song'})
            if not song_list:
                return {'success': False, 'error': '장르 차트 데이터를 찾을 수 없음'}
            
            tracks = []
            rows = song_list.find('tbody').find_all('tr')[:limit]
            
            for idx, row in enumerate(rows, 1):
                try:
                    track_data = self._parse_track_row(row, idx, f'genre_{genre}')
                    if track_data:
                        tracks.append(track_data)
                except Exception as e:
                    continue
            
            self.log(f"멜론 {genre} 장르 차트 완료: {len(tracks)}곡")
            
            return {
                'success': True,
                'genre': genre,
                'total_tracks': len(tracks),
                'tracks': tracks,
                'collected_at': datetime.now().isoformat(),
                'source': 'melon'
            }
            
        except Exception as e:
            error_msg = f"장르 차트 크롤링 오류: {str(e)}"
            self.log(error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_all_charts(self, limit_per_chart=50):
        """
        모든 멜론 차트 데이터 수집
        
        Args:
            limit_per_chart: 차트별 곡 수 제한
        
        Returns:
            통합 차트 데이터
        """
        self.log("멜론 전체 차트 데이터 수집 시작")
        
        all_data = {
            'success': True,
            'charts': {},
            'total_tracks': 0,
            'collected_at': datetime.now().isoformat(),
            'source': 'melon'
        }
        
        # 기본 차트들
        for chart_type in ['realtime', 'hot100']:
            self.log(f"수집 중: {chart_type} 차트")
            chart_data = self.get_chart_data(chart_type, limit_per_chart)
            
            if chart_data['success']:
                all_data['charts'][chart_type] = chart_data
                all_data['total_tracks'] += chart_data['total_tracks']
            else:
                self.log(f"{chart_type} 차트 수집 실패: {chart_data.get('error', '알 수 없는 오류')}")
            
            # 요청 간격 (서버 부하 방지)
            time.sleep(1)
        
        # 주요 장르들
        major_genres = ['kpop', 'ballad', 'hiphop', 'dance']
        for genre in major_genres:
            self.log(f"수집 중: {genre} 장르")
            genre_data = self.get_genre_chart(genre, min(30, limit_per_chart))
            
            if genre_data['success']:
                all_data['charts'][f'genre_{genre}'] = genre_data
                all_data['total_tracks'] += genre_data['total_tracks']
            
            time.sleep(1)
        
        self.log(f"멜론 전체 차트 수집 완료: 총 {all_data['total_tracks']}곡")
        return all_data
    
    def get_top_artists(self, chart_data):
        """차트에서 인기 아티스트 추출"""
        if not chart_data.get('success') or not chart_data.get('tracks'):
            return []
        
        artist_counts = Counter()
        artist_ranks = {}
        
        for track in chart_data['tracks']:
            artist = track.get('artist', '').strip()
            if artist:
                artist_counts[artist] += 1
                if artist not in artist_ranks:
                    artist_ranks[artist] = track.get('rank', 999)
        
        # 순위와 곡 수를 고려한 정렬
        top_artists = []
        for artist, count in artist_counts.most_common(20):
            avg_rank = artist_ranks[artist]
            top_artists.append({
                'artist': artist,
                'track_count': count,
                'best_rank': avg_rank,
                'score': count * 10 + (101 - avg_rank)  # 점수 계산
            })
        
        return sorted(top_artists, key=lambda x: x['score'], reverse=True)
    
    def analyze_chart_trends(self, chart_data):
        """차트 트렌드 분석"""
        if not chart_data.get('success'):
            return {'success': False, 'error': '차트 데이터 없음'}
        
        analysis = {
            'total_tracks': len(chart_data.get('tracks', [])),
            'top_artists': self.get_top_artists(chart_data),
            'genre_distribution': {},
            'title_keywords': [],
            'collected_at': chart_data.get('collected_at'),
            'chart_type': chart_data.get('chart_type', 'unknown')
        }
        
        # 제목에서 키워드 추출
        title_words = []
        for track in chart_data.get('tracks', []):
            title = track.get('title', '')
            # 한글, 영문, 숫자만 추출
            words = re.findall(r'[가-힣a-zA-Z0-9]+', title)
            title_words.extend([word.lower() for word in words if len(word) > 1])
        
        # 상위 키워드
        keyword_counts = Counter(title_words)
        analysis['title_keywords'] = [
            {'keyword': word, 'count': count} 
            for word, count in keyword_counts.most_common(10)
        ]
        
        return analysis

# 테스트 함수
def test_melon_connector():
    """멜론 커넥터 테스트"""
    print("=== 멜론 커넥터 테스트 ===")
    
    connector = MelonConnector()
    
    # 실시간 차트 테스트
    print("\n1. 실시간 차트 테스트 (상위 10곡)")
    chart_data = connector.get_chart_data('realtime', 10)
    
    if chart_data['success']:
        print(f"성공: {chart_data['total_tracks']}곡 수집")
        for track in chart_data['tracks'][:5]:
            print(f"  #{track['rank']} {track['title']} - {track['artist']}")
    else:
        print(f"실패: {chart_data['error']}")
    
    # 장르 차트 테스트
    print("\n2. K-POP 장르 차트 테스트 (상위 5곡)")
    genre_data = connector.get_genre_chart('kpop', 5)
    
    if genre_data['success']:
        print(f"성공: {genre_data['total_tracks']}곡 수집")
        for track in genre_data['tracks']:
            print(f"  #{track['rank']} {track['title']} - {track['artist']}")
    else:
        print(f"실패: {genre_data['error']}")

if __name__ == "__main__":
    test_melon_connector()