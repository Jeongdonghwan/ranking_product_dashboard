# ========================================
# 메인 프로젝트 세션 공유 인증 미들웨어
# ========================================
# mbizsquare.com에서 생성된 세션 쿠키를 읽어 사용자 인증
# 주의: SECRET_KEY가 메인 프로젝트와 동일해야 세션 디코딩 가능

from functools import wraps
from flask import session, request, redirect, current_app, g
import logging

logger = logging.getLogger(__name__)

# ========================================
# 설정값 (TODO: 실제 값으로 변경 필요)
# ========================================

# 메인 사이트 로그인 페이지 URL
# 세션이 없을 경우 이 URL로 리다이렉트됨
MAIN_LOGIN_URL = 'https://mbizsquare.com/login'

# 세션에서 사용자 정보를 찾을 키 이름
# 메인 프로젝트의 세션 키와 동일해야 함
USER_ID_KEY = 'user_id'
USERNAME_KEY = 'username'
EMAIL_KEY = 'email'


# ========================================
# 인증 확인 함수들
# ========================================

def get_main_session_user():
    """
    메인 프로젝트 세션에서 사용자 정보 추출

    Returns:
        dict: 사용자 정보 (user_id, username, email 등)
        None: 세션이 없거나 유효하지 않은 경우

    Note:
        - 메인 프로젝트와 SECRET_KEY가 동일해야 세션 디코딩 가능
        - SESSION_COOKIE_DOMAIN이 '.mbizsquare.com'으로 설정되어야 함
    """
    try:
        user_id = session.get(USER_ID_KEY)

        if not user_id:
            logger.debug("세션에 user_id가 없습니다.")
            return None

        # 사용자 정보 구성
        user = {
            'user_id': user_id,
            'username': session.get(USERNAME_KEY, str(user_id)),
            'email': session.get(EMAIL_KEY, ''),
        }

        # 추가 세션 정보가 있으면 포함
        for key in session.keys():
            if key not in ['_permanent', '_fresh', USER_ID_KEY, USERNAME_KEY, EMAIL_KEY]:
                user[key] = session.get(key)

        logger.debug(f"세션에서 사용자 정보 추출 성공: user_id={user_id}")
        return user

    except Exception as e:
        logger.error(f"세션 사용자 정보 추출 실패: {e}")
        return None


def is_authenticated():
    """
    현재 요청이 인증되었는지 확인

    Returns:
        bool: 인증 여부
    """
    return get_main_session_user() is not None


def get_current_user():
    """
    현재 인증된 사용자 정보 반환 (캐싱 적용)

    Returns:
        dict: 사용자 정보
        None: 인증되지 않은 경우

    Note:
        g 객체에 캐싱하여 한 요청 내에서 중복 조회 방지
    """
    if not hasattr(g, '_current_user'):
        g._current_user = get_main_session_user()
    return g._current_user


def get_current_user_id():
    """
    현재 인증된 사용자 ID 반환

    Returns:
        int/str: 사용자 ID
        None: 인증되지 않은 경우
    """
    user = get_current_user()
    return user.get('user_id') if user else None


# ========================================
# 인증 데코레이터
# ========================================

def require_main_auth(f):
    """
    메인 프로젝트 세션 인증 필수 데코레이터

    사용법:
        @ad_bp.route('/protected')
        @require_main_auth
        def protected_route():
            user = get_current_user()
            return f"Hello, {user['username']}"

    동작:
        - API 요청 (/api/*): 401 JSON 응답 반환
        - 페이지 요청: 메인 로그인 페이지로 리다이렉트
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            logger.warning(f"인증되지 않은 접근 시도: {request.path}")

            # API 요청인 경우 JSON 응답
            if request.path.startswith('/api/'):
                return {'error': 'Unauthorized', 'message': '로그인이 필요합니다.'}, 401

            # 페이지 요청인 경우 메인 로그인으로 리다이렉트
            login_url = current_app.config.get('MAIN_LOGIN_URL', MAIN_LOGIN_URL)

            # 현재 URL을 리다이렉트 파라미터로 전달 (선택적)
            # next_url = request.url
            # return redirect(f"{login_url}?next={next_url}")

            return redirect(login_url)

        return f(*args, **kwargs)

    return decorated_function


def require_main_auth_api(f):
    """
    API 전용 인증 데코레이터 (항상 JSON 응답)

    사용법:
        @ad_bp.route('/api/data')
        @require_main_auth_api
        def api_data():
            return {'data': ...}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            logger.warning(f"인증되지 않은 API 접근 시도: {request.path}")
            return {
                'error': 'Unauthorized',
                'message': '로그인이 필요합니다.',
                'code': 'AUTH_REQUIRED'
            }, 401

        return f(*args, **kwargs)

    return decorated_function


# ========================================
# before_request 글로벌 인증 체크
# ========================================

# 인증 체크를 건너뛸 경로 패턴
AUTH_EXEMPT_PATHS = [
    '/health',           # 헬스체크
    '/static/',          # 정적 파일
    '/favicon.ico',      # 파비콘
]

# 인증 체크를 건너뛸 경로 prefix
AUTH_EXEMPT_PREFIXES = [
    '/admin/',           # 관리자 영역 (별도 인증 사용)
    '/api/public/',      # 공개 API (있는 경우)
    '/api/banners/public',  # 공개 배너 API
]


def is_auth_exempt_path(path):
    """
    인증 체크 제외 경로인지 확인

    Args:
        path: 요청 경로

    Returns:
        bool: 제외 여부
    """
    # 정확히 일치하는 경로
    if path in AUTH_EXEMPT_PATHS:
        return True

    # prefix로 시작하는 경로
    for prefix in AUTH_EXEMPT_PREFIXES:
        if path.startswith(prefix):
            return True

    return False


def check_auth_before_request():
    """
    before_request에서 호출할 글로벌 인증 체크 함수

    사용법 (app/__init__.py):
        from app.utils.main_session_auth import check_auth_before_request

        @app.before_request
        def before_request():
            return check_auth_before_request()

    Returns:
        None: 인증됨 또는 제외 경로
        Response: 인증 실패 시 리다이렉트 또는 에러 응답
    """
    path = request.path

    # 제외 경로 체크
    if is_auth_exempt_path(path):
        return None

    # 인증 체크
    if not is_authenticated():
        logger.warning(f"글로벌 인증 체크 실패: {path}")

        # API 요청
        if path.startswith('/api/'):
            return {'error': 'Unauthorized', 'message': '로그인이 필요합니다.'}, 401

        # 페이지 요청 - 메인 로그인으로 리다이렉트
        login_url = current_app.config.get('MAIN_LOGIN_URL', MAIN_LOGIN_URL)
        return redirect(login_url)

    # 인증 성공 - 요청 컨텍스트에 사용자 정보 저장
    g.current_user = get_current_user()

    return None


# ========================================
# 유틸리티 함수들
# ========================================

def clear_session():
    """
    현재 세션 클리어 (로그아웃 시 사용)

    Note:
        실제 로그아웃은 메인 프로젝트에서 처리해야 함
        이 함수는 로컬 세션 데이터만 클리어
    """
    session.clear()
    if hasattr(g, '_current_user'):
        delattr(g, '_current_user')
    logger.info("로컬 세션 클리어됨")


def debug_session():
    """
    세션 디버깅용 함수 (개발 환경에서만 사용)

    Returns:
        dict: 세션 정보 (민감 정보 마스킹)
    """
    if not current_app.debug:
        return {'error': '디버그 모드에서만 사용 가능'}

    return {
        'session_keys': list(session.keys()),
        'is_authenticated': is_authenticated(),
        'user_id': session.get(USER_ID_KEY),
        'username': session.get(USERNAME_KEY),
    }
