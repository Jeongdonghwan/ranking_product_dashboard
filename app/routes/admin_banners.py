"""
관리자 배너 관리 라우트
"""

from flask import Blueprint, render_template, request, jsonify, make_response, redirect, url_for
from werkzeug.utils import secure_filename
from app.services.banner_service import BannerService
from app.utils.admin_decorators import require_admin

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/banners', methods=['GET'])
@require_admin
def banners_page():
    """배너 관리 페이지"""
    # g.user.get('userId') .. 관리자는 관리자 아이디가 필요할경우에 그냥 하드코딩해도 된다.. admin 으로 박아버려도 됨
    return render_template('admin/banners.html')


@admin_bp.route('/api/banners/<banner_type>', methods=['GET'])
@require_admin
def get_banners(banner_type):
    """배너 목록 조회 API"""
    banners = BannerService.get_all_banners(banner_type)
    return jsonify({'success': True, 'banners': banners})


@admin_bp.route('/api/banners', methods=['POST'])
@require_admin
def create_banner():
    """배너 생성 API"""
    try:
        # 파일 체크
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': '이미지 파일이 필요합니다'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': '파일이 선택되지 않았습니다'}), 400

        # 모바일 이미지 체크 (선택)
        mobile_file = None
        if 'mobile_image' in request.files:
            mobile_file = request.files['mobile_image']
            if mobile_file.filename == '':
                mobile_file = None

        # 데이터 파싱
        data = {
            'banner_type': request.form.get('banner_type'),
            'title': request.form.get('title'),
            'link_url': request.form.get('link_url'),
            'position_order': int(request.form.get('position_order', 0)),
            'is_active': request.form.get('is_active', 'true').lower() == 'true',
            'start_date': request.form.get('start_date') or None,
            'end_date': request.form.get('end_date') or None
        }

        # 배너 생성 (모바일 이미지 포함)
        banner_id = BannerService.create_banner(data, file, mobile_file)

        return jsonify({'success': True, 'banner_id': banner_id, 'message': '배너가 생성되었습니다'})

    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'배너 생성 실패: {str(e)}'}), 500


@admin_bp.route('/api/banners/<int:banner_id>', methods=['PUT'])
@require_admin
def update_banner(banner_id):
    """배너 수정 API"""
    try:
        data = {}
        file = None
        mobile_file = None

        # JSON 또는 form-data 처리
        if request.is_json:
            data = request.get_json()
        else:
            # form-data에서 데이터 추출
            for key in ['banner_type', 'title', 'link_url', 'position_order', 'is_active', 'start_date', 'end_date']:
                if key in request.form:
                    value = request.form.get(key)
                    if key == 'position_order':
                        data[key] = int(value) if value else 0
                    elif key == 'is_active':
                        data[key] = value.lower() == 'true'
                    else:
                        data[key] = value or None

            # 데스크톱 이미지 파일이 있으면 가져오기
            if 'image' in request.files:
                file = request.files['image']
                if file.filename == '':
                    file = None

            # 모바일 이미지 파일이 있으면 가져오기
            if 'mobile_image' in request.files:
                mobile_file = request.files['mobile_image']
                if mobile_file.filename == '':
                    mobile_file = None

        success = BannerService.update_banner(banner_id, data, file, mobile_file)

        if success:
            return jsonify({'success': True, 'message': '배너가 수정되었습니다'})
        else:
            return jsonify({'success': False, 'message': '배너를 찾을 수 없습니다'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': f'배너 수정 실패: {str(e)}'}), 500


@admin_bp.route('/api/banners/<int:banner_id>', methods=['DELETE'])
@require_admin
def delete_banner(banner_id):
    """배너 삭제 API"""
    try:
        success = BannerService.delete_banner(banner_id)

        if success:
            return jsonify({'success': True, 'message': '배너가 삭제되었습니다'})
        else:
            return jsonify({'success': False, 'message': '배너를 찾을 수 없습니다'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': f'배너 삭제 실패: {str(e)}'}), 500


@admin_bp.route('/api/banners/reorder', methods=['POST'])
@require_admin
def reorder_banners():
    """배너 순서 변경 API"""
    try:
        data = request.get_json()
        banner_type = data.get('banner_type')
        order_list = data.get('order_list', [])

        if not banner_type or not order_list:
            return jsonify({'success': False, 'message': '배너 타입과 순서 목록이 필요합니다'}), 400

        success = BannerService.reorder_banners(banner_type, order_list)

        if success:
            return jsonify({'success': True, 'message': '순서가 변경되었습니다'})
        else:
            return jsonify({'success': False, 'message': '순서 변경 실패'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': f'순서 변경 실패: {str(e)}'}), 500


@admin_bp.route('/api/banners/stats', methods=['GET'])
@require_admin
def get_stats():
    """배너 통계 API"""
    banner_type = request.args.get('banner_type')
    stats = BannerService.get_banner_stats(banner_type)
    return jsonify({'success': True, 'stats': stats})
