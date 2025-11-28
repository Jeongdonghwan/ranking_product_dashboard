"""
공개 배너 API 라우트
- 활성 배너 조회
- 노출/클릭 카운트
"""

from flask import Blueprint, jsonify, request
from app.services.banner_service import BannerService

public_banner_bp = Blueprint('public_banners', __name__)


@public_banner_bp.route('/api/banners/<banner_type>', methods=['GET'])
def get_banners(banner_type):
    """
    활성 배너 조회 API (공개)

    Args:
        banner_type: home_top, home_bottom, home_grid, grid_general, grid_coupang

    Response:
        {
            "success": true,
            "banners": [
                {
                    "id": 1,
                    "title": "배너 제목",
                    "image_url": "/static/uploads/banners/...",
                    "link_url": "https://...",
                    "position_order": 1
                }
            ]
        }
    """
    try:
        banners = BannerService.get_active_banners(banner_type)
        return jsonify({'success': True, 'banners': banners})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@public_banner_bp.route('/api/banners/<int:banner_id>/impression', methods=['POST'])
def track_impression(banner_id):
    """
    배너 노출 카운트 증가

    Args:
        banner_id: 배너 ID
    """
    try:
        BannerService.increment_impression(banner_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@public_banner_bp.route('/api/banners/<int:banner_id>/click', methods=['POST'])
def track_click(banner_id):
    """
    배너 클릭 카운트 증가

    Args:
        banner_id: 배너 ID
    """
    try:
        BannerService.increment_click(banner_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
