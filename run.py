#!/usr/bin/env python3
# ========================================
# Application Entry Point
# ========================================
# Flask 애플리케이션 실행 스크립트

import os
from app import create_app

# Flask 앱 생성
app = create_app()

if __name__ == '__main__':
    # 개발 서버 실행
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 8080))  # 포트 변경: 5000 → 8080

    app.logger.info(f"개발 서버 시작: http://{host}:{port}")
    app.logger.info("Ctrl+C로 종료할 수 있습니다.")

    app.run(
        host=host,
        port=port,
        debug=app.config['DEBUG'],
        threaded=True
    )
