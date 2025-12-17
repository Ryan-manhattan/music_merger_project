import os

class Config:
    # 기본 설정
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    
    # 파일 업로드 설정
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB 제한
    
    # 경로 설정 (app/ 폴더 기준 상대 경로 또는 절대 경로)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'uploads')
    PROCESSED_FOLDER = os.path.join(BASE_DIR, 'app', 'processed')
    
    # 허용된 확장자
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'mp4', 'webm'}
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'gif'}

    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
