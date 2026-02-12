-- ============================================================================
-- Additional Sample Policies for Parametric Insurance Demo
-- Power Outage Business Interruption
-- 40 New Policies (BI-012 through BI-051)
-- ============================================================================
-- Fabric DW compatibility:
--   - Each INSERT uses a single-row VALUES clause
--   - No PRINT statements
--   - Explicit created_at/updated_at values (no DEFAULT constraints)
-- ============================================================================

-- ============================================================================
-- Chicago, IL Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-012', 'Magnificent Mile Steakhouse', 'Restaurant', '60611',
    '401 N Michigan Ave', 'Chicago', 'IL', 41.8902, -87.6245,
    60, 900, 20000, 'active', '2026-01-01',
    'manager@magmilesteaks.com', '312-555-0112', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-013', 'Loop Data Solutions', 'Data Center', '60601',
    '200 E Randolph St', 'Chicago', 'IL', 41.8855, -87.6196,
    30, 2500, 75000, 'active', '2026-01-01',
    'ops@loopdata.com', '312-555-0113', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-014', 'Wicker Park Craft Brewery', 'Brewery', '60622',
    '1515 N Milwaukee Ave', 'Chicago', 'IL', 41.9087, -87.6742,
    120, 550, 12000, 'active', '2026-01-01',
    'brew@wickerparkcraft.com', '312-555-0114', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-015', 'Lincoln Park Veterinary Clinic', 'Veterinary Clinic', '60614',
    '2340 N Clark St', 'Chicago', 'IL', 41.9260, -87.6398,
    90, 700, 15000, 'active', '2026-01-01',
    'vet@lincolnparkvet.com', '312-555-0115', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Miami, FL Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-016', 'South Beach Luxury Hotel', 'Hotel', '33139',
    '1000 Ocean Dr', 'Miami Beach', 'FL', 25.7826, -80.1310,
    60, 2000, 50000, 'active', '2026-01-01',
    'gm@southbeachluxury.com', '305-555-0116', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-017', 'Brickell Financial Services', 'Financial Services', '33131',
    '701 Brickell Ave', 'Miami', 'FL', 25.7650, -80.1901,
    30, 1800, 45000, 'active', '2026-01-01',
    'admin@brickellfinancial.com', '305-555-0117', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-018', 'Wynwood Art Gallery', 'Art Gallery', '33127',
    '2520 NW 2nd Ave', 'Miami', 'FL', 25.8019, -80.1992,
    180, 350, 8000, 'active', '2026-01-01',
    'curator@wynwoodgallery.com', '305-555-0118', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-019', 'Little Havana Pharmacy', 'Pharmacy', '33135',
    '1600 SW 8th St', 'Miami', 'FL', 25.7655, -80.2155,
    60, 800, 18000, 'active', '2026-01-01',
    'rx@littlehavanapharmacy.com', '305-555-0119', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Houston, TX Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-020', 'Galleria Medical Center', 'Medical Office', '77056',
    '5015 Westheimer Rd', 'Houston', 'TX', 29.7374, -95.4612,
    45, 1500, 35000, 'active', '2026-01-01',
    'admin@galleriamedical.com', '713-555-0120', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-021', 'Heights BBQ Smokehouse', 'Restaurant', '77008',
    '710 W 19th St', 'Houston', 'TX', 29.8024, -95.3989,
    90, 650, 14000, 'active', '2026-01-01',
    'pitmaster@heightsbbq.com', '713-555-0121', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-022', 'Energy Corridor Tech Hub', 'Co-Working Space', '77079',
    '14100 Park Row', 'Houston', 'TX', 29.7601, -95.6145,
    120, 500, 15000, 'active', '2026-01-01',
    'info@energycorridorhub.com', '713-555-0122', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-023', 'Montrose Pet Grooming Spa', 'Pet Services', '77006',
    '1220 Westheimer Rd', 'Houston', 'TX', 29.7432, -95.3899,
    120, 300, 7000, 'active', '2026-01-01',
    'paws@montrosepetspa.com', '713-555-0123', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Denver, CO Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-024', 'LoDo Dispensary & Wellness', 'Retail', '80202',
    '1600 Wazee St', 'Denver', 'CO', 39.7530, -104.9992,
    90, 600, 13000, 'active', '2026-01-01',
    'shop@lodowellness.com', '303-555-0124', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-025', 'RiNo Artisan Bakery', 'Bakery', '80205',
    '2901 Blake St', 'Denver', 'CO', 39.7621, -104.9811,
    120, 450, 10000, 'active', '2026-01-01',
    'baker@rinobakery.com', '303-555-0125', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-026', 'Cherry Creek Dental Practice', 'Dental Office', '80206',
    '222 Milwaukee St', 'Denver', 'CO', 39.7170, -104.9553,
    60, 850, 20000, 'active', '2026-01-01',
    'office@cherrycreekdental.com', '303-555-0126', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Boston, MA Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-027', 'Faneuil Hall Seafood Market', 'Seafood Market', '02109',
    '1 Faneuil Hall Sq', 'Boston', 'MA', 42.3601, -71.0545,
    60, 1000, 22000, 'active', '2026-01-01',
    'sales@faneuilseafood.com', '617-555-0127', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-028', 'Cambridge Biotech Lab', 'Laboratory', '02139',
    '100 Binney St', 'Cambridge', 'MA', 42.3664, -71.0823,
    30, 3000, 80000, 'active', '2026-01-01',
    'labops@cambridgebiotech.com', '617-555-0128', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-029', 'Back Bay Luxury Salon', 'Salon', '02116',
    '200 Newbury St', 'Boston', 'MA', 42.3503, -71.0792,
    120, 400, 9000, 'active', '2026-01-01',
    'bookings@backbaysalon.com', '617-555-0129', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-030', 'South Boston Fitness Club', 'Gym', '02127',
    '450 W Broadway', 'Boston', 'MA', 42.3388, -71.0480,
    180, 350, 8500, 'active', '2026-01-01',
    'info@southbostonfitness.com', '617-555-0130', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Atlanta, GA Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-031', 'Midtown Atlanta Coworking', 'Co-Working Space', '30309',
    '999 Peachtree St NE', 'Atlanta', 'GA', 33.7816, -84.3830,
    120, 500, 15000, 'active', '2026-01-01',
    'hello@midtowncowork.com', '404-555-0131', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-032', 'Buckhead Prime Steakhouse', 'Restaurant', '30326',
    '3060 Peachtree Rd NW', 'Atlanta', 'GA', 33.8430, -84.3791,
    60, 1100, 25000, 'active', '2026-01-01',
    'reservations@buckheadprime.com', '404-555-0132', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-033', 'Decatur Cold Storage Warehouse', 'Cold Storage', '30030',
    '315 W Ponce de Leon Ave', 'Decatur', 'GA', 33.7748, -84.2963,
    30, 2000, 55000, 'active', '2026-01-01',
    'ops@decaturcoldstorage.com', '404-555-0133', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Phoenix, AZ Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-034', 'Scottsdale Resort & Spa', 'Hotel', '85251',
    '7700 E McCormick Pkwy', 'Scottsdale', 'AZ', 33.5098, -111.9207,
    60, 1800, 45000, 'active', '2026-01-01',
    'concierge@scottsdaleresort.com', '480-555-0134', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-035', 'Tempe Server Farm', 'Data Center', '85281',
    '525 S Forest Ave', 'Tempe', 'AZ', 33.4148, -111.9396,
    15, 3500, 90000, 'active', '2026-01-01',
    'noc@tempeserverfarm.com', '480-555-0135', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-036', 'Downtown Phoenix Urgent Care', 'Medical Office', '85004',
    '100 W Washington St', 'Phoenix', 'AZ', 33.4484, -112.0773,
    45, 1200, 28000, 'active', '2026-01-01',
    'admin@dtphxurgentcare.com', '602-555-0136', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Austin, TX Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-037', 'South Congress Live Music Venue', 'Entertainment Venue', '78704',
    '1315 S Congress Ave', 'Austin', 'TX', 30.2489, -97.7491,
    60, 1000, 22000, 'active', '2026-01-01',
    'booking@socomusic.com', '512-555-0137', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-038', 'Domain Tech Startup Hub', 'Co-Working Space', '78758',
    '11501 Domain Dr', 'Austin', 'TX', 30.4015, -97.7256,
    90, 600, 15000, 'active', '2026-01-01',
    'hello@domaintechhub.com', '512-555-0138', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-039', 'East Austin Taco Joint', 'Restaurant', '78702',
    '1209 E 7th St', 'Austin', 'TX', 30.2649, -97.7260,
    120, 400, 9000, 'active', '2026-01-01',
    'hola@eastaustintacos.com', '512-555-0139', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Nashville, TN Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-040', 'Broadway Honky Tonk Bar', 'Entertainment Venue', '37203',
    '412 Broadway', 'Nashville', 'TN', 36.1592, -86.7762,
    90, 800, 18000, 'active', '2026-01-01',
    'events@broadwayhonkytonk.com', '615-555-0140', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-041', 'Gulch Recording Studio', 'Recording Studio', '37203',
    '500 11th Ave S', 'Nashville', 'TN', 36.1530, -86.7886,
    30, 1500, 35000, 'active', '2026-01-01',
    'studio@gulchrecording.com', '615-555-0141', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-042', 'East Nashville Farm-to-Table', 'Restaurant', '37206',
    '1000 Main St', 'Nashville', 'TN', 36.1783, -86.7536,
    90, 650, 14000, 'active', '2026-01-01',
    'chef@eastnashfarm.com', '615-555-0142', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Washington, DC Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-043', 'Georgetown Boutique Hotel', 'Hotel', '20007',
    '1310 Wisconsin Ave NW', 'Washington', 'DC', 38.9076, -77.0632,
    60, 1400, 32000, 'active', '2026-01-01',
    'front.desk@georgetownboutique.com', '202-555-0143', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-044', 'Dupont Circle Law Firm', 'Law Office', '20036',
    '1800 Massachusetts Ave NW', 'Washington', 'DC', 38.9061, -77.0439,
    30, 2200, 55000, 'active', '2026-01-01',
    'admin@dupontcirclelaw.com', '202-555-0144', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-045', 'Capitol Hill Daycare Center', 'Childcare Center', '20003',
    '400 Pennsylvania Ave SE', 'Washington', 'DC', 38.8853, -76.9988,
    45, 750, 16000, 'active', '2026-01-01',
    'director@capitolhilldaycare.com', '202-555-0145', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Minneapolis, MN Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-046', 'North Loop Craft Brewery', 'Brewery', '55401',
    '212 N 2nd St', 'Minneapolis', 'MN', 44.9847, -93.2691,
    120, 500, 11000, 'active', '2026-01-01',
    'taproom@northloopbrew.com', '612-555-0146', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-047', 'Uptown Minneapolis Yoga Studio', 'Fitness Studio', '55408',
    '3001 Hennepin Ave', 'Minneapolis', 'MN', 44.9490, -93.2984,
    180, 250, 6000, 'active', '2026-01-01',
    'namaste@uptownyoga.com', '612-555-0147', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Detroit, MI Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-048', 'Corktown Auto Parts Manufacturer', 'Manufacturing', '48216',
    '1850 Michigan Ave', 'Detroit', 'MI', 42.3286, -83.0715,
    60, 1800, 42000, 'active', '2026-01-01',
    'plant@corktownauto.com', '313-555-0148', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-049', 'Midtown Detroit Grocery Co-op', 'Grocery Store', '48201',
    '4700 Cass Ave', 'Detroit', 'MI', 42.3570, -83.0672,
    90, 600, 13000, 'active', '2026-01-01',
    'orders@midtowngrocerycoop.com', '313-555-0149', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Charlotte, NC Policies
-- ============================================================================

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-050', 'Uptown Charlotte Banking HQ', 'Financial Services', '28202',
    '200 S Tryon St', 'Charlotte', 'NC', 35.2252, -80.8434,
    30, 2500, 65000, 'active', '2026-01-01',
    'facilities@uptownbanking.com', '704-555-0150', SYSUTCDATETIME(), SYSUTCDATETIME()
);

INSERT INTO policies (
    policy_id, business_name, business_type, zip_code, address, city, state,
    latitude, longitude, threshold_minutes, hourly_rate, max_payout,
    status, effective_date, contact_email, contact_phone, created_at, updated_at
) VALUES (
    'BI-051', 'NoDa Arts District Gallery', 'Art Gallery', '28206',
    '3000 N Davidson St', 'Charlotte', 'NC', 35.2510, -80.8105,
    150, 300, 7000, 'active', '2026-01-01',
    'gallery@nodaarts.com', '704-555-0151', SYSUTCDATETIME(), SYSUTCDATETIME()
);

-- ============================================================================
-- Verification Query
-- ============================================================================

SELECT
    city + ', ' + state AS location,
    COUNT(*) AS policy_count,
    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_count,
    MIN(hourly_rate) AS min_hourly_rate,
    MAX(hourly_rate) AS max_hourly_rate,
    MIN(max_payout) AS min_max_payout,
    MAX(max_payout) AS max_max_payout
FROM policies
WHERE policy_id LIKE 'BI-%'
GROUP BY city, state
ORDER BY policy_count DESC;
