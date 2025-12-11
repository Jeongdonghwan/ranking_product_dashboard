"""
관리자 권한 데코레이터
"""
import os
from functools import wraps
from flask import request, jsonify, session, g, current_app


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
        flask_env = current_app.config.get('FLASK_ENV', os.getenv('FLASK_ENV', 'development'))
        print('???????????????????', flask_env)
        if flask_env == 'development':
            return f(*args, **kwargs)

        userId = g.user.get('userId')
        isAdmin = g.user.get('isAdmin')
        print('************************', userId, isAdmin, not userId, not isAdmin)
        if not userId or not isAdmin:
            return jsonify({'error': 'Unauthorized', 'message': '로그인이 필요합니다'}), 401

        return f(*args, **kwargs)

    return decorated_function
