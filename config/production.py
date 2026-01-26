# ========================================
# Production Configuration
# ========================================
# 운영 환경 설정

import os
from datetime import timedelta


class ProductionConfig:
    """운영 환경 설정"""

    # Flask 기본 설정
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY')  # 필수! 환경변수로만 설정

    # if not SECRET_KEY:
    #     raise ValueError("SECRET_KEY 환경변수가 설정되지 않았습니다!")

    # JWT 설정
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    # if not JWT_SECRET_KEY:
    #     raise ValueError("JWT_SECRET_KEY 환경변수가 설정되지 않았습니다!")

    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_DELTA = timedelta(minutes=5)

    # 데이터베이스 설정
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    DB_CHARSET = 'utf8mb4'

    # Production에서만 DB 검증 (Development는 체크하지 않음)
    # if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    #     raise ValueError("데이터베이스 환경변수(DB_USER, DB_PASSWORD, DB_NAME)가 누락되었습니다!")

    # 데이터베이스 연결 풀 설정 (운영환경은 더 많은 커넥션)
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 20))
    DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', 40))

    # 세션 설정
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')  # 운영환경은 Redis 권장
    SESSION_FILE_DIR = os.getenv('SESSION_FILE_DIR', 'flask_session')
    SESSION_PERMANENT = os.getenv('SESSION_PERMANENT', 'false').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))
    )
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'insight_session'
    SESSION_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN')  # 도메인 설정

    # Redis 설정 (SESSION_TYPE=redis 사용 시)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # CORS 설정
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://mbizsquare.com').split(',')
    CORS_SUPPORTS_CREDENTIALS = True

    # 파일 업로드 설정
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE_MB', 50)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

    # 배너 업로드 설정
    BANNER_UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads', 'banners')
    MAX_BANNER_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_BANNER_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

    # OpenAI 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    AI_INSIGHTS_ENABLED = os.getenv('AI_INSIGHTS_ENABLED', 'false').lower() == 'true'
    OPENAI_MODEL = 'gpt-4'
    OPENAI_MAX_TOKENS = 1500
    OPENAI_TEMPERATURE = 0.7

    # 메인 사이트 설정
    MAIN_SITE_URL = os.getenv('MAIN_SITE_URL', 'https://mbizsquare.com')

    # 메인 프로젝트 인증 설정
    # TODO: 실제 메인 프로젝트의 로그인 URL로 변경 필요
    MAIN_LOGIN_URL = os.getenv('MAIN_LOGIN_URL', 'https://mbizsquare.com/login')

    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/var/log/insight/app.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 10))

    # 타임존
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Seoul')

    # 헬스체크 엔드포인트
    HEALTH_CHECK_ENABLED = True

    # 에러 페이지 표시 (운영환경은 커스텀 에러 페이지)
    PROPAGATE_EXCEPTIONS = False

    # 보안 헤더
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

    @staticmethod
    def init_app(app):
        """앱 초기화 시 추가 설정"""
        # 업로드 폴더 생성
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)

        # 로그 폴더 생성
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # 세션 폴더 생성 (filesystem 타입인 경우)
        if app.config['SESSION_TYPE'] == 'filesystem':
            session_dir = app.config['SESSION_FILE_DIR']
            if not os.path.exists(session_dir):
                os.makedirs(session_dir, exist_ok=True)

        # 보안 헤더 추가
        @app.after_request
        def add_security_headers(response):
            for header, value in app.config['SECURITY_HEADERS'].items():
                response.headers[header] = value
            return response

        # 운영 환경 경고
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=" * 50)
        logger.info("운영 환경(PRODUCTION)으로 실행 중입니다.")
        logger.info(f"DB Host: {app.config['DB_HOST']}")
        logger.info(f"Session Type: {app.config['SESSION_TYPE']}")
        logger.info(f"AI Insights: {'활성화' if app.config['AI_INSIGHTS_ENABLED'] else '비활성화'}")
        logger.info("=" * 50)
