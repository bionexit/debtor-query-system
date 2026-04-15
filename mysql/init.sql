-- Debtor Query System Database Initialization Script
-- MySQL 8.0+

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS debtor_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE debtor_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'operator', 'viewer') DEFAULT 'operator',
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,
    failed_login_attempts INT DEFAULT 0,
    locked_until DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Debtors table
CREATE TABLE IF NOT EXISTS debtors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    id_card VARCHAR(18) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    address VARCHAR(255),
    debt_amount FLOAT DEFAULT 0.0,
    status ENUM('active', 'blacklisted', 'cleared') DEFAULT 'active',
    remark TEXT,
    batch_id INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_id_card (id_card),
    INDEX idx_phone (phone),
    FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Batches table
CREATE TABLE IF NOT EXISTS batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_no VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    total_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    fail_count INT DEFAULT 0,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_batch_no (batch_no),
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Vouchers table
CREATE TABLE IF NOT EXISTS vouchers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    total_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    fail_count INT DEFAULT 0,
    error_details TEXT,
    uploaded_by INT,
    reviewed_by INT,
    reviewed_at DATETIME,
    review_comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SMS Templates table
CREATE TABLE IF NOT EXISTS sms_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    variables VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SMS Channels table
CREATE TABLE IF NOT EXISTS channels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    endpoint VARCHAR(500),
    api_key VARCHAR(255),
    status ENUM('active', 'inactive', 'testing') DEFAULT 'testing',
    priority INT DEFAULT 1,
    success_rate FLOAT DEFAULT 0.0,
    avg_response_time FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SMS Tasks table
CREATE TABLE IF NOT EXISTS sms_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_no VARCHAR(50) NOT NULL UNIQUE,
    template_id INT,
    channel_id INT,
    recipient_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    fail_count INT DEFAULT 0,
    status ENUM('pending', 'sent', 'failed', 'delivered') DEFAULT 'pending',
    scheduled_at DATETIME,
    sent_at DATETIME,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task_no (task_no),
    FOREIGN KEY (template_id) REFERENCES sms_templates(id) ON DELETE SET NULL,
    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SMS Logs table
CREATE TABLE IF NOT EXISTS sms_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT,
    phone VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    provider_msg_id VARCHAR(100),
    error_message TEXT,
    sent_at DATETIME,
    delivered_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone (phone),
    INDEX idx_task_id (task_id),
    FOREIGN KEY (task_id) REFERENCES sms_tasks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- H5 Users table
CREATE TABLE IF NOT EXISTS h5_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(50),
    id_card VARCHAR(18),
    captcha VARCHAR(10),
    captcha_expire_at DATETIME,
    verification_attempts INT DEFAULT 0,
    is_locked BOOLEAN DEFAULT FALSE,
    locked_until DATETIME,
    last_query_at DATETIME,
    daily_query_count INT DEFAULT 0,
    query_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Partners table
CREATE TABLE IF NOT EXISTS partners (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    api_key VARCHAR(100) NOT NULL UNIQUE,
    secret_key VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit INT DEFAULT 100,
    daily_limit INT DEFAULT 10000,
    today_usage INT DEFAULT 0,
    last_used_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_api_key (api_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Debt Info table
CREATE TABLE IF NOT EXISTS debt_infos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    h5_user_id INT NOT NULL,
    debtor_id INT NOT NULL,
    query_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    result_code VARCHAR(20),
    result_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_h5_user_id (h5_user_id),
    INDEX idx_debtor_id (debtor_id),
    FOREIGN KEY (h5_user_id) REFERENCES h5_users(id) ON DELETE CASCADE,
    FOREIGN KEY (debtor_id) REFERENCES debtors(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payment Accounts table
CREATE TABLE IF NOT EXISTS payment_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL,
    account_no VARCHAR(50) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    bank_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Configs table
CREATE TABLE IF NOT EXISTS configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    changed_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_config_key (config_key),
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Config Change Logs table
CREATE TABLE IF NOT EXISTS config_change_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_id INT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by INT,
    change_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_config_id (config_id),
    FOREIGN KEY (config_id) REFERENCES configs(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, role, is_active)
VALUES ('admin', 'admin@debtor.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiiGTMwFYjOa', 'admin', TRUE)
ON DUPLICATE KEY UPDATE username = username;

-- Insert default SMS channel for mock server
INSERT INTO channels (name, provider, endpoint, api_key, status, is_active)
VALUES ('Mock SMS Provider', 'mock', 'http://sms-mock:8001/api/send', 'mock-sms-api-key', 'active', TRUE)
ON DUPLICATE KEY UPDATE name = name;

-- Insert default config
INSERT INTO configs (config_key, config_value, description)
VALUES ('system_version', '1.0.0', 'System version')
ON DUPLICATE KEY UPDATE config_key = config_key;
