-- ============================================================
-- Opaline Attachment Defence System — Database Schema
-- Database: malicious_email
-- ============================================================

CREATE DATABASE IF NOT EXISTS malicious_email
    CHARACTER SET utf8
    COLLATE utf8_general_ci;

USE malicious_email;

-- ── 1. User (email account holders) ─────────────────────────
CREATE TABLE IF NOT EXISTS register (
    id       INT          PRIMARY KEY AUTO_INCREMENT,
    name     VARCHAR(100) NOT NULL,
    mobile   VARCHAR(15),
    uname    VARCHAR(100) NOT NULL UNIQUE,
    pass     VARCHAR(255) NOT NULL,
    created_at TIMESTAMP  DEFAULT CURRENT_TIMESTAMP
);

-- ── 2. Admin ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admin (
    id         INT          PRIMARY KEY AUTO_INCREMENT,
    username   VARCHAR(100) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ── 3. Email Configuration ───────────────────────────────────
CREATE TABLE IF NOT EXISTS email_config (
    config_id    INT          PRIMARY KEY AUTO_INCREMENT,
    user_id      INT          NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    smtp_server  VARCHAR(255) DEFAULT 'smtp.gmail.com',
    smtp_port    INT          DEFAULT 465,
    imap_server  VARCHAR(255) DEFAULT 'imap.gmail.com',
    imap_port    INT          DEFAULT 993,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES register(id) ON DELETE CASCADE
);

-- ── 4. CANet Model Training Data ─────────────────────────────
CREATE TABLE IF NOT EXISTS canet_model (
    training_id   INT          PRIMARY KEY AUTO_INCREMENT,
    dataset_name  VARCHAR(255) NOT NULL,
    feature_set   TEXT,
    training_data TEXT,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ── 5. Prediction Results ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS prediction (
    prediction_id        INT          PRIMARY KEY AUTO_INCREMENT,
    user_id              INT,
    email_id             INT,
    prediction_result    VARCHAR(255) COMMENT 'spam or ham',
    prediction_timestamp TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    model_version        VARCHAR(50)  DEFAULT 'CANet-v1',
    FOREIGN KEY (user_id) REFERENCES register(id) ON DELETE SET NULL
);

-- ── 6. Attachment Conversion Log ─────────────────────────────
CREATE TABLE IF NOT EXISTS attachment_conversion (
    conversion_id          INT          PRIMARY KEY AUTO_INCREMENT,
    email_id               INT,
    original_attachment    VARCHAR(255) COMMENT 'path to original file',
    converted_attachment   VARCHAR(255) COMMENT 'path to PNG image',
    conversion_status      VARCHAR(50)  DEFAULT 'Successful',
    conversion_timestamp   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ── 7. Security Alerts ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS security_alerts (
    alert_id        INT          PRIMARY KEY AUTO_INCREMENT,
    user_id         INT,
    email_id        INT,
    alert_message   TEXT,
    alert_type      VARCHAR(50)  COMMENT 'e.g. Malicious Attachment, Suspicious Activity',
    alert_timestamp TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    status          VARCHAR(50)  DEFAULT 'Pending',
    FOREIGN KEY (user_id) REFERENCES register(id) ON DELETE SET NULL
);

-- ── 8. Email Read / Scan Log ──────────────────────────────────
CREATE TABLE IF NOT EXISTS read_data (
    id         INT          PRIMARY KEY AUTO_INCREMENT,
    subject    VARCHAR(255),
    sender     VARCHAR(255),
    uname      VARCHAR(100),
    message    TEXT,
    spam_st    VARCHAR(10)  COMMENT '0 = spam, 1 = ham',
    filename   VARCHAR(255),
    img_count  INT          DEFAULT 0,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ── Default admin seed ────────────────────────────────────────
INSERT IGNORE INTO admin (username, password)
VALUES ('admin', 'admin123');
