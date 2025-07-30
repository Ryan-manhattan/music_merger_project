#!/usr/bin/env python3
"""
Chart Analysis - 음원사별 차트 비교 분석 및 시각화
국내 주요 음원사 차트 데이터 분석 및 인사이트 생성
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import re

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    plt.rcParams['font.family'] = ['Malgun Gothic', 'AppleGothic', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("matplotlib/seaborn이 설치되지 않아 시각화 기능을 사용할 수 없습니다.")

class ChartAnalyzer:
    """차트 비교 분석기"""
    
    def __init__(self, console_log=None):
        self.console_log = console_log or print
        
        # 분석 결과 저장 디렉토리
        self.analysis_dir = os.path.join(os.path.dirname(__file__), 'chart_analysis')
        os.makedirs(self.analysis_dir, exist_ok=True)
        
        # 시각화 디렉토리
        self.viz_dir = os.path.join(self.analysis_dir, 'visualizations')
        os.makedirs(self.viz_dir, exist_ok=True)
        
        self.log("차트 분석기 초기화 완료")
    
    def log(self, message):
        """로그 출력"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.console_log(f"[{timestamp}] [Analysis] {message}")
    
    def analyze_service_differences(self, chart_data):
        """음원사별 차이점 분석"""
        if not chart_data.get('success') or not chart_data.get('services'):
            return {'success': False, 'error': '차트 데이터 없음'}
        
        self.log("음원사별 차이점 분석 시작")
        
        analysis = {
            'service_stats': {},
            'genre_preferences': {},
            'artist_dominance': {},
            'ranking_correlations': {},
            'unique_tracks': {},
            'overlap_analysis': {},
            'temporal_patterns': {},
            'generated_at': datetime.now().isoformat()
        }
        
        services = chart_data['services']
        
        # 1. 서비스별 기본 통계
        analysis['service_stats'] = self._analyze_service_stats(services)
        
        # 2. 장르 선호도 분석
        analysis['genre_preferences'] = self._analyze_genre_preferences(services)
        
        # 3. 아티스트 지배력 분석
        analysis['artist_dominance'] = self._analyze_artist_dominance(services)
        
        # 4. 순위 상관관계 분석
        analysis['ranking_correlations'] = self._analyze_ranking_correlations(services)
        
        # 5. 독점 트랙 분석
        analysis['unique_tracks'] = self._analyze_unique_tracks(services)
        
        # 6. 중복도 분석
        analysis['overlap_analysis'] = self._analyze_overlap(services)
        
        # 7. 시각화 생성
        if VISUALIZATION_AVAILABLE:
            viz_paths = self._create_visualizations(analysis, services)
            analysis['visualizations'] = viz_paths
        
        self.log("음원사별 차이점 분석 완료")
        
        # 분석 결과 저장
        self._save_analysis_result(analysis)
        
        return {
            'success': True,
            'analysis': analysis
        }
    
    def _analyze_service_stats(self, services):
        """서비스별 기본 통계 분석"""
        stats = {}
        
        for service, charts in services.items():
            service_stats = {
                'chart_count': len(charts),
                'total_tracks': 0,
                'avg_tracks_per_chart': 0,
                'track_titles_length': [],
                'artist_diversity': set()
            }
            
            for chart_type, chart_data in charts.items():
                if chart_data.get('success') and chart_data.get('tracks'):
                    tracks = chart_data['tracks']
                    service_stats['total_tracks'] += len(tracks)
                    
                    for track in tracks:
                        title_length = len(track.get('title', ''))
                        service_stats['track_titles_length'].append(title_length)
                        service_stats['artist_diversity'].add(track.get('artist', ''))
            
            service_stats['avg_tracks_per_chart'] = (
                service_stats['total_tracks'] / service_stats['chart_count'] 
                if service_stats['chart_count'] > 0 else 0
            )
            service_stats['avg_title_length'] = (
                np.mean(service_stats['track_titles_length']) 
                if service_stats['track_titles_length'] else 0
            )
            service_stats['artist_count'] = len(service_stats['artist_diversity'])
            
            # 임시 데이터 정리
            del service_stats['track_titles_length']
            del service_stats['artist_diversity']
            
            stats[service] = service_stats
        
        return stats
    
    def _analyze_genre_preferences(self, services):
        """장르 선호도 분석 (키워드 기반)"""
        genre_keywords = {
            'ballad': ['발라드', 'ballad', '사랑', '그리움', '눈물', '이별'],
            'dance': ['댄스', 'dance', '파티', 'party', '클럽', 'club'],
            'hiphop': ['랩', 'rap', 'hip', 'hop', '힙합', 'cypher'],
            'rock': ['록', 'rock', '밴드', 'band', '기타', 'guitar'],
            'trot': ['트로트', '뽕짝', '홍진영', '진도'],
            'indie': ['인디', 'indie', '어쿠스틱', 'acoustic'],
            'electronic': ['일렉', 'electronic', 'edm', 'techno']
        }
        
        genre_stats = {}
        
        for service, charts in services.items():
            service_genres = {genre: 0 for genre in genre_keywords.keys()}
            total_tracks = 0
            
            for chart_type, chart_data in charts.items():
                if chart_data.get('success') and chart_data.get('tracks'):
                    for track in chart_data['tracks']:
                        title = track.get('title', '').lower()
                        artist = track.get('artist', '').lower()
                        combined_text = f"{title} {artist}"
                        
                        for genre, keywords in genre_keywords.items():
                            if any(keyword in combined_text for keyword in keywords):
                                service_genres[genre] += 1
                        
                        total_tracks += 1
            
            # 비율로 변환
            if total_tracks > 0:
                for genre in service_genres:
                    service_genres[genre] = round(
                        (service_genres[genre] / total_tracks) * 100, 2
                    )
            
            genre_stats[service] = service_genres
        
        return genre_stats
    
    def _analyze_artist_dominance(self, services):
        """아티스트 지배력 분석"""
        dominance = {}
        
        for service, charts in services.items():
            artist_counts = Counter()
            total_tracks = 0
            
            for chart_type, chart_data in charts.items():
                if chart_data.get('success') and chart_data.get('tracks'):
                    for track in chart_data['tracks']:
                        artist = track.get('artist', '').strip()
                        if artist:
                            artist_counts[artist] += 1
                            total_tracks += 1
            
            # 상위 아티스트들의 지배력 계산
            top_artists = artist_counts.most_common(10)
            top_10_percentage = sum(count for _, count in top_artists) / total_tracks * 100 if total_tracks > 0 else 0
            
            dominance[service] = {
                'total_unique_artists': len(artist_counts),
                'total_tracks': total_tracks,
                'top_artists': [
                    {'artist': artist, 'count': count, 'percentage': round(count/total_tracks*100, 2)}
                    for artist, count in top_artists
                ],
                'top_10_dominance': round(top_10_percentage, 2),
                'diversity_score': round(len(artist_counts) / total_tracks * 100, 2) if total_tracks > 0 else 0
            }
        
        return dominance
    
    def _analyze_ranking_correlations(self, services):
        """순위 상관관계 분석"""
        correlations = {}
        
        # 공통 트랙 찾기
        all_tracks = {}
        service_rankings = {}
        
        for service, charts in services.items():
            service_rankings[service] = {}
            
            for chart_type, chart_data in charts.items():
                if chart_data.get('success') and chart_data.get('tracks'):
                    for track in chart_data['tracks']:
                        track_key = f"{track.get('title', '').strip()} - {track.get('artist', '').strip()}"
                        
                        if track_key not in all_tracks:
                            all_tracks[track_key] = {}
                        
                        all_tracks[track_key][service] = track.get('rank', 999)
                        service_rankings[service][track_key] = track.get('rank', 999)
        
        # 2개 이상 서비스에 공통으로 등장하는 트랙들 찾기
        common_tracks = {
            track_key: rankings 
            for track_key, rankings in all_tracks.items() 
            if len(rankings) >= 2
        }
        
        correlations['common_tracks_count'] = len(common_tracks)
        correlations['total_unique_tracks'] = len(all_tracks)
        correlations['overlap_percentage'] = round(
            len(common_tracks) / len(all_tracks) * 100, 2
        ) if all_tracks else 0
        
        # 서비스 간 순위 상관관계 계산
        service_list = list(services.keys())
        correlations['pairwise_correlations'] = {}
        
        for i, service1 in enumerate(service_list):
            for j, service2 in enumerate(service_list[i+1:], i+1):
                common_tracks_pair = []
                rankings1 = []
                rankings2 = []
                
                for track_key, rankings in common_tracks.items():
                    if service1 in rankings and service2 in rankings:
                        rankings1.append(rankings[service1])
                        rankings2.append(rankings[service2])
                        common_tracks_pair.append(track_key)
                
                if len(rankings1) > 1:
                    correlation = np.corrcoef(rankings1, rankings2)[0, 1]
                    correlations['pairwise_correlations'][f"{service1}_vs_{service2}"] = {
                        'correlation': round(correlation, 3) if not np.isnan(correlation) else 0,
                        'common_tracks': len(common_tracks_pair),
                        'sample_tracks': common_tracks_pair[:5]
                    }
        
        return correlations
    
    def _analyze_unique_tracks(self, services):
        """독점 트랙 분석"""
        unique_analysis = {}
        
        # 모든 트랙 수집
        all_tracks = {}
        
        for service, charts in services.items():
            for chart_type, chart_data in charts.items():
                if chart_data.get('success') and chart_data.get('tracks'):
                    for track in chart_data['tracks']:
                        track_key = f"{track.get('title', '').strip()} - {track.get('artist', '').strip()}"
                        
                        if track_key not in all_tracks:
                            all_tracks[track_key] = []
                        
                        all_tracks[track_key].append(service)
        
        # 서비스별 독점 트랙 찾기
        for service in services.keys():
            exclusive_tracks = []
            
            for track_key, track_services in all_tracks.items():
                if len(track_services) == 1 and track_services[0] == service:
                    exclusive_tracks.append(track_key)
            
            unique_analysis[service] = {
                'exclusive_count': len(exclusive_tracks),
                'exclusive_tracks': exclusive_tracks[:10],  # 상위 10개만
                'exclusivity_rate': round(
                    len(exclusive_tracks) / len([t for t, s in all_tracks.items() if service in s]) * 100, 2
                ) if any(service in s for s in all_tracks.values()) else 0
            }
        
        return unique_analysis
    
    def _analyze_overlap(self, services):
        """중복도 분석"""
        overlap = {}
        
        # 서비스별 트랙 집합 생성
        service_tracks = {}
        
        for service, charts in services.items():
            tracks_set = set()
            
            for chart_type, chart_data in charts.items():
                if chart_data.get('success') and chart_data.get('tracks'):
                    for track in chart_data['tracks']:
                        track_key = f"{track.get('title', '').strip()} - {track.get('artist', '').strip()}"
                        tracks_set.add(track_key)
            
            service_tracks[service] = tracks_set
        
        # 전체 중복도 계산
        all_tracks = set()
        for tracks in service_tracks.values():
            all_tracks.update(tracks)
        
        overlap['total_unique_tracks'] = len(all_tracks)
        overlap['service_track_counts'] = {
            service: len(tracks) for service, tracks in service_tracks.items()
        }
        
        # 서비스 간 중복도 매트릭스
        service_list = list(services.keys())
        overlap_matrix = {}
        
        for service1 in service_list:
            overlap_matrix[service1] = {}
            
            for service2 in service_list:
                if service1 == service2:
                    overlap_rate = 100.0
                else:
                    intersection = len(service_tracks[service1] & service_tracks[service2])
                    union = len(service_tracks[service1] | service_tracks[service2])
                    overlap_rate = round((intersection / union * 100), 2) if union > 0 else 0
                
                overlap_matrix[service1][service2] = overlap_rate
        
        overlap['overlap_matrix'] = overlap_matrix
        
        return overlap
    
    def _create_visualizations(self, analysis, services):
        """시각화 생성"""
        viz_paths = []
        
        try:
            # 1. 서비스별 트랙 수 비교
            self._create_track_count_chart(analysis['service_stats'], viz_paths)
            
            # 2. 장르 선호도 히트맵
            self._create_genre_heatmap(analysis['genre_preferences'], viz_paths)
            
            # 3. 아티스트 다양성 비교
            self._create_diversity_chart(analysis['artist_dominance'], viz_paths)
            
            # 4. 중복도 매트릭스
            self._create_overlap_matrix(analysis['overlap_analysis'], viz_paths)
            
            self.log(f"시각화 생성 완료: {len(viz_paths)}개")
            
        except Exception as e:
            self.log(f"시각화 생성 오류: {str(e)}")
        
        return viz_paths
    
    def _create_track_count_chart(self, service_stats, viz_paths):
        """서비스별 트랙 수 비교 차트"""
        services = list(service_stats.keys())
        track_counts = [stats['total_tracks'] for stats in service_stats.values()]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(services, track_counts, color=['#1DB954', '#FF6B00', '#FF0080', '#03C75A'])
        
        plt.title('음원사별 수집 트랙 수 비교', fontsize=16, fontweight='bold')
        plt.xlabel('음원사', fontsize=12)
        plt.ylabel('트랙 수', fontsize=12)
        
        # 막대 위에 값 표시
        for bar, count in zip(bars, track_counts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        filepath = os.path.join(self.viz_dir, 'track_count_comparison.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        viz_paths.append(filepath)
    
    def _create_genre_heatmap(self, genre_preferences, viz_paths):
        """장르 선호도 히트맵"""
        if not genre_preferences:
            return
        
        # 데이터 준비
        services = list(genre_preferences.keys())
        genres = list(next(iter(genre_preferences.values())).keys())
        
        data = []
        for service in services:
            data.append([genre_preferences[service][genre] for genre in genres])
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(data, 
                   xticklabels=genres, 
                   yticklabels=services,
                   annot=True, 
                   fmt='.1f',
                   cmap='YlOrRd',
                   cbar_kws={'label': '비율 (%)'})
        
        plt.title('음원사별 장르 선호도 히트맵', fontsize=16, fontweight='bold')
        plt.xlabel('장르', fontsize=12)
        plt.ylabel('음원사', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        filepath = os.path.join(self.viz_dir, 'genre_preferences_heatmap.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        viz_paths.append(filepath)
    
    def _create_diversity_chart(self, artist_dominance, viz_paths):
        """아티스트 다양성 차트"""
        services = list(artist_dominance.keys())
        diversity_scores = [stats['diversity_score'] for stats in artist_dominance.values()]
        top_10_dominance = [stats['top_10_dominance'] for stats in artist_dominance.values()]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 다양성 점수
        bars1 = ax1.bar(services, diversity_scores, color=['#1DB954', '#FF6B00', '#FF0080', '#03C75A'])
        ax1.set_title('아티스트 다양성 점수', fontweight='bold')
        ax1.set_ylabel('다양성 점수 (%)')
        
        for bar, score in zip(bars1, diversity_scores):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{score:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 상위 10개 아티스트 지배력
        bars2 = ax2.bar(services, top_10_dominance, color=['#1DB954', '#FF6B00', '#FF0080', '#03C75A'])
        ax2.set_title('상위 10개 아티스트 지배력', fontweight='bold')
        ax2.set_ylabel('지배력 (%)')
        
        for bar, dominance in zip(bars2, top_10_dominance):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{dominance:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        filepath = os.path.join(self.viz_dir, 'artist_diversity_analysis.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        viz_paths.append(filepath)
    
    def _create_overlap_matrix(self, overlap_analysis, viz_paths):
        """중복도 매트릭스 히트맵"""
        if not overlap_analysis.get('overlap_matrix'):
            return
        
        matrix = overlap_analysis['overlap_matrix']
        services = list(matrix.keys())
        
        data = []
        for service1 in services:
            row = []
            for service2 in services:
                row.append(matrix[service1][service2])
            data.append(row)
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(data,
                   xticklabels=services,
                   yticklabels=services,
                   annot=True,
                   fmt='.1f',
                   cmap='Blues',
                   cbar_kws={'label': '중복률 (%)'})
        
        plt.title('음원사 간 차트 중복률 매트릭스', fontsize=16, fontweight='bold')
        plt.xlabel('음원사', fontsize=12)
        plt.ylabel('음원사', fontsize=12)
        plt.tight_layout()
        
        filepath = os.path.join(self.viz_dir, 'overlap_matrix.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        viz_paths.append(filepath)
    
    def _save_analysis_result(self, analysis):
        """분석 결과 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"chart_analysis_{timestamp}.json"
            filepath = os.path.join(self.analysis_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            
            # 최신 분석 결과 링크 업데이트
            latest_path = os.path.join(self.analysis_dir, 'latest_analysis.json')
            import shutil
            shutil.copy2(filepath, latest_path)
            
            self.log(f"분석 결과 저장 완료: {filename}")
            
        except Exception as e:
            self.log(f"분석 결과 저장 오류: {str(e)}")
    
    def generate_insights_report(self, analysis):
        """인사이트 보고서 생성"""
        if not analysis.get('success'):
            return {'success': False, 'error': '분석 데이터 없음'}
        
        data = analysis['analysis']
        insights = []
        
        # 1. 수집 성과 인사이트
        service_stats = data.get('service_stats', {})
        if service_stats:
            max_service = max(service_stats.items(), key=lambda x: x[1]['total_tracks'])
            min_service = min(service_stats.items(), key=lambda x: x[1]['total_tracks'])
            
            insights.append({
                'category': '데이터 수집',
                'insight': f"{max_service[0]}에서 가장 많은 {max_service[1]['total_tracks']}곡을 수집했으며, "
                          f"{min_service[0]}에서 {min_service[1]['total_tracks']}곡으로 가장 적게 수집했습니다.",
                'importance': 'high'
            })
        
        # 2. 장르 선호도 인사이트
        genre_prefs = data.get('genre_preferences', {})
        if genre_prefs:
            for service, genres in genre_prefs.items():
                if genres:
                    top_genre = max(genres.items(), key=lambda x: x[1])
                    if top_genre[1] > 5:  # 5% 이상인 경우만
                        insights.append({
                            'category': '장르 선호도',
                            'insight': f"{service}에서는 {top_genre[0]} 장르가 {top_genre[1]}%로 가장 높은 비율을 차지합니다.",
                            'importance': 'medium'
                        })
        
        # 3. 아티스트 지배력 인사이트
        artist_dom = data.get('artist_dominance', {})
        if artist_dom:
            for service, stats in artist_dom.items():
                if stats['top_10_dominance'] > 50:
                    insights.append({
                        'category': '아티스트 집중도',
                        'insight': f"{service}에서 상위 10개 아티스트가 전체 차트의 {stats['top_10_dominance']}%를 차지하여 집중도가 높습니다.",
                        'importance': 'high'
                    })
        
        # 4. 중복도 인사이트
        overlap = data.get('overlap_analysis', {})
        if overlap and overlap.get('overlap_percentage'):
            insights.append({
                'category': '차트 중복도',
                'insight': f"전체 수집곡 중 {overlap['overlap_percentage']}%가 여러 음원사에서 공통으로 차트에 올랐습니다.",
                'importance': 'medium'
            })
        
        return {
            'success': True,
            'insights': insights,
            'summary': {
                'total_insights': len(insights),
                'high_importance': len([i for i in insights if i['importance'] == 'high']),
                'generated_at': datetime.now().isoformat()
            }
        }

# 테스트 함수
def test_chart_analyzer():
    """차트 분석기 테스트"""
    print("=== 차트 분석기 테스트 ===")
    
    # 샘플 데이터로 테스트
    sample_data = {
        'success': True,
        'services': {
            'melon': {
                'realtime': {
                    'success': True,
                    'tracks': [
                        {'rank': 1, 'title': '사랑하는 사람아', 'artist': '홍길동'},
                        {'rank': 2, 'title': 'Dance Tonight', 'artist': '김철수'},
                        {'rank': 3, 'title': '힙합 라이프', 'artist': '박영희'}
                    ]
                }
            },
            'bugs': {
                'realtime': {
                    'success': True,
                    'tracks': [
                        {'rank': 1, 'title': 'Dance Tonight', 'artist': '김철수'},
                        {'rank': 2, 'title': '록 스피릿', 'artist': '이민수'},
                        {'rank': 3, 'title': '사랑하는 사람아', 'artist': '홍길동'}
                    ]
                }
            }
        }
    }
    
    analyzer = ChartAnalyzer()
    result = analyzer.analyze_service_differences(sample_data)
    
    if result['success']:
        print("분석 성공!")
        print(f"서비스 통계: {result['analysis']['service_stats']}")
        overlap_analysis = result['analysis'].get('overlap_analysis', {})
        print(f"중복도: {overlap_analysis.get('overlap_percentage', 0)}%")
        
        # 인사이트 생성
        insights = analyzer.generate_insights_report(result)
        if insights['success']:
            print(f"\n인사이트 {insights['summary']['total_insights']}개 생성:")
            for insight in insights['insights']:
                print(f"- [{insight['category']}] {insight['insight']}")
    else:
        print(f"분석 실패: {result['error']}")

if __name__ == "__main__":
    test_chart_analyzer()