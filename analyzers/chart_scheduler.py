#!/usr/bin/env python3
"""
Chart Scheduler - 주기적 차트 수집 자동화
국내 주요 음원사 차트 데이터를 스케줄에 따라 자동 수집
"""

import os
import json
import time
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

try:
    from korea_music_charts_connector import KoreaMusicChartsConnector
    KOREA_CHARTS_AVAILABLE = True
except ImportError:
    KOREA_CHARTS_AVAILABLE = False
    print("KoreaMusicChartsConnector를 찾을 수 없습니다.")

class ChartScheduler:
    """차트 수집 스케줄러"""
    
    def __init__(self, console_log=None):
        self.console_log = console_log or print
        self.running = False
        self.scheduler_thread = None
        
        # 로그 설정
        self.setup_logging()
        
        # 스케줄 설정
        self.schedule_config = {
            'realtime_interval': 30,  # 실시간 차트 - 30분마다
            'daily_time': '09:00',    # 일일 수집 - 오전 9시
            'services': ['melon', 'bugs', 'genie', 'vibe'],
            'limit_per_chart': 100,
            'data_retention_days': 7  # 데이터 보관 기간
        }
        
        # 데이터 저장소 설정
        self.data_dir = os.path.join(os.path.dirname(__file__), 'chart_data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.log("차트 스케줄러 초기화 완료")
    
    def setup_logging(self):
        """로깅 설정"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'chart_scheduler.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def log(self, message):
        """로그 출력"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [Scheduler] {message}"
        self.console_log(log_message)
        self.logger.info(message)
    
    def start_scheduler(self):
        """스케줄러 시작"""
        if self.running:
            self.log("스케줄러가 이미 실행 중입니다.")
            return
        
        if not KOREA_CHARTS_AVAILABLE:
            self.log("KoreaMusicChartsConnector를 사용할 수 없어 스케줄러를 시작할 수 없습니다.")
            return
        
        self.log("차트 수집 스케줄러 시작")
        self.running = True
        
        # 스케줄 등록
        self.setup_schedules()
        
        # 스케줄러 스레드 시작
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.log(f"스케줄 등록 완료:")
        self.log(f"  - 실시간 차트: {self.schedule_config['realtime_interval']}분마다")
        self.log(f"  - 일일 차트: 매일 {self.schedule_config['daily_time']}")
        self.log(f"  - 대상 서비스: {', '.join(self.schedule_config['services'])}")
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        if not self.running:
            self.log("스케줄러가 실행되지 않았습니다.")
            return
        
        self.log("차트 수집 스케줄러 중지")
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
    
    def setup_schedules(self):
        """스케줄 설정"""
        # 실시간 차트 스케줄 (주기적)
        schedule.every(self.schedule_config['realtime_interval']).minutes.do(
            self.collect_realtime_charts
        )
        
        # 일일 종합 차트 스케줄
        schedule.every().day.at(self.schedule_config['daily_time']).do(
            self.collect_daily_charts
        )
        
        # 데이터 정리 스케줄 (매일 자정)
        schedule.every().day.at("00:00").do(
            self.cleanup_old_data
        )
        
        # 즉시 한 번 실행 (시작 시 데이터 수집)
        schedule.every().minute.do(
            lambda: self.collect_realtime_charts(immediate=True)
        ).tag('immediate')
    
    def _run_scheduler(self):
        """스케줄러 실행 루프"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
            except Exception as e:
                self.log(f"스케줄러 실행 오류: {str(e)}")
                time.sleep(60)
    
    def collect_realtime_charts(self, immediate=False):
        """실시간 차트 수집"""
        try:
            if immediate:
                # 즉시 실행 스케줄 제거
                schedule.clear('immediate')
            
            self.log("실시간 차트 수집 시작")
            
            # 통합 차트 커넥터 초기화
            connector = KoreaMusicChartsConnector(self.console_log)
            
            # 차트 데이터 수집
            chart_data = connector.get_all_charts(
                services=self.schedule_config['services'],
                limit_per_chart=self.schedule_config['limit_per_chart']
            )
            
            if chart_data['success']:
                # 크로스 플랫폼 분석 추가
                cross_analysis = connector.get_cross_platform_analysis(chart_data)
                if cross_analysis.get('success'):
                    chart_data['cross_platform_analysis'] = cross_analysis
                
                # 데이터 저장
                self.save_chart_data(chart_data, 'realtime')
                
                self.log(f"실시간 차트 수집 완료: {chart_data['successful_services']}/{chart_data['total_services']} 서비스, {chart_data['total_tracks']}곡")
            else:
                self.log("실시간 차트 수집 실패")
                
        except Exception as e:
            self.log(f"실시간 차트 수집 오류: {str(e)}")
    
    def collect_daily_charts(self):
        """일일 종합 차트 수집"""
        try:
            self.log("일일 종합 차트 수집 시작")
            
            connector = KoreaMusicChartsConnector(self.console_log)
            
            # 더 많은 데이터 수집 (일일은 더 상세하게)
            chart_data = connector.get_all_charts(
                services=self.schedule_config['services'],
                limit_per_chart=200  # 일일 차트는 더 많이
            )
            
            if chart_data['success']:
                cross_analysis = connector.get_cross_platform_analysis(chart_data)
                if cross_analysis.get('success'):
                    chart_data['cross_platform_analysis'] = cross_analysis
                
                # 일일 데이터로 저장
                self.save_chart_data(chart_data, 'daily')
                
                # 주간 통계 생성
                self.generate_weekly_stats()
                
                self.log(f"일일 종합 차트 수집 완료: {chart_data['total_tracks']}곡")
            else:
                self.log("일일 종합 차트 수집 실패")
                
        except Exception as e:
            self.log(f"일일 차트 수집 오류: {str(e)}")
    
    def save_chart_data(self, data, data_type='realtime'):
        """차트 데이터 저장"""
        try:
            timestamp = datetime.now()
            
            # 파일명 생성
            if data_type == 'realtime':
                filename = f"charts_realtime_{timestamp.strftime('%Y%m%d_%H%M')}.json"
            else:
                filename = f"charts_daily_{timestamp.strftime('%Y%m%d')}.json"
            
            filepath = os.path.join(self.data_dir, filename)
            
            # 저장할 데이터에 메타데이터 추가
            save_data = {
                'metadata': {
                    'collection_type': data_type,
                    'collected_at': timestamp.isoformat(),
                    'scheduler_version': '1.0'
                },
                'chart_data': data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.log(f"차트 데이터 저장: {filename}")
            
            # 최신 데이터 링크 업데이트
            self.update_latest_data_link(filepath, data_type)
            
        except Exception as e:
            self.log(f"데이터 저장 오류: {str(e)}")
    
    def update_latest_data_link(self, filepath, data_type):
        """최신 데이터 링크 업데이트"""
        try:
            link_name = f"latest_{data_type}.json"
            link_path = os.path.join(self.data_dir, link_name)
            
            # Windows에서는 심볼릭 링크 대신 복사
            import shutil
            shutil.copy2(filepath, link_path)
            
            self.log(f"최신 데이터 링크 업데이트: {link_name}")
            
        except Exception as e:
            self.log(f"링크 업데이트 오류: {str(e)}")
    
    def cleanup_old_data(self):
        """오래된 데이터 정리"""
        try:
            self.log("오래된 데이터 정리 시작")
            
            cutoff_date = datetime.now() - timedelta(days=self.schedule_config['data_retention_days'])
            deleted_count = 0
            
            for filename in os.listdir(self.data_dir):
                if filename.startswith('charts_') and filename.endswith('.json'):
                    filepath = os.path.join(self.data_dir, filename)
                    
                    # 파일 생성 시간 확인
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    if file_time < cutoff_date and not filename.startswith('latest_'):
                        os.remove(filepath)
                        deleted_count += 1
            
            self.log(f"오래된 데이터 정리 완료: {deleted_count}개 파일 삭제")
            
        except Exception as e:
            self.log(f"데이터 정리 오류: {str(e)}")
    
    def generate_weekly_stats(self):
        """주간 통계 생성"""
        try:
            # 지난 7일간의 일일 데이터 수집
            weekly_data = []
            for i in range(7):
                date = datetime.now() - timedelta(days=i)
                filename = f"charts_daily_{date.strftime('%Y%m%d')}.json"
                filepath = os.path.join(self.data_dir, filename)
                
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        weekly_data.append(data)
            
            if weekly_data:
                # 주간 통계 계산
                stats = self.calculate_weekly_stats(weekly_data)
                
                # 주간 통계 저장
                stats_filename = f"weekly_stats_{datetime.now().strftime('%Y%m%d')}.json"
                stats_filepath = os.path.join(self.data_dir, stats_filename)
                
                with open(stats_filepath, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
                
                self.log("주간 통계 생성 완료")
            
        except Exception as e:
            self.log(f"주간 통계 생성 오류: {str(e)}")
    
    def calculate_weekly_stats(self, weekly_data):
        """주간 통계 계산"""
        # 간단한 주간 통계 예시
        total_tracks = sum(data['chart_data'].get('total_tracks', 0) for data in weekly_data)
        avg_success_rate = sum(data['chart_data'].get('success_rate', 0) for data in weekly_data) / len(weekly_data)
        
        # 가장 자주 나타난 크로스 플랫폼 히트곡들
        all_hits = []
        for data in weekly_data:
            cross_analysis = data['chart_data'].get('cross_platform_analysis', {})
            if cross_analysis.get('success'):
                all_hits.extend(cross_analysis.get('cross_platform_hits', []))
        
        # 곡별 등장 횟수 계산
        hit_counts = {}
        for hit in all_hits:
            key = f"{hit['title']} - {hit['artist']}"
            hit_counts[key] = hit_counts.get(key, 0) + 1
        
        top_weekly_hits = sorted(hit_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            'period': f"{(datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')} ~ {datetime.now().strftime('%Y-%m-%d')}",
            'total_collections': len(weekly_data),
            'total_tracks_collected': total_tracks,
            'average_success_rate': round(avg_success_rate, 2),
            'top_weekly_hits': [{'track': track, 'appearances': count} for track, count in top_weekly_hits],
            'generated_at': datetime.now().isoformat()
        }
    
    def get_status(self):
        """스케줄러 상태 반환"""
        return {
            'running': self.running,
            'schedule_config': self.schedule_config,
            'data_dir': self.data_dir,
            'next_realtime': schedule.next_run() if schedule.jobs else None,
            'data_files_count': len([f for f in os.listdir(self.data_dir) if f.endswith('.json')])
        }
    
    def update_config(self, new_config):
        """스케줄 설정 업데이트"""
        try:
            self.schedule_config.update(new_config)
            
            if self.running:
                # 스케줄러 재시작
                self.stop_scheduler()
                time.sleep(1)
                self.start_scheduler()
            
            self.log("스케줄 설정 업데이트 완료")
            
        except Exception as e:
            self.log(f"설정 업데이트 오류: {str(e)}")

# 전역 스케줄러 인스턴스
_global_scheduler = None

def get_scheduler():
    """전역 스케줄러 인스턴스 반환"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = ChartScheduler()
    return _global_scheduler

def start_chart_scheduler():
    """차트 스케줄러 시작"""
    scheduler = get_scheduler()
    scheduler.start_scheduler()
    return scheduler

def stop_chart_scheduler():
    """차트 스케줄러 중지"""
    scheduler = get_scheduler()
    scheduler.stop_scheduler()

# 테스트 및 CLI 실행
if __name__ == "__main__":
    import sys
    
    scheduler = ChartScheduler()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            print("차트 스케줄러를 시작합니다...")
            scheduler.start_scheduler()
            
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\n스케줄러를 중지합니다...")
                scheduler.stop_scheduler()
                
        elif command == 'status':
            status = scheduler.get_status()
            print(f"스케줄러 상태: {status}")
            
        elif command == 'test':
            print("차트 수집 테스트를 실행합니다...")
            scheduler.collect_realtime_charts(immediate=True)
            
        else:
            print("사용법: python chart_scheduler.py [start|status|test]")
    else:
        # 기본 테스트 실행
        print("=== 차트 스케줄러 테스트 ===")
        print("차트 수집 테스트 실행...")
        scheduler.collect_realtime_charts(immediate=True)
        print("테스트 완료!")