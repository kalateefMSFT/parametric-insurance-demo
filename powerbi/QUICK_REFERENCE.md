# Power BI Dashboard - Quick Reference Card

## Essential Information

**Dashboard Name:** Parametric Insurance Monitor  
**Pages:** 5 (Overview, Claims, Outages, Policies, AI Insights)  
**Data Source:** Fabric Warehouse (parametric_insurance_warehouse)  
**Refresh:** Every 15 minutes (or DirectQuery for real-time)

---

## Quick Setup Checklist

- [ ] Install Power BI Desktop
- [ ] Connect to Fabric Lakehouse
- [ ] Import tables (claims, policies, outages, payouts, weather)
- [ ] Create relationships
- [ ] Add DAX measures
- [ ] Build 5 dashboard pages
- [ ] Publish to workspace
- [ ] Configure refresh schedule
- [ ] Share with stakeholders

---

## Key Metrics (KPIs)

| Metric | DAX Formula | Target |
|--------|-------------|---------|
| Total Claims | `COUNT(claims[claim_id])` | N/A |
| Total Payout | `SUM(payouts[amount])` | N/A |
| Approval Rate | `DIVIDE(approved, total, 0)` | >90% |
| Avg Confidence | `AVERAGE(claims[ai_confidence_score])` | >85% |
| Active Outages | `COUNTROWS(FILTER(active))` | <10 |
| Avg Processing | `AVERAGE(DATEDIFF(...))` | <60 min |

---

## Data Tables

### Fact Tables
1. **claims** - Insurance claims (main)
2. **payouts** - Payment records
3. **outage_events** - Power outages
4. **weather_data** - Weather conditions

### Dimension Tables
5. **policies** - Insurance policies

### Views (Pre-aggregated)
6. **v_claim_statistics** - Summary stats
7. **v_policy_performance** - Policy metrics
8. **v_outage_impact** - Outage analysis

---

## Page Layout

### Page 1: Overview
- 4 KPI cards (top)
- Claims by status (donut)
- Claims trend (line chart)
- Top policies (bar chart)
- Outage map
- AI confidence histogram

### Page 2: Claims Processing
- Recent claims table
- Processing funnel
- Avg time by hour
- Payout distribution

### Page 3: Outage Monitoring
- Active outages map
- Outage timeline
- Outage causes (treemap)
- Weather correlation

### Page 4: Policy Performance
- Performance matrix
- Policies by location (map)
- Business type analysis

### Page 5: AI Insights
- Confidence vs outcome (scatter)
- Fraud detection summary
- AI accuracy trend
- Processing time by confidence

---

## Color Codes

| Status | Color | Hex |
|--------|-------|-----|
| Approved | Green | #107C10 |
| Denied | Red | #D13438 |
| Pending | Yellow | #FFB900 |
| Validating | Orange | #D83B01 |
| Info | Blue | #0078D4 |

---

## Common DAX Formulas

### Total Claims
```dax
Total Claims = COUNT(claims[claim_id])
```

### Approval Rate
```dax
Approval Rate = 
DIVIDE(
    COUNTROWS(FILTER(claims, claims[status] = "approved")),
    COUNTROWS(claims),
    0
)
```

### Avg Processing Time
```dax
Avg Processing Time = 
AVERAGEX(
    FILTER(claims, NOT(ISBLANK(claims[validated_at]))),
    DATEDIFF(claims[filed_at], claims[validated_at], MINUTE)
)
```

### Claims Today
```dax
Claims Today = 
CALCULATE(
    COUNT(claims[claim_id]),
    claims[filed_at] >= TODAY()
)
```

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Refresh data | Ctrl + R |
| Edit query | Ctrl + E |
| New measure | Ctrl + Shift + M |
| New column | Ctrl + Shift + C |
| Format visual | Ctrl + Shift + F |
| Duplicate page | Ctrl + D |
| Save | Ctrl + S |
| Publish | Alt + P |

---

## Troubleshooting

### Data Not Loading
1. Check Fabric connection
2. Verify credentials
3. Test SQL query manually
4. Check firewall rules

### Slow Performance
1. Use DirectQuery for large data
2. Create aggregated views
3. Reduce visual count per page
4. Enable query folding

### Visuals Not Updating
1. Refresh data
2. Check filters
3. Clear cache
4. Verify relationships

---

## Best Practices

✅ Use DirectQuery for real-time data  
✅ Create relationships, not calculated columns  
✅ Use measures instead of calculated columns  
✅ Keep visuals per page under 20  
✅ Use bookmarks for different views  
✅ Add tooltips to all visuals  
✅ Enable drill-through where appropriate  
✅ Set appropriate data types  
✅ Use consistent color scheme  
✅ Add filters/slicers to each page  

---

## Sharing Options

| Method | Use Case |
|--------|----------|
| Publish to workspace | Team collaboration |
| Create app | Business users |
| Export to PDF | Static reports |
| Embed in Teams | Daily monitoring |
| Email subscription | Scheduled updates |

---

## Refresh Schedule

### Import Mode
- Frequency: Every 15 minutes
- Active hours: 6 AM - 11 PM
- Days: Mon-Sun
- Gateway: Not required (cloud source)

### DirectQuery
- Real-time updates
- No refresh needed
- Queries run on view
- Timeout: 300 seconds

---

## Quick SQL Queries

### Get All Claims
```sql
SELECT * FROM claims 
WHERE filed_at >= DATEADD(DAY, -30, GETUTCDATE())
```

### Get Active Outages
```sql
SELECT * FROM outage_events 
WHERE status = 'active'
```

### Get Policy Performance
```sql
SELECT * FROM v_policy_performance
```

---

## Support Resources

📖 **Setup Guide:** powerbi/POWERBI_SETUP.md  
📊 **SQL Queries:** powerbi/queries.sql  
🎨 **Mockups:** powerbi/DASHBOARD_MOCKUPS.md  
📧 **Support:** demo-support@yourcompany.com  

---

## Connection String

```
Server: <workspace>.datawarehouse.fabric.microsoft.com
Database: parametric_insurance_lakehouse
Authentication: Microsoft Account
```

---

**Last Updated:** February 2026  
**Version:** 1.0  
**Compatible With:** Power BI Desktop (latest)
