"""
관리자 권한 데코레이터
"""

from functools import wraps
from flask import request, jsonify
from app.services.admin_auth_service import AdminAuthService


def require_admin(f):
    """
    관리자 권한 확인 데코레이터

    Usage:
        @require_admin
        def admin_only_view():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 쿠키에서 토큰 가져오기
        token = request.cookies.get('admin_token')

        if not token:
            return jsonify({'error': 'Unauthorized', 'message': '로그인이 필요합니다'}), 401

        # 세션 검증
        admin_info = AdminAuthService.validate_session(token)

        if not admin_info:
            return jsonify({'error': 'Unauthorized', 'message': '유효하지 않은 세션입니다'}), 401

        # request에 관리자 정보 추가
        request.admin_info = admin_info

        return f(*args, **kwargs)

    return decorated_function
