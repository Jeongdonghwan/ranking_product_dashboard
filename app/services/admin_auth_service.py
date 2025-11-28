"""
관리자 인증 서비스
- 로그인/로그아웃
- 세션 관리
- bcrypt 비밀번호 검증
"""

import bcrypt
import secrets
from datetime import datetime, timedelta
from flask import current_app
from app.utils.db_utils import get_db_cursor, DatabaseError


class AdminAuthService:
    """관리자 인증 서비스 클래스"""

    # 🔧 임시 Mock 데이터 (DB 연결 실패 시 사용)
    MOCK_ADMIN = {
        'id': 1,
        'username': 'admin',
        'password_hash': '$2b$12$OFwl74QIoFPr9DykOHQBEOeB3ErxBporp3dgCOkEBerVHN8Z3gJ.u'  # 비밀번호: admin
    }
    MOCK_SESSIONS = {}  # {token: {'admin_id': 1, 'username': 'admin', 'expires_at': datetime}}

    @staticmethod
    def login(username, password):
        """
        관리자 로그인

        Args:
            username: 사용자명
            password: 비밀번호 (평문)

        Returns:
            dict: {'success': bool, 'token': str, 'admin_id': int} 또는 {'success': False, 'message': str}
        """
        try:
            with get_db_cursor() as cursor:
                # 관리자 조회
                cursor.execute(
                    "SELECT id, username, password_hash FROM admin_users WHERE username = %s",
                    (username,)
                )
                admin = cursor.fetchone()

                if not admin:
                    return {'success': False, 'message': '사용자를 찾을 수 없습니다'}

                # 비밀번호 검증
                if not bcrypt.checkpw(password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
                    return {'success': False, 'message': '비밀번호가 일치하지 않습니다'}

                # 세션 토큰 생성
                token = AdminAuthService._create_session(admin['id'])

                return {
                    'success': True,
                    'token': token,
                    'admin_id': admin['id'],
                    'username': admin['username']
                }

        except Exception as e:
            current_app.logger.error(f"login error: {e} - Using mock auth")
            # 🔧 DB 연결 실패 시 Mock 인증 사용
            return AdminAuthService._mock_login(username, password)

    @staticmethod
    def _create_session(admin_id):
        """
        세션 생성

        Args:
            admin_id: 관리자 ID

        Returns:
            str: 세션 토큰
        """
        try:
            # 토큰 생성 (64자 안전한 랜덤 문자열)
            token = secrets.token_urlsafe(48)

            # 만료 시간 (8시간)
            expires_at = datetime.now() + timedelta(hours=8)

            with get_db_cursor(commit=True) as cursor:
                query = """
                    INSERT INTO admin_sessions (admin_id, session_token, expires_at)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(query, (admin_id, token, expires_at))

            return token

        except Exception as e:
            current_app.logger.error(f"create_session error: {e}")
            raise DatabaseError("세션 생성 실패")

    @staticmethod
    def validate_session(token):
        """
        세션 검증

        Args:
            token: 세션 토큰

        Returns:
            dict: 관리자 정보 또는 None
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT s.admin_id, s.expires_at, a.username
                    FROM admin_sessions s
                    JOIN admin_users a ON s.admin_id = a.id
                    WHERE s.session_token = %s
                      AND s.expires_at > NOW()
                """
                cursor.execute(query, (token,))
                session = cursor.fetchone()

                if session:
                    return {
                        'admin_id': session['admin_id'],
                        'username': session['username']
                    }
                return None

        except Exception as e:
            current_app.logger.error(f"validate_session error: {e} - Using mock validation")
            # 🔧 DB 연결 실패 시 Mock 세션 검증
            return AdminAuthService._mock_validate_session(token)

    @staticmethod
    def logout(token):
        """
        로그아웃 (세션 삭제)

        Args:
            token: 세션 토큰

        Returns:
            bool: 성공 여부
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("DELETE FROM admin_sessions WHERE session_token = %s", (token,))
                return True
        except Exception as e:
            current_app.logger.error(f"logout error: {e}")
            return False

    @staticmethod
    def cleanup_expired_sessions():
        """만료된 세션 정리 (크론 작업용)"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("DELETE FROM admin_sessions WHERE expires_at < NOW()")
                return cursor.rowcount
        except Exception as e:
            current_app.logger.error(f"cleanup_expired_sessions error: {e}")
            return 0

    # ========================================
    # 🔧 Mock 인증 메서드 (DB 없이 테스트용)
    # ========================================

    @staticmethod
    def _mock_login(username, password):
        """Mock 로그인 (DB 연결 실패 시)"""
        if username != AdminAuthService.MOCK_ADMIN['username']:
            return {'success': False, 'message': '사용자를 찾을 수 없습니다'}

        # 비밀번호 검증
        if not bcrypt.checkpw(password.encode('utf-8'), AdminAuthService.MOCK_ADMIN['password_hash'].encode('utf-8')):
            return {'success': False, 'message': '비밀번호가 일치하지 않습니다'}

        # 세션 토큰 생성
        token = secrets.token_urlsafe(48)
        expires_at = datetime.now() + timedelta(hours=8)

        # Mock 세션 저장
        AdminAuthService.MOCK_SESSIONS[token] = {
            'admin_id': AdminAuthService.MOCK_ADMIN['id'],
            'username': AdminAuthService.MOCK_ADMIN['username'],
            'expires_at': expires_at
        }

        current_app.logger.info(f"🔧 Mock login successful for user: {username}")

        return {
            'success': True,
            'token': token,
            'admin_id': AdminAuthService.MOCK_ADMIN['id'],
            'username': AdminAuthService.MOCK_ADMIN['username']
        }

    @staticmethod
    def _mock_validate_session(token):
        """Mock 세션 검증 (DB 연결 실패 시)"""
        session = AdminAuthService.MOCK_SESSIONS.get(token)

        if not session:
            return None

        # 만료 확인
        if session['expires_at'] < datetime.now():
            del AdminAuthService.MOCK_SESSIONS[token]
            return None

        return {
            'admin_id': session['admin_id'],
            'username': session['username']
        }
