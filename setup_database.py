"""
데이터베이스 테이블 생성 스크립트
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'mbizsquare'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'client_flag': pymysql.constants.CLIENT.MULTI_STATEMENTS
}

print("="*60)
print("🗄️  데이터베이스 테이블 생성")
print("="*60)

try:
    # 데이터베이스 연결
    print(f"\n연결 중: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("✅ 데이터베이스 연결 성공\n")

    # ========================================
    # 1. banners 테이블
    # ========================================
    print("📊 1. banners 테이블 생성...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banners (
            id INT PRIMARY KEY AUTO_INCREMENT,
            banner_type ENUM('home_top', 'home_bottom', 'home_grid', 'grid_general', 'grid_coupang', 'grid_profit', 'grid_efficiency', 'grid_keyword') NOT NULL,
            title VARCHAR(255) NOT NULL,
            image_url VARCHAR(500) NOT NULL,
            link_url VARCHAR(500) DEFAULT NULL,
            position_order INT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            start_date DATE DEFAULT NULL,
            end_date DATE DEFAULT NULL,
            click_count INT DEFAULT 0,
            impression_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_type_active (banner_type, is_active, position_order),
            INDEX idx_dates (start_date, end_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("   ✅ banners 테이블 생성 완료")

    # ========================================
    # 2. admin_users 테이블
    # ========================================
    print("\n👤 2. admin_users 테이블 생성...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_username (username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("   ✅ admin_users 테이블 생성 완료")

    # ========================================
    # 3. admin_sessions 테이블
    # ========================================
    print("\n🔐 3. admin_sessions 테이블 생성...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_sessions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            admin_id INT NOT NULL,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE,
            INDEX idx_token (session_token),
            INDEX idx_expires (expires_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("   ✅ admin_sessions 테이블 생성 완료")

    # ========================================
    # 4. banner_analytics 테이블
    # ========================================
    print("\n📈 4. banner_analytics 테이블 생성...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banner_analytics (
            id INT PRIMARY KEY AUTO_INCREMENT,
            banner_id INT NOT NULL,
            event_type ENUM('impression', 'click') NOT NULL,
            event_date DATE NOT NULL,
            event_count INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (banner_id) REFERENCES banners(id) ON DELETE CASCADE,
            UNIQUE KEY uk_banner_event_date (banner_id, event_type, event_date),
            INDEX idx_date (event_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("   ✅ banner_analytics 테이블 생성 완료")

    conn.commit()

    # ========================================
    # 5. 초기 관리자 계정 생성
    # ========================================
    print("\n👨‍💼 5. 초기 관리자 계정 생성...")

    # 이미 존재하는지 확인
    cursor.execute("SELECT COUNT(*) as count FROM admin_users WHERE username = 'admin'")
    result = cursor.fetchone()

    if result['count'] == 0:
        # bcrypt 해시: admin2024!@
        password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWTVNaNK5KxlXLWe'

        cursor.execute(
            "INSERT INTO admin_users (username, password_hash) VALUES (%s, %s)",
            ('admin', password_hash)
        )
        conn.commit()

        print("   ✅ 관리자 계정 생성 완료")
        print("   📝 아이디: admin")
        print("   📝 비밀번호: admin2024!@")
    else:
        print("   ℹ️  관리자 계정이 이미 존재합니다")

    # ========================================
    # 6. 테이블 확인
    # ========================================
    print("\n📋 생성된 테이블 목록:")

    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    banner_tables = ['banners', 'admin_users', 'admin_sessions', 'banner_analytics']

    for table in banner_tables:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        if cursor.fetchone():
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"   ✅ {table} ({count}개 레코드)")
        else:
            print(f"   ❌ {table} (없음)")

    cursor.close()
    conn.close()

    print("\n" + "="*60)
    print("✅ 데이터베이스 설정 완료!")
    print("="*60)
    print("\n이제 http://127.0.0.1:8080/admin/login 에서 로그인하세요")
    print("아이디: admin")
    print("비밀번호: admin2024!@\n")

except Exception as e:
    print(f"\n❌ 오류 발생: {str(e)}")
    print(f"오류 타입: {type(e).__name__}")
    import traceback
    traceback.print_exc()
