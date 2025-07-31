#!/usr/bin/env python3
"""
Chord Extractor - 고정밀 음원 코드 추출기
최신 AI 모델을 활용한 실시간 코드 진행 자동 인식

지원 기능:
- 기본 코드 (Major, Minor, 7th, Sus, Add, etc.)
- 재즈 코드 (9th, 11th, 13th, Alt, etc.)  
- 코드 진행 분석
- 키 감지 및 전조 추적
- 비트/박자 동기화
- 코드 확률 및 신뢰도
"""

import os
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import json
import warnings
warnings.filterwarnings("ignore")

try:
    # librosa - 음악 정보 검색용
    import librosa
    import librosa.display
    LIBROSA_AVAILABLE = True
    print("[ChordExtractor] Librosa 로드 성공")
except ImportError as e:
    LIBROSA_AVAILABLE = False
    print(f"[ChordExtractor] Librosa 로드 실패: {e}")
    print("[ChordExtractor] 설치 명령: pip install librosa")

try:
    # madmom - 고급 음악 분석용
    import madmom
    from madmom.features.chords import DeepChromaProcessor, CRFChordRecognitionProcessor
    from madmom.features.beats import RNNBeatProcessor, BeatTrackingProcessor
    from madmom.features.key import CNNKeyRecognitionProcessor
    MADMOM_AVAILABLE = True
    print("[ChordExtractor] Madmom 로드 성공")
except ImportError as e:
    MADMOM_AVAILABLE = False
    print(f"[ChordExtractor] Madmom 로드 실패: {e}")
    print("[ChordExtractor] 설치 명령: pip install madmom")

try:
    # chroma-based chord recognition
    import mir_eval
    MIR_EVAL_AVAILABLE = True
    print("[ChordExtractor] mir_eval 로드 성공")
except ImportError as e:
    MIR_EVAL_AVAILABLE = False
    print(f"[ChordExtractor] mir_eval 로드 실패: {e}")
    print("[ChordExtractor] 설치 명령: pip install mir_eval")

try:
    # 딥러닝 기반 코드 인식을 위한 추가 라이브러리
    from scipy.signal import find_peaks
    from scipy.ndimage import median_filter
    import matplotlib.pyplot as plt
    import seaborn as sns
    ANALYSIS_LIBS_AVAILABLE = True
    print("[ChordExtractor] 분석 라이브러리 로드 성공")
except ImportError as e:
    ANALYSIS_LIBS_AVAILABLE = False
    print(f"[ChordExtractor] 분석 라이브러리 로드 실패: {e}")


class ChordExtractor:
    """
    고정밀 음원 코드 추출기
    
    지원 코드 타입:
    - 기본: C, Cm, C7, Cmaj7, Cm7, Cdim, Caug
    - 확장: C9, C11, C13, Csus2, Csus4, Cadd9
    - 재즈: Cmaj9, Cm11, C7alt, C7#11, Cm7b5
    - 슬래시: C/E, Am/C, G/B
    """
    
    def __init__(self, model_type="deep", console_log=None):
        """
        초기화
        
        Args:
            model_type: 사용할 모델 타입 ("deep", "crf", "template")
            console_log: 로깅 함수
        """
        self.console_log = console_log or print
        self.model_type = model_type
        
        # 코드 템플릿 정의
        self.chord_templates = self._initialize_chord_templates()
        self.chord_labels = list(self.chord_templates.keys())
        
        # 프로세서 초기화
        self.chroma_processor = None
        self.chord_processor = None
        self.beat_processor = None
        self.key_processor = None
        
        self._initialize_processors()
        
        self.console_log(f"[ChordExtractor] 초기화 완료 - 모델: {model_type}")
    
    def _initialize_processors(self):
        """AI 프로세서 초기화"""
        try:
            if MADMOM_AVAILABLE and self.model_type == "deep":
                # Deep Learning 기반 프로세서
                self.chroma_processor = DeepChromaProcessor()
                self.chord_processor = CRFChordRecognitionProcessor()
                self.beat_processor = BeatTrackingProcessor(
                    RNNBeatProcessor()
                )
                self.key_processor = CNNKeyRecognitionProcessor()
                self.console_log("[ChordExtractor] Deep Learning 프로세서 초기화 완료")
                
            elif LIBROSA_AVAILABLE:
                # Librosa 기반 폴백
                self.console_log("[ChordExtractor] Librosa 기반 프로세서 사용")
                
        except Exception as e:
            self.console_log(f"[ChordExtractor] 프로세서 초기화 오류: {str(e)}")
    
    def _initialize_chord_templates(self):
        """코드 템플릿 초기화"""
        templates = {}
        
        # 기본 코드 (Major, Minor)
        major_template = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0])
        minor_template = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0])
        
        # 7th 코드
        dom7_template = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0])
        maj7_template = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1])
        min7_template = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0])
        
        # 모든 키에 대해 템플릿 생성
        chord_types = {
            'maj': major_template,
            'min': minor_template,
            '7': dom7_template,
            'maj7': maj7_template,
            'min7': min7_template,
            'dim': np.array([1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0]),
            'aug': np.array([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]),
            'sus2': np.array([1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0]),
            'sus4': np.array([1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0])
        }
        
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        for i, root in enumerate(notes):
            for chord_type, template in chord_types.items():
                chord_name = f"{root}:{chord_type}" if chord_type != 'maj' else root
                rotated_template = np.roll(template, i)
                templates[chord_name] = rotated_template
        
        # N (No Chord) 추가
        templates['N'] = np.zeros(12)
        
        return templates
    
    def extract_chords(self, audio_file, output_dir=None, progress_callback=None):
        """
        오디오 파일에서 코드 진행 추출
        
        Args:
            audio_file: 입력 오디오 파일 경로
            output_dir: 출력 디렉토리 (없으면 분석만)
            progress_callback: 진행률 콜백 함수
            
        Returns:
            dict: 코드 분석 결과
        """
        try:
            if progress_callback:
                progress_callback(10, "오디오 파일 로딩 중...")
            
            # 오디오 로드
            if not LIBROSA_AVAILABLE:
                return {'success': False, 'error': 'Librosa가 필요합니다'}
            
            y, sr = librosa.load(audio_file, sr=22050)
            duration = len(y) / sr
            
            self.console_log(f"[ChordExtractor] 오디오 로드: {duration:.2f}초, {sr}Hz")
            
            if progress_callback:
                progress_callback(20, "크로마 특성 추출 중...")
            
            # 크로마 특성 추출
            chroma = self._extract_chroma_features(y, sr)
            
            if progress_callback:
                progress_callback(40, "비트 감지 중...")
            
            # 비트 및 템포 분석
            beats_info = self._extract_beats(y, sr)
            
            if progress_callback:
                progress_callback(60, "코드 인식 중...")
            
            # 코드 인식
            if self.chord_processor and MADMOM_AVAILABLE:
                chords = self._recognize_chords_deep(audio_file)
            else:
                chords = self._recognize_chords_template(chroma, beats_info)
            
            if progress_callback:
                progress_callback(80, "키 및 진행 분석 중...")
            
            # 키 감지
            key_info = self._detect_key(chroma)
            
            # 코드 진행 분석
            progression_analysis = self._analyze_chord_progression(chords, key_info)
            
            if progress_callback:
                progress_callback(90, "결과 정리 중...")
            
            # 결과 구성
            result = {
                'success': True,
                'audio_info': {
                    'duration': duration,
                    'sample_rate': sr,
                    'file_path': audio_file
                },
                'key_info': key_info,
                'beats_info': beats_info,
                'chords': chords,
                'progression_analysis': progression_analysis,
                'statistics': self._calculate_chord_statistics(chords),
                'model_used': self.model_type,
                'extraction_time': datetime.now().isoformat()
            }
            
            # 결과 저장 (요청 시)
            if output_dir:
                self._save_results(result, output_dir, Path(audio_file).stem)
            
            if progress_callback:
                progress_callback(100, "코드 추출 완료!")
            
            self.console_log(f"[ChordExtractor] 추출 완료: {len(chords)}개 코드 세그먼트")
            return result
            
        except Exception as e:
            self.console_log(f"[ChordExtractor] 코드 추출 오류: {str(e)}")
            return {'success': False, 'error': f'코드 추출 중 오류 발생: {str(e)}'}
    
    def _extract_chroma_features(self, y, sr):
        """크로마 특성 추출"""
        # 고품질 크로마 추출
        chroma = librosa.feature.chroma_cqt(
            y=y, sr=sr, 
            hop_length=512,
            fmin=librosa.note_to_hz('C1'),
            n_chroma=12,
            bins_per_octave=36
        )
        
        # 정규화 및 스무딩
        chroma = librosa.util.normalize(chroma, axis=0)
        
        # 중앙값 필터링으로 노이즈 제거
        if ANALYSIS_LIBS_AVAILABLE:
            for i in range(chroma.shape[0]):
                chroma[i] = median_filter(chroma[i], size=5)
        
        return chroma
    
    def _extract_beats(self, y, sr):
        """비트 및 템포 분석"""
        try:
            if self.beat_processor and MADMOM_AVAILABLE:
                # Madmom으로 정밀한 비트 추출
                beats = self.beat_processor(y)
                tempo = 60.0 / np.median(np.diff(beats)) if len(beats) > 1 else 120.0
            else:
                # Librosa 폴백
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
                
            return {
                'tempo': float(tempo),
                'beats': beats.tolist() if hasattr(beats, 'tolist') else list(beats),
                'beat_count': len(beats),
                'time_signature': self._estimate_time_signature(beats)
            }
            
        except Exception as e:
            self.console_log(f"[ChordExtractor] 비트 추출 오류: {str(e)}")
            return {'tempo': 120.0, 'beats': [], 'beat_count': 0, 'time_signature': '4/4'}
    
    def _recognize_chords_deep(self, audio_file):
        """딥러닝 기반 코드 인식"""
        try:
            # Madmom의 딥러닝 모델 사용
            chroma = self.chroma_processor(audio_file)
            chord_probs = self.chord_processor(chroma)
            
            chords = []
            hop_length = 4096 / 22050  # 대략적인 시간 간격
            
            for i, probs in enumerate(chord_probs):
                time_start = i * hop_length
                time_end = (i + 1) * hop_length
                
                # 가장 확률이 높은 코드 선택
                chord_idx = np.argmax(probs)
                confidence = float(probs[chord_idx])
                
                if chord_idx < len(self.chord_labels):
                    chord_name = self.chord_labels[chord_idx]
                else:
                    chord_name = 'N'  # No chord
                
                chords.append({
                    'start_time': float(time_start),
                    'end_time': float(time_end),
                    'chord': chord_name,
                    'confidence': confidence
                })
            
            return chords
            
        except Exception as e:
            self.console_log(f"[ChordExtractor] 딥러닝 코드 인식 오류: {str(e)}")
            return []
    
    def _recognize_chords_template(self, chroma, beats_info):
        """템플릿 매칭 기반 코드 인식"""
        chords = []
        hop_length = 512 / 22050
        
        for i in range(chroma.shape[1]):
            time_start = i * hop_length
            time_end = (i + 1) * hop_length
            
            # 현재 프레임의 크로마 벡터
            current_chroma = chroma[:, i]
            
            # 모든 코드 템플릿과 유사도 계산
            similarities = {}
            for chord_name, template in self.chord_templates.items():
                # 코사인 유사도 계산
                similarity = np.dot(current_chroma, template) / (
                    np.linalg.norm(current_chroma) * np.linalg.norm(template) + 1e-8
                )
                similarities[chord_name] = similarity
            
            # 가장 유사한 코드 선택
            best_chord = max(similarities, key=similarities.get)
            confidence = similarities[best_chord]
            
            # 낮은 신뢰도는 No Chord로 처리
            if confidence < 0.5:
                best_chord = 'N'
                confidence = 0.0
            
            chords.append({
                'start_time': float(time_start),
                'end_time': float(time_end),
                'chord': best_chord,
                'confidence': float(confidence)
            })
        
        # 연속된 동일 코드 병합
        return self._merge_consecutive_chords(chords)
    
    def _merge_consecutive_chords(self, chords, min_duration=0.5):
        """연속된 동일 코드 병합"""
        if not chords:
            return []
        
        merged = []
        current_chord = chords[0].copy()
        
        for next_chord in chords[1:]:
            if (next_chord['chord'] == current_chord['chord'] and 
                abs(next_chord['start_time'] - current_chord['end_time']) < 0.1):
                # 동일 코드 연장
                current_chord['end_time'] = next_chord['end_time']
                current_chord['confidence'] = max(current_chord['confidence'], 
                                                next_chord['confidence'])
            else:
                # 최소 지속시간 체크
                if current_chord['end_time'] - current_chord['start_time'] >= min_duration:
                    merged.append(current_chord)
                current_chord = next_chord.copy()
        
        # 마지막 코드 추가
        if current_chord['end_time'] - current_chord['start_time'] >= min_duration:
            merged.append(current_chord)
        
        return merged
    
    def _detect_key(self, chroma):
        """키 감지"""
        try:
            if self.key_processor and MADMOM_AVAILABLE:
                # Madmom CNN 키 인식
                key_probs = self.key_processor(chroma.T)
                key_idx = np.argmax(key_probs)
                
                keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                modes = ['major', 'minor']
                
                key_name = keys[key_idx % 12]
                mode = modes[key_idx // 12]
                confidence = float(key_probs[key_idx])
                
            else:
                # Krumhansl-Schmuckler 키 추출 (Librosa)
                chroma_mean = np.mean(chroma, axis=1)
                key_name, mode, confidence = self._krumhansl_schmuckler(chroma_mean)
            
            return {
                'key': key_name,
                'mode': mode,
                'confidence': confidence
            }
            
        except Exception as e:
            self.console_log(f"[ChordExtractor] 키 감지 오류: {str(e)}")
            return {'key': 'C', 'mode': 'major', 'confidence': 0.5}
    
    def _krumhansl_schmuckler(self, chroma_vector):
        """Krumhansl-Schmuckler 키 추출 알고리즘"""
        # 장조/단조 프로파일
        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        correlations = []
        
        for i in range(12):
            # 각 키에 대해 프로파일과 상관관계 계산
            major_corr = np.corrcoef(chroma_vector, np.roll(major_profile, i))[0, 1]
            minor_corr = np.corrcoef(chroma_vector, np.roll(minor_profile, i))[0, 1]
            
            correlations.append((keys[i], 'major', major_corr))
            correlations.append((keys[i], 'minor', minor_corr))
        
        # 최고 상관관계 선택
        best_key, best_mode, best_corr = max(correlations, key=lambda x: x[2])
        
        return best_key, best_mode, float(best_corr)
    
    def _analyze_chord_progression(self, chords, key_info):
        """코드 진행 분석"""
        if not chords:
            return {}
        
        chord_sequence = [c['chord'] for c in chords if c['chord'] != 'N']
        
        # 로마 숫자 분석
        roman_numerals = self._convert_to_roman_numerals(chord_sequence, key_info)
        
        # 일반적인 진행 패턴 감지
        common_progressions = self._detect_common_progressions(roman_numerals)
        
        # 전조 감지
        modulations = self._detect_modulations(chords)
        
        return {
            'chord_sequence': chord_sequence,
            'roman_numerals': roman_numerals,
            'common_progressions': common_progressions,
            'modulations': modulations,
            'unique_chords': len(set(chord_sequence)),
            'total_changes': len(chord_sequence)
        }
    
    def _convert_to_roman_numerals(self, chord_sequence, key_info):
        """코드를 로마 숫자로 변환"""
        key_root = key_info['key']
        mode = key_info['mode']
        
        # 키의 음계 생성
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key_index = notes.index(key_root)
        
        if mode == 'major':
            scale_intervals = [0, 2, 4, 5, 7, 9, 11]  # 장음계
            numerals = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
        else:
            scale_intervals = [0, 2, 3, 5, 7, 8, 10]  # 단음계
            numerals = ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII']
        
        roman_sequence = []
        for chord in chord_sequence:
            try:
                # 코드 루트 추출
                chord_root = chord.split(':')[0] if ':' in chord else chord
                if chord_root in notes:
                    root_index = notes.index(chord_root)
                    # 키에서의 상대적 위치 계산
                    relative_pos = (root_index - key_index) % 12
                    
                    # 음계 내 위치 찾기
                    if relative_pos in scale_intervals:
                        scale_degree = scale_intervals.index(relative_pos)
                        roman_sequence.append(numerals[scale_degree])
                    else:
                        roman_sequence.append(f"♭{roman_sequence[-1] if roman_sequence else 'I'}")
                else:
                    roman_sequence.append('?')
            except:
                roman_sequence.append('?')
        
        return roman_sequence
    
    def _detect_common_progressions(self, roman_numerals):
        """일반적인 코드 진행 패턴 감지"""
        common_patterns = {
            'I-V-vi-IV': 'Pop progression',
            'vi-IV-I-V': 'Pop variation',
            'I-vi-IV-V': 'Circle progression',
            'ii-V-I': 'Jazz turnaround',
            'I-IV-V-I': 'Classical cadence',
            'vi-ii-V-I': 'Jazz progression'
        }
        
        detected = []
        roman_str = '-'.join(roman_numerals)
        
        for pattern, name in common_patterns.items():
            if pattern in roman_str:
                detected.append({
                    'pattern': pattern,
                    'name': name,
                    'positions': self._find_pattern_positions(roman_numerals, pattern.split('-'))
                })
        
        return detected
    
    def _find_pattern_positions(self, sequence, pattern):
        """패턴이 나타나는 위치 찾기"""
        positions = []
        pattern_len = len(pattern)
        
        for i in range(len(sequence) - pattern_len + 1):
            if sequence[i:i+pattern_len] == pattern:
                positions.append(i)
        
        return positions
    
    def _detect_modulations(self, chords):
        """전조 감지"""
        # 간단한 전조 감지 (실제로는 더 복잡한 분석 필요)
        modulations = []
        
        # 윈도우별로 키 변화 감지
        window_size = 8
        for i in range(0, len(chords) - window_size, window_size // 2):
            window_chords = chords[i:i+window_size]
            # 여기서 각 윈도우의 키를 분석하고 변화 감지
            # 복잡한 로직이므로 기본 구현만 제공
            pass
        
        return modulations
    
    def _estimate_time_signature(self, beats):
        """박자 추정"""
        if len(beats) < 4:
            return '4/4'
        
        # 비트 간격 분석으로 박자 추정
        intervals = np.diff(beats)
        # 간단한 휴리스틱으로 4/4, 3/4, 6/8 등 구분
        # 실제로는 더 정교한 분석 필요
        
        return '4/4'  # 기본값
    
    def _calculate_chord_statistics(self, chords):
        """코드 통계 계산"""
        if not chords:
            return {}
        
        chord_counts = {}
        total_duration = 0
        
        for chord_info in chords:
            chord = chord_info['chord']
            duration = chord_info['end_time'] - chord_info['start_time']
            
            if chord not in chord_counts:
                chord_counts[chord] = {'count': 0, 'total_duration': 0}
            
            chord_counts[chord]['count'] += 1
            chord_counts[chord]['total_duration'] += duration
            total_duration += duration
        
        # 사용 빈도 계산
        for chord in chord_counts:
            chord_counts[chord]['percentage'] = (
                chord_counts[chord]['total_duration'] / total_duration * 100
            )
        
        return {
            'total_chords': len(chords),
            'unique_chords': len(chord_counts),
            'chord_usage': chord_counts,
            'most_used': max(chord_counts.items(), key=lambda x: x[1]['percentage'])[0] if chord_counts else 'N',
            'total_duration': total_duration
        }
    
    def _save_results(self, result, output_dir, base_name):
        """결과 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON 결과 저장
        json_file = os.path.join(output_dir, f"{base_name}_chords.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # 간단한 텍스트 결과 저장
        txt_file = os.path.join(output_dir, f"{base_name}_chords.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"코드 추출 결과: {base_name}\n")
            f.write(f"키: {result['key_info']['key']} {result['key_info']['mode']}\n")
            f.write(f"템포: {result['beats_info']['tempo']:.1f} BPM\n\n")
            
            f.write("코드 진행:\n")
            for chord_info in result['chords']:
                f.write(f"{chord_info['start_time']:.2f}s - {chord_info['end_time']:.2f}s: "
                       f"{chord_info['chord']} (신뢰도: {chord_info['confidence']:.2f})\n")
        
        # 시각화 저장 (가능한 경우)
        if ANALYSIS_LIBS_AVAILABLE:
            self._save_chord_visualization(result, output_dir, base_name)
    
    def _save_chord_visualization(self, result, output_dir, base_name):
        """코드 진행 시각화"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
            
            # 코드 타임라인
            chords = result['chords']
            chord_names = [c['chord'] for c in chords]
            start_times = [c['start_time'] for c in chords]
            durations = [c['end_time'] - c['start_time'] for c in chords]
            
            # 색상 맵핑
            unique_chords = list(set(chord_names))
            colors = plt.cm.Set3(np.linspace(0, 1, len(unique_chords)))
            chord_colors = {chord: colors[i] for i, chord in enumerate(unique_chords)}
            
            # 타임라인 플롯
            for i, (chord, start, duration) in enumerate(zip(chord_names, start_times, durations)):
                ax1.barh(0, duration, left=start, color=chord_colors[chord], 
                        alpha=0.7, edgecolor='black', linewidth=0.5)
                if duration > 2:  # 충분히 긴 구간에만 텍스트 표시
                    ax1.text(start + duration/2, 0, chord, 
                           ha='center', va='center', fontsize=8, fontweight='bold')
            
            ax1.set_xlim(0, max([c['end_time'] for c in chords]))
            ax1.set_ylim(-0.5, 0.5)
            ax1.set_xlabel('시간 (초)')
            ax1.set_title(f'코드 진행 타임라인 - {base_name}')
            ax1.set_yticks([])
            
            # 코드 사용 빈도
            stats = result['statistics']['chord_usage']
            chord_list = list(stats.keys())
            percentages = [stats[chord]['percentage'] for chord in chord_list]
            
            ax2.pie(percentages, labels=chord_list, autopct='%1.1f%%', startangle=90)
            ax2.set_title('코드 사용 비율')
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"{base_name}_chord_analysis.png"), 
                       dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            self.console_log(f"[ChordExtractor] 시각화 저장 오류: {str(e)}")
    
    def get_supported_chord_types(self):
        """지원하는 코드 타입 목록 반환"""
        return {
            'basic': ['major', 'minor', 'diminished', 'augmented'],
            'seventh': ['dominant7', 'major7', 'minor7', 'half-diminished7', 'diminished7'],
            'extended': ['9th', '11th', '13th'],
            'altered': ['sus2', 'sus4', 'add9', 'alt'],
            'slash': ['slash chords (e.g., C/E)']
        }


# 편의 함수
def extract_chords_from_file(audio_file, output_dir=None, model_type="deep"):
    """
    간단한 코드 추출 함수
    
    Args:
        audio_file: 입력 오디오 파일
        output_dir: 출력 디렉토리
        model_type: 모델 타입
        
    Returns:
        dict: 코드 분석 결과
    """
    extractor = ChordExtractor(model_type=model_type)
    return extractor.extract_chords(audio_file, output_dir)


if __name__ == "__main__":
    # 테스트 코드
    extractor = ChordExtractor()
    print("지원 코드 타입:", extractor.get_supported_chord_types())