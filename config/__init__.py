# ========================================
# Config Module
# ========================================
# 환경별 설정을 로드하는 팩토리 함수

import os
from .development import DevelopmentConfig
from .production import ProductionConfig


# 환경별 설정 매핑
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': DevelopmentConfig  # 테스트 환경은 개발 환경 설정 사용
}


def get_config():
    """
    환경 변수 FLASK_ENV에 따라 적절한 설정 객체 반환

    Returns:
        Config: 환경별 설정 객체
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
