-- ========================================
-- Banner Management System Database Schema
-- ========================================
-- 배너 관리 시스템 데이터베이스 스키마
-- 생성일: 2024-11-20

-- 1. 배너 테이블
CREATE TABLE IF NOT EXISTS banners (
    id INT PRIMARY KEY AUTO_INCREMENT,
    banner_type ENUM('home_top', 'home_bottom', 'home_grid', 'grid_general', 'grid_coupang') NOT NULL COMMENT '배너 타입',
    title VARCHAR(255) NOT NULL COMMENT '배너 제목 (관리용)',
    image_url VARCHAR(500) NOT NULL COMMENT '업로드된 이미지 경로',
    link_url VARCHAR(500) DEFAULT NULL COMMENT '클릭 시 이동할 URL',
    position_order INT DEFAULT 0 COMMENT '정렬 순서 (1~8, 작을수록 앞)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성화 여부',
    start_date DATE DEFAULT NULL COMMENT '게시 시작일',
    end_date DATE DEFAULT NULL COMMENT '게시 종료일',
    click_count INT DEFAULT 0 COMMENT '총 클릭 수',
    impression_count INT DEFAULT 0 COMMENT '총 노출 수',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    INDEX idx_type_active (banner_type, is_active, position_order),
    INDEX idx_dates (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='배너 정보';

-- 2. 관리자 계정 테이블
CREATE TABLE IF NOT EXISTS admin_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '관리자 아이디',
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt 해시 비밀번호',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='관리자 계정';

-- 3. 관리자 세션 테이블
CREATE TABLE IF NOT EXISTS admin_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL COMMENT '관리자 ID',
    session_token VARCHAR(64) UNIQUE NOT NULL COMMENT '세션 토큰 (UUID)',
    expires_at TIMESTAMP NOT NULL COMMENT '만료 시간 (8시간)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE,
    INDEX idx_token (session_token),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='관리자 세션';

-- 4. 배너 클릭/노출 로그 테이블
CREATE TABLE IF NOT EXISTS banner_analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    banner_id INT NOT NULL COMMENT '배너 ID',
    event_type ENUM('impression', 'click') NOT NULL COMMENT '이벤트 타입',
    ip_address VARCHAR(45) DEFAULT NULL COMMENT '클라이언트 IP 주소',
    user_agent TEXT DEFAULT NULL COMMENT '브라우저 정보',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '발생일시',
    FOREIGN KEY (banner_id) REFERENCES banners(id) ON DELETE CASCADE,
    INDEX idx_banner_date (banner_id, created_at),
    INDEX idx_event_type (event_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='배너 분석 로그';

-- 완료 메시지
SELECT '✅ 배너 관리 시스템 데이터베이스 스키마 생성 완료' AS status;
