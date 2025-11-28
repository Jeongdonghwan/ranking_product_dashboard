"""
범용 헬퍼 함수
- 파일 검증
- 포맷팅 (금액, 퍼센트, 날짜)
- 안전한 파일명 처리
"""

import os
import re
import logging
from datetime import datetime, date
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}


def allowed_file(filename):
    """
    파일 확장자 검증

    Args:
        filename (str): 파일명

    Returns:
        bool: 허용된 확장자 여부

    Example:
        if allowed_file('data.xlsx'):
            # 업로드 허용
    """
    if not filename:
        return False

    has_extension = '.' in filename
    extension = filename.rsplit('.', 1)[1].lower() if has_extension else ''

    is_allowed = extension in ALLOWED_EXTENSIONS

    if not is_allowed:
        logger.warning(f"File extension not allowed: {filename}")

    return is_allowed


def clean_filename(filename):
    """
    안전한 파일명 생성

    Args:
        filename (str): 원본 파일명

    Returns:
        str: 안전한 파일명

    Example:
        safe_name = clean_filename("../../etc/passwd.txt")
        # 결과: "etc_passwd.txt"
    """
    # Werkzeug의 secure_filename 사용
    safe_name = secure_filename(filename)

    # 한글 파일명 처리 (ASCII 변환 시 빈 문자열 방지)
    if not safe_name or safe_name == '':
        # 타임스탬프 기반 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'file'
        safe_name = f"upload_{timestamp}.{extension}"
        logger.info(f"Generated safe filename: {safe_name}")

    return safe_name


def get_unique_filename(upload_folder, filename):
    """
    중복되지 않는 파일명 생성

    Args:
        upload_folder (str): 업로드 폴더 경로
        filename (str): 원본 파일명

    Returns:
        str: 중복되지 않는 파일명

    Example:
        unique_name = get_unique_filename('/uploads', 'data.xlsx')
        # 결과: 'data_1.xlsx' (data.xlsx가 이미 존재하는 경우)
    """
    safe_name = clean_filename(filename)
    base_name, extension = os.path.splitext(safe_name)

    counter = 1
    new_filename = safe_name

    while os.path.exists(os.path.join(upload_folder, new_filename)):
        new_filename = f"{base_name}_{counter}{extension}"
        counter += 1

    if new_filename != safe_name:
        logger.debug(f"Filename changed to avoid conflict: {safe_name} -> {new_filename}")

    return new_filename


def format_currency(amount, include_symbol=True):
    """
    금액 포맷팅 (원화)

    Args:
        amount (float | int): 금액
        include_symbol (bool): "원" 기호 포함 여부

    Returns:
        str: 포맷된 금액

    Example:
        format_currency(1500000)  # "1,500,000원"
        format_currency(1500000, include_symbol=False)  # "1,500,000"
    """
    if amount is None:
        return "0원" if include_symbol else "0"

    try:
        formatted = f"{int(amount):,}"
        return f"{formatted}원" if include_symbol else formatted
    except (ValueError, TypeError):
        logger.error(f"Invalid currency value: {amount}")
        return "0원" if include_symbol else "0"


def format_percentage(value, decimals=2):
    """
    퍼센트 포맷팅

    Args:
        value (float): 퍼센트 값 (예: 3.456)
        decimals (int): 소수점 자릿수

    Returns:
        str: 포맷된 퍼센트

    Example:
        format_percentage(3.456)  # "3.46%"
        format_percentage(3.456, decimals=1)  # "3.5%"
    """
    if value is None:
        return "0%"

    try:
        formatted = f"{float(value):.{decimals}f}"
        return f"{formatted}%"
    except (ValueError, TypeError):
        logger.error(f"Invalid percentage value: {value}")
        return "0%"


def format_number(value, decimals=0):
    """
    숫자 포맷팅 (천 단위 구분)

    Args:
        value (float | int): 숫자
        decimals (int): 소수점 자릿수

    Returns:
        str: 포맷된 숫자

    Example:
        format_number(1500)  # "1,500"
        format_number(1500.567, decimals=2)  # "1,500.57"
    """
    if value is None:
        return "0"

    try:
        if decimals == 0:
            return f"{int(value):,}"
        else:
            return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        logger.error(f"Invalid number value: {value}")
        return "0"


def format_date(date_obj, format_str='%Y-%m-%d'):
    """
    날짜 포맷팅

    Args:
        date_obj (date | datetime | str): 날짜 객체 또는 문자열
        format_str (str): 포맷 문자열

    Returns:
        str: 포맷된 날짜

    Example:
        format_date(datetime.now())  # "2024-11-12"
        format_date("2024-11-12", format_str='%Y년 %m월 %d일')  # "2024년 11월 12일"
    """
    if date_obj is None:
        return ""

    try:
        if isinstance(date_obj, str):
            # 문자열을 datetime으로 변환
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d')

        if isinstance(date_obj, (datetime, date)):
            return date_obj.strftime(format_str)

        return str(date_obj)

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid date value: {date_obj}, error: {e}")
        return ""


def parse_date(date_str):
    """
    문자열을 날짜 객체로 변환

    Args:
        date_str (str): 날짜 문자열 (YYYY-MM-DD)

    Returns:
        date: 날짜 객체 또는 None

    Example:
        date_obj = parse_date("2024-11-12")
    """
    if not date_str:
        return None

    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.error(f"Invalid date string: {date_str}")
        return None


def calculate_roas(revenue, spend):
    """
    ROAS 계산 (Return on Ad Spend)

    Args:
        revenue (float): 매출
        spend (float): 광고비

    Returns:
        float: ROAS (소수점 2자리)

    Example:
        roas = calculate_roas(500000, 100000)  # 5.0
    """
    if not spend or spend == 0:
        return 0.0

    return round(float(revenue) / float(spend), 2)


def calculate_ctr(clicks, impressions):
    """
    CTR 계산 (Click Through Rate)

    Args:
        clicks (int): 클릭수
        impressions (int): 노출수

    Returns:
        float: CTR (%, 소수점 2자리)

    Example:
        ctr = calculate_ctr(100, 10000)  # 1.0 (%)
    """
    if not impressions or impressions == 0:
        return 0.0

    return round((float(clicks) / float(impressions)) * 100, 2)


def calculate_cpc(spend, clicks):
    """
    CPC 계산 (Cost Per Click)

    Args:
        spend (float): 광고비
        clicks (int): 클릭수

    Returns:
        float: CPC (원, 소수점 0자리)

    Example:
        cpc = calculate_cpc(100000, 500)  # 200
    """
    if not clicks or clicks == 0:
        return 0.0

    return round(float(spend) / float(clicks), 0)


def calculate_cpa(spend, conversions):
    """
    CPA 계산 (Cost Per Acquisition)

    Args:
        spend (float): 광고비
        conversions (int): 전환수

    Returns:
        float: CPA (원, 소수점 0자리)

    Example:
        cpa = calculate_cpa(100000, 50)  # 2000
    """
    if not conversions or conversions == 0:
        return 0.0

    return round(float(spend) / float(conversions), 0)


def calculate_cvr(conversions, clicks):
    """
    CVR 계산 (Conversion Rate)

    Args:
        conversions (int): 전환수
        clicks (int): 클릭수

    Returns:
        float: CVR (%, 소수점 2자리)

    Example:
        cvr = calculate_cvr(50, 1000)  # 5.0 (%)
    """
    if not clicks or clicks == 0:
        return 0.0

    return round((float(conversions) / float(clicks)) * 100, 2)


def sanitize_campaign_name(name):
    """
    캠페인명 정제 (특수문자 제거, 공백 정리)

    Args:
        name (str): 원본 캠페인명

    Returns:
        str: 정제된 캠페인명

    Example:
        sanitize_campaign_name("  블프_신규!!!  ")  # "블프_신규"
    """
    if not name:
        return "Unknown"

    # 앞뒤 공백 제거
    name = name.strip()

    # 연속된 공백을 하나로
    name = re.sub(r'\s+', ' ', name)

    # 특수문자 제거 (언더스코어, 하이픈, 한글, 영문, 숫자만 허용)
    name = re.sub(r'[^\w\s\-가-힣]', '', name)

    return name if name else "Unknown"


def validate_upload_size(file_size, max_size_mb=10):
    """
    파일 크기 검증

    Args:
        file_size (int): 파일 크기 (bytes)
        max_size_mb (int): 최대 크기 (MB)

    Returns:
        tuple: (성공 여부, 에러 메시지)

    Example:
        valid, error = validate_upload_size(file.content_length)
        if not valid:
            return jsonify({'error': error}), 400
    """
    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        return False, f"파일 크기가 {max_size_mb}MB를 초과합니다."

    return True, None


def get_file_extension(filename):
    """
    파일 확장자 추출

    Args:
        filename (str): 파일명

    Returns:
        str: 확장자 (소문자, 점 제외)

    Example:
        get_file_extension("data.XLSX")  # "xlsx"
    """
    if not filename or '.' not in filename:
        return ""

    return filename.rsplit('.', 1)[1].lower()


def create_error_response(message, status_code=400):
    """
    에러 응답 생성 (API용)

    Args:
        message (str): 에러 메시지
        status_code (int): HTTP 상태 코드

    Returns:
        tuple: (dict, status_code)

    Example:
        return create_error_response("파일을 찾을 수 없습니다", 404)
    """
    return {
        'success': False,
        'error': message
    }, status_code


def create_success_response(data=None, message=None):
    """
    성공 응답 생성 (API용)

    Args:
        data (dict): 응답 데이터
        message (str): 성공 메시지

    Returns:
        dict: 응답 객체

    Example:
        return create_success_response({'snapshot_id': 123}, "업로드 성공")
    """
    response = {'success': True}

    if data:
        response.update(data)

    if message:
        response['message'] = message

    return response


def truncate_text(text, max_length=100, suffix='...'):
    """
    텍스트 잘라내기

    Args:
        text (str): 원본 텍스트
        max_length (int): 최대 길이
        suffix (str): 접미사

    Returns:
        str: 잘라낸 텍스트

    Example:
        truncate_text("매우 긴 텍스트" * 20, max_length=50)
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def ensure_directory_exists(directory):
    """
    디렉토리 존재 확인 및 생성

    Args:
        directory (str): 디렉토리 경로

    Example:
        ensure_directory_exists('/uploads')
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")
