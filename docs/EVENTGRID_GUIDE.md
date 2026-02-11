# Event Grid Integration Guide

How the unified notebook publishes events to Azure Event Grid, and how to wire subscribers.

## Event Types

The notebook publishes 4 event types at different stages of the pipeline:

| Event Type | Published When | Payload Includes |
|-----------|---------------|-----------------|
| `outage.detected` | An outage matches one or more policies (Step 5) | event_id, utility, city, affected_customers, affected_policies[] |
| `claim.approved` | AI validates and approves a claim (Step 6) | claim_id, policy_id, payout_amount, ai_confidence_score |
| `claim.denied` | AI denies a claim (Step 6) | claim_id, policy_id, denial reasoning |
| `payout.processed` | Payment record created (Step 7) | payout_id, claim_id, amount, transaction_id |

## How Events Are Published

The notebook includes an embedded `NotebookEventGridClient` that posts directly to the Event Grid REST API. No SDK installation required.

```python
# Simplified view of what happens inside the notebook:
eg_client.publish_event(
    event_type="outage.detected",
    subject="outage/PRESTO-WA-20260210-4521",
    data={
        "event_id": "PRESTO-WA-20260210-4521",
        "utility_name": "Seattle City Light",
        "city": "Seattle",
        "affected_customers": 8420,
        "affected_policies": ["BI-001", "BI-002"],
        "policy_count": 2,
    },
)
```

When Event Grid is not configured, a `LocalEventLogger` records events in the same format for the audit table — the notebook runs identically either way.

## Setting Up Event Grid

### 1. Create the Topic

The easiest path is to run the setup script:

```bash
cd setup
./azure-setup.sh   # creates topic + supporting resources
```

Or create manually:

```bash
az eventgrid topic create \
  --name parametric-insurance-events \
  --resource-group parametric-insurance-rg \
  --location eastus

# Get endpoint and key
az eventgrid topic show --name parametric-insurance-events -g parametric-insurance-rg --query endpoint -o tsv
az eventgrid topic key list --name parametric-insurance-events -g parametric-insurance-rg --query key1 -o tsv
```

### 2. Configure the Notebook

Set in `DemoConfig` (Step 0):

```python
eventgrid_topic_endpoint = "https://parametric-insurance-events.eastus-1.eventgrid.azure.net/api/events"
eventgrid_topic_key = "your-sas-key"
```

Or via environment variables: `EVENTGRID_TOPIC_ENDPOINT` and `EVENTGRID_KEY`.

### 3. Create Subscriptions

#### Option A: Azure Functions (from archive/v1)

```bash
TOPIC_ID=$(az eventgrid topic show --name parametric-insurance-events -g parametric-insurance-rg --query id -o tsv)
FUNC_ID=$(az functionapp show --name <your-func-app> -g parametric-insurance-rg --query id -o tsv)

# ThresholdEvaluator ← outage.detected
az eventgrid event-subscription create \
  --name threshold-evaluator \
  --source-resource-id $TOPIC_ID \
  --endpoint "$FUNC_ID/functions/ThresholdEvaluator" \
  --endpoint-type azurefunction \
  --included-event-types "outage.detected"

# PayoutProcessor ← claim.approved
az eventgrid event-subscription create \
  --name payout-processor \
  --source-resource-id $TOPIC_ID \
  --endpoint "$FUNC_ID/functions/PayoutProcessor" \
  --endpoint-type azurefunction \
  --included-event-types "claim.approved"
```

#### Option B: Logic Apps (for notifications)

1. Create a Logic App in the Azure Portal
2. Use the **When a resource event occurs** trigger
3. Filter for event type `payout.processed`
4. Add an **Send an email** action with the payout details

#### Option C: Webhook (custom)

```bash
az eventgrid event-subscription create \
  --name my-webhook \
  --source-resource-id $TOPIC_ID \
  --endpoint "https://your-app.azurewebsites.net/api/events" \
  --endpoint-type webhook \
  --included-event-types "payout.processed"
```

## Event Audit Log

Every event (published, local-only, or failed) is stored in the `event_audit_log` Delta table:

| Column | Description |
|--------|------------|
| sequence | Auto-incrementing counter |
| event_id | UUID of the event |
| event_type | e.g. `outage.detected` |
| subject | e.g. `outage/PRESTO-WA-...` |
| event_time | ISO timestamp |
| data_summary | First 500 chars of the JSON payload |
| status | `published`, `local_only`, or `failed` |
| error | Error message (if failed) |

Query it in the notebook or via Spark SQL:

```sql
SELECT event_type, status, COUNT(*) AS count
FROM event_audit_log
GROUP BY event_type, status
ORDER BY event_type
```

## Monitoring

### Azure Portal

1. Open the Event Grid Topic in the Azure Portal
2. Check **Metrics** → Published Events, Delivery Succeeded, Delivery Failed
3. Check **Event Subscriptions** → delivery status per subscriber

### Application Insights

If you deployed Functions with the setup script, logs are in Application Insights:

```bash
az monitor app-insights metrics show \
  --app parametric-insurance-insights \
  --resource-group parametric-insurance-rg \
  --metrics requests/count
```

### Notebook Audit Table

The `event_audit_log` table in the Lakehouse provides a notebook-level view independent of Azure monitoring.
