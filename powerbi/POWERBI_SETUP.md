# Power BI Dashboard Setup Guide

Complete guide to building the Parametric Insurance monitoring dashboard in Power BI.

## Prerequisites

- Power BI Desktop (latest version)
- Access to Fabric Warehouse
- Completed SQL schema setup

## Quick Setup

### Option 1: Connect to Fabric Warehouse

1. Open Power BI Desktop
2. **Get Data** → **SQL Server**
3. Enter connection details:
   ```
   Server: <workspace>.datawarehouse.fabric.microsoft.com
   Database: parametric_insurance_lakehouse
   ```
4. Authentication: **Microsoft Account**
5. Select tables and views
6. Click **Load**

### Option 2: Use Direct Query (Recommended for Real-Time)

1. In connection dialog, choose **DirectQuery** instead of **Import**
2. This enables real-time dashboard updates
3. Data refreshes automatically when viewed

## Data Model

### Tables to Import

**Fact Tables:**
- `claims`
- `outage_events`
- `payouts`
- `weather_data`

**Dimension Tables:**
- `policies`

**Views (Pre-aggregated):**
- `v_claim_statistics`
- `v_policy_performance`
- `v_outage_impact`
- `v_active_claims`

### Relationships

Create these relationships in Model view:

```
policies[policy_id] ──1:∞── claims[policy_id]
claims[claim_id] ──1:1── payouts[claim_id]
claims[outage_event_id] ──∞:1── outage_events[event_id]
outage_events[event_id] ──1:∞── weather_data[event_id]
```

## DAX Measures

Create these measures in a new table called "Measures":

### KPI Measures

```dax
// Total Claims
Total Claims = COUNT(claims[claim_id])

// Total Payout Amount
Total Payout = SUM(payouts[amount])

// Average Payout
Average Payout = AVERAGE(payouts[amount])

// Approval Rate
Approval Rate = 
DIVIDE(
    COUNTROWS(FILTER(claims, claims[status] = "approved")),
    COUNTROWS(claims),
    0
)

// Active Outages
Active Outages = 
COUNTROWS(FILTER(outage_events, outage_events[status] = "active"))

// Average AI Confidence
Average AI Confidence = AVERAGE(claims[ai_confidence_score])

// Claims Today
Claims Today = 
CALCULATE(
    COUNT(claims[claim_id]),
    claims[filed_at] >= TODAY()
)

// Payouts Today
Payouts Today = 
CALCULATE(
    SUM(payouts[amount]),
    payouts[initiated_at] >= TODAY()
)

// Average Processing Time (minutes)
Avg Processing Time = 
AVERAGEX(
    FILTER(claims, NOT(ISBLANK(claims[validated_at]))),
    DATEDIFF(claims[filed_at], claims[validated_at], MINUTE)
)

// Fraud Detection Rate
Fraud Flags = 
COUNTROWS(
    FILTER(claims, NOT(ISBLANK(claims[fraud_flags])))
)

// Policies at Risk
Policies at Risk = 
CALCULATE(
    DISTINCTCOUNT(claims[policy_id]),
    claims[status] IN {"pending", "validating"}
)
```

### Time Intelligence Measures

```dax
// Claims Last 7 Days
Claims L7D = 
CALCULATE(
    COUNT(claims[claim_id]),
    DATESINPERIOD(claims[filed_at], LASTDATE(claims[filed_at]), -7, DAY)
)

// Payout MTD
Payout MTD = 
CALCULATE(
    SUM(payouts[amount]),
    DATESMTD(payouts[initiated_at])
)

// Claims YTD
Claims YTD = 
CALCULATE(
    COUNT(claims[claim_id]),
    DATESYTD(claims[filed_at])
)

// MoM Growth
Payout MoM Growth = 
VAR CurrentMonth = [Total Payout]
VAR PreviousMonth = 
    CALCULATE(
        [Total Payout],
        DATEADD(payouts[initiated_at], -1, MONTH)
    )
RETURN
    DIVIDE(CurrentMonth - PreviousMonth, PreviousMonth, 0)
```

### Calculated Columns

```dax
// In claims table:
Processing Duration (min) = 
DATEDIFF(claims[filed_at], claims[validated_at], MINUTE)

Status Color = 
SWITCH(
    claims[status],
    "approved", "Green",
    "denied", "Red",
    "pending", "Yellow",
    "validating", "Orange",
    "Gray"
)

// In outage_events table:
Severity Level = 
SWITCH(
    TRUE(),
    outage_events[affected_customers] > 10000, "Critical",
    outage_events[affected_customers] > 5000, "High",
    outage_events[affected_customers] > 1000, "Medium",
    "Low"
)

Duration Hours = 
DIVIDE(outage_events[duration_minutes], 60, 0)
```

## Dashboard Pages

### Page 1: Overview Dashboard

**Layout:** 1920x1080 (16:9)

#### Top KPI Cards (4 cards in a row)

1. **Total Claims** (Card visual)
   - Field: `[Total Claims]`
   - Format: Whole number
   - Color: #0078D4 (Blue)

2. **Total Payout** (Card visual)
   - Field: `[Total Payout]`
   - Format: Currency ($)
   - Color: #107C10 (Green)

3. **Active Outages** (Card visual)
   - Field: `[Active Outages]`
   - Format: Whole number
   - Color: #D83B01 (Orange)

4. **Approval Rate** (Card visual)
   - Field: `[Approval Rate]`
   - Format: Percentage
   - Color: #8764B8 (Purple)

#### Main Visuals

5. **Claims by Status** (Donut Chart)
   - Legend: `claims[status]`
   - Values: `[Total Claims]`
   - Colors: 
     - Approved: Green (#107C10)
     - Denied: Red (#D13438)
     - Pending: Yellow (#FFB900)
     - Validating: Orange (#D83B01)

6. **Claims Over Time** (Line Chart)
   - X-Axis: `claims[filed_at]` (by Day)
   - Y-Axis: `[Total Claims]`
   - Secondary Y-Axis: `[Total Payout]`
   - Show data labels: Yes

7. **Top Policies by Claims** (Bar Chart)
   - X-Axis: `[Total Claims]`
   - Y-Axis: `policies[business_name]`
   - Data labels: Yes
   - Top 10 only

8. **Map - Outages & Policies** (Map visual)
   - Location: `policies[latitude]`, `policies[longitude]`
   - Size: `[Total Payout]`
   - Color: `claims[status]`
   - Add outage locations as separate layer

9. **AI Confidence Distribution** (Histogram)
   - X-Axis: `claims[ai_confidence_score]` (Bins: 0.1)
   - Y-Axis: Count
   - Color: Gradient blue

#### Slicers

10. **Date Range** (Date slicer)
    - Field: `claims[filed_at]`
    - Type: Between
    - Default: Last 30 days

11. **Status Filter** (Slicer)
    - Field: `claims[status]`
    - Type: Dropdown
    - Multi-select: Yes

### Page 2: Claims Processing

#### Grid Layout

1. **Claims Table** (Table visual)
   - Columns:
     - `claims[claim_id]`
     - `policies[business_name]`
     - `claims[filed_at]`
     - `claims[status]`
     - `claims[payout_amount]` (Currency)
     - `claims[ai_confidence_score]` (Percentage)
     - `[Processing Duration (min)]`
   - Conditional formatting:
     - Status: Color by value
     - Confidence: Data bars (green)
   - Enable sorting
   - Page size: 25 rows

2. **Processing Funnel** (Funnel Chart)
   - Stages:
     - Filed: `[Total Claims]`
     - Validating: Count of validating claims
     - Approved: Count of approved claims
     - Paid: Count where status = "paid"
   - Show conversion rates

3. **Average Processing Time by Hour** (Column Chart)
   - X-Axis: `claims[filed_at]` (Hour of day)
   - Y-Axis: `[Avg Processing Time]`
   - Goal line: 60 minutes (1 hour)

4. **Payout Distribution** (Box and Whisker)
   - Category: `policies[business_type]`
   - Values: `payouts[amount]`
   - Show outliers: Yes

### Page 3: Outage Monitoring

1. **Active Outages Map** (Map visual)
   - Location: `outage_events[latitude]`, `outage_events[longitude]`
   - Size: `outage_events[affected_customers]`
   - Color: `[Severity Level]`
   - Tooltips: Show utility, duration, cause

2. **Outages Timeline** (Gantt Chart)
   - Task: `outage_events[event_id]`
   - Start: `outage_events[outage_start]`
   - Duration: `outage_events[duration_minutes]`
   - Color: `outage_events[utility_name]`

3. **Outage Causes** (Treemap)
   - Category: `outage_events[reported_cause]`
   - Values: `[Total Claims]`
   - Tooltips: Show count and total payout

4. **Weather Correlation** (Scatter Chart)
   - X-Axis: `weather_data[wind_speed_mph]`
   - Y-Axis: `[Total Payout]`
   - Size: `outage_events[duration_minutes]`
   - Color: `weather_data[severe_weather_alert]`

5. **Outage Duration vs Payout** (Line and Stacked Column)
   - Shared X-Axis: `outage_events[duration_minutes]` (Bins: 30)
   - Column: Count of claims
   - Line: Average payout

### Page 4: Policy Performance

1. **Policy Performance Table** (Matrix)
   - Rows: `policies[business_name]`
   - Columns: `claims[status]`
   - Values: 
     - Count of claims
     - Sum of payouts
   - Subtotals: Yes
   - Grand total: Yes

2. **Policies by City** (Map)
   - Location: `policies[city]`, `policies[state]`
   - Size: `[Total Payout]`
   - Color: `[Average Payout]`
   - Bubble layers

3. **Business Type Analysis** (Stacked Bar Chart)
   - Y-Axis: `policies[business_type]`
   - X-Axis: `[Total Claims]`
   - Legend: `claims[status]`

4. **Policy Risk Score** (KPI visual)
   - Indicator: Claims per policy
   - Trend: Last 30 days
   - Target: Industry average (custom value)

5. **Top/Bottom Performers** (Table)
   - Show top 5 and bottom 5 policies
   - Metrics: Claims, Payouts, Approval rate

### Page 5: AI Validation Insights

1. **AI Confidence vs Actual Outcome** (Scatter)
   - X-Axis: `claims[ai_confidence_score]`
   - Y-Axis: `claims[payout_amount]`
   - Color: `claims[status]`
   - Size: `[Processing Duration]`
   - Trend line: Yes

2. **Fraud Detection Dashboard**
   - Card: `[Fraud Flags]`
   - Table: Claims with fraud flags
   - Columns: claim_id, policy, fraud_flags, status

3. **AI Accuracy Over Time** (Line Chart)
   - X-Axis: `claims[filed_at]` (by Week)
   - Y-Axis: `[Average AI Confidence]`
   - Secondary: `[Approval Rate]`
   - Goal line: 85% confidence

4. **Evidence Sources** (Stacked Area Chart)
   - X-Axis: `claims[filed_at]`
   - Y-Axis: Count of claims
   - Legend: Evidence types (from AI reasoning)

5. **Processing Time by Confidence** (Box Plot)
   - Category: `claims[ai_confidence_score]` (bins: 0.2)
   - Values: `[Processing Duration]`
   - Show median, quartiles

## Formatting & Themes

### Color Palette

```
Primary: #0078D4 (Azure Blue)
Success: #107C10 (Green)
Warning: #FFB900 (Yellow)
Error: #D13438 (Red)
Info: #8764B8 (Purple)
Neutral: #605E5C (Gray)
```

### Font Settings

- **Headers**: Segoe UI Semibold, 16pt
- **KPIs**: Segoe UI Bold, 28pt
- **Body**: Segoe UI, 11pt
- **Legends**: Segoe UI, 9pt

### Background

- Page background: #F3F2F1 (Light gray)
- Visual background: White
- Card background: White with subtle shadow

## Refresh Settings

### Scheduled Refresh (Import Mode)

```
Frequency: Every 15 minutes
Time range: 6 AM - 11 PM
Days: Monday - Sunday
```

### DirectQuery (Real-time)

- No refresh needed
- Data updates on dashboard view
- Query timeout: 300 seconds

## Sharing & Publishing

### Publish to Workspace

1. **Home** → **Publish**
2. Select workspace: `Parametric Insurance`
3. Confirm

### Create App

1. In workspace, **Create app**
2. Setup:
   - Name: Parametric Insurance Monitor
   - Description: Real-time claims monitoring
3. Navigation: Configure page order
4. Publish

### Row-Level Security (Optional)

Create role for business owners to see only their policies:

```dax
// RLS filter on policies table
[contact_email] = USERPRINCIPALNAME()
```

## Mobile Layout

Create mobile-optimized version:

1. **View** → **Mobile Layout**
2. Drag visuals to mobile canvas
3. Priority order:
   - KPI cards (top)
   - Claims status chart
   - Recent claims table
   - Map (bottom)

## Alerts

Set up data alerts for stakeholders:

1. Pin KPI to dashboard
2. **More options** → **Manage alerts**
3. Configure:
   - Metric: Active Outages
   - Threshold: > 5
   - Frequency: Hourly
   - Recipients: Operations team

## Performance Optimization

### Tips for Large Datasets

1. **Use aggregations**:
   - Create aggregation tables in Fabric
   - Enable automatic aggregations in Power BI

2. **Optimize DAX**:
   - Use variables for repeated calculations
   - Filter early in calculations
   - Avoid calculated columns when possible

3. **Reduce visual count**:
   - Max 20 visuals per page
   - Use bookmarks for alternate views

4. **DirectQuery optimization**:
   - Create indexed views in SQL
   - Use query folding where possible

## Sample DAX for Advanced Scenarios

### Rolling Average (7-day)

```dax
Payout 7-Day Avg = 
AVERAGEX(
    DATESINPERIOD(
        payouts[initiated_at],
        LASTDATE(payouts[initiated_at]),
        -7,
        DAY
    ),
    [Total Payout]
)
```

### Year-over-Year Comparison

```dax
Claims YoY = 
VAR CurrentYearClaims = [Total Claims]
VAR PreviousYearClaims = 
    CALCULATE(
        [Total Claims],
        SAMEPERIODLASTYEAR(claims[filed_at])
    )
RETURN
    CurrentYearClaims - PreviousYearClaims
```

### Conditional Formatting Rules

```dax
// For AI Confidence color
Confidence Color = 
SWITCH(
    TRUE(),
    claims[ai_confidence_score] >= 0.9, "#107C10",
    claims[ai_confidence_score] >= 0.7, "#FFB900",
    "#D13438"
)
```

## Troubleshooting

### Connection Issues

```
Error: Cannot connect to data source
Solution: 
1. Verify Fabric warehouse is running
2. Check firewall rules
3. Refresh credentials in Power BI
```

### Performance Issues

```
Problem: Dashboard slow to load
Solution:
1. Switch to DirectQuery for real-time data
2. Create aggregated views in SQL
3. Reduce number of visuals per page
4. Disable auto date/time
```

### Data Not Refreshing

```
Problem: Data appears stale
Solution:
1. Check refresh schedule
2. Verify gateway status (if on-premises)
3. Check data source credentials
4. Review refresh history for errors
```

## Next Steps

1. ✅ Create Power BI report
2. ⬜ Publish to workspace
3. ⬜ Configure scheduled refresh
4. ⬜ Share with stakeholders
5. ⬜ Set up alerts
6. ⬜ Create mobile layout

---

**Power BI Template:** Use the JSON template in `powerbi/template.json` as a starting point

**Need Help?** Check Power BI documentation: https://docs.microsoft.com/power-bi
