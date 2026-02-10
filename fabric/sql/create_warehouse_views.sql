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

-- Drop existing views first (depend on tables)
DROP VIEW IF EXISTS v_outage_impact;
DROP VIEW IF EXISTS v_policy_performance;
DROP VIEW IF EXISTS v_claim_statistics;
DROP VIEW IF EXISTS v_active_claims;

-- ============================================================================
-- ANALYTICS VIEWS
-- ============================================================================

-- Active Claims View
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
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify views
SELECT name 
FROM sys.views 
ORDER BY name;
