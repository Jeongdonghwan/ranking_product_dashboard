"""
관리자 권한 데코레이터
"""

from functools import wraps
from flask import request, jsonify, session


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
        
        userId = session.get('userId')
        isAdmin = session.get('isAdmin')

        if not userId or not isAdmin:
            return jsonify({'error': 'Unauthorized', 'message': '로그인이 필요합니다'}), 401

        return f(*args, **kwargs)

    return decorated_function
