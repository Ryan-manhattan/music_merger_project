#!/usr/bin/env python3
"""
SQLite 뷰어 - 데이터베이스 내용을 쉽게 확인할 수 있는 도구
"""

import sqlite3
import sys
from tabulate import tabulate

class SQLiteViewer:
    def __init__(self, db_path='music_analysis.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def execute_query(self, query):
        """SQL 쿼리 실행"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ 쿼리 실행 오류: {e}")
            return []
    
    def show_tables(self):
        """테이블 목록 표시"""
        print("📊 테이블 목록:")
        results = self.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        for row in results:
            print(f"  - {row['name']}")
    
    def show_table_schema(self, table_name):
        """테이블 스키마 표시"""
        print(f"🗂️  {table_name} 테이블 구조:")
        results = self.execute_query(f"PRAGMA table_info({table_name})")
        headers = ['Column', 'Type', 'NotNull', 'Default', 'PrimaryKey']
        data = []
        for row in results:
            data.append([row['name'], row['type'], bool(row['notnull']), 
                        row['dflt_value'], bool(row['pk'])])
        print(tabulate(data, headers=headers, tablefmt='grid'))
    
    def show_table_data(self, table_name, limit=10):
        """테이블 데이터 표시"""
        print(f"📄 {table_name} 데이터 (최대 {limit}개):")
        results = self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")
        if results:
            headers = list(results[0].keys())
            data = []
            for row in results:
                data.append([str(row[col])[:50] + ('...' if len(str(row[col])) > 50 else '') 
                           for col in headers])
            print(tabulate(data, headers=headers, tablefmt='grid'))
        else:
            print("  데이터 없음")
    
    def show_comments_by_session(self, session_id):
        """특정 세션의 댓글 표시"""
        print(f"💬 세션 {session_id}의 댓글:")
        query = """
        SELECT author, text, sentiment_score, like_count 
        FROM comments 
        WHERE session_id = ? 
        ORDER BY like_count DESC
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (session_id,))
        results = cursor.fetchall()
        
        if results:
            for i, row in enumerate(results, 1):
                sentiment = '😊' if row['sentiment_score'] > 0.1 else '😞' if row['sentiment_score'] < -0.1 else '😐'
                print(f"  [{i}] {sentiment} {row['author']}")
                print(f"      💬 {row['text'][:100]}...")
                print(f"      ❤️ {row['like_count']}, 감성: {row['sentiment_score']:.2f}")
                print()
        else:
            print("  댓글 없음")
    
    def show_statistics(self):
        """통계 표시"""
        print("📊 데이터베이스 통계:")
        
        # 기본 통계
        stats = []
        for table in ['analysis_sessions', 'comments', 'video_tags', 'genre_scores', 'mood_scores']:
            count = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            stats.append([table, count[0]['count'] if count else 0])
        
        print(tabulate(stats, headers=['테이블', '데이터 수'], tablefmt='grid'))
        
        # 장르별 분석 수
        print("\n🎵 장르별 분석:")
        genre_stats = self.execute_query("""
            SELECT primary_genre, COUNT(*) as count 
            FROM analysis_sessions 
            GROUP BY primary_genre 
            ORDER BY count DESC
        """)
        if genre_stats:
            data = [[row['primary_genre'], row['count']] for row in genre_stats]
            print(tabulate(data, headers=['장르', '분석 수'], tablefmt='grid'))
        
        # 감성 분석 통계
        print("\n😊 댓글 감성 분석:")
        sentiment_stats = self.execute_query("""
            SELECT 
                COUNT(*) as total,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(CASE WHEN sentiment_score > 0.1 THEN 1 END) as positive,
                COUNT(CASE WHEN sentiment_score < -0.1 THEN 1 END) as negative,
                COUNT(CASE WHEN sentiment_score BETWEEN -0.1 AND 0.1 THEN 1 END) as neutral
            FROM comments
        """)
        if sentiment_stats:
            row = sentiment_stats[0]
            data = [
                ['총 댓글', row['total']],
                ['평균 감성점수', f"{row['avg_sentiment']:.3f}" if row['avg_sentiment'] else '0'],
                ['긍정 댓글', row['positive']],
                ['부정 댓글', row['negative']],
                ['중립 댓글', row['neutral']]
            ]
            print(tabulate(data, headers=['항목', '값'], tablefmt='grid'))
    
    def interactive_mode(self):
        """대화형 모드"""
        print("🚀 SQLite 뷰어 - 대화형 모드")
        print("사용 가능한 명령어:")
        print("  tables          - 테이블 목록")
        print("  schema <table>  - 테이블 구조")
        print("  data <table>    - 테이블 데이터")
        print("  comments <id>   - 세션 댓글")
        print("  stats           - 통계")
        print("  sql <query>     - SQL 직접 실행")
        print("  quit            - 종료")
        print("-" * 50)
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if command == 'quit':
                    break
                elif command == 'tables':
                    self.show_tables()
                elif command.startswith('schema '):
                    table = command.split(' ', 1)[1]
                    self.show_table_schema(table)
                elif command.startswith('data '):
                    table = command.split(' ', 1)[1]
                    self.show_table_data(table)
                elif command.startswith('comments '):
                    session_id = int(command.split(' ', 1)[1])
                    self.show_comments_by_session(session_id)
                elif command == 'stats':
                    self.show_statistics()
                elif command.startswith('sql '):
                    query = command.split(' ', 1)[1]
                    results = self.execute_query(query)
                    if results:
                        headers = list(results[0].keys())
                        data = [[row[col] for col in headers] for row in results]
                        print(tabulate(data, headers=headers, tablefmt='grid'))
                    else:
                        print("결과 없음")
                else:
                    print("❌ 알 수 없는 명령어")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 오류: {e}")
        
        print("\n👋 뷰어를 종료합니다.")
    
    def close(self):
        """연결 종료"""
        self.conn.close()

if __name__ == '__main__':
    viewer = SQLiteViewer()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'tables':
            viewer.show_tables()
        elif sys.argv[1] == 'stats':
            viewer.show_statistics()
        elif sys.argv[1] == 'interactive':
            viewer.interactive_mode()
    else:
        # 기본 요약 정보 표시
        print("🎵 Music Analysis Database 요약")
        print("=" * 40)
        viewer.show_tables()
        print()
        viewer.show_statistics()
        print("\n💡 더 자세한 정보를 보려면:")
        print("  python sql_viewer.py interactive")
    
    viewer.close()