# ========================================
# Flask App Factory
# ========================================
# Flask 애플리케이션 생성 및 초기화

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
import hashlib
from flask.sessions import SecureCookieSessionInterface
from itsdangerous import URLSafeTimedSerializer

# 환경변수 로드 (override=True로 .env 파일 값 우선)
load_dotenv(override=True)

# Config 임포트
from config import get_config

class SHA1SessionInterface(SecureCookieSessionInterface):
    def get_signing_serializer(self, app):
        if not app.secret_key:
            return None
        
        # 여기서 SHA1을 강제 적용합니다 (아까 진단 스크립트와 동일한 원리)
        signer_kwargs = dict(
            key_derivation='hmac',
            digest_method=hashlib.sha1
        )
        
        return URLSafeTimedSerializer(
            app.secret_key,
            salt=app.config.get('SESSION_COOKIE_SALT', 'cookie-session'),
            serializer=self.serializer,
            signer_kwargs=signer_kwargs
        )

def create_app():
    """
    Flask 애플리케이션 팩토리 함수

    Returns:
        Flask: 설정된 Flask 애플리케이션 인스턴스
    """
    # Flask 앱 생성
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # 환경별 설정 로드
    config_class = get_config()
    app.config.from_object(config_class)
    app.config['SECRET_KEY'] = "WJDEHDGHKS"
    app.session_interface = SHA1SessionInterface()

    # 추가 초기화 (폴더 생성 등)
    config_class.init_app(app)

    # 로깅 설정
    setup_logging(app)

    # CORS 설정
    CORS(app,
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'])

    # Redis 세션 설정 (SESSION_TYPE=redis인 경우)
    if app.config.get('SESSION_TYPE') == 'redis':
        import redis
        try:
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            app.config['SESSION_REDIS'] = redis.from_url(redis_url)
            app.logger.info(f"Redis 세션 연결 성공: {redis_url}")
        except Exception as e:
            app.logger.error(f"Redis 세션 연결 실패: {e}")
            app.logger.warning("Filesystem 세션으로 fallback...")
            app.config['SESSION_TYPE'] = 'filesystem'

    # 세션 설정
    Session(app)

    # 블루프린트 등록
    register_blueprints(app)

    # 에러 핸들러 등록
    register_error_handlers(app)


    # 헬스체크 엔드포인트
    if app.config.get('HEALTH_CHECK_ENABLED', True):
        @app.route('/health')
        def health_check():
            """헬스체크 엔드포인트"""
            return {'status': 'ok', 'service': 'insight'}, 200

    # 네이버 사이트 소유권 확인 파일 (인증 불필요)
    @app.route('/naver5c5df9165d15c739c9d6c9a94a4bc39a.html')
    def naver_verification():
        """네이버 검색 어드바이저 사이트 소유권 확인"""
        return 'naver-site-verification: naver5c5df9165d15c739c9d6c9a94a4bc39a.html', 200, {'Content-Type': 'text/html'}

    # 사이트맵 (검색엔진용)
    @app.route('/sitemap.xml')
    def sitemap():
        """사이트맵 - 검색엔진 크롤링용"""
        base_url = 'https://dashboard.mbizsquare.com'
        pages = [
            {'loc': '/', 'changefreq': 'daily', 'priority': '1.0'},
            {'loc': '/landing', 'changefreq': 'weekly', 'priority': '1.0'},
            {'loc': '/ad-dashboard', 'changefreq': 'daily', 'priority': '0.9'},
            {'loc': '/ad-dashboard/coupang', 'changefreq': 'daily', 'priority': '0.9'},
            {'loc': '/ad-dashboard/ad-efficiency', 'changefreq': 'weekly', 'priority': '0.8'},
            {'loc': '/ad-dashboard/profit-simulator', 'changefreq': 'weekly', 'priority': '0.8'},
            {'loc': '/ad-dashboard/keyword-combiner', 'changefreq': 'weekly', 'priority': '0.8'},
            {'loc': '/guide', 'changefreq': 'monthly', 'priority': '0.7'},
        ]

        urls_xml = '\n'.join([
            f'''    <url>
        <loc>{base_url}{p['loc']}</loc>
        <changefreq>{p['changefreq']}</changefreq>
        <priority>{p['priority']}</priority>
    </url>''' for p in pages
        ])

        sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}
</urlset>'''
        return sitemap_xml, 200, {'Content-Type': 'application/xml'}

    # robots.txt (검색엔진 크롤링 안내)
    @app.route('/robots.txt')
    def robots():
        """robots.txt - 검색엔진 크롤링 규칙"""
        robots_txt = '''User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /login
Disallow: /logout

Sitemap: https://dashboard.mbizsquare.com/sitemap.xml'''
        return robots_txt, 200, {'Content-Type': 'text/plain'}

    # 시작 로그
    app.logger.info("=" * 60)
    app.logger.info(f"Flask App 시작: {app.config['FLASK_ENV'] if 'FLASK_ENV' in app.config else os.getenv('FLASK_ENV', 'development')} 모드")
    app.logger.info(f"Debug 모드: {app.config['DEBUG']}")
    app.logger.info(f"AI 인사이트: {'활성화' if app.config['AI_INSIGHTS_ENABLED'] else '비활성화'}")
    app.logger.info("=" * 60)

    return app


def setup_logging(app):
    """
    로깅 설정

    Args:
        app: Flask 앱 인스턴스
    """
    # 로그 레벨 설정
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    app.logger.setLevel(log_level)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # 파일 핸들러 (Rotating)
    try:
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)d] %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        app.logger.addHandler(file_handler)
    except Exception as e:
        app.logger.warning(f"파일 로그 핸들러 생성 실패: {e}")

    # 콘솔 핸들러 추가
    app.logger.addHandler(console_handler)

    # Werkzeug 로거도 설정
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(log_level)
    werkzeug_logger.addHandler(console_handler)


def register_blueprints(app):
    """
    블루프린트 등록

    Args:
        app: Flask 앱 인스턴스
    """
    # 광고 분석 블루프린트
    from app.routes.ad_analysis import ad_bp
    app.register_blueprint(ad_bp)

    # 배너 관리 블루프린트 (관리자용)
    from app.routes.admin_banners import admin_bp
    app.register_blueprint(admin_bp)

    # 배너 조회 블루프린트 (공개용)
    from app.routes.public_banners import public_banner_bp
    app.register_blueprint(public_banner_bp)

    app.logger.info("블루프린트 등록 완료")


def register_error_handlers(app):
    """
    에러 핸들러 등록

    Args:
        app: Flask 앱 인스턴스
    """

    @app.errorhandler(400)
    def bad_request(error):
        """잘못된 요청"""
        app.logger.warning(f"400 Bad Request: {error}")
        return {'error': 'Bad Request', 'message': str(error)}, 400

    @app.errorhandler(401)
    def unauthorized(error):
        """인증 실패"""
        app.logger.warning(f"401 Unauthorized: {error}")
        return {'error': 'Unauthorized', 'message': '로그인이 필요합니다.'}, 401

    @app.errorhandler(403)
    def forbidden(error):
        """권한 없음"""
        app.logger.warning(f"403 Forbidden: {error}")
        return {'error': 'Forbidden', 'message': '접근 권한이 없습니다.'}, 403

    @app.errorhandler(404)
    def not_found(error):
        """리소스 없음"""
        app.logger.warning(f"404 Not Found: {error}")
        return {'error': 'Not Found', 'message': '요청한 리소스를 찾을 수 없습니다.'}, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """허용되지 않은 메서드"""
        app.logger.warning(f"405 Method Not Allowed: {error}")
        return {'error': 'Method Not Allowed', 'message': '허용되지 않은 HTTP 메서드입니다.'}, 405

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """파일 크기 초과"""
        app.logger.warning(f"413 Payload Too Large: {error}")
        max_size_mb = app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
        return {
            'error': 'Payload Too Large',
            'message': f'파일 크기가 너무 큽니다. 최대 {max_size_mb:.0f}MB까지 업로드 가능합니다.'
        }, 413

    @app.errorhandler(500)
    def internal_server_error(error):
        """서버 내부 오류"""
        app.logger.error(f"500 Internal Server Error: {error}", exc_info=True)
        if app.config['DEBUG']:
            return {'error': 'Internal Server Error', 'message': str(error)}, 500
        else:
            return {'error': 'Internal Server Error', 'message': '서버 오류가 발생했습니다.'}, 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """처리되지 않은 예외"""
        app.logger.error(f"Unhandled Exception: {error}", exc_info=True)
        if app.config['DEBUG']:
            return {'error': 'Exception', 'message': str(error)}, 500
        else:
            return {'error': 'Internal Server Error', 'message': '예상치 못한 오류가 발생했습니다.'}, 500

    app.logger.info("에러 핸들러 등록 완료")


