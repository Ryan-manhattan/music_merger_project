#!/usr/bin/env python3
"""
Database Manager - SQLite 데이터베이스 관리 모듈
YouTube 분석 결과와 댓글 데이터 저장
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = None, console_log=None):
        """
        데이터베이스 매니저 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로 (기본: music_analysis.db)
            console_log: 로그 출력 함수
        """
        self.db_path = db_path or os.path.join(os.getcwd(), 'music_analysis.db')
        self.console_log = console_log or print
        
        # 데이터베이스 초기화
        self.init_database()
    
    def init_database(self):
        """데이터베이스 테이블 생성"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 분석 세션 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id TEXT NOT NULL,
                        video_url TEXT NOT NULL,
                        video_title TEXT,
                        channel_name TEXT,
                        artist TEXT,
                        song TEXT,
                        duration INTEGER,
                        view_count INTEGER,
                        like_count INTEGER,
                        primary_genre TEXT,
                        primary_mood TEXT,
                        estimated_bpm INTEGER,
                        estimated_key TEXT,
                        energy_level TEXT,
                        sentiment_score REAL,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        thumbnail_url TEXT,
                        published_at TEXT,
                        UNIQUE(video_id, analyzed_at)
                    )
                ''')
                
                # 댓글 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        author TEXT NOT NULL,
                        text TEXT NOT NULL,
                        like_count INTEGER DEFAULT 0,
                        published_at TEXT,
                        sentiment_score REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES analysis_sessions (id)
                    )
                ''')
                
                # 태그 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS video_tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        tag TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES analysis_sessions (id)
                    )
                ''')
                
                # 장르 점수 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS genre_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        genre TEXT NOT NULL,
                        score INTEGER DEFAULT 0,
                        FOREIGN KEY (session_id) REFERENCES analysis_sessions (id)
                    )
                ''')
                
                # 분위기 점수 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mood_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        mood TEXT NOT NULL,
                        score INTEGER DEFAULT 0,
                        FOREIGN KEY (session_id) REFERENCES analysis_sessions (id)
                    )
                ''')
                
                # 인덱스 생성
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_id ON analysis_sessions(video_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyzed_at ON analysis_sessions(analyzed_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_comments ON comments(session_id)')
                
                conn.commit()
                self.console_log("[Database] 데이터베이스 초기화 완료")
                
        except Exception as e:
            self.console_log(f"[Database] 초기화 오류: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태 결과
        try:
            yield conn
        finally:
            conn.close()
    
    def save_analysis_result(self, analysis_result: Dict) -> int:
        """
        분석 결과를 데이터베이스에 저장
        
        Args:
            analysis_result: music_analyzer의 분석 결과
            
        Returns:
            저장된 세션 ID
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기본 분석 정보 추출
                video_info = analysis_result['video_info']
                music_analysis = analysis_result['music_analysis']
                comments_data = analysis_result.get('comments_data', {})
                
                # 분석 세션 저장
                cursor.execute('''
                    INSERT INTO analysis_sessions (
                        video_id, video_url, video_title, channel_name,
                        artist, song, duration, view_count, like_count,
                        primary_genre, primary_mood, estimated_bpm, 
                        estimated_key, energy_level, sentiment_score,
                        thumbnail_url, published_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_info['video_id'],
                    video_info['url'],
                    video_info['title'],
                    video_info['channel'],
                    music_analysis['artist'],
                    music_analysis['song'],
                    video_info['duration'],
                    video_info['view_count'],
                    video_info['like_count'],
                    music_analysis['genre']['primary_genre'],
                    music_analysis['mood']['primary_mood'],
                    music_analysis['estimated_bpm'],
                    music_analysis['estimated_key'],
                    music_analysis['energy_level'],
                    comments_data.get('sentiment_analysis', {}).get('average_sentiment', 0),
                    video_info['thumbnail'],
                    video_info['published_at']
                ))
                
                session_id = cursor.lastrowid
                
                # 댓글 저장
                if 'comments' in comments_data:
                    for comment in comments_data['comments']:
                        sentiment = self._calculate_sentiment(comment['text'])
                        cursor.execute('''
                            INSERT INTO comments (
                                session_id, author, text, like_count, 
                                published_at, sentiment_score
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            session_id,
                            comment['author'],
                            comment['text'],
                            comment['like_count'],
                            comment['published_at'],
                            sentiment
                        ))
                
                # 태그 저장
                if 'tags' in music_analysis:
                    for tag in music_analysis['tags']:
                        cursor.execute('''
                            INSERT INTO video_tags (session_id, tag) VALUES (?, ?)
                        ''', (session_id, tag))
                
                # 장르 점수 저장
                if 'genre_scores' in music_analysis['genre']:
                    for genre, score in music_analysis['genre']['genre_scores'].items():
                        cursor.execute('''
                            INSERT INTO genre_scores (session_id, genre, score) VALUES (?, ?, ?)
                        ''', (session_id, genre, score))
                
                # 분위기 점수 저장
                if 'mood_scores' in music_analysis['mood']:
                    for mood, score in music_analysis['mood']['mood_scores'].items():
                        cursor.execute('''
                            INSERT INTO mood_scores (session_id, mood, score) VALUES (?, ?, ?)
                        ''', (session_id, mood, score))
                
                conn.commit()
                self.console_log(f"[Database] 분석 결과 저장 완료: session_id={session_id}")
                return session_id
                
        except Exception as e:
            self.console_log(f"[Database] 저장 오류: {str(e)}")
            raise
    
    def get_analysis_history(self, limit: int = 50) -> List[Dict]:
        """
        분석 이력 조회
        
        Args:
            limit: 조회할 최대 개수
            
        Returns:
            분석 이력 리스트
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM analysis_sessions 
                    ORDER BY analyzed_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                sessions = [dict(row) for row in cursor.fetchall()]
                
                # 각 세션의 댓글 수 추가
                for session in sessions:
                    cursor.execute('''
                        SELECT COUNT(*) as comment_count 
                        FROM comments 
                        WHERE session_id = ?
                    ''', (session['id'],))
                    
                    session['comment_count'] = cursor.fetchone()['comment_count']
                
                return sessions
                
        except Exception as e:
            self.console_log(f"[Database] 이력 조회 오류: {str(e)}")
            return []
    
    def get_session_details(self, session_id: int) -> Optional[Dict]:
        """
        특정 세션의 상세 정보 조회 (댓글 포함)
        
        Args:
            session_id: 세션 ID
            
        Returns:
            세션 상세 정보
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 세션 기본 정보
                cursor.execute('SELECT * FROM analysis_sessions WHERE id = ?', (session_id,))
                session = cursor.fetchone()
                
                if not session:
                    return None
                
                session_dict = dict(session)
                
                # 댓글 조회
                cursor.execute('''
                    SELECT * FROM comments 
                    WHERE session_id = ? 
                    ORDER BY like_count DESC, published_at DESC
                ''', (session_id,))
                session_dict['comments'] = [dict(row) for row in cursor.fetchall()]
                
                # 태그 조회
                cursor.execute('SELECT tag FROM video_tags WHERE session_id = ?', (session_id,))
                session_dict['tags'] = [row['tag'] for row in cursor.fetchall()]
                
                # 장르 점수 조회
                cursor.execute('SELECT genre, score FROM genre_scores WHERE session_id = ?', (session_id,))
                session_dict['genre_scores'] = {row['genre']: row['score'] for row in cursor.fetchall()}
                
                # 분위기 점수 조회
                cursor.execute('SELECT mood, score FROM mood_scores WHERE session_id = ?', (session_id,))
                session_dict['mood_scores'] = {row['mood']: row['score'] for row in cursor.fetchall()}
                
                return session_dict
                
        except Exception as e:
            self.console_log(f"[Database] 세션 조회 오류: {str(e)}")
            return None
    
    def search_by_artist(self, artist: str) -> List[Dict]:
        """아티스트로 검색"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM analysis_sessions 
                    WHERE artist LIKE ? 
                    ORDER BY analyzed_at DESC
                ''', (f'%{artist}%',))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.console_log(f"[Database] 아티스트 검색 오류: {str(e)}")
            return []
    
    def search_by_genre(self, genre: str) -> List[Dict]:
        """장르로 검색"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM analysis_sessions 
                    WHERE primary_genre = ? 
                    ORDER BY analyzed_at DESC
                ''', (genre,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.console_log(f"[Database] 장르 검색 오류: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict:
        """데이터베이스 통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 총 분석 수
                cursor.execute('SELECT COUNT(*) as total_analyses FROM analysis_sessions')
                total_analyses = cursor.fetchone()['total_analyses']
                
                # 총 댓글 수
                cursor.execute('SELECT COUNT(*) as total_comments FROM comments')
                total_comments = cursor.fetchone()['total_comments']
                
                # 장르별 분석 수
                cursor.execute('''
                    SELECT primary_genre, COUNT(*) as count 
                    FROM analysis_sessions 
                    GROUP BY primary_genre 
                    ORDER BY count DESC
                ''')
                genre_stats = {row['primary_genre']: row['count'] for row in cursor.fetchall()}
                
                # 분위기별 분석 수
                cursor.execute('''
                    SELECT primary_mood, COUNT(*) as count 
                    FROM analysis_sessions 
                    GROUP BY primary_mood 
                    ORDER BY count DESC
                ''')
                mood_stats = {row['primary_mood']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'total_analyses': total_analyses,
                    'total_comments': total_comments,
                    'genre_distribution': genre_stats,
                    'mood_distribution': mood_stats
                }
                
        except Exception as e:
            self.console_log(f"[Database] 통계 조회 오류: {str(e)}")
            return {}
    
    def _calculate_sentiment(self, text: str) -> float:
        """텍스트 감성 점수 계산"""
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except:
            return 0.0
    
    def delete_session(self, session_id: int) -> bool:
        """세션 및 관련 데이터 삭제"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 관련 데이터 삭제 (외래키 제약 때문에 순서 중요)
                cursor.execute('DELETE FROM comments WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM video_tags WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM genre_scores WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM mood_scores WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM analysis_sessions WHERE id = ?', (session_id,))
                
                conn.commit()
                self.console_log(f"[Database] 세션 삭제 완료: session_id={session_id}")
                return True
                
        except Exception as e:
            self.console_log(f"[Database] 삭제 오류: {str(e)}")
            return False