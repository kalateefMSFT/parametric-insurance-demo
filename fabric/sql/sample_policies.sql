-- ============================================================================
-- Sample Policies for Parametric Insurance Demo
-- Power Outage Business Interruption
-- ============================================================================

-- Clear existing sample data
DELETE FROM payouts WHERE policy_id LIKE 'BI-%';
DELETE FROM claims WHERE policy_id LIKE 'BI-%';
DELETE FROM policies WHERE policy_id LIKE 'BI-%';

-- ============================================================================
-- Seattle, WA Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone
) VALUES
(
    'BI-001',
    'Pike Place Coffee Co',
    'Coffee Shop',
    '98101',
    '123 Pike St',
    'Seattle',
    'WA',
    47.6097,
    -122.3425,
    120,  -- 2 hour threshold
    500,  -- $500/hour
    10000,  -- $10,000 max
    'active',
    '2026-01-01',
    'owner@pikeplacecoffee.com',
    '206-555-0101'
),
(
    'BI-002',
    'Broadway Restaurant & Bar',
    'Restaurant',
    '98102',
    '456 Broadway Ave E',
    'Seattle',
    'WA',
    47.6234,
    -122.3212,
    60,   -- 1 hour threshold (restaurant loses more during peak hours)
    750,  -- $750/hour
    15000,  -- $15,000 max
    'active',
    '2026-01-01',
    'manager@broadwayrestaurant.com',
    '206-555-0102'
),
(
    'BI-003',
    'Capitol Hill Fitness Center',
    'Gym',
    '98102',
    '789 E Pine St',
    'Seattle',
    'WA',
    47.6145,
    -122.3201,
    180,  -- 3 hour threshold
    300,  -- $300/hour
    8000,  -- $8,000 max
    'active',
    '2026-01-01',
    'info@capitolhillfitness.com',
    '206-555-0103'
);

-- ============================================================================
-- Portland, OR Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone
) VALUES
(
    'BI-004',
    'Downtown Portland Bakery',
    'Bakery',
    '97201',
    '321 SW Morrison St',
    'Portland',
    'OR',
    45.5202,
    -122.6742,
    90,   -- 1.5 hour threshold
    600,  -- $600/hour
    12000,  -- $12,000 max
    'active',
    '2026-01-01',
    'baker@portlandbakery.com',
    '503-555-0104'
),
(
    'BI-005',
    'Pearl District Co-Working',
    'Co-Working Space',
    '97209',
    '555 NW 13th Ave',
    'Portland',
    'OR',
    45.5276,
    -122.6847,
    240,  -- 4 hour threshold
    400,  -- $400/hour
    20000,  -- $20,000 max
    'active',
    '2026-01-01',
    'admin@pearlcowork.com',
    '503-555-0105'
);

-- ============================================================================
-- San Francisco, CA Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone
) VALUES
(
    'BI-006',
    'Mission District Brewery',
    'Brewery',
    '94110',
    '888 Valencia St',
    'San Francisco',
    'CA',
    37.7599,
    -122.4214,
    120,  -- 2 hour threshold
    900,  -- $900/hour (high revenue business)
    25000,  -- $25,000 max
    'active',
    '2026-01-01',
    'owner@missionbrewery.com',
    '415-555-0106'
),
(
    'BI-007',
    'Financial District Data Center',
    'Data Center',
    '94111',
    '100 California St',
    'San Francisco',
    'CA',
    37.7935,
    -122.3989,
    30,   -- 30 minute threshold (critical infrastructure)
    2000, -- $2,000/hour (very high revenue impact)
    50000,  -- $50,000 max
    'active',
    '2026-01-01',
    'ops@fdatacenter.com',
    '415-555-0107'
);

-- ============================================================================
-- Los Angeles, CA Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone
) VALUES
(
    'BI-008',
    'Santa Monica Beach Cafe',
    'Cafe',
    '90401',
    '1550 Ocean Ave',
    'Santa Monica',
    'CA',
    34.0195,
    -118.4912,
    90,   -- 1.5 hour threshold
    550,  -- $550/hour
    10000,  -- $10,000 max
    'active',
    '2026-01-01',
    'info@beachcafe.com',
    '310-555-0108'
),
(
    'BI-009',
    'Hollywood Production Studio',
    'Production Studio',
    '90028',
    '6500 Sunset Blvd',
    'Los Angeles',
    'CA',
    34.0983,
    -118.3267,
    60,   -- 1 hour threshold (time-sensitive production)
    1500, -- $1,500/hour
    40000,  -- $40,000 max
    'active',
    '2026-01-01',
    'production@hollywoodstudio.com',
    '323-555-0109'
);

-- ============================================================================
-- New York, NY Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone
) VALUES
(
    'BI-010',
    'Manhattan Fine Dining',
    'Restaurant',
    '10022',
    '300 Park Ave',
    'New York',
    'NY',
    40.7614,
    -73.9776,
    45,   -- 45 minute threshold (high-end restaurant)
    1200, -- $1,200/hour
    30000,  -- $30,000 max
    'active',
    '2026-01-01',
    'reservations@manhattanfine.com',
    '212-555-0110'
),
(
    'BI-011',
    'Brooklyn Artisan Market',
    'Retail',
    '11211',
    '200 Bedford Ave',
    'Brooklyn',
    'NY',
    40.7181,
    -73.9571,
    120,  -- 2 hour threshold
    400,  -- $400/hour
    9000,  -- $9,000 max
    'active',
    '2026-01-01',
    'market@brooklynartisan.com',
    '718-555-0111'
);

-- ============================================================================
-- Test/Demo Policy (Expired)
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, expiration_date, contact_email, contact_phone
) VALUES
(
    'BI-999',
    'Test Business - EXPIRED',
    'Test',
    '98101',
    '999 Test St',
    'Seattle',
    'WA',
    47.6062,
    -122.3321,
    60,
    100,
    1000,
    'expired',
    '2025-01-01',
    '2025-12-31',
    'test@example.com',
    '555-555-5555'
);

-- ============================================================================
-- Verification
-- ============================================================================

-- Show all policies
SELECT 
    policy_id,
    business_name,
    city,
    state,
    zip_code,
    threshold_minutes,
    hourly_rate,
    max_payout,
    status
FROM policies
WHERE policy_id LIKE 'BI-%'
  AND status = 'active'
ORDER BY city, business_name;

-- Summary statistics
SELECT 
    COUNT(*) as total_policies,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_policies,
    AVG(threshold_minutes) as avg_threshold_minutes,
    AVG(hourly_rate) as avg_hourly_rate,
    AVG(max_payout) as avg_max_payout,
    SUM(max_payout) as total_max_exposure
FROM policies
WHERE policy_id LIKE 'BI-%';

-- Policies by city
SELECT 
    city,
    state,
    COUNT(*) as policy_count,
    AVG(hourly_rate) as avg_rate,
    SUM(max_payout) as total_exposure
FROM policies
WHERE policy_id LIKE 'BI-%'
  AND status = 'active'
GROUP BY city, state
ORDER BY policy_count DESC, city;

-- Policies by business type
SELECT 
    business_type,
    COUNT(*) as count,
    AVG(threshold_minutes) as avg_threshold,
    AVG(hourly_rate) as avg_rate
FROM policies
WHERE policy_id LIKE 'BI-%'
  AND status = 'active'
GROUP BY business_type
ORDER BY avg_rate DESC;

PRINT 'Sample policies created successfully!';
PRINT 'Total policies: ' + CAST((SELECT COUNT(*) FROM policies WHERE policy_id LIKE 'BI-%' AND status = 'active') AS VARCHAR);
