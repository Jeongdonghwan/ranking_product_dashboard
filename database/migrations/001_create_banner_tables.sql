-- ========================================
-- Banner Management System Database Schema
-- ========================================
-- 배너 관리 시스템 데이터베이스 스키마
-- 생성일: 2024-11-20
-- 수정일: 2024-12-02 (불필요한 admin 테이블 제거)
--
-- 참고: 관리자 인증은 기존 세션의 g.user.get('userId') == 'admin' 사용

-- 1. 배너 테이블
CREATE TABLE IF NOT EXISTS banners (
    id INT PRIMARY KEY AUTO_INCREMENT,
    banner_type ENUM('home_top', 'home_bottom', 'home_grid', 'grid_general', 'grid_coupang', 'grid_profit', 'grid_efficiency', 'grid_keyword') NOT NULL COMMENT '배너 타입',
    title VARCHAR(255) NOT NULL COMMENT '배너 제목 (관리용)',
    image_url VARCHAR(500) NOT NULL COMMENT '업로드된 이미지 경로 (데스크톱용)',
    mobile_image_url VARCHAR(500) DEFAULT NULL COMMENT '모바일용 이미지 (선택, 없으면 모바일에서 숨김)',
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

-- 2. 배너 클릭/노출 로그 테이블
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

-- 3. 기존 테이블에 mobile_image_url 컬럼 추가 (이미 있으면 무시)
-- ALTER TABLE banners ADD COLUMN IF NOT EXISTS mobile_image_url VARCHAR(500) DEFAULT NULL COMMENT '모바일용 이미지 (선택, 없으면 모바일에서 숨김)' AFTER image_url;
-- MariaDB에서는 IF NOT EXISTS가 안될 수 있으므로 아래 방식 사용:
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'banners' AND COLUMN_NAME = 'mobile_image_url') = 0,
    'ALTER TABLE banners ADD COLUMN mobile_image_url VARCHAR(500) DEFAULT NULL COMMENT "모바일용 이미지" AFTER image_url',
    'SELECT 1'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 완료 메시지
SELECT '✅ 배너 관리 시스템 데이터베이스 스키마 생성 완료' AS status;
