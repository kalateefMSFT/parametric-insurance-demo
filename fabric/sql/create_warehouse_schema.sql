-- Fabric DW compatibility notes:
--   * No PRIMARY/FOREIGN KEY or DEFAULT constraints
--   * No IDENTITY columns or manual indexes (Fabric auto-manages storage)
--   * No BIT or VARCHAR(MAX) types (use SMALLINT / VARCHAR(8000))
--   * No GO batch separators, PRINT statements, stored procedures, or triggers
--   * All temporal columns explicitly typed as DATETIME2(0)

-- Drop dependent views first
DROP VIEW IF EXISTS v_outage_impact;
DROP VIEW IF EXISTS v_policy_performance;
DROP VIEW IF EXISTS v_claim_statistics;
DROP VIEW IF EXISTS v_active_claims;

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
    fraud_flags VARCHAR(8000),
    created_at DATETIME2(0),
    updated_at DATETIME2(0)
);

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
GO
-- ============================================================================
-- ANALYTICS VIEWS
-- ============================================================================

CREATE VIEW v_active_claims AS
SELECT 
    c.claim_id,
    c.policy_id,
    p.business_name,
    c.status,
    c.filed_at,
    c.payout_amount,
    c.ai_confidence_score,
    o.utility_name,
    o.outage_start,
    o.duration_minutes,
    o.affected_customers
FROM claims c
INNER JOIN policies p ON c.policy_id = p.policy_id
INNER JOIN outage_events o ON c.outage_event_id = o.event_id
WHERE c.status IN ('pending', 'validating', 'approved');
GO
-- Claim Summary Statistics
CREATE VIEW v_claim_statistics AS
SELECT 
    COUNT(*) as total_claims,
    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_claims,
    SUM(CASE WHEN status = 'denied' THEN 1 ELSE 0 END) as denied_claims,
    SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_claims,
    AVG(CASE WHEN payout_amount IS NOT NULL THEN payout_amount END) as avg_payout,
    SUM(CASE WHEN payout_amount IS NOT NULL THEN payout_amount ELSE 0 END) as total_payout,
    AVG(ai_confidence_score) as avg_confidence_score
FROM claims
WHERE filed_at >= DATEADD(day, -30, SYSUTCDATETIME());
GO
-- Policy Performance View
CREATE VIEW v_policy_performance AS
SELECT 
    p.policy_id,
    p.business_name,
    p.zip_code,
    COUNT(c.claim_id) as claim_count,
    SUM(CASE WHEN c.status = 'approved' THEN 1 ELSE 0 END) as approved_count,
    SUM(c.payout_amount) as total_payout,
    AVG(c.payout_amount) as avg_payout,
    MAX(c.filed_at) as last_claim_date
FROM policies p
LEFT JOIN claims c ON p.policy_id = c.policy_id
WHERE p.status = 'active'
GROUP BY p.policy_id, p.business_name, p.zip_code;
GO
-- Outage Impact Analysis
CREATE VIEW v_outage_impact AS
SELECT 
    o.event_id,
    o.utility_name,
    o.zip_code,
    o.outage_start,
    o.duration_minutes,
    o.affected_customers,
    COUNT(DISTINCT c.policy_id) as policies_affected,
    COUNT(c.claim_id) as claims_filed,
    SUM(c.payout_amount) as total_payout_amount,
    w.severe_weather_alert,
    w.wind_speed_mph,
    w.conditions
FROM outage_events o
LEFT JOIN claims c ON o.event_id = c.outage_event_id
LEFT JOIN weather_data w ON o.event_id = w.event_id
WHERE o.status = 'active' OR o.outage_end >= DATEADD(day, -7, SYSUTCDATETIME())
GROUP BY o.event_id, o.utility_name, o.zip_code, o.outage_start, 
         o.duration_minutes, o.affected_customers, w.severe_weather_alert,
         w.wind_speed_mph, w.conditions;
GO

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

-- Get policies affected by outage
CREATE PROCEDURE sp_get_affected_policies
    @zip_code VARCHAR(10),
    @latitude DECIMAL(10, 8),
    @longitude DECIMAL(11, 8),
    @radius_miles DECIMAL(10, 2) = 10
AS
BEGIN
    -- Policies in same ZIP
    SELECT DISTINCT p.*
    FROM policies p
    WHERE p.zip_code = @zip_code
      AND p.status = 'active'
    
    UNION
    
    -- Policies within radius (Haversine formula)
    SELECT DISTINCT p.*
    FROM policies p
    WHERE p.status = 'active'
      AND (
          3959 * acos(
              cos(radians(@latitude)) * cos(radians(p.latitude)) * 
              cos(radians(p.longitude) - radians(@longitude)) + 
              sin(radians(@latitude)) * sin(radians(p.latitude))
          )
      ) <= @radius_miles;
END;

GO

-- Get claim processing metrics
CREATE PROCEDURE sp_get_claim_metrics
    @days INT = 30
AS
BEGIN
    SELECT 
        CAST(filed_at AS DATE) as claim_date,
        COUNT(*) as claims_filed,
        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
        SUM(CASE WHEN status = 'denied' THEN 1 ELSE 0 END) as denied,
        AVG(DATEDIFF(minute, filed_at, validated_at)) as avg_validation_time_minutes,
        SUM(payout_amount) as total_payout
    FROM claims
    WHERE filed_at >= DATEADD(day, -@days, GETUTCDATE())
    GROUP BY CAST(filed_at AS DATE)
    ORDER BY claim_date DESC;
END;

GO

-- ============================================================================
-- TRIGGERS FOR AUDIT
-- ============================================================================

-- Update timestamp trigger for policies
CREATE TRIGGER tr_policies_update
ON policies
AFTER UPDATE
AS
BEGIN
    UPDATE policies
    SET updated_at = GETUTCDATE()
    FROM policies p
    INNER JOIN inserted i ON p.policy_id = i.policy_id;
END;

GO

-- Update timestamp trigger for claims
CREATE TRIGGER tr_claims_update
ON claims
AFTER UPDATE
AS
BEGIN
    UPDATE claims
    SET updated_at = GETUTCDATE()
    FROM claims c
    INNER JOIN inserted i ON c.claim_id = i.claim_id;
END;

GO

-- ============================================================================
-- GRANT PERMISSIONS (adjust as needed)
-- ============================================================================

-- GRANT SELECT, INSERT, UPDATE ON policies TO [AppServicePrincipal];
-- GRANT SELECT, INSERT, UPDATE ON outage_events TO [AppServicePrincipal];
-- GRANT SELECT, INSERT, UPDATE ON claims TO [AppServicePrincipal];
-- GRANT SELECT, INSERT, UPDATE ON payouts TO [AppServicePrincipal];
-- GRANT SELECT ON v_active_claims TO [ReportingUser];
-- GRANT SELECT ON v_claim_statistics TO [ReportingUser];

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

-- Verify views
SELECT name 
FROM sys.views 
ORDER BY name;

-- Verify stored procedures
SELECT name 
FROM sys.procedures 
ORDER BY name;

