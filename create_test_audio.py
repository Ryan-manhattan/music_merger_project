"""
테스트용 샘플 오디오 파일 생성 스크립트
"""

from pydub import AudioSegment
from pydub.generators import Sine
import os

def create_test_audio_files():
    """테스트용 오디오 파일 생성"""
    test_dir = "test_audio"
    os.makedirs(test_dir, exist_ok=True)
    
    # 음정 (Hz)
    notes = {
        'C4': 261.63,
        'E4': 329.63,
        'G4': 392.00,
        'C5': 523.25
    }
    
    # 각 음정별로 3초짜리 사인파 생성
    for note_name, freq in notes.items():
        print(f"생성 중: {note_name} ({freq}Hz)")
        
        # 사인파 생성 (3초)
        tone = Sine(freq).to_audio_segment(duration=3000)
        
        # 페이드인/아웃 적용
        tone = tone.fade_in(500).fade_out(500)
        
        # 볼륨 조절 (-10dB)
        tone = tone - 10
        
        # 파일 저장
        filename = f"{test_dir}/test_{note_name}.mp3"
        tone.export(filename, format="mp3")
        print(f"✅ 생성 완료: {filename}")
    
    print(f"\n✅ 모든 테스트 파일이 {test_dir} 폴더에 생성되었습니다!")
    print("이제 웹 인터페이스에서 이 파일들을 업로드하여 테스트할 수 있습니다.")

if __name__ == "__main__":
    create_test_audio_files()
