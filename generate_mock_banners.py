"""
Mock 배너 이미지 생성 스크립트
- 970x90 (홈 상단/하단)
- 728x90 (대체 사이즈)
- 200x60 (그리드 배너)
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
from PIL import Image, ImageDraw, ImageFont

def create_mock_banner(width, height, text, filename, bg_color=(52, 152, 219)):
    """Mock 배너 이미지 생성"""

    # 이미지 생성
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 테두리 추가
    border_color = (41, 128, 185)
    draw.rectangle([(0, 0), (width-1, height-1)], outline=border_color, width=3)

    # 텍스트 추가 (중앙 정렬)
    try:
        # 시스템 폰트 사용 시도
        font_size = min(height // 3, 24)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # 폰트 로드 실패 시 기본 폰트
        font = ImageFont.load_default()

    # 텍스트 크기 계산
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 중앙 위치 계산
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # 텍스트 그림자
    draw.text((x+2, y+2), text, font=font, fill=(0, 0, 0, 128))
    # 실제 텍스트
    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    # 저장
    img.save(filename)
    print(f'✅ 생성됨: {filename} ({width}x{height})')


def main():
    # 디렉토리 생성
    output_dir = 'app/static/images/mock'
    os.makedirs(output_dir, exist_ok=True)

    print('='*60)
    print('Mock 배너 이미지 생성 시작')
    print('='*60)

    # 배너 이미지 생성
    create_mock_banner(
        970, 90,
        'Mock Banner 970x90',
        f'{output_dir}/banner_970x90.png',
        bg_color=(52, 152, 219)  # 파란색
    )

    create_mock_banner(
        728, 90,
        'Mock Banner 728x90',
        f'{output_dir}/banner_728x90.png',
        bg_color=(46, 204, 113)  # 초록색
    )

    create_mock_banner(
        200, 60,
        'Grid Banner',
        f'{output_dir}/banner_200x60.png',
        bg_color=(155, 89, 182)  # 보라색
    )

    print('='*60)
    print('✅ 모든 Mock 배너 이미지 생성 완료!')
    print('='*60)
    print(f'저장 위치: {output_dir}/')
    print('- banner_970x90.png (홈 상단/하단 배너)')
    print('- banner_728x90.png (대체 사이즈)')
    print('- banner_200x60.png (그리드 배너)')


if __name__ == '__main__':
    main()
