#!/usr/bin/env python3
"""
MIDI Generator - 고정밀 오디오→MIDI 변환기
최신 AI 모델을 활용한 다중 악기 MIDI 생성

지원 기능:
- 멜로디 추출 및 MIDI 변환
- 다중 악기 분리 및 개별 MIDI 트랙 생성
- 리듬/드럼 패턴 MIDI 변환
- 화성 진행 MIDI 변환
- 타이밍 및 벨로시티 정보 보존
- General MIDI 호환 출력
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
    # 기본 MIDI 처리
    import mido
    from mido import MidiFile, MidiTrack, Message
    MIDO_AVAILABLE = True
    print("[MidiGenerator] mido 로드 성공")
except ImportError as e:
    MIDO_AVAILABLE = False
    print(f"[MidiGenerator] mido 로드 실패: {e}")
    print("[MidiGenerator] 설치 명령: pip install mido")

try:
    # 고급 MIDI 생성을 위한 pretty_midi
    import pretty_midi
    PRETTY_MIDI_AVAILABLE = True
    print("[MidiGenerator] pretty_midi 로드 성공")
except ImportError as e:
    PRETTY_MIDI_AVAILABLE = False
    print(f"[MidiGenerator] pretty_midi 로드 실패: {e}")
    print("[MidiGenerator] 설치 명령: pip install pretty_midi")

try:
    # 오디오 분석용
    import librosa
    import librosa.display
    LIBROSA_AVAILABLE = True
    print("[MidiGenerator] librosa 로드 성공")
except ImportError as e:
    LIBROSA_AVAILABLE = False
    print(f"[MidiGenerator] librosa 로드 실패: {e}")

try:
    # 최신 AI 기반 transcription을 위한 basic-pitch
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    BASIC_PITCH_AVAILABLE = True
    print("[MidiGenerator] basic-pitch 로드 성공")
except ImportError as e:
    BASIC_PITCH_AVAILABLE = False
    print(f"[MidiGenerator] basic-pitch 로드 실패: {e}")
    print("[MidiGenerator] 설치 명령: pip install basic-pitch")

try:
    # 피아노 전사를 위한 추가 라이브러리
    from scipy.signal import find_peaks
    from scipy.ndimage import gaussian_filter1d
    import matplotlib.pyplot as plt
    ANALYSIS_LIBS_AVAILABLE = True
    print("[MidiGenerator] 분석 라이브러리 로드 성공")
except ImportError as e:
    ANALYSIS_LIBS_AVAILABLE = False
    print(f"[MidiGenerator] 분석 라이브러리 로드 실패: {e}")


class MidiGenerator:
    """
    고정밀 오디오→MIDI 변환기
    
    지원 변환 타입:
    - melody: 멜로디 라인 추출
    - harmony: 화음 진행 추출  
    - rhythm: 리듬/드럼 패턴 추출
    - full: 전체 다중 트랙 분석
    - piano: 피아노 전용 고정밀 전사
    """
    
    def __init__(self, model_type="basic_pitch", console_log=None):
        """
        초기화
        
        Args:
            model_type: 사용할 모델 타입 ("basic_pitch", "librosa", "hybrid")
            console_log: 로깅 함수
        """
        self.console_log = console_log or print
        self.model_type = model_type
        
        # MIDI 설정
        self.sample_rate = 22050
        self.hop_length = 512
        self.frame_length = 2048
        
        # General MIDI 악기 맵핑
        self.instruments = {
            'piano': 0,
            'guitar': 24,
            'bass': 32,
            'strings': 40,
            'trumpet': 56,
            'saxophone': 64,
            'flute': 73,
            'violin': 40,
            'drums': 128  # Percussion
        }
        
        # 음표 지속시간 (4분음표 기준)
        self.note_durations = {
            'whole': 4.0,
            'half': 2.0,
            'quarter': 1.0,
            'eighth': 0.5,
            'sixteenth': 0.25,
            'thirty_second': 0.125
        }
        
        self.console_log(f"[MidiGenerator] 초기화 완료 - 모델: {model_type}")
    
    def generate_midi(self, audio_file, output_dir, conversion_type="full", progress_callback=None):
        """
        오디오 파일을 MIDI로 변환
        
        Args:
            audio_file: 입력 오디오 파일 경로
            output_dir: 출력 디렉토리
            conversion_type: 변환 타입 ("melody", "harmony", "rhythm", "full", "piano")
            progress_callback: 진행률 콜백 함수
            
        Returns:
            dict: MIDI 생성 결과  
        """
        try:
            if not LIBROSA_AVAILABLE:
                return {'success': False, 'error': 'librosa가 필요합니다'}
            
            if progress_callback:
                progress_callback(10, "오디오 파일 로딩 중...")
            
            # 오디오 로드
            y, sr = librosa.load(audio_file, sr=self.sample_rate)
            duration = len(y) / sr
            
            self.console_log(f"[MidiGenerator] 오디오 로드: {duration:.2f}초, {sr}Hz")
            
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            base_name = Path(audio_file).stem
            
            if progress_callback:
                progress_callback(20, "오디오 분석 중...")
            
            # 변환 타입에 따른 처리
            if conversion_type == "melody":
                result = self._generate_melody_midi(y, sr, output_dir, base_name, progress_callback)
            elif conversion_type == "harmony":
                result = self._generate_harmony_midi(y, sr, output_dir, base_name, progress_callback)
            elif conversion_type == "rhythm":
                result = self._generate_rhythm_midi(y, sr, output_dir, base_name, progress_callback)
            elif conversion_type == "piano":
                result = self._generate_piano_midi(audio_file, output_dir, base_name, progress_callback)
            else:  # full
                result = self._generate_full_midi(audio_file, y, sr, output_dir, base_name, progress_callback)
            
            if progress_callback:
                progress_callback(90, "메타데이터 생성 중...")
            
            # 결과 메타데이터 추가
            result.update({
                'audio_info': {
                    'duration': duration,
                    'sample_rate': sr,
                    'file_path': audio_file
                },
                'conversion_type': conversion_type,
                'model_used': self.model_type,
                'generation_time': datetime.now().isoformat()
            })
            
            # 메타데이터 저장
            meta_file = os.path.join(output_dir, f"{base_name}_midi_info.json")
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            if progress_callback:
                progress_callback(100, "MIDI 생성 완료!")
            
            self.console_log(f"[MidiGenerator] MIDI 생성 완료: {conversion_type}")
            return result
            
        except Exception as e:
            self.console_log(f"[MidiGenerator] MIDI 생성 오류: {str(e)}")
            return {'success': False, 'error': f'MIDI 생성 중 오류 발생: {str(e)}'}
    
    def _generate_melody_midi(self, y, sr, output_dir, base_name, progress_callback=None):
        """멜로디 라인 MIDI 생성"""
        try:
            if progress_callback:
                progress_callback(30, "멜로디 추출 중...")
            
            # 피치 추출
            pitches, magnitudes = librosa.piptrack(
                y=y, sr=sr, 
                hop_length=self.hop_length,
                fmin=80, fmax=2000,
                threshold=0.1
            )
            
            # 시간 축 계산
            times = librosa.frames_to_time(
                np.arange(pitches.shape[1]), 
                sr=sr, hop_length=self.hop_length
            )
            
            if progress_callback:
                progress_callback(50, "멜로디 정리 중...")
            
            # 멜로디 라인 추출
            melody_notes = self._extract_melody_line(pitches, magnitudes, times)
            
            if progress_callback:
                progress_callback(70, "MIDI 파일 생성 중...")
            
            # MIDI 파일 생성
            midi_file = self._create_midi_from_notes(melody_notes, base_name + "_melody")
            
            # 저장
            output_path = os.path.join(output_dir, f"{base_name}_melody.mid")
            midi_file.save(output_path)
            
            return {
                'success': True,
                'melody_file': output_path,
                'note_count': len(melody_notes),
                'notes': melody_notes
            }
            
        except Exception as e:
            self.console_log(f"[MidiGenerator] 멜로디 생성 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_harmony_midi(self, y, sr, output_dir, base_name, progress_callback=None):
        """화성 진행 MIDI 생성"""
        try:
            if progress_callback:
                progress_callback(30, "화성 분석 중...")
            
            # 크로마 특성 추출
            chroma = librosa.feature.chroma_cqt(
                y=y, sr=sr,
                hop_length=self.hop_length,
                fmin=librosa.note_to_hz('C1')
            )
            
            # 시간 축
            times = librosa.frames_to_time(
                np.arange(chroma.shape[1]),
                sr=sr, hop_length=self.hop_length
            )
            
            if progress_callback:
                progress_callback(50, "코드 추출 중...")
            
            # 코드 진행 추출
            chord_progression = self._extract_chord_progression(chroma, times)
            
            if progress_callback:
                progress_callback(70, "화성 MIDI 생성 중...")
            
            # 화성 MIDI 생성
            harmony_midi = self._create_harmony_midi(chord_progression, base_name + "_harmony")
            
            # 저장
            output_path = os.path.join(output_dir, f"{base_name}_harmony.mid")
            harmony_midi.save(output_path)
            
            return {
                'success': True,
                'harmony_file': output_path,
                'chord_count': len(chord_progression),
                'chords': chord_progression
            }
            
        except Exception as e:
            self.console_log(f"[MidiGenerator] 화성 생성 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_rhythm_midi(self, y, sr, output_dir, base_name, progress_callback=None):
        """리듬 패턴 MIDI 생성"""
        try:
            if progress_callback:
                progress_callback(30, "리듬 분석 중...")
            
            # 비트 추출
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
            
            # 온셋 검출
            onset_frames = librosa.onset.onset_detect(
                y=y, sr=sr,
                hop_length=self.hop_length,
                backtrack=True
            )
            onsets = librosa.frames_to_time(onset_frames, sr=sr, hop_length=self.hop_length)
            
            if progress_callback:
                progress_callback(50, "드럼 패턴 추출 중...")
            
            # 드럼 패턴 분석
            drum_pattern = self._extract_drum_pattern(y, sr, beats, onsets)
            
            if progress_callback:
                progress_callback(70, "리듬 MIDI 생성 중...")
            
            # 리듬 MIDI 생성
            rhythm_midi = self._create_rhythm_midi(drum_pattern, tempo, base_name + "_rhythm")
            
            # 저장
            output_path = os.path.join(output_dir, f"{base_name}_rhythm.mid")
            rhythm_midi.save(output_path)
            
            return {
                'success': True,
                'rhythm_file': output_path,
                'tempo': float(tempo),
                'beat_count': len(beats),
                'pattern': drum_pattern
            }
            
        except Exception as e:
            self.console_log(f"[MidiGenerator] 리듬 생성 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_piano_midi(self, audio_file, output_dir, base_name, progress_callback=None):
        """피아노 전용 고정밀 MIDI 생성"""
        try:
            if BASIC_PITCH_AVAILABLE:
                if progress_callback:
                    progress_callback(30, "AI 모델로 피아노 전사 중...")
                
                # Basic Pitch로 고정밀 전사
                model_output, midi_data, note_events = predict(audio_file)
                
                if progress_callback:
                    progress_callback(70, "MIDI 파일 정리 중...")
                
                # 결과 저장
                output_path = os.path.join(output_dir, f"{base_name}_piano.mid")
                midi_data.write(output_path)
                
                # 통계 정보 계산
                note_count = len(note_events) if note_events is not None else 0
                
                return {
                    'success': True,
                    'piano_file': output_path,
                    'note_count': note_count,
                    'model_used': 'basic_pitch'
                }
            else:
                # Librosa 폴백
                return self._generate_piano_midi_fallback(audio_file, output_dir, base_name, progress_callback)
                
        except Exception as e:
            self.console_log(f"[MidiGenerator] 피아노 전사 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_piano_midi_fallback(self, audio_file, output_dir, base_name, progress_callback=None):
        """피아노 MIDI 생성 폴백 (librosa 사용)"""
        try:
            y, sr = librosa.load(audio_file, sr=self.sample_rate)
            
            if progress_callback:
                progress_callback(40, "CQT 스펙트로그램 분석 중...")
            
            # 고해상도 CQT로 피아노 분석
            cqt = librosa.cqt(
                y=y, sr=sr,
                hop_length=self.hop_length,
                fmin=librosa.note_to_hz('C1'),
                n_bins=84,  # 7 옥타브
                bins_per_octave=12
            )
            
            if progress_callback:
                progress_callback(60, "음표 추출 중...")
            
            # 음표 추출
            piano_notes = self._extract_piano_notes_from_cqt(cqt, sr)
            
            if progress_callback:
                progress_callback(80, "피아노 MIDI 생성 중...")
            
            # MIDI 생성
            midi_file = self._create_piano_midi(piano_notes, base_name + "_piano")
            
            # 저장
            output_path = os.path.join(output_dir, f"{base_name}_piano_fallback.mid")
            midi_file.save(output_path)
            
            return {
                'success': True,
                'piano_file': output_path,
                'note_count': len(piano_notes),
                'model_used': 'librosa_cqt'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_full_midi(self, audio_file, y, sr, output_dir, base_name, progress_callback=None):
        """전체 다중 트랙 MIDI 생성"""
        try:
            results = {}
            
            # 1. 멜로디 트랙
            if progress_callback:
                progress_callback(20, "멜로디 트랙 생성 중...")
            melody_result = self._generate_melody_midi(y, sr, output_dir, base_name)
            results['melody'] = melody_result
            
            # 2. 화성 트랙  
            if progress_callback:
                progress_callback(40, "화성 트랙 생성 중...")
            harmony_result = self._generate_harmony_midi(y, sr, output_dir, base_name)
            results['harmony'] = harmony_result
            
            # 3. 리듬 트랙
            if progress_callback:
                progress_callback(60, "리듬 트랙 생성 중...")
            rhythm_result = self._generate_rhythm_midi(y, sr, output_dir, base_name)
            results['rhythm'] = rhythm_result
            
            # 4. 통합 MIDI 생성
            if progress_callback:
                progress_callback(80, "통합 MIDI 생성 중...")
            
            combined_midi = self._create_combined_midi(results, base_name + "_full")
            output_path = os.path.join(output_dir, f"{base_name}_full.mid")
            combined_midi.save(output_path)
            
            results['combined'] = {
                'success': True,
                'full_file': output_path,
                'tracks': ['melody', 'harmony', 'rhythm']
            }
            
            return results
            
        except Exception as e:
            self.console_log(f"[MidiGenerator] 전체 MIDI 생성 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_melody_line(self, pitches, magnitudes, times):
        """멜로디 라인 추출"""
        melody_notes = []
        
        for i in range(pitches.shape[1]):
            # 각 시간 프레임에서 가장 강한 피치 선택
            frame_pitches = pitches[:, i]
            frame_magnitudes = magnitudes[:, i]
            
            if np.max(frame_magnitudes) > 0.1:  # 임계값
                max_idx = np.argmax(frame_magnitudes)
                pitch_hz = frame_pitches[max_idx]
                
                if pitch_hz > 0:
                    midi_note = librosa.hz_to_midi(pitch_hz)
                    
                    melody_notes.append({
                        'start_time': float(times[i]),
                        'pitch': float(pitch_hz),
                        'midi_note': int(np.round(midi_note)),
                        'velocity': int(np.clip(frame_magnitudes[max_idx] * 127, 1, 127))
                    })
        
        # 연속된 같은 음표 병합
        return self._merge_consecutive_notes(melody_notes)
    
    def _merge_consecutive_notes(self, notes, min_duration=0.1):
        """연속된 같은 음표 병합"""
        if not notes:
            return []
        
        merged = []
        current_note = notes[0].copy()
        current_note['duration'] = min_duration
        
        for next_note in notes[1:]:
            if (next_note['midi_note'] == current_note['midi_note'] and
                abs(next_note['start_time'] - current_note['start_time'] - current_note['duration']) < 0.05):
                # 같은 음표 연장
                current_note['duration'] = next_note['start_time'] - current_note['start_time'] + min_duration
            else:
                # 다른 음표
                if current_note['duration'] >= min_duration:
                    merged.append(current_note)
                current_note = next_note.copy()
                current_note['duration'] = min_duration
        
        # 마지막 음표 추가
        if current_note['duration'] >= min_duration:
            merged.append(current_note)
        
        return merged
    
    def _extract_chord_progression(self, chroma, times):
        """크로마에서 코드 진행 추출"""
        chord_progression = []
        
        # 간단한 코드 템플릿
        chord_templates = {
            'C': np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]),
            'Dm': np.array([0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0]),
            'Em': np.array([0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1]),
            'F': np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0]),
            'G': np.array([0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1]),
            'Am': np.array([1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0]),
        }
        
        # 윈도우 단위로 코드 분석
        window_size = 8  # 프레임 수
        for i in range(0, chroma.shape[1] - window_size, window_size // 2):
            window_chroma = np.mean(chroma[:, i:i+window_size], axis=1)
            
            # 템플릿 매칭
            best_chord = 'N'
            best_score = 0
            
            for chord_name, template in chord_templates.items():
                score = np.dot(window_chroma, template)
                if score > best_score:
                    best_score = score
                    best_chord = chord_name
            
            if best_score > 0.5:  # 임계값
                chord_progression.append({
                    'start_time': float(times[i]),
                    'end_time': float(times[min(i + window_size, len(times) - 1)]),
                    'chord': best_chord,
                    'confidence': float(best_score)
                })
        
        return chord_progression
    
    def _extract_drum_pattern(self, y, sr, beats, onsets):
        """드럼 패턴 추출"""
        # 주파수 대역별 분석으로 드럼 소리 분류
        # 킥: 20-60Hz, 스네어: 150-250Hz, 하이햇: 5-10kHz
        
        drum_events = []
        
        # 간단한 온셋 기반 드럼 이벤트 생성
        for onset_time in onsets:
            # 가장 가까운 비트에 맞춤
            closest_beat_idx = np.argmin(np.abs(beats - onset_time))
            beat_time = beats[closest_beat_idx]
            
            if abs(onset_time - beat_time) < 0.1:  # 비트에 가까우면
                drum_events.append({
                    'time': float(onset_time),
                    'type': 'kick',  # 실제로는 주파수 분석으로 구분
                    'velocity': 80
                })
        
        return drum_events
    
    def _extract_piano_notes_from_cqt(self, cqt, sr):
        """CQT에서 피아노 음표 추출"""
        # CQT 매그니튜드
        cqt_mag = np.abs(cqt)
        
        # 각 음표별 피크 찾기
        piano_notes = []
        
        for note_idx in range(cqt_mag.shape[0]):
            note_signal = cqt_mag[note_idx]
            
            # 피크 찾기
            if ANALYSIS_LIBS_AVAILABLE:
                peaks, properties = find_peaks(
                    note_signal,
                    height=np.max(note_signal) * 0.3,
                    distance=int(sr / self.hop_length * 0.1)  # 최소 100ms 간격
                )
                
                for peak in peaks:
                    time = librosa.frames_to_time(peak, sr=sr, hop_length=self.hop_length)
                    midi_note = 24 + note_idx  # C1부터 시작
                    velocity = int(np.clip(note_signal[peak] * 127, 1, 127))
                    
                    piano_notes.append({
                        'start_time': float(time),
                        'midi_note': midi_note,
                        'velocity': velocity,
                        'duration': 0.5  # 기본 지속시간
                    })
        
        return sorted(piano_notes, key=lambda x: x['start_time'])
    
    def _create_midi_from_notes(self, notes, track_name="Melody"):
        """음표 리스트에서 MIDI 파일 생성"""
        if not MIDO_AVAILABLE:
            raise ImportError("mido가 필요합니다")
        
        midi_file = MidiFile()
        track = MidiTrack()
        midi_file.tracks.append(track)
        
        # 트랙 이름 설정
        track.append(Message('track_name', name=track_name, time=0))
        
        # 악기 설정 (피아노)
        track.append(Message('program_change', program=0, time=0))
        
        # 음표들을 시간 순으로 정렬
        sorted_notes = sorted(notes, key=lambda x: x['start_time'])
        
        current_time = 0
        for note in sorted_notes:
            # 음표 시작 시간까지의 델타 시간
            note_start_ticks = int(note['start_time'] * 480)  # 480 ticks per quarter note
            delta_time = note_start_ticks - current_time
            
            # Note On
            track.append(Message(
                'note_on',
                channel=0,
                note=note['midi_note'],
                velocity=note['velocity'],
                time=delta_time
            ))
            
            # Note Off
            note_duration_ticks = int(note.get('duration', 0.5) * 480)
            track.append(Message(
                'note_off',
                channel=0,
                note=note['midi_note'],
                velocity=0,
                time=note_duration_ticks
            ))
            
            current_time = note_start_ticks + note_duration_ticks
        
        return midi_file
    
    def _create_harmony_midi(self, chord_progression, track_name="Harmony"):
        """코드 진행에서 화성 MIDI 생성"""
        if not MIDO_AVAILABLE:
            raise ImportError("mido가 필요합니다")
        
        midi_file = MidiFile()
        track = MidiTrack()
        midi_file.tracks.append(track)
        
        track.append(Message('track_name', name=track_name, time=0))
        track.append(Message('program_change', program=0, time=0))  # 피아노
        
        # 코드를 MIDI 노트로 변환
        chord_notes = {
            'C': [60, 64, 67],      # C E G
            'Dm': [62, 65, 69],     # D F A
            'Em': [64, 67, 71],     # E G B
            'F': [65, 69, 72],      # F A C
            'G': [67, 71, 74],      # G B D
            'Am': [57, 60, 64],     # A C E
        }
        
        current_time = 0
        for chord_info in chord_progression:
            chord_name = chord_info['chord']
            start_time = int(chord_info['start_time'] * 480)
            duration = int((chord_info['end_time'] - chord_info['start_time']) * 480)
            
            delta_time = start_time - current_time
            
            if chord_name in chord_notes:
                notes = chord_notes[chord_name]
                
                # 코드 시작
                for i, note in enumerate(notes):
                    track.append(Message(
                        'note_on',
                        channel=0,
                        note=note,
                        velocity=60,
                        time=delta_time if i == 0 else 0
                    ))
                
                # 코드 종료
                for i, note in enumerate(notes):
                    track.append(Message(
                        'note_off',
                        channel=0,
                        note=note,
                        velocity=0,
                        time=duration if i == 0 else 0
                    ))
                
                current_time = start_time + duration
        
        return midi_file
    
    def _create_rhythm_midi(self, drum_pattern, tempo, track_name="Rhythm"):
        """드럼 패턴에서 리듬 MIDI 생성"""
        if not MIDO_AVAILABLE:
            raise ImportError("mido가 필요합니다")
        
        midi_file = MidiFile()
        track = MidiTrack()
        midi_file.tracks.append(track)
        
        track.append(Message('track_name', name=track_name, time=0))
        track.append(Message('program_change', program=0, channel=9, time=0))  # 드럼 채널
        
        # General MIDI 드럼 맵
        drum_map = {
            'kick': 36,      # Bass Drum 1
            'snare': 38,     # Acoustic Snare
            'hihat': 42,     # Closed Hi-Hat
            'crash': 49      # Crash Cymbal 1
        }
        
        current_time = 0
        for event in drum_pattern:
            event_time = int(event['time'] * 480)
            delta_time = event_time - current_time
            
            drum_note = drum_map.get(event['type'], 36)
            
            # Drum hit
            track.append(Message(
                'note_on',
                channel=9,  # 드럼 채널
                note=drum_note,
                velocity=event['velocity'],
                time=delta_time
            ))
            
            track.append(Message(
                'note_off',
                channel=9,
                note=drum_note,
                velocity=0,
                time=120  # 짧은 지속시간
            ))
            
            current_time = event_time + 120
        
        return midi_file
    
    def _create_piano_midi(self, piano_notes, track_name="Piano"):
        """피아노 음표에서 MIDI 생성"""
        return self._create_midi_from_notes(piano_notes, track_name)
    
    def _create_combined_midi(self, results, track_name="Combined"):
        """여러 트랙을 하나의 MIDI 파일로 결합"""
        if not MIDO_AVAILABLE:
            raise ImportError("mido가 필요합니다")
        
        midi_file = MidiFile()
        
        # 각 결과에서 트랙 추출하여 추가
        track_channels = {'melody': 0, 'harmony': 1, 'rhythm': 9}
        
        for track_type, result in results.items():
            if result.get('success') and track_type in track_channels:
                # 간단한 트랙 생성 (실제로는 각 결과의 MIDI 파일을 읽어서 합쳐야 함)
                track = MidiTrack()
                track.append(Message('track_name', name=f"{track_type.title()} Track", time=0))
                midi_file.tracks.append(track)
        
        return midi_file
    
    def get_supported_instruments(self):
        """지원하는 악기 목록 반환"""
        return self.instruments
    
    def get_conversion_types(self):
        """지원하는 변환 타입 반환"""
        return {
            'melody': '멜로디 라인 추출',
            'harmony': '화성 진행 추출',
            'rhythm': '리듬/드럼 패턴 추출',
            'piano': '피아노 전용 고정밀 전사',
            'full': '전체 다중 트랙 분석'
        }


# 편의 함수
def convert_audio_to_midi(audio_file, output_dir, conversion_type="full", model_type="basic_pitch"):
    """
    간단한 오디오→MIDI 변환 함수
    
    Args:
        audio_file: 입력 오디오 파일
        output_dir: 출력 디렉토리
        conversion_type: 변환 타입
        model_type: 모델 타입
        
    Returns:
        dict: 변환 결과
    """
    generator = MidiGenerator(model_type=model_type)
    return generator.generate_midi(audio_file, output_dir, conversion_type)


if __name__ == "__main__":
    # 테스트 코드
    generator = MidiGenerator()
    print("지원 악기:", generator.get_supported_instruments())
    print("변환 타입:", generator.get_conversion_types())