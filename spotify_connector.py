#!/usr/bin/env python3
"""
Spotify Connector - Spotify Web API를 통한 음악 트렌드 데이터 수집
차트, 플레이리스트, 아티스트, 트랙 정보 및 오디오 특성 분석
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter
import base64

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False
    print("Spotipy 라이브러리가 설치되지 않았습니다. 'pip install spotipy' 실행")

class SpotifyConnector:
    def __init__(self, console_log=None):
        """
        Spotify 연결기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        self.spotify = None
        self.session = requests.Session()
        
        if SPOTIPY_AVAILABLE:
            self._initialize_spotify()
        
        # 음악 시장 관련 플레이리스트 ID들 (한국/글로벌)
        self.trending_playlists = {
            'korea': {
                'viral': '37i9dQZEVXbJZGli0rRP3r',  # Viral 50 - South Korea
                'top': '37i9dQZEVXbNxXF4SkHj9F',     # Top 50 - South Korea
                'kpop': '37i9dQZF1DX9tPFwDMOaN1'     # K-pop Central
            },
            'global': {
                'viral': '37i9dQZEVXbLiRSasKsNU9',  # Viral 50 - Global
                'top': '37i9dQZEVXbMDoHDwVN2tF',     # Global Top 50
                'trends': '37i9dQZF1DX0XUsuxWHRQd'   # RapCaviar (Hip-Hop)
            }
        }
        
        # 장르별 시드 데이터
        self.genre_seeds = {
            'pop': 'pop',
            'kpop': 'k-pop',
            'hiphop': 'hip-hop',
            'rock': 'rock',
            'electronic': 'electronic',
            'ballad': 'ballad',
            'jazz': 'jazz',
            'classical': 'classical',
            'rnb': 'r-n-b',
            'indie': 'indie'
        }
    
    def _initialize_spotify(self):
        """Spotify API 초기화"""
        try:
            # 환경변수에서 Spotify API 크리덴셜 읽기
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                self.console_log("[Spotify] API 크리덴셜이 설정되지 않았습니다")
                self.console_log("[Spotify] 환경변수 SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET 설정 필요")
                return
            
            # 클라이언트 크리덴셜 방식으로 인증
            client_credentials_manager = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            
            self.spotify = spotipy.Spotify(
                client_credentials_manager=client_credentials_manager,
                requests_timeout=10
            )
            
            # 연결 테스트
            self.spotify.search(q='test', type='track', limit=1)
            self.console_log("[Spotify] API 연결 성공")
            
        except Exception as e:
            self.console_log(f"[Spotify] API 초기화 오류: {str(e)}")
            self.spotify = None
    
    def get_trending_tracks(self, region: str = 'korea', playlist_type: str = 'top', limit: int = 50) -> Dict:
        """
        트렌딩 트랙 수집
        
        Args:
            region: 지역 ('korea', 'global')
            playlist_type: 플레이리스트 타입 ('top', 'viral', 'kpop', 'trends')
            limit: 수집할 트랙 수
            
        Returns:
            트렌딩 트랙 데이터
        """
        try:
            if not self.spotify:
                return {'success': False, 'error': 'Spotify API가 초기화되지 않았습니다'}
            
            # 플레이리스트 ID 가져오기
            playlist_id = self.trending_playlists.get(region, {}).get(playlist_type)
            if not playlist_id:
                return {'success': False, 'error': f'플레이리스트를 찾을 수 없습니다: {region}/{playlist_type}'}
            
            self.console_log(f"[Spotify] 트렌딩 트랙 수집: {region}/{playlist_type}")
            
            # 플레이리스트 트랙 가져오기
            playlist = self.spotify.playlist(playlist_id)
            tracks_data = []
            
            for idx, item in enumerate(playlist['tracks']['items'][:limit]):
                if item['track'] is None:
                    continue
                
                track = item['track']
                
                # 기본 트랙 정보
                track_data = {
                    'rank': idx + 1,
                    'id': track['id'],
                    'name': track['name'],
                    'popularity': track['popularity'],
                    'explicit': track['explicit'],
                    'duration_ms': track['duration_ms'],
                    'preview_url': track['preview_url'],
                    'external_urls': track['external_urls']['spotify'],
                    'added_at': item.get('added_at')
                }
                
                # 아티스트 정보
                artists = []
                for artist in track['artists']:
                    artists.append({
                        'id': artist['id'],
                        'name': artist['name'],
                        'external_urls': artist['external_urls']['spotify']
                    })
                track_data['artists'] = artists
                track_data['main_artist'] = artists[0]['name'] if artists else 'Unknown'
                
                # 앨범 정보
                album = track['album']
                track_data['album'] = {
                    'id': album['id'],
                    'name': album['name'],
                    'release_date': album['release_date'],
                    'total_tracks': album['total_tracks'],
                    'album_type': album['album_type'],
                    'images': album['images']
                }
                
                tracks_data.append(track_data)
                
                # API 제한 고려
                if idx % 10 == 0:
                    time.sleep(0.1)
            
            result = {
                'success': True,
                'region': region,
                'playlist_type': playlist_type,
                'playlist_name': playlist['name'],
                'playlist_description': playlist['description'],
                'total_tracks': len(tracks_data),
                'tracks': tracks_data,
                'collected_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Spotify] 트렌딩 트랙 수집 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_audio_features(self, track_ids: List[str]) -> Dict:
        """
        트랙 오디오 특성 분석
        
        Args:
            track_ids: Spotify 트랙 ID 목록
            
        Returns:
            오디오 특성 데이터
        """
        try:
            if not self.spotify:
                return {'success': False, 'error': 'Spotify API가 초기화되지 않았습니다'}
            
            self.console_log(f"[Spotify] 오디오 특성 분석: {len(track_ids)}개 트랙")
            
            # Spotify API는 한 번에 100개까지 처리 가능
            all_features = []
            
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                features = self.spotify.audio_features(batch)
                
                for feature in features:
                    if feature:  # None이 아닌 경우만
                        all_features.append(feature)
                
                time.sleep(0.1)
            
            # 통계 계산
            if all_features:
                avg_features = {}
                for key in ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness', 'liveness', 'speechiness']:
                    values = [f[key] for f in all_features if f[key] is not None]
                    avg_features[key] = sum(values) / len(values) if values else 0
                
                # 템포 분석
                tempos = [f['tempo'] for f in all_features if f['tempo']]
                avg_features['tempo'] = sum(tempos) / len(tempos) if tempos else 0
                
                # 키 분석
                keys = [f['key'] for f in all_features if f['key'] is not None]
                key_distribution = Counter(keys)
                
                # 모드 분석 (Major/Minor)
                modes = [f['mode'] for f in all_features if f['mode'] is not None]
                mode_distribution = Counter(modes)
            else:
                avg_features = {}
                key_distribution = {}
                mode_distribution = {}
            
            result = {
                'success': True,
                'analyzed_tracks': len(all_features),
                'average_features': avg_features,
                'key_distribution': dict(key_distribution.most_common()),
                'mode_distribution': dict(mode_distribution),
                'individual_features': all_features,
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Spotify] 오디오 특성 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_artist_trends(self, artist_id: str) -> Dict:
        """
        아티스트 트렌드 분석
        
        Args:
            artist_id: Spotify 아티스트 ID
            
        Returns:
            아티스트 트렌드 데이터
        """
        try:
            if not self.spotify:
                return {'success': False, 'error': 'Spotify API가 초기화되지 않았습니다'}
            
            # 아티스트 기본 정보
            artist = self.spotify.artist(artist_id)
            
            # 아티스트 탑 트랙
            top_tracks = self.spotify.artist_top_tracks(artist_id, country='KR')
            
            # 아티스트 앨범
            albums = self.spotify.artist_albums(artist_id, album_type='album,single', limit=20)
            
            # 관련 아티스트
            related_artists = self.spotify.artist_related_artists(artist_id)
            
            result = {
                'success': True,
                'artist_info': {
                    'id': artist['id'],
                    'name': artist['name'],
                    'popularity': artist['popularity'],
                    'followers': artist['followers']['total'],
                    'genres': artist['genres'],
                    'external_urls': artist['external_urls']['spotify'],
                    'images': artist['images']
                },
                'top_tracks': [{
                    'id': track['id'],
                    'name': track['name'],
                    'popularity': track['popularity'],
                    'preview_url': track['preview_url']
                } for track in top_tracks['tracks'][:10]],
                'recent_releases': [{
                    'id': album['id'],
                    'name': album['name'],
                    'release_date': album['release_date'],
                    'album_type': album['album_type'],
                    'total_tracks': album['total_tracks']
                } for album in albums['items'][:10]],
                'related_artists': [{
                    'id': artist['id'],
                    'name': artist['name'],
                    'popularity': artist['popularity'],
                    'genres': artist['genres']
                } for artist in related_artists['artists'][:10]],
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Spotify] 아티스트 트렌드 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def search_trending_keywords(self, keyword: str, search_type: str = 'track', limit: int = 50) -> Dict:
        """
        키워드 기반 트렌드 검색
        
        Args:
            keyword: 검색 키워드
            search_type: 검색 타입 ('track', 'artist', 'album', 'playlist')
            limit: 결과 수 제한
            
        Returns:
            검색 결과 및 트렌드 분석
        """
        try:
            if not self.spotify:
                return {'success': False, 'error': 'Spotify API가 초기화되지 않았습니다'}
            
            self.console_log(f"[Spotify] 키워드 검색: {keyword} ({search_type})")
            
            # 검색 실행
            search_results = self.spotify.search(q=keyword, type=search_type, limit=limit, market='KR')
            
            results_data = []
            if search_type == 'track':
                for track in search_results['tracks']['items']:
                    track_data = {
                        'id': track['id'],
                        'name': track['name'],
                        'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                        'popularity': track['popularity'],
                        'explicit': track['explicit'],
                        'preview_url': track['preview_url'],
                        'release_date': track['album']['release_date'],
                        'external_urls': track['external_urls']['spotify']
                    }
                    results_data.append(track_data)
            
            elif search_type == 'artist':
                for artist in search_results['artists']['items']:
                    artist_data = {
                        'id': artist['id'],
                        'name': artist['name'],
                        'popularity': artist['popularity'],
                        'followers': artist['followers']['total'],
                        'genres': artist['genres'],
                        'external_urls': artist['external_urls']['spotify']
                    }
                    results_data.append(artist_data)
            
            # 인기도 분석
            popularities = [item['popularity'] for item in results_data if 'popularity' in item]
            avg_popularity = sum(popularities) / len(popularities) if popularities else 0
            
            result = {
                'success': True,
                'keyword': keyword,
                'search_type': search_type,
                'total_results': len(results_data),
                'average_popularity': avg_popularity,
                'results': results_data,
                'trend_score': min(avg_popularity * len(results_data) / 100, 100),  # 0-100 스케일
                'searched_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Spotify] 키워드 검색 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_genre_recommendations(self, genre: str, limit: int = 20) -> Dict:
        """
        장르별 추천 트랙 및 트렌드
        
        Args:
            genre: 장르명
            limit: 추천 트랙 수
            
        Returns:
            장르 추천 및 분석 결과
        """
        try:
            if not self.spotify:
                return {'success': False, 'error': 'Spotify API가 초기화되지 않았습니다'}
            
            genre_seed = self.genre_seeds.get(genre.lower(), genre)
            
            # 장르 기반 추천
            recommendations = self.spotify.recommendations(
                seed_genres=[genre_seed],
                limit=limit,
                market='KR'
            )
            
            tracks_data = []
            for track in recommendations['tracks']:
                track_data = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                    'popularity': track['popularity'],
                    'preview_url': track['preview_url'],
                    'external_urls': track['external_urls']['spotify']
                }
                tracks_data.append(track_data)
            
            # 장르 트렌드 점수 계산
            popularities = [track['popularity'] for track in tracks_data]
            avg_popularity = sum(popularities) / len(popularities) if popularities else 0
            
            result = {
                'success': True,
                'genre': genre,
                'genre_seed': genre_seed,
                'total_recommendations': len(tracks_data),
                'average_popularity': avg_popularity,
                'trend_score': avg_popularity,
                'recommendations': tracks_data,
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Spotify] 장르 추천 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_playlist_trends(self, playlist_url: str) -> Dict:
        """
        플레이리스트 트렌드 분석
        
        Args:
            playlist_url: Spotify 플레이리스트 URL 또는 ID
            
        Returns:
            플레이리스트 분석 결과
        """
        try:
            if not self.spotify:
                return {'success': False, 'error': 'Spotify API가 초기화되지 않았습니다'}
            
            # URL에서 플레이리스트 ID 추출
            playlist_id = playlist_url.split('/')[-1].split('?')[0] if '/' in playlist_url else playlist_url
            
            # 플레이리스트 정보
            playlist = self.spotify.playlist(playlist_id)
            
            # 트랙 정보 수집
            tracks = []
            artists = Counter()
            genres = Counter()
            
            for item in playlist['tracks']['items']:
                if item['track']:
                    track = item['track']
                    tracks.append({
                        'name': track['name'],
                        'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                        'popularity': track['popularity']
                    })
                    
                    # 아티스트 카운트
                    for artist in track['artists']:
                        artists[artist['name']] += 1
            
            # 트랙 ID 수집하여 오디오 특성 분석
            track_ids = [item['track']['id'] for item in playlist['tracks']['items'] 
                        if item['track'] and item['track']['id']]
            
            audio_analysis = {}
            if track_ids:
                audio_features = self.get_audio_features(track_ids[:50])  # 처음 50개만
                if audio_features['success']:
                    audio_analysis = audio_features['average_features']
            
            result = {
                'success': True,
                'playlist_info': {
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'description': playlist['description'],
                    'followers': playlist['followers']['total'],
                    'total_tracks': playlist['tracks']['total']
                },
                'top_artists': dict(artists.most_common(10)),
                'average_popularity': sum(t['popularity'] for t in tracks) / len(tracks) if tracks else 0,
                'audio_characteristics': audio_analysis,
                'tracks': tracks[:20],  # 상위 20개 트랙
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Spotify] 플레이리스트 분석 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_api_status(self) -> Dict:
        """Spotify API 연결 상태 확인"""
        return {
            'spotipy_available': SPOTIPY_AVAILABLE,
            'spotify_connected': self.spotify is not None,
            'regions_configured': list(self.trending_playlists.keys()),
            'genres_available': list(self.genre_seeds.keys()),
            'playlist_types': list(self.trending_playlists.get('korea', {}).keys())
        }