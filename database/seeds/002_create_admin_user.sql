-- ========================================
-- Initial Admin User Creation
-- ========================================
-- 초기 관리자 계정 생성
-- 생성일: 2024-11-20

-- Username: admin
-- Password: admin2024!@
-- Bcrypt hash: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWTVNaNK5KxlXLWe

INSERT INTO admin_users (username, password_hash)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWTVNaNK5KxlXLWe')
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash);

-- 완료 메시지
SELECT '✅ 초기 관리자 계정 생성 완료' AS status;
SELECT 'Username: admin' AS info;
SELECT 'Password: admin2024!@' AS info;
SELECT '⚠️  보안을 위해 첫 로그인 후 비밀번호를 변경하세요!' AS warning;
