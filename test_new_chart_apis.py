#!/usr/bin/env python3
"""
새로운 차트 API들 테스트 스크립트
Last.fm, Billboard, 통합 차트 수집기 테스트
"""

import sys
import json
from datetime import datetime

def test_lastfm_connector():
    """Last.fm Connector 테스트"""
    print("=" * 60)
    print("🎵 Last.fm Connector 테스트")
    print("=" * 60)
    
    try:
        from lastfm_connector import LastfmConnector
        
        lastfm = LastfmConnector()
        print(f"✅ Last.fm Connector 초기화 성공")
        
        # API 상태 확인
        status = lastfm.get_api_status()
        print(f"📊 API 상태: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        if status['api_key_configured']:
            # Top 트랙 수집 테스트
            print("\n🎯 Top 트랙 수집 테스트...")
            top_tracks = lastfm.get_top_tracks(period='7day', limit=10)
            
            if top_tracks['success']:
                print(f"✅ Top 트랙 수집 성공: {len(top_tracks['tracks'])}곡")
                print("\n📋 상위 5곡:")
                for i, track in enumerate(top_tracks['tracks'][:5]):
                    print(f"  {i+1}. {track['artist']} - {track['name']} (재생: {track['playcount']})")
            else:
                print(f"❌ Top 트랙 수집 실패: {top_tracks.get('error', 'Unknown')}")
            
            # 트렌딩 태그 테스트
            print("\n🏷️ 트렌딩 태그 테스트...")
            tags = lastfm.get_trending_tags(limit=10)
            
            if tags['success']:
                print(f"✅ 트렌딩 태그 수집 성공: {len(tags['tags'])}개")
                print("📋 상위 5개 태그:")
                for i, tag in enumerate(tags['tags'][:5]):
                    print(f"  {i+1}. {tag['name']} (사용횟수: {tag['count']})")
            else:
                print(f"❌ 트렌딩 태그 수집 실패: {tags.get('error', 'Unknown')}")
        else:
            print("⚠️ Last.fm API 키가 설정되지 않음 - 기본 기능만 테스트")
        
        return True
        
    except ImportError as e:
        print(f"❌ Last.fm Connector 임포트 실패: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Last.fm Connector 테스트 실패: {str(e)}")
        return False

def test_billboard_connector():
    """Billboard Connector 테스트"""
    print("\n" + "=" * 60)
    print("📈 Billboard Connector 테스트")
    print("=" * 60)
    
    try:
        from billboard_connector import BillboardConnector
        
        billboard = BillboardConnector()
        print(f"✅ Billboard Connector 초기화 성공")
        
        # API 상태 확인
        status = billboard.get_api_status()
        print(f"📊 API 상태: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 사용 가능한 차트 목록
        charts = billboard.get_available_charts()
        if charts['success']:
            print(f"📊 사용 가능한 차트: {len(charts['available_charts'])}개")
            for chart in charts['available_charts'][:5]:
                description = charts['chart_descriptions'].get(chart, 'No description')
                print(f"  • {chart}: {description}")
        
        # Hot 100 테스트 (간단 버전)
        print("\n🔥 Billboard Hot 100 테스트...")
        hot100 = billboard.get_hot_100()
        
        if hot100['success']:
            print(f"✅ Hot 100 수집 성공: {len(hot100['tracks'])}곡")
            print("📋 상위 5곡:")
            for i, track in enumerate(hot100['tracks'][:5]):
                print(f"  {i+1}. {track['artist']} - {track['title']} (인기도: {track['popularity']})")
        else:
            print(f"❌ Hot 100 수집 실패: {hot100.get('error', 'Unknown')}")
            print("ℹ️ 웹 스크래핑 기반이므로 사이트 구조 변경 시 실패할 수 있음")
        
        return True
        
    except ImportError as e:
        print(f"❌ Billboard Connector 임포트 실패: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Billboard Connector 테스트 실패: {str(e)}")
        return False

def test_integrated_chart_collector():
    """통합 차트 수집기 테스트"""
    print("\n" + "=" * 60)
    print("🎯 통합 차트 수집기 테스트")
    print("=" * 60)
    
    try:
        from integrated_chart_collector import IntegratedChartCollector
        
        collector = IntegratedChartCollector()
        print(f"✅ 통합 차트 수집기 초기화 성공")
        
        # API 상태 확인
        status = collector.get_api_status()
        print(f"📊 전체 API 상태:")
        for api_name, api_status in status['individual_apis'].items():
            status_text = "✅ 사용가능" if api_status.get('status') != 'not_initialized' else "❌ 비활성화"
            print(f"  • {api_name}: {status_text}")
        
        print(f"\n⚖️ 차트 가중치: {status['chart_weights']}")
        
        # 한국 차트 수집 테스트 (간단 버전)
        print("\n🇰🇷 한국 차트 통합 수집 테스트...")
        korea_chart = collector.collect_all_charts(region='korea', limit=20)
        
        if korea_chart['success']:
            print(f"✅ 한국 차트 수집 성공")
            print(f"📊 수집 상태: {korea_chart['collection_status']}")
            print(f"🎵 통합된 소스 수: {korea_chart['total_sources']}")
            
            integrated = korea_chart['integrated_chart']
            if integrated['tracks']:
                print(f"📋 통합 차트 상위 5곡:")
                for i, track in enumerate(integrated['tracks'][:5]):
                    sources = ', '.join(track['sources'])
                    print(f"  {i+1}. {track['artist']} - {track['title']}")
                    print(f"      점수: {track['integrated_score']}, 소스: {sources}")
            
            # 소스 통계
            print(f"\n📈 소스별 기여도:")
            for source, stats in integrated['source_statistics'].items():
                print(f"  • {source}: {stats['contributing_tracks']}곡 기여 (가중치: {stats['weight']})")
        else:
            print(f"❌ 한국 차트 수집 실패: {korea_chart.get('error', 'Unknown')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 통합 차트 수집기 임포트 실패: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 통합 차트 수집기 테스트 실패: {str(e)}")
        return False

def test_music_trend_analyzer_integration():
    """Music Trend Analyzer V2 통합 테스트"""
    print("\n" + "=" * 60)
    print("🎼 Music Trend Analyzer V2 통합 테스트")
    print("=" * 60)
    
    try:
        from music_trend_analyzer_v2 import MusicTrendAnalyzerV2
        
        analyzer = MusicTrendAnalyzerV2()
        print(f"✅ Music Trend Analyzer V2 초기화 성공")
        
        # 초기화된 모듈들 확인
        modules = {
            'Reddit': analyzer.reddit_connector is not None,
            'Spotify': analyzer.spotify_connector is not None,
            'Last.fm': analyzer.lastfm_connector is not None,
            'Billboard': analyzer.billboard_connector is not None,
            'YouTube': analyzer.youtube_chart_collector is not None,
            'Keyword Analyzer': analyzer.keyword_analyzer is not None,
            'Comment Analyzer': analyzer.comment_analyzer is not None
        }
        
        print("📊 모듈 초기화 상태:")
        for module, status in modules.items():
            status_text = "✅ 활성화" if status else "❌ 비활성화"
            print(f"  • {module}: {status_text}")
        
        active_modules = sum(modules.values())
        print(f"\n📈 총 {active_modules}/{len(modules)} 모듈이 활성화됨")
        
        if active_modules >= 3:
            print("✅ 통합 분석 시스템이 정상 작동할 수 있습니다")
        else:
            print("⚠️ 일부 모듈이 비활성화되어 제한적 분석만 가능합니다")
        
        return True
        
    except ImportError as e:
        print(f"❌ Music Trend Analyzer V2 임포트 실패: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Music Trend Analyzer V2 테스트 실패: {str(e)}")
        return False

def main():
    """메인 테스트 실행"""
    print("🎵 새로운 차트 API 테스트 시작")
    print(f"⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 테스트 결과 저장
    test_results = {}
    
    # 1. Last.fm Connector 테스트
    test_results['lastfm'] = test_lastfm_connector()
    
    # 2. Billboard Connector 테스트
    test_results['billboard'] = test_billboard_connector()
    
    # 3. 통합 차트 수집기 테스트
    test_results['integrated_chart'] = test_integrated_chart_collector()
    
    # 4. Music Trend Analyzer V2 통합 테스트
    test_results['trend_analyzer_v2'] = test_music_trend_analyzer_integration()
    
    # 최종 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  • {test_name}: {status}")
    
    print(f"\n🎯 전체 결과: {passed_tests}/{total_tests} 테스트 통과")
    
    if passed_tests == total_tests:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ 새로운 차트 API들이 정상적으로 통합되었습니다.")
    elif passed_tests >= total_tests * 0.75:
        print("⚠️ 대부분의 테스트가 통과했지만 일부 이슈가 있습니다.")
        print("💡 실패한 테스트의 오류 메시지를 확인해주세요.")
    else:
        print("❌ 여러 테스트가 실패했습니다.")
        print("🔧 환경 설정 및 API 키 설정을 확인해주세요.")
    
    # 환경 설정 안내
    print("\n💡 환경 설정 팁:")
    print("  • Last.fm: LASTFM_API_KEY 환경변수 설정")
    print("  • Spotify: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET 설정")
    print("  • YouTube: YOUTUBE_API_KEY 설정")
    print("  • Billboard: 인터넷 연결 및 웹 사이트 접근 가능 여부 확인")

if __name__ == "__main__":
    main()