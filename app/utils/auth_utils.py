"""
인증 및 세션 관리 유틸리티
- JWT 토큰 검증
- Flask 세션 생성
- 인증 데코레이터
"""

import jwt
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import session, request, jsonify, redirect, url_for, current_app

from .db_utils import get_user_by_id, DatabaseError

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """인증 오류 커스텀 예외"""
    pass


def verify_jwt_token(token):
    """
    JWT 토큰 검증

    Args:
        token (str): JWT 토큰

    Returns:
        dict: 디코딩된 페이로드 (user_id 포함)

    Raises:
        AuthenticationError: 토큰이 유효하지 않을 경우

    Example:
        payload = verify_jwt_token("eyJhbGciOiJIUzI1NiIs...")
        user_id = payload['user_id']
    """
    try:
        # JWT 디코딩
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )

        logger.info(f"JWT verified successfully for user: {payload.get('user_id')}")
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise AuthenticationError("토큰이 만료되었습니다. 다시 로그인하세요.")

    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {e}")
        raise AuthenticationError("유효하지 않은 토큰입니다.")

    except Exception as e:
        logger.error(f"JWT verification failed: {e}")
        raise AuthenticationError(f"토큰 검증 실패: {str(e)}")


def create_session_from_jwt(token):
    """
    JWT 토큰에서 Flask 세션 생성

    Args:
        token (str): JWT 토큰

    Returns:
        dict: 사용자 정보

    Raises:
        AuthenticationError: 토큰 검증 실패 또는 사용자 없음

    Side Effects:
        - session['user_id'] 설정
        - session['username'] 설정
        - session['logged_in_at'] 설정
    """
    # JWT 검증
    payload = verify_jwt_token(token)
    user_id = payload.get('user_id')

    if not user_id:
        raise AuthenticationError("토큰에 사용자 ID가 없습니다.")

    # DB에서 사용자 조회
    try:
        user = get_user_by_id(user_id)

        if not user:
            raise AuthenticationError(f"사용자를 찾을 수 없습니다: {user_id}")

        # Flask 세션 생성
        session.clear()  # 기존 세션 정리
        session['user_id'] = user['user_id']
        session['username'] = user.get('username', user_id)
        session['logged_in_at'] = datetime.now().isoformat()
        session.permanent = True  # PERMANENT_SESSION_LIFETIME 설정 적용

        logger.info(f"Session created for user: {user_id}")

        return {
            'user_id': user['user_id'],
            'username': user.get('username'),
            'email': user.get('email')
        }

    except DatabaseError as e:
        logger.error(f"Database error during session creation: {e}")
        raise AuthenticationError(f"사용자 조회 실패: {str(e)}")


def check_session():
    """
    현재 세션 유효성 확인

    Returns:
        bool: 세션 유효 여부

    Example:
        if check_session():
            # 인증된 사용자
        else:
            # 미인증
    """
    if 'user_id' not in session:
        return False

    # 세션 만료 확인 (선택적)
    if 'logged_in_at' in session:
        logged_in_at = datetime.fromisoformat(session['logged_in_at'])
        session_lifetime = timedelta(hours=current_app.config.get('SESSION_LIFETIME_HOURS', 1))

        if datetime.now() - logged_in_at > session_lifetime:
            logger.warning(f"Session expired for user: {session.get('user_id')}")
            session.clear()
            return False

    return True


def get_current_user_id():
    """
    현재 로그인한 사용자 ID 반환

    Returns:
        str | None: 사용자 ID 또는 None

    Example:
        user_id = get_current_user_id()
        if user_id:
            # 인증된 요청 처리
    """
    return session.get('user_id')


def get_current_user():
    """
    현재 로그인한 사용자 정보 반환

    Returns:
        dict | None: 사용자 정보 또는 None

    Example:
        user = get_current_user()
        if user:
            print(f"Welcome, {user['username']}")
    """
    user_id = get_current_user_id()

    if not user_id:
        return None

    try:
        return get_user_by_id(user_id)
    except DatabaseError:
        return None


def logout():
    """
    로그아웃 (세션 삭제)

    Example:
        logout()
        return redirect('/login')
    """
    user_id = session.get('user_id')
    session.clear()
    logger.info(f"User logged out: {user_id}")


def require_auth(f):
    """
    인증 필수 데코레이터 (Flask 라우트용)

    인증되지 않은 요청은 401 또는 로그인 페이지로 리다이렉트

    Example:
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            user_id = get_current_user_id()
            return jsonify({'user_id': user_id})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_session():
            # API 요청인 경우 JSON 응답
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Unauthorized',
                    'message': '로그인이 필요합니다.'
                }), 401

            # 일반 페이지 요청인 경우 로그인 페이지로 리다이렉트
            logger.warning(f"Unauthorized access attempt to: {request.path}")
            return redirect(url_for('ad_analysis.login'))

        return f(*args, **kwargs)

    return decorated_function


def optional_auth(f):
    """
    선택적 인증 데코레이터

    인증되지 않아도 접근 가능하지만, 인증 상태를 확인할 수 있음

    Example:
        @app.route('/api/public')
        @optional_auth
        def public_route():
            user_id = get_current_user_id()
            if user_id:
                return jsonify({'message': f'Hello, {user_id}'})
            else:
                return jsonify({'message': 'Hello, guest'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 세션 체크만 하고 강제하지 않음
        check_session()
        return f(*args, **kwargs)

    return decorated_function


def check_ownership(resource_user_id):
    """
    리소스 소유권 확인

    현재 로그인한 사용자가 해당 리소스의 소유자인지 확인

    Args:
        resource_user_id (str): 리소스의 user_id

    Returns:
        bool: 소유권 여부

    Example:
        snapshot = get_snapshot(snapshot_id)
        if not check_ownership(snapshot['user_id']):
            return jsonify({'error': 'Forbidden'}), 403
    """
    current_user_id = get_current_user_id()

    if not current_user_id:
        return False

    is_owner = current_user_id == resource_user_id

    if not is_owner:
        logger.warning(
            f"Ownership check failed: user {current_user_id} "
            f"tried to access resource of user {resource_user_id}"
        )

    return is_owner


def generate_jwt_token(user_id, expires_in=300):
    """
    JWT 토큰 생성 (주로 mbizsquare.com에서 사용)

    Args:
        user_id (str): 사용자 ID
        expires_in (int): 만료 시간 (초 단위, 기본 300초 = 5분)

    Returns:
        str: JWT 토큰

    Example:
        # mbizsquare.com에서 호출 예시
        token = generate_jwt_token('test_user', expires_in=300)
        redirect_url = f"http://insight.mbizsquare.com/?token={token}"
    """
    payload = {
        'user_id': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=expires_in)
    }

    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )

    logger.info(f"JWT token generated for user: {user_id}, expires_in: {expires_in}s")

    return token


def refresh_session():
    """
    세션 갱신 (logged_in_at 업데이트)

    장시간 활동하는 사용자의 세션 만료 방지

    Example:
        # API 호출마다 세션 갱신
        @app.before_request
        def before_request():
            if check_session():
                refresh_session()
    """
    if 'user_id' in session:
        session['logged_in_at'] = datetime.now().isoformat()
        logger.debug(f"Session refreshed for user: {session['user_id']}")


def get_session_info():
    """
    현재 세션 정보 조회 (디버깅용)

    Returns:
        dict: 세션 정보

    Example:
        info = get_session_info()
        print(f"Session: {info}")
    """
    if not check_session():
        return {'authenticated': False}

    logged_in_at = session.get('logged_in_at')
    if logged_in_at:
        logged_in_at = datetime.fromisoformat(logged_in_at)
        session_age = (datetime.now() - logged_in_at).total_seconds() / 60  # 분 단위

    return {
        'authenticated': True,
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'logged_in_at': session.get('logged_in_at'),
        'session_age_minutes': round(session_age, 2) if logged_in_at else None
    }
