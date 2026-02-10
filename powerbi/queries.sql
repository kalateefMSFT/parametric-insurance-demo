-- ============================================================================
-- Power BI Data Source Queries
-- Optimized queries for Power BI DirectQuery and Import modes
-- ============================================================================

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- Claims Data (Main fact table)
-- Use this for real-time claims monitoring
SELECT 
    c.claim_id,
    c.policy_id,
    c.outage_event_id,
    c.status,
    c.filed_at,
    c.validated_at,
    c.approved_at,
    c.payout_amount,
    c.ai_confidence_score,
    c.ai_reasoning,
    DATEDIFF(MINUTE, c.filed_at, c.validated_at) as processing_time_minutes,
    DATEPART(HOUR, c.filed_at) as filed_hour,
    DATEPART(WEEKDAY, c.filed_at) as filed_weekday,
    CASE 
        WHEN c.status = 'approved' THEN 'Approved'
        WHEN c.status = 'denied' THEN 'Denied'
        WHEN c.status = 'pending' THEN 'Pending'
        WHEN c.status = 'validating' THEN 'Validating'
        ELSE 'Other'
    END as status_display
FROM claims c
WHERE c.filed_at >= DATEADD(MONTH, -6, GETUTCDATE());  -- Last 6 months


-- Payouts Data
SELECT 
    p.payout_id,
    p.claim_id,
    p.policy_id,
    p.amount,
    p.status,
    p.initiated_at,
    p.completed_at,
    p.payment_method,
    DATEDIFF(MINUTE, p.initiated_at, p.completed_at) as processing_time_minutes
FROM payouts p
WHERE p.initiated_at >= DATEADD(MONTH, -6, GETUTCDATE());


-- Outage Events Data
SELECT 
    o.event_id,
    o.utility_name,
    o.zip_code,
    o.latitude,
    o.longitude,
    o.affected_customers,
    o.outage_start,
    o.outage_end,
    o.duration_minutes,
    CAST(o.duration_minutes AS FLOAT) / 60 as duration_hours,
    o.status,
    o.cause,
    o.reported_cause,
    CASE 
        WHEN o.affected_customers >= 10000 THEN 'Critical'
        WHEN o.affected_customers >= 5000 THEN 'High'
        WHEN o.affected_customers >= 1000 THEN 'Medium'
        ELSE 'Low'
    END as severity_level
FROM outage_events o
WHERE o.outage_start >= DATEADD(MONTH, -6, GETUTCDATE());


-- Weather Data
SELECT 
    w.weather_id,
    w.event_id,
    w.zip_code,
    w.latitude,
    w.longitude,
    w.timestamp,
    w.temperature_f,
    w.wind_speed_mph,
    w.wind_gust_mph,
    w.precipitation_inches,
    w.humidity_percent,
    w.conditions,
    w.severe_weather_alert,
    w.alert_type,
    w.lightning_strikes,
    CASE 
        WHEN w.severe_weather_alert = 1 THEN 'Severe'
        WHEN w.wind_speed_mph > 40 THEN 'High'
        WHEN w.wind_speed_mph > 25 THEN 'Medium'
        ELSE 'Low'
    END as weather_severity
FROM weather_data w
WHERE w.timestamp >= DATEADD(MONTH, -6, GETUTCDATE());


-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Policies Dimension
SELECT 
    p.policy_id,
    p.business_name,
    p.business_type,
    p.zip_code,
    p.address,
    p.city,
    p.state,
    p.latitude,
    p.longitude,
    p.threshold_minutes,
    CAST(p.threshold_minutes AS FLOAT) / 60 as threshold_hours,
    p.hourly_rate,
    p.max_payout,
    p.status,
    p.effective_date,
    p.expiration_date,
    CASE 
        WHEN p.status = 'active' THEN 1
        ELSE 0
    END as is_active
FROM policies p;


-- Date Dimension (Create for time intelligence)
-- Run this once to create a date table
WITH DateRange AS (
    SELECT DATEADD(DAY, number, '2024-01-01') as Date
    FROM master..spt_values
    WHERE type = 'P' 
    AND number <= DATEDIFF(DAY, '2024-01-01', '2027-12-31')
)
SELECT 
    Date,
    YEAR(Date) as Year,
    MONTH(Date) as Month,
    DAY(Date) as Day,
    DATEPART(QUARTER, Date) as Quarter,
    DATEPART(WEEK, Date) as Week,
    DATEPART(WEEKDAY, Date) as Weekday,
    DATENAME(MONTH, Date) as MonthName,
    DATENAME(WEEKDAY, Date) as WeekdayName,
    CASE WHEN DATEPART(WEEKDAY, Date) IN (1, 7) THEN 1 ELSE 0 END as IsWeekend
FROM DateRange;


-- ============================================================================
-- AGGREGATED VIEWS (For Performance)
-- ============================================================================

-- Daily Claims Summary
SELECT 
    CAST(c.filed_at AS DATE) as claim_date,
    COUNT(*) as total_claims,
    SUM(CASE WHEN c.status = 'approved' THEN 1 ELSE 0 END) as approved_claims,
    SUM(CASE WHEN c.status = 'denied' THEN 1 ELSE 0 END) as denied_claims,
    SUM(CASE WHEN c.status IN ('pending', 'validating') THEN 1 ELSE 0 END) as pending_claims,
    AVG(c.payout_amount) as avg_payout,
    SUM(c.payout_amount) as total_payout,
    AVG(c.ai_confidence_score) as avg_confidence,
    AVG(DATEDIFF(MINUTE, c.filed_at, c.validated_at)) as avg_processing_time
FROM claims c
WHERE c.filed_at >= DATEADD(MONTH, -6, GETUTCDATE())
GROUP BY CAST(c.filed_at AS DATE);


-- Policy Performance Summary
SELECT 
    p.policy_id,
    p.business_name,
    p.city,
    p.state,
    p.business_type,
    COUNT(c.claim_id) as total_claims,
    SUM(CASE WHEN c.status = 'approved' THEN 1 ELSE 0 END) as approved_claims,
    SUM(pay.amount) as total_payout,
    AVG(pay.amount) as avg_payout,
    MAX(c.filed_at) as last_claim_date,
    AVG(c.ai_confidence_score) as avg_confidence
FROM policies p
LEFT JOIN claims c ON p.policy_id = c.policy_id
LEFT JOIN payouts pay ON c.claim_id = pay.claim_id
WHERE p.status = 'active'
GROUP BY p.policy_id, p.business_name, p.city, p.state, p.business_type;


-- Outage Impact Summary
SELECT 
    o.event_id,
    o.utility_name,
    o.zip_code,
    o.outage_start,
    o.duration_minutes,
    o.affected_customers,
    COUNT(DISTINCT c.policy_id) as policies_affected,
    COUNT(c.claim_id) as claims_filed,
    SUM(pay.amount) as total_payout,
    MAX(w.wind_speed_mph) as max_wind_speed,
    MAX(CASE WHEN w.severe_weather_alert = 1 THEN 1 ELSE 0 END) as had_severe_weather
FROM outage_events o
LEFT JOIN claims c ON o.event_id = c.outage_event_id
LEFT JOIN payouts pay ON c.claim_id = pay.claim_id
LEFT JOIN weather_data w ON o.event_id = w.event_id
WHERE o.outage_start >= DATEADD(MONTH, -6, GETUTCDATE())
GROUP BY o.event_id, o.utility_name, o.zip_code, o.outage_start, 
         o.duration_minutes, o.affected_customers;


-- ============================================================================
-- KPI QUERIES (For Card Visuals)
-- ============================================================================

-- Current Month Statistics
SELECT 
    COUNT(*) as claims_this_month,
    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_this_month,
    SUM(payout_amount) as payout_this_month,
    AVG(ai_confidence_score) as avg_confidence_this_month
FROM claims
WHERE filed_at >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETUTCDATE()), 0);


-- Real-Time Active Metrics
SELECT 
    (SELECT COUNT(*) FROM outage_events WHERE status = 'active') as active_outages,
    (SELECT COUNT(*) FROM claims WHERE status IN ('pending', 'validating')) as pending_claims,
    (SELECT COUNT(*) FROM policies WHERE status = 'active') as active_policies,
    (SELECT SUM(amount) FROM payouts WHERE status = 'processing') as pending_payouts;


-- Today's Activity
SELECT 
    (SELECT COUNT(*) FROM claims WHERE CAST(filed_at AS DATE) = CAST(GETUTCDATE() AS DATE)) as claims_today,
    (SELECT COUNT(*) FROM payouts WHERE CAST(initiated_at AS DATE) = CAST(GETUTCDATE() AS DATE)) as payouts_today,
    (SELECT SUM(amount) FROM payouts WHERE CAST(initiated_at AS DATE) = CAST(GETUTCDATE() AS DATE)) as payout_amount_today;


-- ============================================================================
-- TIME SERIES QUERIES (For Line Charts)
-- ============================================================================

-- Claims Trend (Last 30 Days)
SELECT 
    CAST(filed_at AS DATE) as date,
    COUNT(*) as claim_count,
    SUM(payout_amount) as total_payout,
    AVG(ai_confidence_score) as avg_confidence
FROM claims
WHERE filed_at >= DATEADD(DAY, -30, GETUTCDATE())
GROUP BY CAST(filed_at AS DATE)
ORDER BY CAST(filed_at AS DATE);


-- Hourly Claims Pattern (for identifying peak hours)
SELECT 
    DATEPART(HOUR, filed_at) as hour_of_day,
    COUNT(*) as claim_count,
    AVG(DATEDIFF(MINUTE, filed_at, validated_at)) as avg_processing_time
FROM claims
WHERE filed_at >= DATEADD(DAY, -7, GETUTCDATE())
GROUP BY DATEPART(HOUR, filed_at)
ORDER BY DATEPART(HOUR, filed_at);


-- ============================================================================
-- GEOGRAPHIC QUERIES (For Map Visuals)
-- ============================================================================

-- Active Outages with Location
SELECT 
    o.event_id,
    o.utility_name,
    o.latitude,
    o.longitude,
    o.zip_code,
    o.affected_customers,
    o.duration_minutes,
    o.outage_start,
    COUNT(c.claim_id) as related_claims,
    SUM(pay.amount) as total_payout
FROM outage_events o
LEFT JOIN claims c ON o.event_id = c.outage_event_id
LEFT JOIN payouts pay ON c.claim_id = pay.claim_id
WHERE o.status = 'active'
GROUP BY o.event_id, o.utility_name, o.latitude, o.longitude, 
         o.zip_code, o.affected_customers, o.duration_minutes, o.outage_start;


-- Policy Locations with Claims
SELECT 
    p.policy_id,
    p.business_name,
    p.latitude,
    p.longitude,
    p.city,
    p.state,
    COUNT(c.claim_id) as total_claims,
    SUM(pay.amount) as total_payout
FROM policies p
LEFT JOIN claims c ON p.policy_id = c.policy_id
LEFT JOIN payouts pay ON c.claim_id = pay.claim_id
WHERE p.status = 'active'
GROUP BY p.policy_id, p.business_name, p.latitude, p.longitude, p.city, p.state;


-- ============================================================================
-- AI INSIGHTS QUERIES
-- ============================================================================

-- AI Confidence vs Outcome
SELECT 
    ROUND(ai_confidence_score, 1) as confidence_bucket,
    COUNT(*) as claim_count,
    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_count,
    SUM(CASE WHEN status = 'denied' THEN 1 ELSE 0 END) as denied_count,
    AVG(payout_amount) as avg_payout
FROM claims
WHERE ai_confidence_score IS NOT NULL
GROUP BY ROUND(ai_confidence_score, 1)
ORDER BY ROUND(ai_confidence_score, 1);


-- Fraud Detection Summary
SELECT 
    c.claim_id,
    c.policy_id,
    p.business_name,
    c.filed_at,
    c.fraud_flags,
    c.status,
    c.ai_confidence_score
FROM claims c
JOIN policies p ON c.policy_id = p.policy_id
WHERE c.fraud_flags IS NOT NULL AND c.fraud_flags != '[]'
ORDER BY c.filed_at DESC;


-- ============================================================================
-- PERFORMANCE METRICS
-- ============================================================================

-- Processing Time Distribution
SELECT 
    CASE 
        WHEN DATEDIFF(MINUTE, filed_at, validated_at) <= 5 THEN '0-5 min'
        WHEN DATEDIFF(MINUTE, filed_at, validated_at) <= 15 THEN '5-15 min'
        WHEN DATEDIFF(MINUTE, filed_at, validated_at) <= 30 THEN '15-30 min'
        WHEN DATEDIFF(MINUTE, filed_at, validated_at) <= 60 THEN '30-60 min'
        ELSE '60+ min'
    END as processing_time_bucket,
    COUNT(*) as claim_count,
    AVG(ai_confidence_score) as avg_confidence
FROM claims
WHERE validated_at IS NOT NULL
GROUP BY CASE 
    WHEN DATEDIFF(MINUTE, filed_at, validated_at) <= 5 THEN '0-5 min'
    WHEN DATEDIFF(MINUTE, filed_at, validated_at) <= 15 THEN '5-15 min'
    WHEN DATEDIFF(MINUTE, filed_at, validated_at) <= 30 THEN '15-30 min'
    WHEN DATEDIFF(MINUTE, filed_at, validated_at) <= 60 THEN '30-60 min'
    ELSE '60+ min'
END;


-- ============================================================================
-- CREATING INDEXED VIEWS FOR PERFORMANCE
-- ============================================================================

-- Create indexed view for daily metrics
CREATE VIEW v_daily_metrics
WITH SCHEMABINDING
AS
SELECT 
    CAST(c.filed_at AS DATE) as claim_date,
    COUNT_BIG(*) as claim_count,
    SUM(ISNULL(c.payout_amount, 0)) as total_payout
FROM dbo.claims c
GROUP BY CAST(c.filed_at AS DATE);
GO

-- Create unique clustered index on the view
CREATE UNIQUE CLUSTERED INDEX IX_v_daily_metrics 
ON v_daily_metrics(claim_date);
GO


-- ============================================================================
-- NOTES FOR POWER BI SETUP
-- ============================================================================

/*
1. Use these queries as Custom SQL in Power BI for DirectQuery
2. For Import mode, use the aggregated views for better performance
3. Create relationships based on:
   - policies[policy_id] = claims[policy_id]
   - claims[claim_id] = payouts[claim_id]
   - claims[outage_event_id] = outage_events[event_id]
   - outage_events[event_id] = weather_data[event_id]

4. For real-time updates, use DirectQuery on main fact tables
5. For historical analysis, use Import mode with scheduled refresh
6. Combine both using Composite model for optimal performance
*/
