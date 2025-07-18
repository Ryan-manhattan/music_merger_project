#!/usr/bin/env python3
"""
Comment Trend Analyzer - 댓글 중심 음악 트렌드 분석
감정분석, 토픽모델링, 키워드 추출, MCP 통합
"""

import os
import re
import json
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from collections import Counter, defaultdict
import statistics

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.decomposition import LatentDirichletAllocation
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

class CommentTrendAnalyzer:
    def __init__(self, console_log=None):
        """
        댓글 트렌드 분석기 초기화
        
        Args:
            console_log: 로그 출력 함수
        """
        self.console_log = console_log or print
        
        # 감정 분석기 초기화
        self.vader_analyzer = None
        if VADER_AVAILABLE:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                self.console_log("[Comment] VADER 감정 분석기 초기화 완료")
            except Exception as e:
                self.console_log(f"[Comment] VADER 초기화 오류: {str(e)}")
        
        # 토픽 모델링 설정
        self.topic_model = None
        self.vectorizer = None
        
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8
            )
        
        # 음악 관련 감정 키워드 확장
        self.music_sentiment_keywords = {
            'positive_intense': {
                'words': ['대박', '미쳤다', '짱', '최고', '완벽', '레전드', '명곡', '갓곡', 'masterpiece', 'amazing', 'incredible'],
                'weight': 2.0
            },
            'positive_mild': {
                'words': ['좋다', '괜찮다', '마음에들어', '듣기좋다', 'good', 'nice', 'love', 'like'],
                'weight': 1.0
            },
            'negative_intense': {
                'words': ['최악', '별로', '짜증', '실망', '망했다', 'terrible', 'awful', 'hate', 'worst'],
                'weight': -2.0
            },
            'negative_mild': {
                'words': ['아쉽다', '그저그렇다', '별로야', 'okay', 'meh', 'not bad'],
                'weight': -1.0
            },
            'excitement': {
                'words': ['신난다', '흥겹다', '춤추고싶어', '에너지', 'energetic', 'exciting', 'pump', 'hype'],
                'weight': 1.5
            },
            'calm': {
                'words': ['편안하다', '잔잔하다', '힐링', '차분하다', 'chill', 'relaxing', 'peaceful', 'soothing'],
                'weight': 0.8
            }
        }
        
        # 음악 장르 관련 키워드
        self.genre_indicators = {
            'kpop': ['아이돌', 'idol', '케이팝', 'k-pop', '한국', 'korean', '그룹'],
            'hiphop': ['랩', 'rap', '힙합', 'hip-hop', '비트', 'beat', 'flow', '라이밍'],
            'ballad': ['발라드', 'ballad', '감성', '슬프다', 'emotional', 'sad'],
            'dance': ['댄스', 'dance', '신나다', '클럽', 'club', 'party'],
            'rock': ['록', 'rock', '기타', 'guitar', '밴드', 'band'],
            'pop': ['팝', 'pop', '멜로디', 'melody', 'catchy']
        }
        
        # 트렌드 지표 키워드
        self.trend_indicators = {
            'viral': ['바이럴', 'viral', '유행', 'trending', '인기폭발'],
            'chart': ['차트', 'chart', '순위', '1위', 'number one', 'top'],
            'new_release': ['신곡', 'new song', '새로나온', 'latest', 'just released'],
            'comeback': ['컴백', 'comeback', '돌아왔다', 'return'],
            'collaboration': ['콜라보', 'collab', '피처링', 'feat', 'featuring']
        }
    
    def analyze_comment_sentiment(self, comments: List[Dict]) -> Dict:
        """
        댓글 감정 분석
        
        Args:
            comments: 댓글 리스트 [{'text': str, 'timestamp': str, 'source': str}]
            
        Returns:
            감정 분석 결과
        """
        try:
            if not comments:
                return {'error': '분석할 댓글이 없습니다'}
            
            sentiment_results = []
            emotion_distribution = defaultdict(int)
            platform_sentiment = defaultdict(list)
            
            for comment in comments:
                text = comment.get('text', '')
                source = comment.get('source', 'unknown')
                
                if not text.strip():
                    continue
                
                # 다중 감정 분석
                sentiment_scores = {}
                
                # VADER 감정 분석 (영어 중심)
                if self.vader_analyzer:
                    vader_scores = self.vader_analyzer.polarity_scores(text)
                    sentiment_scores['vader'] = {
                        'compound': vader_scores['compound'],
                        'positive': vader_scores['pos'],
                        'negative': vader_scores['neg'],
                        'neutral': vader_scores['neu']
                    }
                
                # TextBlob 감정 분석
                if TEXTBLOB_AVAILABLE:
                    try:
                        blob = TextBlob(text)
                        sentiment_scores['textblob'] = {
                            'polarity': blob.sentiment.polarity,
                            'subjectivity': blob.sentiment.subjectivity
                        }
                    except:
                        pass
                
                # 커스텀 음악 감정 분석
                music_sentiment = self._analyze_music_sentiment(text)
                sentiment_scores['music_custom'] = music_sentiment
                
                # 종합 감정 점수 계산
                final_sentiment = self._calculate_combined_sentiment(sentiment_scores)
                
                # 감정 카테고리 분류
                emotion_category = self._categorize_emotion(final_sentiment)
                emotion_distribution[emotion_category] += 1
                
                # 플랫폼별 감정 저장
                platform_sentiment[source].append(final_sentiment['score'])
                
                sentiment_results.append({
                    'text': text[:100] + '...' if len(text) > 100 else text,
                    'sentiment_scores': sentiment_scores,
                    'final_sentiment': final_sentiment,
                    'emotion_category': emotion_category,
                    'source': source,
                    'timestamp': comment.get('timestamp')
                })
            
            # 전체 통계 계산
            all_scores = [result['final_sentiment']['score'] for result in sentiment_results]
            
            # 플랫폼별 평균 감정
            platform_averages = {}
            for platform, scores in platform_sentiment.items():
                platform_averages[platform] = {
                    'average': statistics.mean(scores) if scores else 0,
                    'count': len(scores)
                }
            
            result = {
                'total_comments_analyzed': len(sentiment_results),
                'overall_sentiment': {
                    'average_score': statistics.mean(all_scores) if all_scores else 0,
                    'median_score': statistics.median(all_scores) if all_scores else 0,
                    'std_deviation': statistics.stdev(all_scores) if len(all_scores) > 1 else 0
                },
                'emotion_distribution': dict(emotion_distribution),
                'platform_sentiment': platform_averages,
                'detailed_results': sentiment_results[:20],  # 상위 20개만 저장
                'sentiment_trend': self._calculate_sentiment_trend(sentiment_results),
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Comment] 댓글 감정 분석 오류: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_music_sentiment(self, text: str) -> Dict:
        """음악 관련 커스텀 감정 분석"""
        text_lower = text.lower()
        sentiment_score = 0
        matched_categories = []
        
        for category, data in self.music_sentiment_keywords.items():
            matches = 0
            for keyword in data['words']:
                if keyword.lower() in text_lower:
                    matches += text_lower.count(keyword.lower())
            
            if matches > 0:
                sentiment_score += matches * data['weight']
                matched_categories.append(category)
        
        # 정규화 (-1 ~ 1)
        normalized_score = max(-1, min(1, sentiment_score / 5))
        
        return {
            'score': normalized_score,
            'matched_categories': matched_categories,
            'confidence': min(1.0, abs(sentiment_score) / 2)
        }
    
    def _calculate_combined_sentiment(self, sentiment_scores: Dict) -> Dict:
        """여러 감정 분석 결과 종합"""
        scores = []
        weights = {'vader': 0.3, 'textblob': 0.3, 'music_custom': 0.4}
        
        final_score = 0
        total_weight = 0
        
        # VADER 점수
        if 'vader' in sentiment_scores:
            vader_score = sentiment_scores['vader']['compound']
            final_score += vader_score * weights['vader']
            total_weight += weights['vader']
        
        # TextBlob 점수
        if 'textblob' in sentiment_scores:
            textblob_score = sentiment_scores['textblob']['polarity']
            final_score += textblob_score * weights['textblob']
            total_weight += weights['textblob']
        
        # 음악 커스텀 점수
        if 'music_custom' in sentiment_scores:
            music_score = sentiment_scores['music_custom']['score']
            final_score += music_score * weights['music_custom']
            total_weight += weights['music_custom']
        
        # 가중 평균
        if total_weight > 0:
            final_score = final_score / total_weight
        
        # 신뢰도 계산
        confidence = total_weight / sum(weights.values())
        
        return {
            'score': final_score,
            'confidence': confidence,
            'label': 'positive' if final_score > 0.1 else 'negative' if final_score < -0.1 else 'neutral'
        }
    
    def _categorize_emotion(self, sentiment: Dict) -> str:
        """감정을 세부 카테고리로 분류"""
        score = sentiment['score']
        
        if score > 0.5:
            return 'very_positive'
        elif score > 0.1:
            return 'positive'
        elif score > -0.1:
            return 'neutral'
        elif score > -0.5:
            return 'negative'
        else:
            return 'very_negative'
    
    def _calculate_sentiment_trend(self, sentiment_results: List[Dict]) -> Dict:
        """감정 변화 트렌드 계산"""
        if len(sentiment_results) < 5:
            return {'trend': 'insufficient_data'}
        
        # 시간순 정렬 (timestamp가 있는 경우)
        sorted_results = sorted(
            [r for r in sentiment_results if r.get('timestamp')],
            key=lambda x: x['timestamp']
        )
        
        if len(sorted_results) < 5:
            # timestamp가 없으면 순서대로 분석
            sorted_results = sentiment_results
        
        # 초기 vs 최근 비교
        first_half = sorted_results[:len(sorted_results)//2]
        second_half = sorted_results[len(sorted_results)//2:]
        
        first_avg = statistics.mean([r['final_sentiment']['score'] for r in first_half])
        second_avg = statistics.mean([r['final_sentiment']['score'] for r in second_half])
        
        change = second_avg - first_avg
        
        if change > 0.1:
            trend = 'improving'
        elif change < -0.1:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_magnitude': change,
            'early_sentiment': first_avg,
            'recent_sentiment': second_avg
        }
    
    def extract_comment_topics(self, comments: List[str], num_topics: int = 5) -> Dict:
        """
        댓글에서 토픽 추출 (LDA 모델링)
        
        Args:
            comments: 댓글 텍스트 리스트
            num_topics: 추출할 토픽 수
            
        Returns:
            토픽 모델링 결과
        """
        try:
            if not SKLEARN_AVAILABLE:
                return {'error': 'scikit-learn이 설치되지 않았습니다'}
            
            if len(comments) < 10:
                return {'error': '토픽 분석을 위해 최소 10개 이상의 댓글이 필요합니다'}
            
            # 텍스트 전처리
            processed_comments = []
            for comment in comments:
                # 기본 전처리
                clean_text = re.sub(r'[^\w\s]', ' ', comment.lower())
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                if len(clean_text) > 10:  # 너무 짧은 댓글 제외
                    processed_comments.append(clean_text)
            
            if len(processed_comments) < 5:
                return {'error': '분석 가능한 댓글이 부족합니다'}
            
            # TF-IDF 벡터화
            try:
                tfidf_matrix = self.vectorizer.fit_transform(processed_comments)
                feature_names = self.vectorizer.get_feature_names_out()
            except Exception as e:
                return {'error': f'벡터화 오류: {str(e)}'}
            
            # LDA 토픽 모델링
            lda_model = LatentDirichletAllocation(
                n_components=min(num_topics, len(processed_comments)//2),
                random_state=42,
                max_iter=10
            )
            
            try:
                lda_model.fit(tfidf_matrix)
            except Exception as e:
                return {'error': f'LDA 모델링 오류: {str(e)}'}
            
            # 토픽별 키워드 추출
            topics = []
            for topic_idx, topic in enumerate(lda_model.components_):
                # 상위 키워드 추출
                top_keywords_idx = topic.argsort()[-10:][::-1]
                top_keywords = [feature_names[i] for i in top_keywords_idx]
                topic_weights = [topic[i] for i in top_keywords_idx]
                
                # 토픽 라벨 생성
                topic_label = self._generate_topic_label(top_keywords)
                
                topics.append({
                    'topic_id': topic_idx,
                    'label': topic_label,
                    'keywords': top_keywords,
                    'weights': topic_weights,
                    'music_relevance': self._calculate_music_relevance(top_keywords)
                })
            
            # 댓글별 토픽 분포
            doc_topic_dist = lda_model.transform(tfidf_matrix)
            
            # 토픽별 댓글 수 계산
            topic_comment_counts = defaultdict(int)
            for doc_topics in doc_topic_dist:
                dominant_topic = doc_topics.argmax()
                topic_comment_counts[dominant_topic] += 1
            
            result = {
                'num_topics_found': len(topics),
                'topics': topics,
                'topic_distribution': dict(topic_comment_counts),
                'total_comments_analyzed': len(processed_comments),
                'model_perplexity': lda_model.perplexity(tfidf_matrix),
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Comment] 토픽 추출 오류: {str(e)}")
            return {'error': str(e)}
    
    def _generate_topic_label(self, keywords: List[str]) -> str:
        """키워드 기반 토픽 라벨 생성"""
        # 음악 관련 키워드 우선 검사
        for genre, indicators in self.genre_indicators.items():
            for indicator in indicators:
                if any(indicator.lower() in keyword.lower() for keyword in keywords[:3]):
                    return f"음악_{genre}"
        
        # 트렌드 관련 키워드 검사
        for trend_type, indicators in self.trend_indicators.items():
            for indicator in indicators:
                if any(indicator.lower() in keyword.lower() for keyword in keywords[:3]):
                    return f"트렌드_{trend_type}"
        
        # 일반 라벨 (상위 2개 키워드 조합)
        return f"{keywords[0]}_{keywords[1]}" if len(keywords) >= 2 else keywords[0]
    
    def _calculate_music_relevance(self, keywords: List[str]) -> float:
        """키워드의 음악 관련성 점수 계산"""
        music_related_count = 0
        
        # 모든 음악 관련 키워드와 비교
        all_music_keywords = []
        for genre_keywords in self.genre_indicators.values():
            all_music_keywords.extend(genre_keywords)
        for trend_keywords in self.trend_indicators.values():
            all_music_keywords.extend(trend_keywords)
        
        for keyword in keywords[:5]:  # 상위 5개 키워드만 검사
            for music_keyword in all_music_keywords:
                if music_keyword.lower() in keyword.lower():
                    music_related_count += 1
                    break
        
        return music_related_count / min(len(keywords), 5)
    
    def analyze_comment_patterns(self, comments: List[Dict]) -> Dict:
        """
        댓글 패턴 분석
        
        Args:
            comments: 댓글 데이터 리스트
            
        Returns:
            댓글 패턴 분석 결과
        """
        try:
            if not comments:
                return {'error': '분석할 댓글이 없습니다'}
            
            # 기본 통계
            comment_lengths = [len(comment.get('text', '')) for comment in comments]
            word_counts = [len(comment.get('text', '').split()) for comment in comments]
            
            # 시간 패턴 분석
            time_patterns = self._analyze_time_patterns(comments)
            
            # 언어 패턴 분석
            language_patterns = self._analyze_language_patterns(comments)
            
            # 참여도 패턴 분석
            engagement_patterns = self._analyze_engagement_patterns(comments)
            
            # 이모지/이모티콘 분석
            emoji_patterns = self._analyze_emoji_patterns(comments)
            
            result = {
                'basic_statistics': {
                    'total_comments': len(comments),
                    'avg_comment_length': statistics.mean(comment_lengths) if comment_lengths else 0,
                    'avg_word_count': statistics.mean(word_counts) if word_counts else 0,
                    'max_comment_length': max(comment_lengths) if comment_lengths else 0,
                    'min_comment_length': min(comment_lengths) if comment_lengths else 0
                },
                'time_patterns': time_patterns,
                'language_patterns': language_patterns,
                'engagement_patterns': engagement_patterns,
                'emoji_patterns': emoji_patterns,
                'analyzed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.console_log(f"[Comment] 댓글 패턴 분석 오류: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_time_patterns(self, comments: List[Dict]) -> Dict:
        """댓글 시간 패턴 분석"""
        timestamps = []
        for comment in comments:
            timestamp = comment.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    timestamps.append(dt)
                except:
                    continue
        
        if not timestamps:
            return {'error': '시간 정보가 없습니다'}
        
        # 시간대별 분포
        hour_distribution = defaultdict(int)
        day_distribution = defaultdict(int)
        
        for ts in timestamps:
            hour_distribution[ts.hour] += 1
            day_distribution[ts.strftime('%A')] += 1
        
        # 피크 시간 찾기
        peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else None
        peak_day = max(day_distribution.items(), key=lambda x: x[1])[0] if day_distribution else None
        
        return {
            'hour_distribution': dict(hour_distribution),
            'day_distribution': dict(day_distribution),
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'total_timespan_hours': (max(timestamps) - min(timestamps)).total_seconds() / 3600 if len(timestamps) > 1 else 0
        }
    
    def _analyze_language_patterns(self, comments: List[Dict]) -> Dict:
        """언어 패턴 분석"""
        korean_count = 0
        english_count = 0
        mixed_count = 0
        emoji_count = 0
        
        for comment in comments:
            text = comment.get('text', '')
            
            korean_chars = len(re.findall(r'[가-힣]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            emoji_chars = len(re.findall(r'[😀-🙏]', text))
            
            if emoji_chars > 0:
                emoji_count += 1
            
            if korean_chars > english_chars * 2:
                korean_count += 1
            elif english_chars > korean_chars * 2:
                english_count += 1
            else:
                mixed_count += 1
        
        total = len(comments)
        return {
            'korean_dominant': korean_count,
            'english_dominant': english_count,
            'mixed_language': mixed_count,
            'emoji_usage': emoji_count,
            'korean_percentage': (korean_count / total * 100) if total > 0 else 0,
            'english_percentage': (english_count / total * 100) if total > 0 else 0,
            'emoji_percentage': (emoji_count / total * 100) if total > 0 else 0
        }
    
    def _analyze_engagement_patterns(self, comments: List[Dict]) -> Dict:
        """참여도 패턴 분석"""
        scores = [comment.get('score', 0) for comment in comments if 'score' in comment]
        reply_counts = [comment.get('reply_count', 0) for comment in comments if 'reply_count' in comment]
        
        if not scores and not reply_counts:
            return {'error': '참여도 데이터가 없습니다'}
        
        result = {}
        
        if scores:
            result['score_stats'] = {
                'avg_score': statistics.mean(scores),
                'max_score': max(scores),
                'min_score': min(scores),
                'high_score_comments': len([s for s in scores if s > 10])
            }
        
        if reply_counts:
            result['reply_stats'] = {
                'avg_replies': statistics.mean(reply_counts),
                'max_replies': max(reply_counts),
                'comments_with_replies': len([r for r in reply_counts if r > 0])
            }
        
        return result
    
    def _analyze_emoji_patterns(self, comments: List[Dict]) -> Dict:
        """이모지/이모티콘 패턴 분석"""
        emoji_counter = Counter()
        emoticon_counter = Counter()
        
        # 이모티콘 패턴 (간단한)
        emoticon_patterns = [
            r':-?\)', r':-?\(', r':-?D', r':-?P', r':-?o', r':-?\|',
            r':\)', r':\(', r':D', r':P', r':o', r':\|',
            r'\^_\^', r'T_T', r'ㅠㅠ', r'ㅋㅋ', r'ㅎㅎ'
        ]
        
        for comment in comments:
            text = comment.get('text', '')
            
            # 이모지 카운트
            emojis = re.findall(r'[😀-🙏]', text)
            for emoji in emojis:
                emoji_counter[emoji] += 1
            
            # 이모티콘 카운트
            for pattern in emoticon_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    emoticon_counter[match] += 1
        
        return {
            'top_emojis': dict(emoji_counter.most_common(10)),
            'top_emoticons': dict(emoticon_counter.most_common(10)),
            'total_emoji_usage': sum(emoji_counter.values()),
            'total_emoticon_usage': sum(emoticon_counter.values()),
            'emoji_diversity': len(emoji_counter),
            'emoticon_diversity': len(emoticon_counter)
        }
    
    def get_analysis_status(self) -> Dict:
        """분석기 상태 확인"""
        return {
            'sklearn_available': SKLEARN_AVAILABLE,
            'textblob_available': TEXTBLOB_AVAILABLE,
            'vader_available': VADER_AVAILABLE,
            'vader_initialized': self.vader_analyzer is not None,
            'vectorizer_ready': self.vectorizer is not None,
            'sentiment_categories': len(self.music_sentiment_keywords),
            'genre_indicators': len(self.genre_indicators),
            'trend_indicators': len(self.trend_indicators)
        }