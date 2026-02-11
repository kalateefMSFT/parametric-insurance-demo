-- ============================================================================
-- Microsoft Fabric Data Warehouse Schema
-- Parametric Insurance Demo - Power Outage Business Interruption
-- ============================================================================
-- Fabric DW compatibility notes:
--   - No PRIMARY KEY, FOREIGN KEY, or DEFAULT constraints
--   - No IDENTITY columns, triggers, stored procedures, or indexes
--   - No VARCHAR(MAX) (use VARCHAR(8000)), no BIT (use SMALLINT)
--   - No GO batch separators or PRINT statements
--   - Fabric auto-manages storage and indexing via V-Order
-- ============================================================================

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS payouts;
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS weather_data;
DROP TABLE IF EXISTS social_signals;
DROP TABLE IF EXISTS outage_events;
DROP TABLE IF EXISTS outage_raw;
DROP TABLE IF EXISTS policies;

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Policies table
CREATE TABLE policies (
    policy_id VARCHAR(50) NOT NULL,
    business_name VARCHAR(200) NOT NULL,
    business_type VARCHAR(100),
    zip_code VARCHAR(10) NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(2),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    threshold_minutes INT NOT NULL,
    hourly_rate DECIMAL(10, 2) NOT NULL,
    max_payout DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20),
    effective_date DATETIME2(0),
    expiration_date DATETIME2(0),
    contact_email VARCHAR(200),
    contact_phone VARCHAR(20),
    created_at DATETIME2(0),
    updated_at DATETIME2(0)
);

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- Outage Events table
CREATE TABLE outage_events (
    event_id VARCHAR(100) NOT NULL,
    utility_name VARCHAR(200) NOT NULL,
    zip_code VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    affected_customers INT,
    outage_start DATETIME2(0) NOT NULL,
    outage_end DATETIME2(0),
    duration_minutes INT,
    status VARCHAR(20) NOT NULL,
    cause VARCHAR(100),
    reported_cause VARCHAR(100),
    data_source VARCHAR(50),
    last_updated DATETIME2(0),
    created_at DATETIME2(0)
);

-- Weather Data table
CREATE TABLE weather_data (
    weather_id INT,
    event_id VARCHAR(100),
    zip_code VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    [timestamp] DATETIME2(0) NOT NULL,
    temperature_f DECIMAL(5, 2),
    wind_speed_mph DECIMAL(5, 2),
    wind_gust_mph DECIMAL(5, 2),
    precipitation_inches DECIMAL(5, 2),
    humidity_percent INT,
    conditions VARCHAR(200),
    severe_weather_alert SMALLINT,
    alert_type VARCHAR(100),
    lightning_strikes INT,
    ingestion_timestamp DATETIME2(0)
);

-- Social Signals table (social media mentions)
CREATE TABLE social_signals (
    signal_id VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    [text] VARCHAR(500),
    zip_code VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    [timestamp] DATETIME2(0) NOT NULL,
    user_id VARCHAR(100),
    engagement_count INT,
    relevance_score DECIMAL(3, 2),
    event_id VARCHAR(100),
    created_at DATETIME2(0)
);

-- Claims table
CREATE TABLE claims (
    claim_id VARCHAR(100) NOT NULL,
    policy_id VARCHAR(50) NOT NULL,
    outage_event_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    filed_at DATETIME2(0),
    validated_at DATETIME2(0),
    approved_at DATETIME2(0),
    denied_at DATETIME2(0),
    denial_reason VARCHAR(500),
    payout_amount DECIMAL(12, 2),
    ai_confidence_score DECIMAL(3, 2),
    ai_reasoning VARCHAR(8000),
    fraud_flags VARCHAR(8000), -- JSON array
    created_at DATETIME2(0),
    updated_at DATETIME2(0)
);

-- Payouts table
CREATE TABLE payouts (
    payout_id VARCHAR(100) NOT NULL,
    claim_id VARCHAR(100) NOT NULL,
    policy_id VARCHAR(50) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    initiated_at DATETIME2(0),
    completed_at DATETIME2(0),
    transaction_id VARCHAR(100),
    payment_method VARCHAR(50),
    created_at DATETIME2(0)
);

-- ============================================================================
-- RAW DATA TABLE (for Lakehouse)
-- ============================================================================

-- Raw outage data from APIs
CREATE TABLE outage_raw (
    id INT,
    event_id VARCHAR(100),
    utility_name VARCHAR(200),
    state VARCHAR(2),
    affected_customers INT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    zip_code VARCHAR(10),
    data_source VARCHAR(50),
    raw_json VARCHAR(8000),
    last_updated DATETIME2(0),
    ingestion_timestamp DATETIME2(0)
);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify schema creation
SELECT 
    TABLE_NAME,
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = t.TABLE_NAME) as column_count
FROM INFORMATION_SCHEMA.TABLES t
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

