"""
배너 관리 서비스
- 배너 CRUD
- 통계 관리
- 이미지 업로드 처리
"""

import os
import uuid
from datetime import datetime
from flask import current_app
from app.utils.db_utils import get_db_cursor, DatabaseError


class BannerService:
    """배너 관리 서비스 클래스"""

    @staticmethod
    def _get_mock_banners(banner_type):
        """임시 테스트용 Mock 배너 데이터 (로컬 이미지 사용)"""
        mock_data = {
            'home_top': [
                {
                    'id': 1,
                    'banner_type': 'home_top',
                    'title': '홈 상단 배너 샘플',
                    'image_url': '/static/images/mock/banner_970x90.png',
                    'mobile_image_url': None,  # 모바일 이미지 없음 = 모바일에서 숨김
                    'link_url': 'https://example.com',
                    'position_order': 1,
                    'click_count': 120,
                    'impression_count': 5430
                }
            ],
            'home_grid': [
                {
                    'id': i,
                    'banner_type': 'home_grid',
                    'title': f'홈 그리드 배너 {i}',
                    'image_url': '/static/images/mock/banner_200x60.png',
                    'mobile_image_url': None,
                    'link_url': f'https://example.com/grid{i}',
                    'position_order': i,
                    'click_count': 10 + i,
                    'impression_count': 500 + i * 10
                } for i in range(2, 10)  # 2~9번 ID로 8개 생성
            ],
            'home_bottom': [
                {
                    'id': 10,
                    'banner_type': 'home_bottom',
                    'title': '홈 하단 배너 샘플',
                    'image_url': '/static/images/mock/banner_728x90.png',
                    'mobile_image_url': None,
                    'link_url': 'https://example.com',
                    'position_order': 1,
                    'click_count': 85,
                    'impression_count': 3200
                }
            ],
            'grid_general': [
                {
                    'id': 10 + i,
                    'banner_type': 'grid_general',
                    'title': f'일반+메타 배너 {i}',
                    'image_url': '/static/images/mock/banner_200x60.png',
                    'mobile_image_url': None,
                    'link_url': f'https://example.com/general{i}',
                    'position_order': i,
                    'click_count': 5 + i,
                    'impression_count': 300 + i * 5
                } for i in range(1, 9)  # 11~18번 ID로 8개 생성
            ],
            'grid_coupang': [
                {
                    'id': 18 + i,
                    'banner_type': 'grid_coupang',
                    'title': f'쿠팡 배너 {i}',
                    'image_url': '/static/images/mock/banner_200x60.png',
                    'mobile_image_url': None,
                    'link_url': f'https://example.com/coupang{i}',
                    'position_order': i,
                    'click_count': 15 + i,
                    'impression_count': 600 + i * 20
                } for i in range(1, 9)  # 19~26번 ID로 8개 생성
            ]
        }
        return mock_data.get(banner_type, [])

    @staticmethod
    def get_active_banners(banner_type):
        """
        활성 배너 조회

        Args:
            banner_type: 배너 타입 (home_top, home_bottom, home_grid, grid_general, grid_coupang)

        Returns:
            list: 활성 배너 리스트
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT id, banner_type, title, image_url, mobile_image_url, link_url, position_order,
                           click_count, impression_count
                    FROM banners
                    WHERE banner_type = %s
                      AND is_active = TRUE
                      AND (start_date IS NULL OR start_date <= CURDATE())
                      AND (end_date IS NULL OR end_date >= CURDATE())
                    ORDER BY position_order ASC, created_at ASC
                """
                cursor.execute(query, (banner_type,))
                return cursor.fetchall()
        except Exception as e:
            current_app.logger.error(f"get_active_banners error: {e} - Using mock data")
            # 🔧 DB 연결 실패 시 Mock 데이터 반환
            return BannerService._get_mock_banners(banner_type)

    @staticmethod
    def get_all_banners(banner_type=None):
        """
        모든 배너 조회 (관리자용)

        Args:
            banner_type: 배너 타입 (None이면 전체)

        Returns:
            list: 배너 리스트
        """
        try:
            with get_db_cursor() as cursor:
                if banner_type:
                    query = """
                        SELECT id, banner_type, title, image_url, mobile_image_url, link_url, position_order,
                               is_active, start_date, end_date, click_count, impression_count,
                               created_at, updated_at
                        FROM banners
                        WHERE banner_type = %s
                        ORDER BY position_order ASC, created_at DESC
                    """
                    cursor.execute(query, (banner_type,))
                else:
                    query = """
                        SELECT id, banner_type, title, image_url, mobile_image_url, link_url, position_order,
                               is_active, start_date, end_date, click_count, impression_count,
                               created_at, updated_at
                        FROM banners
                        ORDER BY banner_type, position_order ASC, created_at DESC
                    """
                    cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            current_app.logger.error(f"get_all_banners error: {e} - Using mock data")
            # 🔧 DB 연결 실패 시 Mock 데이터 반환
            if banner_type:
                return BannerService._get_mock_all_banners(banner_type)
            return []

    @staticmethod
    def _get_mock_all_banners(banner_type):
        """관리자용 Mock 배너 데이터 (상세 정보 포함)"""
        base_data = BannerService._get_mock_banners(banner_type)
        # 관리자용 추가 필드 포함
        for banner in base_data:
            banner.update({
                'is_active': True,
                'start_date': None,
                'end_date': None,
                'created_at': '2025-11-20 12:00:00',
                'updated_at': '2025-11-20 12:00:00',
                'mobile_image_url': banner.get('mobile_image_url')
            })
        return base_data

    @staticmethod
    def create_banner(data, file, mobile_file=None):
        """
        배너 생성

        Args:
            data: 배너 정보 딕셔너리
            file: 업로드 파일 객체 (데스크톱용)
            mobile_file: 모바일용 이미지 파일 (선택)

        Returns:
            int: 생성된 배너 ID
        """
        try:
            # 파일 저장
            image_url = BannerService._save_banner_image(file)
            mobile_image_url = None
            if mobile_file:
                mobile_image_url = BannerService._save_banner_image(mobile_file)

            with get_db_cursor(commit=True) as cursor:
                query = """
                    INSERT INTO banners (banner_type, title, image_url, mobile_image_url, link_url,
                                       position_order, is_active, start_date, end_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    data['banner_type'],
                    data['title'],
                    image_url,
                    mobile_image_url,
                    data.get('link_url'),
                    data.get('position_order', 0),
                    data.get('is_active', True),
                    data.get('start_date'),
                    data.get('end_date')
                ))
                return cursor.lastrowid
        except Exception as e:
            current_app.logger.error(f"create_banner error: {e}")
            raise DatabaseError(f"배너 생성 실패: {str(e)}")

    @staticmethod
    def update_banner(banner_id, data, file=None, mobile_file=None):
        """
        배너 수정

        Args:
            banner_id: 배너 ID
            data: 수정할 정보 딕셔너리
            file: 새 이미지 파일 (선택, 데스크톱용)
            mobile_file: 새 모바일 이미지 파일 (선택)

        Returns:
            bool: 성공 여부
        """
        try:
            # 파일이 있으면 새로 저장
            if file:
                image_url = BannerService._save_banner_image(file)
                data['image_url'] = image_url

            # 모바일 이미지 파일이 있으면 새로 저장
            if mobile_file:
                mobile_image_url = BannerService._save_banner_image(mobile_file)
                data['mobile_image_url'] = mobile_image_url

            # 업데이트할 필드 동적 생성
            update_fields = []
            values = []

            for key in ['banner_type', 'title', 'image_url', 'mobile_image_url', 'link_url',
                       'position_order', 'is_active', 'start_date', 'end_date']:
                if key in data:
                    update_fields.append(f"{key} = %s")
                    values.append(data[key])

            if not update_fields:
                return True

            values.append(banner_id)

            with get_db_cursor(commit=True) as cursor:
                query = f"UPDATE banners SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(query, values)
                return cursor.rowcount > 0
        except Exception as e:
            current_app.logger.error(f"update_banner error: {e}")
            raise DatabaseError(f"배너 수정 실패: {str(e)}")

    @staticmethod
    def delete_banner(banner_id):
        """
        배너 삭제

        Args:
            banner_id: 배너 ID

        Returns:
            bool: 성공 여부
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                # 이미지 URL 가져오기 (데스크톱 + 모바일)
                cursor.execute("SELECT image_url, mobile_image_url FROM banners WHERE id = %s", (banner_id,))
                result = cursor.fetchone()

                if result:
                    # 데스크톱 이미지 파일 삭제
                    if result.get('image_url'):
                        BannerService._delete_banner_image(result['image_url'])
                    # 모바일 이미지 파일 삭제
                    if result.get('mobile_image_url'):
                        BannerService._delete_banner_image(result['mobile_image_url'])

                # DB 삭제
                cursor.execute("DELETE FROM banners WHERE id = %s", (banner_id,))
                return cursor.rowcount > 0
        except Exception as e:
            current_app.logger.error(f"delete_banner error: {e}")
            return False

    @staticmethod
    def reorder_banners(banner_type, order_list):
        """
        배너 순서 변경

        Args:
            banner_type: 배너 타입
            order_list: [banner_id, banner_id, ...] 순서대로

        Returns:
            bool: 성공 여부
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                for index, banner_id in enumerate(order_list, start=1):
                    query = """
                        UPDATE banners
                        SET position_order = %s
                        WHERE id = %s AND banner_type = %s
                    """
                    cursor.execute(query, (index, banner_id, banner_type))
                return True
        except Exception as e:
            current_app.logger.error(f"reorder_banners error: {e}")
            return False

    @staticmethod
    def increment_impression(banner_id):
        """노출 카운트 증가"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    "UPDATE banners SET impression_count = impression_count + 1 WHERE id = %s",
                    (banner_id,)
                )
                return True
        except Exception as e:
            current_app.logger.error(f"increment_impression error: {e}")
            return False

    @staticmethod
    def increment_click(banner_id):
        """클릭 카운트 증가"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    "UPDATE banners SET click_count = click_count + 1 WHERE id = %s",
                    (banner_id,)
                )
                return True
        except Exception as e:
            current_app.logger.error(f"increment_click error: {e}")
            return False

    @staticmethod
    def get_banner_stats(banner_type=None):
        """
        배너 통계 조회

        Args:
            banner_type: 배너 타입 (None이면 전체)

        Returns:
            dict: 통계 정보
        """
        try:
            with get_db_cursor() as cursor:
                if banner_type:
                    query = """
                        SELECT
                            COUNT(*) as total_banners,
                            SUM(impression_count) as total_impressions,
                            SUM(click_count) as total_clicks,
                            CASE
                                WHEN SUM(impression_count) > 0
                                THEN ROUND(SUM(click_count) * 100.0 / SUM(impression_count), 2)
                                ELSE 0
                            END as avg_ctr
                        FROM banners
                        WHERE banner_type = %s
                    """
                    cursor.execute(query, (banner_type,))
                else:
                    query = """
                        SELECT
                            COUNT(*) as total_banners,
                            SUM(impression_count) as total_impressions,
                            SUM(click_count) as total_clicks,
                            CASE
                                WHEN SUM(impression_count) > 0
                                THEN ROUND(SUM(click_count) * 100.0 / SUM(impression_count), 2)
                                ELSE 0
                            END as avg_ctr
                        FROM banners
                    """
                    cursor.execute(query)
                return cursor.fetchone() or {}
        except Exception as e:
            current_app.logger.error(f"get_banner_stats error: {e}")
            return {}

    @staticmethod
    def _save_banner_image(file):
        """
        배너 이미지 저장

        Args:
            file: 업로드 파일 객체

        Returns:
            str: 저장된 파일 경로 (상대경로)
        """
        if not file:
            raise ValueError("파일이 제공되지 않았습니다")

        # 파일 확장자 검증 (원본 파일명에서 추출 - 한글 파일명 지원)
        original_filename = file.filename
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''

        if ext not in current_app.config['ALLOWED_BANNER_EXTENSIONS']:
            raise ValueError(f"허용되지 않는 파일 형식입니다: {ext}")

        # 고유 파일명 생성 (타임스탬프 + UUID)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"{timestamp}_{unique_id}.{ext}"

        # 저장 경로
        upload_folder = current_app.config['BANNER_UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)

        # 웹 경로 반환 (static 기준 상대경로)
        return f"/static/uploads/banners/{new_filename}"

    @staticmethod
    def _delete_banner_image(image_url):
        """배너 이미지 파일 삭제"""
        try:
            if image_url and image_url.startswith('/static/'):
                # /static/uploads/banners/... -> app/static/uploads/banners/...
                file_path = image_url.replace('/static/', 'app/static/')
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            current_app.logger.warning(f"Failed to delete image file: {e}")
