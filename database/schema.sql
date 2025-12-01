-- ========================================
-- 광고 분석 대시보드 데이터베이스 스키마
-- ========================================
-- 생성일: 2024-11-12
-- 데이터베이스: mbizsquare
-- 인코딩: utf8mb4 (한글 지원)
--
-- 주의사항:
-- 1. 기존 users 테이블이 있어야 함
-- 2. user_id는 VARCHAR(20) 타입
-- 3. 기존 테이블이 있으면 DROP 후 재생성
-- ========================================

-- 기존 테이블 존재 확인 및 삭제 (주의!)
-- DROP TABLE IF EXISTS ad_daily_data;
-- DROP TABLE IF EXISTS ad_campaign_memos;
-- DROP TABLE IF EXISTS ad_monthly_goals;
-- DROP TABLE IF EXISTS ad_analysis_snapshots;

-- ========================================
-- 1. 광고 분석 스냅샷 테이블
-- ========================================
CREATE TABLE IF NOT EXISTS ad_analysis_snapshots (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '스냅샷 ID',
    user_id VARCHAR(20) NOT NULL COMMENT '사용자 ID (users.user_id 참조)',
    snapshot_name VARCHAR(255) NOT NULL COMMENT '분석 이름',
    period_start DATE NOT NULL COMMENT '분석 시작일',
    period_end DATE NOT NULL COMMENT '분석 종료일',
    data_json TEXT NOT NULL COMMENT '원본 데이터 (JSON 형식)',
    metrics_summary JSON COMMENT '계산된 지표 (캐싱용)',
    ai_insights TEXT COMMENT 'AI 생성 인사이트',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    is_saved BOOLEAN DEFAULT FALSE COMMENT '사용자 저장 여부 (true: 저장됨, false: 임시)',
    tags VARCHAR(255) COMMENT '태그 (쉼표 구분, 예: "블프,신규캠페인")',
    memo TEXT COMMENT '사용자 메모',

    -- 외래키 (users 테이블 참조)
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,

    -- 인덱스
    INDEX idx_user_date (user_id, period_start, period_end) COMMENT '사용자별 기간 검색',
    INDEX idx_saved (user_id, is_saved) COMMENT '저장된 분석 필터링',
    INDEX idx_created (created_at) COMMENT '생성일시 정렬'

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='광고 분석 스냅샷 - 각 분석 세션을 저장';


-- ========================================
-- 2. 일별 광고 데이터 테이블
-- ========================================
CREATE TABLE IF NOT EXISTS ad_daily_data (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '데이터 ID',
    snapshot_id INT NOT NULL COMMENT '스냅샷 ID (ad_analysis_snapshots.id 참조)',
    date DATE NOT NULL COMMENT '날짜',
    campaign_name VARCHAR(255) NOT NULL COMMENT '캠페인명',

    -- 광고 지표
    spend DECIMAL(12, 2) NOT NULL COMMENT '지출액 (원)',
    impressions INT DEFAULT 0 COMMENT '노출수',
    clicks INT DEFAULT 0 COMMENT '클릭수',
    conversions INT DEFAULT 0 COMMENT '전환수 (구매)',
    revenue DECIMAL(12, 2) DEFAULT 0 COMMENT '매출액 (원)',

    -- 외래키 (CASCADE 삭제: 스냅샷 삭제 시 일별 데이터도 자동 삭제)
    FOREIGN KEY (snapshot_id) REFERENCES ad_analysis_snapshots(id) ON DELETE CASCADE,

    -- 인덱스
    INDEX idx_snapshot_date (snapshot_id, date) COMMENT '스냅샷별 일별 데이터 조회',
    INDEX idx_campaign (campaign_name) COMMENT '캠페인별 검색',
    INDEX idx_date (date) COMMENT '날짜별 검색'

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='일별 광고 데이터 - 스냅샷의 상세 데이터';


-- ========================================
-- 3. 캠페인 메모 테이블
-- ========================================
CREATE TABLE IF NOT EXISTS ad_campaign_memos (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '메모 ID',
    user_id VARCHAR(20) NOT NULL COMMENT '사용자 ID',
    campaign_name VARCHAR(255) NOT NULL COMMENT '캠페인명',
    memo TEXT NOT NULL COMMENT '메모 내용',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '작성일시',

    -- 외래키
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,

    -- 인덱스
    INDEX idx_user_campaign (user_id, campaign_name) COMMENT '사용자별 캠페인 메모 조회',
    INDEX idx_created (created_at) COMMENT '작성일시 정렬'

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='캠페인 메모 - 특정 캠페인에 대한 사용자 메모';


-- ========================================
-- 4. 월별 목표 테이블
-- ========================================
CREATE TABLE IF NOT EXISTS ad_monthly_goals (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '목표 ID',
    user_id VARCHAR(20) NOT NULL COMMENT '사용자 ID',
    year_month VARCHAR(7) NOT NULL COMMENT '대상 월 (YYYY-MM 형식)',

    -- 목표 지표
    budget DECIMAL(12, 2) COMMENT '월 예산 (원)',
    target_roas DECIMAL(5, 2) COMMENT '목표 ROAS (예: 4.0 = 광고비 대비 4배 매출)',
    target_revenue DECIMAL(12, 2) COMMENT '목표 매출 (원)',

    -- 외래키
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,

    -- 유니크 제약 (한 사용자는 한 달에 하나의 목표만)
    UNIQUE KEY uk_user_month (user_id, year_month) COMMENT '사용자별 월 단위 유니크',

    -- 인덱스
    INDEX idx_year_month (year_month) COMMENT '월별 검색'

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='월별 목표 설정 - 예산 및 목표 ROAS';


-- ========================================
-- 샘플 데이터 (선택적)
-- ========================================

-- 주석 해제하여 테스트 데이터 삽입 가능
/*
-- 샘플 스냅샷 (user_id가 실제로 존재해야 함)
INSERT INTO ad_analysis_snapshots
(user_id, snapshot_name, period_start, period_end, data_json, is_saved, tags)
VALUES
('test_user', '11월 1주차 테스트', '2024-11-04', '2024-11-10', '[]', true, '테스트,샘플');

-- 샘플 일별 데이터
INSERT INTO ad_daily_data
(snapshot_id, date, campaign_name, spend, impressions, clicks, conversions, revenue)
VALUES
(1, '2024-11-04', '블프_신규', 150000, 45000, 1200, 48, 540000),
(1, '2024-11-05', '블프_신규', 160000, 48000, 1300, 52, 580000),
(1, '2024-11-04', '기존고객_A', 80000, 20000, 800, 30, 360000);

-- 샘플 목표
INSERT INTO ad_monthly_goals
(user_id, year_month, budget, target_roas, target_revenue)
VALUES
('test_user', '2024-11', 10000000, 4.0, 40000000);

-- 샘플 메모
INSERT INTO ad_campaign_memos
(user_id, campaign_name, memo)
VALUES
('test_user', '블프_신규', '소재 #3으로 교체 예정');
*/


-- ========================================
-- 데이터베이스 상태 확인 쿼리
-- ========================================

-- 생성된 테이블 확인
-- SHOW TABLES LIKE 'ad_%';

-- 테이블 구조 확인
-- DESCRIBE ad_analysis_snapshots;
-- DESCRIBE ad_daily_data;
-- DESCRIBE ad_campaign_memos;
-- DESCRIBE ad_monthly_goals;

-- 인덱스 확인
-- SHOW INDEX FROM ad_analysis_snapshots;
-- SHOW INDEX FROM ad_daily_data;

-- 외래키 확인
-- SELECT
--     TABLE_NAME,
--     COLUMN_NAME,
--     CONSTRAINT_NAME,
--     REFERENCED_TABLE_NAME,
--     REFERENCED_COLUMN_NAME
-- FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
-- WHERE TABLE_SCHEMA = 'mbizsquare'
--   AND TABLE_NAME LIKE 'ad_%'
--   AND REFERENCED_TABLE_NAME IS NOT NULL;

-- 테이블 크기 확인
-- SELECT
--     table_name AS '테이블',
--     ROUND(((data_length + index_length) / 1024 / 1024), 2) AS '크기 (MB)',
--     table_rows AS '행 수'
-- FROM information_schema.TABLES
-- WHERE table_schema = 'mbizsquare'
--   AND table_name LIKE 'ad_%';


-- ========================================
-- 스키마 업데이트 히스토리
-- ========================================
-- v1.0 (2024-11-12): 초기 스키마 생성
--   - user_id VARCHAR(20)으로 수정 (기존 users 테이블 구조 반영)
--   - 4개 테이블 생성
--   - 인덱스 최적화
--   - CASCADE 삭제 설정
