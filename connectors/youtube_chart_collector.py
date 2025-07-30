#!/usr/bin/env python3
"""
YouTube Chart Collector - YouTube Data API를 통한 음악 차트 데이터 수집
인기 동영상 기반 차트 생성
"""

import os
import json
import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class YouTubeChartCollector:
    def __init__(self, console_log=None):
        """
        YouTube 차트 수집기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        
        # 차트 수집용 검색 키워드 (한국/글로벌)
        self.chart_keywords = {
            'korea': [
                'kpop 2024 최신곡',
                '한국 음악 차트',
                'K-pop 인기곡',
                'Korean popular music',
                'kpop chart 2024'
            ],
            'global': [
                'popular music 2024',
                'top hits 2024',
                'music chart global',
                'trending music',
                'popular songs 2024'
            ]
        }
        
        # 아티스트명과 곡명을 분리하는 패턴
        self.title_patterns = [
            r'^(.+?)\s*[-–—]\s*(.+?)(?:\s*\(.*\))?(?:\s*\[.*\])?(?:\s*MV|Official|Video|Audio)?$',
            r'^(.+?)\s*[\'\""](.+?)[\'\""]',
            r'^([^-]+?)\s+(.+?)(?:\s*\(.*\))?$'
        ]
        
        if self.api_key:
            self.console_log("[YouTube] YouTube 차트 수집기 초기화 완료")
        else:
            self.console_log("[YouTube] 경고: YouTube API 키가 없습니다.")
    
    def collect_chart_data(self, region: str = 'korea', max_results: int = 25) -> Dict:
        """
        YouTube 데이터로 차트 생성
        
        Args:
            region: 'korea' 또는 'global'
            max_results: 최대 결과 수
            
        Returns:
            차트 데이터
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'YouTube API 키가 설정되지 않았습니다',
                    'chart_tracks': [],
                    'region': region,
                    'source': 'youtube_unavailable'
                }
            
            self.console_log(f"[YouTube] {region} 차트 데이터 수집 시작")
            
            all_videos = []
            keywords = self.chart_keywords.get(region, self.chart_keywords['global'])
            
            for keyword in keywords[:3]:  # 상위 3개 키워드만 사용
                videos = self._search_music_videos(keyword, max_results // len(keywords[:3]), min_view_count=50000)
                all_videos.extend(videos)
                time.sleep(0.1)  # API 호출 간격
            
            # 업로드 날짜 기준으로 정렬하고 중복 제거 (최신순)
            unique_videos = self._deduplicate_videos(all_videos)
            sorted_videos = sorted(unique_videos, key=lambda x: x.get('published_at', ''), reverse=True)
            
            # 상위 결과만 선택
            top_videos = sorted_videos[:max_results]
            
            # 차트 형식으로 변환
            chart_tracks = []
            for i, video in enumerate(top_videos):
                track_data = self._convert_to_track_format(video, i + 1, region)
                if track_data:
                    chart_tracks.append(track_data)
            
            self.console_log(f"[YouTube] {region} 차트 수집 완료: {len(chart_tracks)}곡")
            
            # 트랙이 없으면 실패로 처리
            if len(chart_tracks) == 0:
                return {
                    'success': False,
                    'error': f'YouTube에서 {region} 차트 데이터를 찾을 수 없습니다',
                    'chart_tracks': [],
                    'region': region,
                    'source': 'youtube_empty'
                }
            
            return {
                'success': True,
                'chart_tracks': chart_tracks,
                'region': region,
                'source': 'youtube',
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.console_log(f"[YouTube] 차트 수집 오류: {str(e)}")
            return {
                'success': False,
                'error': f'YouTube API 오류: {str(e)}',
                'chart_tracks': [],
                'region': region,
                'source': 'youtube_error'
            }
    
    def _search_music_videos(self, query: str, max_results: int = 10, min_view_count: int = 50000) -> List[Dict]:
        """YouTube에서 음악 동영상 검색"""
        try:
            search_url = f"{self.base_url}/search"
            params = {
                'key': self.api_key,
                'q': query,
                'part': 'snippet',
                'type': 'video',
                'videoCategoryId': '10',  # 음악 카테고리
                'order': 'date',          # 최신순
                'maxResults': max_results * 3,  # 조회수 필터링을 위해 더 많이 가져옴
                'publishedAfter': (datetime.now() - timedelta(days=90)).isoformat() + 'Z'  # 최근 3개월
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            video_ids = [item['id']['videoId'] for item in data.get('items', [])]
            
            # 상세 정보 가져오기
            if video_ids:
                all_videos = self._get_video_details(video_ids)
                # 조회수 임계값 및 플레이리스트/모음 필터링
                filtered_videos = []
                for v in all_videos:
                    if (v.get('view_count', 0) >= min_view_count and 
                        not self._is_playlist_or_compilation(v.get('title', ''))):
                        filtered_videos.append(v)
                return filtered_videos[:max_results]  # 원하는 수만큼만 반환
            
            return []
            
        except Exception as e:
            self.console_log(f"[YouTube] 검색 오류 ({query}): {str(e)}")
            return []
    
    def _get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """동영상 상세 정보 조회"""
        try:
            videos_url = f"{self.base_url}/videos"
            params = {
                'key': self.api_key,
                'id': ','.join(video_ids),
                'part': 'snippet,statistics,contentDetails'
            }
            
            response = requests.get(videos_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video_info = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'duration': item['contentDetails']['duration'],
                    'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    'url': f"https://www.youtube.com/watch?v={item['id']}"
                }
                videos.append(video_info)
            
            return videos
            
        except Exception as e:
            self.console_log(f"[YouTube] 동영상 상세정보 조회 오류: {str(e)}")
            return []
    
    def _deduplicate_videos(self, videos: List[Dict]) -> List[Dict]:
        """중복 동영상 제거 (제목 유사도 기반)"""
        unique_videos = []
        seen_titles = set()
        
        for video in videos:
            title_lower = video['title'].lower()
            
            # 간단한 중복 검사 (제목의 첫 30글자)
            title_key = title_lower[:30]
            
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_videos.append(video)
        
        return unique_videos
    
    def _convert_to_track_format(self, video: Dict, rank: int, region: str) -> Optional[Dict]:
        """YouTube 동영상을 트랙 형식으로 변환"""
        try:
            title = video['title']
            channel = video['channel']
            view_count = video['view_count']
            
            # 제목에서 아티스트와 곡명 추출
            artist, track_name = self._parse_title(title, channel)
            
            # 조회수를 인기도 점수로 변환 (0-100)
            # 1억 조회수 = 100점 기준
            popularity = min(100, int((view_count / 100_000_000) * 100))
            
            # 최소 점수 보정 (조회수가 적어도 10점 이상)
            if view_count > 100_000:  # 10만 조회수 이상
                popularity = max(10, popularity)
            
            return {
                'id': f"yt_{region}_{video['video_id']}",
                'name': track_name,
                'main_artist': artist,
                'popularity': popularity,
                'chart_region': region,
                'chart_type': 'youtube_top',
                'view_count': view_count,
                'like_count': video['like_count'],
                'youtube_url': video['url'],
                'thumbnail': video['thumbnail'],
                'published_at': video['published_at'],
                'rank': rank
            }
            
        except Exception as e:
            self.console_log(f"[YouTube] 트랙 변환 오류: {str(e)}")
            return None
    
    def _parse_title(self, title: str, channel: str) -> Tuple[str, str]:
        """동영상 제목에서 아티스트명과 곡명 추출"""
        try:
            # 패턴 매칭 시도
            for pattern in self.title_patterns:
                match = re.match(pattern, title.strip(), re.IGNORECASE)
                if match:
                    artist = match.group(1).strip()
                    track = match.group(2).strip()
                    
                    # 결과 검증
                    if len(artist) > 0 and len(track) > 0 and len(artist) < 50 and len(track) < 100:
                        return artist, track
            
            # 패턴 매칭 실패 시 채널명을 아티스트로 사용
            # 제목에서 불필요한 단어 제거
            clean_title = re.sub(r'\b(official|music|video|mv|audio|lyrics?|live|performance)\b', '', title, flags=re.IGNORECASE)
            clean_title = re.sub(r'[\[\(\)〈〉《》【】\[\]].*', '', clean_title).strip()
            
            # 채널명 정리 (Official, VEVO 등 제거)
            clean_channel = re.sub(r'\b(official|vevo|music|records?|entertainment)\b', '', channel, flags=re.IGNORECASE).strip()
            
            return clean_channel or "Unknown Artist", clean_title or "Unknown Track"
            
        except Exception as e:
            return "Unknown Artist", title[:50]
    
    def _is_playlist_or_compilation(self, title: str) -> bool:
        """플레이리스트나 모음 동영상인지 확인"""
        title_lower = title.lower()
        
        # 플레이리스트/모음 관련 키워드들 (핵심만)
        playlist_keywords = [
            '플레이리스트', '노래모음', '최신가요', '인기가요',
            '랜덤플레이', 'random play',
            '1시간', '2시간', '3시간', 'hours',
            '연속재생', '무한재생', 'non-stop', 'nonstop',
            'compilation', 'best of'
        ]
        
        # 키워드 포함 여부 확인
        for keyword in playlist_keywords:
            if keyword in title_lower:
                return True
        
        # 숫자 + 곡, 트랙 패턴 (예: "10곡 모음", "20 tracks")
        import re
        if re.search(r'\d+\s*(곡|tracks?|songs?)', title_lower):
            return True
        
        return False
