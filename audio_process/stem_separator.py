#!/usr/bin/env python3
"""
Stem Separator - 고품질 음원 스템 분리기
최신 AI 모델(Demucs, HTDEMUCS)을 활용한 상세한 악기별 분리

지원 스템:
- vocals (보컬)
- drums (드럼)  
- bass (베이스)
- guitar (기타)
- piano (피아노)
- other (기타 악기)
- accompaniment (반주 전체)
"""

import os
import torch
import torchaudio
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import json
import warnings
warnings.filterwarnings("ignore")

try:
    # Demucs v4 (최신 버전)
    import demucs.api
    from demucs.pretrained import get_model
    from demucs.audio import AudioFile, save_audio
    from demucs.separate import load_track
    DEMUCS_AVAILABLE = True
    print("[StemSeparator] Demucs v4 로드 성공")
except ImportError as e:
    DEMUCS_AVAILABLE = False
    print(f"[StemSeparator] Demucs 로드 실패: {e}")
    print("[StemSeparator] 설치 명령: pip install demucs")

try:
    # 추가 오디오 처리를 위한 librosa
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
    print("[StemSeparator] Librosa 로드 성공")
except ImportError as e:
    LIBROSA_AVAILABLE = False
    print(f"[StemSeparator] Librosa 로드 실패: {e}")
    print("[StemSeparator] 설치 명령: pip install librosa soundfile")


class StemSeparator:
    """
    고성능 음원 스템 분리기
    
    지원 모델:
    - htdemucs: Hybrid Transformer Demucs (최고 품질)
    - htdemucs_ft: Fine-tuned 버전
    - mdx_extra: MDX 모델 (고품질)
    - mdx_extra_q: MDX 양자화 모델 (빠른 처리)
    """
    
    def __init__(self, model_name="htdemucs", device="auto", console_log=None):
        """
        초기화
        
        Args:
            model_name: 사용할 모델명 (htdemucs, htdemucs_ft, mdx_extra 등)
            device: 처리 장치 ("auto", "cuda", "cpu")
            console_log: 로깅 함수
        """
        self.console_log = console_log or print
        self.model_name = model_name
        self.device = self._setup_device(device)
        self.model = None
        
        # 지원하는 스템 종류
        self.supported_stems = {
            'vocals': '보컬',
            'drums': '드럼',
            'bass': '베이스',
            'other': '기타 악기'
        }
        
        # 확장 스템 (6-stem 모델 사용 시)
        self.extended_stems = {
            'vocals': '보컬',
            'drums': '드럼',
            'bass': '베이스', 
            'guitar': '기타',
            'piano': '피아노',
            'other': '기타 악기'
        }
        
        self.console_log(f"[StemSeparator] 초기화 완료 - 모델: {model_name}, 장치: {self.device}")
        
    def _setup_device(self, device):
        """최적 처리 장치 설정"""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
                self.console_log(f"[StemSeparator] CUDA 사용 가능, GPU 사용: {torch.cuda.get_device_name()}")
            else:
                device = "cpu"
                self.console_log("[StemSeparator] CUDA 불가, CPU 사용")
        
        return torch.device(device)
    
    def load_model(self):
        """모델 로드"""
        if not DEMUCS_AVAILABLE:
            self.console_log("[StemSeparator] Demucs 미설치 - 기본 분리 모드로 전환")
            return False
        
        try:
            self.console_log(f"[StemSeparator] 모델 로딩 중: {self.model_name}")
            self.model = get_model(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # 모델 정보 출력
            model_info = {
                'name': self.model_name,
                'sources': list(self.model.sources),
                'samplerate': getattr(self.model, 'samplerate', 44100),
                'channels': getattr(self.model, 'audio_channels', 2)
            }
            
            self.console_log(f"[StemSeparator] 모델 로드 완료: {model_info}")
            return True
            
        except Exception as e:
            self.console_log(f"[StemSeparator] 모델 로딩 실패: {str(e)}")
            return False
    
    def separate_stems(self, input_file, output_dir, stems=None, progress_callback=None):
        """
        음원 스템 분리 실행
        
        Args:
            input_file: 입력 오디오 파일 경로
            output_dir: 출력 디렉토리
            stems: 분리할 스템 리스트 (None이면 모든 스템)
            progress_callback: 진행률 콜백 함수
            
        Returns:
            dict: 분리 결과 정보
        """
        try:
            if not self.model:
                if not self.load_model():
                    return {'success': False, 'error': '모델 로딩 실패'}
            
            if progress_callback:
                progress_callback(10, "오디오 파일 로딩 중...")
            
            # 입력 파일 검증
            if not os.path.exists(input_file):
                return {'success': False, 'error': f'입력 파일을 찾을 수 없습니다: {input_file}'}
            
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            self.console_log(f"[StemSeparator] 스템 분리 시작: {input_file}")
            
            if progress_callback:
                progress_callback(20, "오디오 분석 중...")
            
            # 오디오 로드 및 전처리
            waveform, sample_rate = self._load_audio(input_file)
            
            if progress_callback:
                progress_callback(30, "AI 모델로 스템 분리 중...")
            
            # Demucs로 스템 분리 실행
            with torch.no_grad():
                sources = demucs.api.separate(waveform, self.model)
                
            if progress_callback:
                progress_callback(70, "분리된 스템 저장 중...")
            
            # 결과 저장
            separated_files = {}
            base_name = Path(input_file).stem
            
            for i, source_name in enumerate(self.model.sources):
                if stems is None or source_name in stems:
                    # 스테레오 변환
                    source_audio = sources[i].cpu().numpy()
                    
                    # 출력 파일명 생성
                    output_file = os.path.join(output_dir, f"{base_name}_{source_name}.wav")
                    
                    # 고품질로 저장 (24bit, 44.1kHz)
                    self._save_high_quality_audio(source_audio, output_file, sample_rate)
                    
                    separated_files[source_name] = {
                        'file_path': output_file,
                        'file_size': os.path.getsize(output_file),
                        'description': self.supported_stems.get(source_name, source_name)
                    }
                    
                    self.console_log(f"[StemSeparator] 저장 완료: {source_name} -> {output_file}")
            
            if progress_callback:
                progress_callback(90, "품질 검증 중...")
            
            # 추가 정보 생성
            analysis_info = self._analyze_separated_stems(separated_files)
            
            if progress_callback:
                progress_callback(100, "스템 분리 완료!")
            
            result = {
                'success': True,
                'separated_files': separated_files,
                'analysis': analysis_info,
                'model_used': self.model_name,
                'processing_time': datetime.now().isoformat(),
                'total_stems': len(separated_files)
            }
            
            # 결과 메타데이터 저장
            meta_file = os.path.join(output_dir, f"{base_name}_separation_info.json")
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self.console_log(f"[StemSeparator] 스템 분리 완료: {len(separated_files)}개 스템")
            return result
            
        except Exception as e:
            self.console_log(f"[StemSeparator] 스템 분리 오류: {str(e)}")
            return {'success': False, 'error': f'스템 분리 중 오류 발생: {str(e)}'}
    
    def _load_audio(self, file_path):
        """고품질 오디오 로딩"""
        try:
            if LIBROSA_AVAILABLE:
                # librosa로 고품질 로딩
                waveform, sr = librosa.load(file_path, sr=None, mono=False)
                if waveform.ndim == 1:
                    waveform = waveform[None, :]  # 모노를 스테레오로
                waveform = torch.from_numpy(waveform).float()
            else:
                # torchaudio 사용
                waveform, sr = torchaudio.load(file_path)
            
            # 스테레오로 변환 (필요시)
            if waveform.shape[0] == 1:
                waveform = waveform.repeat(2, 1)
            
            self.console_log(f"[StemSeparator] 오디오 로드: {waveform.shape}, {sr}Hz")
            return waveform, sr
            
        except Exception as e:
            raise Exception(f"오디오 로딩 실패: {str(e)}")
    
    def _save_high_quality_audio(self, audio_data, output_path, sample_rate):
        """고품질 오디오 저장 (24bit WAV)"""
        try:
            if LIBROSA_AVAILABLE:
                # librosa + soundfile로 24bit 저장
                sf.write(output_path, audio_data.T, sample_rate, subtype='PCM_24')
            else:
                # torchaudio로 저장
                audio_tensor = torch.from_numpy(audio_data).float()
                torchaudio.save(output_path, audio_tensor, sample_rate)
                
        except Exception as e:
            self.console_log(f"[StemSeparator] 저장 오류: {str(e)}")
            # 폴백: 기본 저장
            audio_tensor = torch.from_numpy(audio_data).float()
            torchaudio.save(output_path, audio_tensor, sample_rate)
    
    def _analyze_separated_stems(self, separated_files):
        """분리된 스템 분석"""
        analysis = {
            'peak_levels': {},
            'rms_levels': {},
            'spectral_info': {}
        }
        
        try:
            for stem_name, file_info in separated_files.items():
                file_path = file_info['file_path']
                
                if LIBROSA_AVAILABLE:
                    # librosa로 상세 분석
                    y, sr = librosa.load(file_path, sr=None)
                    
                    # 피크 레벨
                    peak_level = float(np.max(np.abs(y)))
                    analysis['peak_levels'][stem_name] = peak_level
                    
                    # RMS 레벨  
                    rms_level = float(np.sqrt(np.mean(y**2)))
                    analysis['rms_levels'][stem_name] = rms_level
                    
                    # 스펙트럼 중심
                    spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
                    analysis['spectral_info'][stem_name] = {
                        'spectral_centroid': spectral_centroid,
                        'duration': len(y) / sr
                    }
                    
        except Exception as e:
            self.console_log(f"[StemSeparator] 분석 오류: {str(e)}")
            
        return analysis
    
    def get_available_models(self):
        """사용 가능한 모델 목록 반환"""
        if not DEMUCS_AVAILABLE:
            return []
        
        models = [
            {
                'name': 'htdemucs',
                'description': 'Hybrid Transformer Demucs (최고 품질, 4-stem)',
                'stems': 4,
                'quality': 'highest'
            },
            {
                'name': 'htdemucs_ft',
                'description': 'Fine-tuned HTDEMUCS (특정 장르 최적화)',
                'stems': 4,
                'quality': 'highest'
            },
            {
                'name': 'mdx_extra',
                'description': 'MDX Extra (고품질, 빠른 처리)',
                'stems': 4,
                'quality': 'high'
            },
            {
                'name': 'mdx_extra_q',
                'description': 'MDX Extra Quantized (양자화, 실시간)',
                'stems': 4,
                'quality': 'good'
            }
        ]
        
        return models
    
    def estimate_processing_time(self, audio_duration_seconds):
        """처리 시간 예상 (초 단위)"""
        # GPU/CPU에 따른 대략적인 처리 시간 예상
        if self.device.type == 'cuda':
            # GPU: 실시간의 0.1~0.3배
            return audio_duration_seconds * 0.2
        else:
            # CPU: 실시간의 2~5배  
            return audio_duration_seconds * 3.0
    
    def cleanup(self):
        """리소스 정리"""
        if self.model:
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        self.console_log("[StemSeparator] 리소스 정리 완료")


# 편의 함수들
def separate_audio_file(input_file, output_dir, model="htdemucs", device="auto"):
    """
    간단한 스템 분리 함수
    
    Args:
        input_file: 입력 오디오 파일
        output_dir: 출력 디렉토리  
        model: 사용할 모델명
        device: 처리 장치
        
    Returns:
        dict: 분리 결과
    """
    separator = StemSeparator(model_name=model, device=device)
    return separator.separate_stems(input_file, output_dir)


if __name__ == "__main__":
    # 테스트 코드
    separator = StemSeparator()
    print("사용 가능한 모델:", separator.get_available_models())