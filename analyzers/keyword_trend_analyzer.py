#!/usr/bin/env python3
"""
Keyword Trend Analyzer - 키워드 중심 음악 트렌드 분석
해시태그, 언급빈도, 감정어, MCP 통합 분석
"""

import os
import re
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from collections import Counter, defaultdict
import math

try:
    import nltk
    from textblob import TextBlob
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    from konlpy.tag import Okt
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False

class KeywordTrendAnalyzer:
    def __init__(self, console_log=None):
        """
        키워드 트렌드 분석기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        
        # 형태소 분석기 초기화 (한국어)
        self.okt = None
        if KONLPY_AVAILABLE:
            try:
                self.okt = Okt()
                self.console_log("[Keyword] 한국어 형태소 분석기 초기화 완료")
            except Exception as e:
                self.console_log(f"[Keyword] 형태소 분석기 초기화 오류: {str(e)}")
        
        # 음악 관련 키워드 사전
        self.music_keywords = {
            'genres': {
                'kpop': ['케이팝', 'k-pop', 'kpop', '아이돌', 'idol', '한국음악'],
                'hiphop': ['힙합', 'hip-hop', 'hiphop', '랩', 'rap', '래퍼', 'rapper'],
                'pop': ['팝', 'pop', '팝송', 'pop music'],
                'rock': ['록', 'rock', '밴드', 'band', '메탈', 'metal'],
                'ballad': ['발라드', 'ballad', '감성', '슬픈노래'],
                'electronic': ['일렉트로닉', 'electronic', 'edm', '댄스뮤직', 'techno', 'house'],
                'jazz': ['재즈', 'jazz', '즉흥연주'],
                'classical': ['클래식', 'classical', '오케스트라', 'orchestra']
            },
            'emotions': {
                'positive': ['좋아', '최고', '대박', '짱', '완벽', '사랑', '행복', '신나', '멋져', '훌륭'],
                'negative': ['별로', '싫어', '짜증', '최악', '실망', '슬퍼', '지루', '아쉬워'],
                'exciting': ['신나', '흥겨워', '춤추고싶어', '에너지', '파워풀', '역동적'],
                'calm': ['잔잔', '편안', '힐링', '차분', '평온', '안정적']
            },
            'trends': {
                'viral': ['바이럴', 'viral', '인기', '핫', 'hot', '트렌드', 'trending'],
                'chart': ['차트', 'chart', '순위', 'ranking', '1위', '톱'],
                'new': ['신곡', '새로운', 'new', '최신', '데뷔', 'debut'],
                'collaboration': ['콜라보', 'collab', '피처링', 'feat', '듀엣', 'duet']
            },
            'platforms': {
                'streaming': ['스포티파이', 'spotify', '멜론', 'melon', 'apple music', '유튜브뮤직'],
                'social': ['틱톡', 'tiktok', '인스타', 'instagram', '트위터', 'twitter'],
                'broadcast': ['음방', '뮤직뱅크', '인기가요', '쇼챔피언']
            }
        }
        
        # 불용어 (제외할 단어들)
        self.stopwords = {
            'korean': ['이', '그', '저', '의', '가', '을', '를', '에', '에서', '와', '과', '도', '는', '은', '로', '으로'],
            'english': ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        }
        
        # 해시태그 패턴
        self.hashtag_pattern = re.compile(r'#[^\s#]+')
        self.mention_pattern = re.compile(r'@[^\s@]+')
        
        # 감정 점수 가중치
        self.emotion_weights = {
            'positive': 1.0,
            'negative': -1.0,
            'exciting': 1.2,
            'calm': 0.8
        }
    
    def extract_hashtags_and_mentions(self, text: str) -> Dict:
        """
        텍스트에서 해시태그와 멘션 추출
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            해시태그와 멘션 정보
        """
        try:
            # 해시태그 추출
            hashtags = self.hashtag_pattern.findall(text)
            hashtags = [tag.lower() for tag in hashtags]
            
            # 멘션 추출
            mentions = self.mention_pattern.findall(text)
            mentions = [mention.lower() for mention in mentions]
            
            # 해시태그 분류
            categorized_hashtags = self._categorize_hashtags(hashtags)
            
            result = {
                'hashtags': hashtags,
                'mentions': mentions,
                'hashtag_count': len(hashtags),
                'mention_count': len(mentions),
                'categorized_hashtags': categorized_hashtags,
                'engagement_score': self._calculate_hashtag_engagement(hashtags)
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Keyword] 해시태그/멘션 추출 오류: {str(e)}")
            return {'hashtags': [], 'mentions': [], 'hashtag_count': 0, 'mention_count': 0}
    
    def _categorize_hashtags(self, hashtags: List[str]) -> Dict:
        """해시태그를 카테고리별로 분류"""
        categorized = defaultdict(list)
        
        for hashtag in hashtags:
            tag_clean = hashtag.replace('#', '').lower()
            
            # 장르 분류
            for genre, keywords in self.music_keywords['genres'].items():
                for keyword in keywords:
                    if keyword.lower() in tag_clean:
                        categorized['genres'].append(genre)
                        break
            
            # 트렌드 분류
            for trend_type, keywords in self.music_keywords['trends'].items():
                for keyword in keywords:
                    if keyword.lower() in tag_clean:
                        categorized['trends'].append(trend_type)
                        break
            
            # 플랫폼 분류
            for platform_type, keywords in self.music_keywords['platforms'].items():
                for keyword in keywords:
                    if keyword.lower() in tag_clean:
                        categorized['platforms'].append(platform_type)
                        break
        
        return dict(categorized)
    
    def _calculate_hashtag_engagement(self, hashtags: List[str]) -> float:
        """해시태그 기반 참여도 점수 계산"""
        if not hashtags:
            return 0.0
        
        # 해시태그 개수와 다양성을 고려한 점수
        unique_hashtags = len(set(hashtags))
        total_hashtags = len(hashtags)
        
        # 점수 = (고유 해시태그 수 * 0.7) + (총 해시태그 수 * 0.3)
        score = (unique_hashtags * 0.7) + (total_hashtags * 0.3)
        
        # 0-10 스케일로 정규화
        return min(score, 10.0)
    
    def analyze_keyword_frequency(self, texts: List[str], language: str = 'mixed') -> Dict:
        """
        키워드 빈도 분석
        
        Args:
            texts: 분석할 텍스트 목록
            language: 언어 ('korean', 'english', 'mixed')
            
        Returns:
            키워드 빈도 분석 결과
        """
        try:
            all_keywords = []
            music_keyword_counts = Counter()
            
            for text in texts:
                # 텍스트 전처리
                clean_text = self._preprocess_text(text)
                
                # 언어별 키워드 추출
                if language == 'korean' or language == 'mixed':
                    korean_keywords = self._extract_korean_keywords(clean_text)
                    all_keywords.extend(korean_keywords)
                
                if language == 'english' or language == 'mixed':
                    english_keywords = self._extract_english_keywords(clean_text)
                    all_keywords.extend(english_keywords)
                
                # 음악 관련 키워드 매칭
                music_matches = self._match_music_keywords(clean_text)
                for category, matches in music_matches.items():
                    for match in matches:
                        music_keyword_counts[f"{category}:{match}"] += 1
            
            # 키워드 빈도 계산
            keyword_frequency = Counter(all_keywords)
            
            # TF-IDF 스타일 중요도 계산
            keyword_importance = self._calculate_keyword_importance(keyword_frequency, len(texts))
            
            result = {
                'total_texts_analyzed': len(texts),
                'total_keywords_extracted': len(all_keywords),
                'unique_keywords': len(keyword_frequency),
                'top_keywords': dict(keyword_frequency.most_common(50)),
                'keyword_importance': keyword_importance,
                'music_keywords': dict(music_keyword_counts.most_common(30)),
                'keyword_density': len(all_keywords) / max(sum(len(text.split()) for text in texts), 1),
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Keyword] 키워드 빈도 분석 오류: {str(e)}")
            return {'error': str(e)}
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # URL 제거
        text = re.sub(r'http[s]?://\S+', '', text)
        # 특수문자 정리 (일부 유지)
        text = re.sub(r'[^\w\s#@가-힣]', ' ', text)
        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_korean_keywords(self, text: str) -> List[str]:
        """한국어 키워드 추출"""
        keywords = []
        
        if self.okt:
            try:
                # 형태소 분석
                morphs = self.okt.morphs(text, stem=True)
                pos_tags = self.okt.pos(text, stem=True)
                
                # 명사, 형용사, 동사만 추출
                for word, pos in pos_tags:
                    if (pos in ['Noun', 'Adjective', 'Verb'] and 
                        len(word) > 1 and 
                        word not in self.stopwords['korean']):
                        keywords.append(word)
                        
            except Exception as e:
                # 형태소 분석 실패 시 단순 분할
                words = text.split()
                keywords = [word for word in words if len(word) > 1 and word not in self.stopwords['korean']]
        else:
            # 형태소 분석기 없을 시 단순 분할
            words = text.split()
            keywords = [word for word in words if len(word) > 1 and word not in self.stopwords['korean']]
        
        return keywords
    
    def _extract_english_keywords(self, text: str) -> List[str]:
        """영어 키워드 추출"""
        # 영어 단어 추출
        english_words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # 불용어 제거 및 길이 필터링
        keywords = [word for word in english_words 
                   if len(word) > 2 and word not in self.stopwords['english']]
        
        return keywords
    
    def _match_music_keywords(self, text: str) -> Dict:
        """음악 관련 키워드 매칭"""
        matches = defaultdict(list)
        text_lower = text.lower()
        
        for category, subcategories in self.music_keywords.items():
            for subcategory, keywords in subcategories.items():
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        matches[category].append(subcategory)
        
        return dict(matches)
    
    def _calculate_keyword_importance(self, keyword_freq: Counter, total_docs: int) -> Dict:
        """키워드 중요도 계산 (TF-IDF 스타일)"""
        importance = {}
        total_keywords = sum(keyword_freq.values())
        
        for keyword, freq in keyword_freq.items():
            # TF (Term Frequency)
            tf = freq / total_keywords
            
            # IDF (Inverse Document Frequency) - 단순화된 버전
            # 빈도가 높을수록 중요도가 높지만, 너무 흔한 단어는 페널티
            idf = math.log(total_docs / (freq + 1)) + 1
            
            # TF-IDF 점수
            tfidf = tf * idf
            importance[keyword] = round(tfidf, 4)
        
        # 중요도 순으로 정렬하여 상위 30개 반환
        sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:30])
        
        return sorted_importance
    
    def analyze_emotion_keywords(self, texts: List[str]) -> Dict:
        """
        감정어 분석
        
        Args:
            texts: 분석할 텍스트 목록
            
        Returns:
            감정어 분석 결과
        """
        try:
            emotion_scores = defaultdict(float)
            emotion_counts = defaultdict(int)
            sentiment_distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            for text in texts:
                text_lower = text.lower()
                text_score = 0
                
                # 감정 키워드 매칭 및 점수 계산
                for emotion_type, keywords in self.music_keywords['emotions'].items():
                    matches = 0
                    for keyword in keywords:
                        if keyword in text_lower:
                            matches += text_lower.count(keyword)
                    
                    if matches > 0:
                        emotion_counts[emotion_type] += matches
                        weight = self.emotion_weights.get(emotion_type, 0)
                        emotion_scores[emotion_type] += matches * weight
                        text_score += matches * weight
                
                # 전체 감정 분포 계산
                if text_score > 0.5:
                    sentiment_distribution['positive'] += 1
                elif text_score < -0.5:
                    sentiment_distribution['negative'] += 1
                else:
                    sentiment_distribution['neutral'] += 1
            
            # 감정 점수 정규화
            total_texts = len(texts)
            normalized_scores = {}
            for emotion, score in emotion_scores.items():
                normalized_scores[emotion] = score / total_texts if total_texts > 0 else 0
            
            # 전반적인 감정 점수
            overall_sentiment = sum(normalized_scores.values())
            
            result = {
                'emotion_scores': dict(normalized_scores),
                'emotion_counts': dict(emotion_counts),
                'overall_sentiment': overall_sentiment,
                'sentiment_distribution': sentiment_distribution,
                'dominant_emotion': max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else 'neutral',
                'emotion_intensity': abs(overall_sentiment),
                'analyzed_texts': total_texts,
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Keyword] 감정어 분석 오류: {str(e)}")
            return {'error': str(e)}
    
    def generate_trend_keywords(self, keyword_data: Dict, hashtag_data: Dict, 
                               emotion_data: Dict, time_weight: float = 1.0) -> Dict:
        """
        종합 트렌드 키워드 생성
        
        Args:
            keyword_data: 키워드 빈도 분석 결과
            hashtag_data: 해시태그 분석 결과
            emotion_data: 감정어 분석 결과
            time_weight: 시간 가중치 (최신일수록 높음)
            
        Returns:
            트렌드 키워드 분석 결과
        """
        try:
            trend_scores = defaultdict(float)
            
            # 키워드 빈도 점수 반영
            if 'keyword_importance' in keyword_data:
                for keyword, importance in keyword_data['keyword_importance'].items():
                    trend_scores[keyword] += importance * 0.4 * time_weight
            
            # 해시태그 점수 반영
            if 'hashtags' in hashtag_data:
                hashtag_freq = Counter(hashtag_data['hashtags'])
                for hashtag, freq in hashtag_freq.items():
                    # 해시태그는 더 높은 가중치
                    trend_scores[hashtag] += freq * 0.6 * time_weight
            
            # 감정 점수 반영
            if 'emotion_scores' in emotion_data:
                for emotion, score in emotion_data['emotion_scores'].items():
                    # 감정 강도가 높을수록 트렌드 점수 증가
                    trend_scores[f"emotion_{emotion}"] += abs(score) * 0.3 * time_weight
            
            # 상위 트렌드 키워드 선별
            top_trends = dict(sorted(trend_scores.items(), key=lambda x: x[1], reverse=True)[:20])
            
            # 카테고리별 트렌드
            categorized_trends = {
                'music_genres': [],
                'emotions': [],
                'viral_terms': [],
                'general': []
            }
            
            for keyword, score in top_trends.items():
                if keyword.startswith('emotion_'):
                    categorized_trends['emotions'].append({'keyword': keyword, 'score': score})
                elif any(genre in keyword.lower() for genre in self.music_keywords['genres'].keys()):
                    categorized_trends['music_genres'].append({'keyword': keyword, 'score': score})
                elif any(trend in keyword.lower() for trend in self.music_keywords['trends']['viral']):
                    categorized_trends['viral_terms'].append({'keyword': keyword, 'score': score})
                else:
                    categorized_trends['general'].append({'keyword': keyword, 'score': score})
            
            # 트렌드 강도 계산
            trend_intensity = sum(top_trends.values()) / len(top_trends) if top_trends else 0
            
            result = {
                'top_trend_keywords': top_trends,
                'categorized_trends': categorized_trends,
                'trend_intensity': trend_intensity,
                'trend_direction': 'rising' if trend_intensity > 5 else 'stable' if trend_intensity > 2 else 'declining',
                'time_weight_applied': time_weight,
                'generated_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Keyword] 트렌드 키워드 생성 오류: {str(e)}")
            return {'error': str(e)}
    
    def analyze_keyword_evolution(self, historical_data: List[Dict], days: int = 7) -> Dict:
        """
        키워드 진화 분석 (시간에 따른 변화)
        
        Args:
            historical_data: 과거 키워드 데이터 리스트
            days: 분석할 일수
            
        Returns:
            키워드 진화 분석 결과
        """
        try:
            if not historical_data:
                return {'error': '분석할 데이터가 없습니다'}
            
            # 시간별 키워드 추적
            keyword_timeline = defaultdict(list)
            
            for data in historical_data[-days:]:  # 최근 N일만 분석
                if 'top_keywords' in data:
                    timestamp = data.get('analyzed_at', datetime.now().isoformat())
                    for keyword, count in data['top_keywords'].items():
                        keyword_timeline[keyword].append({
                            'timestamp': timestamp,
                            'count': count
                        })
            
            # 키워드별 변화율 계산
            keyword_changes = {}
            emerging_keywords = []
            declining_keywords = []
            
            for keyword, timeline in keyword_timeline.items():
                if len(timeline) >= 2:
                    recent_avg = sum(item['count'] for item in timeline[-2:]) / 2
                    older_avg = sum(item['count'] for item in timeline[:-2]) / max(len(timeline) - 2, 1)
                    
                    change_rate = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
                    keyword_changes[keyword] = change_rate
                    
                    if change_rate > 50:  # 50% 이상 증가
                        emerging_keywords.append({'keyword': keyword, 'change_rate': change_rate})
                    elif change_rate < -30:  # 30% 이상 감소
                        declining_keywords.append({'keyword': keyword, 'change_rate': change_rate})
            
            # 정렬
            emerging_keywords.sort(key=lambda x: x['change_rate'], reverse=True)
            declining_keywords.sort(key=lambda x: x['change_rate'])
            
            result = {
                'analysis_period_days': days,
                'total_keywords_tracked': len(keyword_timeline),
                'keyword_changes': keyword_changes,
                'emerging_keywords': emerging_keywords[:10],  # 상위 10개
                'declining_keywords': declining_keywords[:10],  # 하위 10개
                'stability_score': len([k for k, v in keyword_changes.items() if abs(v) < 20]) / len(keyword_changes) if keyword_changes else 0,
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Keyword] 키워드 진화 분석 오류: {str(e)}")
            return {'error': str(e)}
    
    def get_analysis_status(self) -> Dict:
        """분석기 상태 확인"""
        return {
            'nltk_available': NLTK_AVAILABLE,
            'konlpy_available': KONLPY_AVAILABLE,
            'okt_initialized': self.okt is not None,
            'music_keyword_categories': len(self.music_keywords),
            'emotion_categories': len(self.music_keywords['emotions']),
            'supported_languages': ['korean', 'english', 'mixed']
        }