# Monitoring Infrastructure Module

This module provisions the observability stack for AeroInbox, capturing platform logs, traces, and metrics, and establishing automated paging channels for alerts.

## Resources Created
- **Log Analytics Workspace**: Central repository for Container App environment logs.
- **Application Insights**: APM monitoring for distributed transactions across FastAPI backends.
- **Monitor Action Group**: Email alert receiver group for DevOps notification.

## Inputs
- `name_prefix` (string): Workspace name prefix.
- `location` (string): Target Azure region.
- `common_tags` (map): Common tags.
- `alert_email` (string): Email receiver address.
- `log_retention_days` (number): Log storage retention days.

## Outputs
- `workspace_id` (string)
- `workspace_name` (string)
- `app_insights_connection_string` (string, sensitive)
- `app_insights_instrumentation_key` (string, sensitive)
