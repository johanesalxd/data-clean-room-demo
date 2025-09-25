# BigQuery Analytics Hub Setup - Normal Data Exchange

This document explains how to use the `setup_analytics_hub.py` script to automate the creation of a BigQuery Analytics Hub data exchange for normal data sharing (not a clean room).

## Overview

The `setup_analytics_hub.py` script automates the complete setup of a BigQuery Analytics Hub data exchange where the **e-wallet provider** shares their data with the **merchant** through a normal data exchange. This enables direct access to the provider's data without the privacy protections of a clean room.

### What the Script Does

1. **Creates a Data Exchange** in the provider's project
2. **Creates a Listing** within that exchange, pointing to the `ewallet_provider` dataset
3. **Grants Access** to the merchant by setting appropriate IAM policies

## Prerequisites

### 1. Install Dependencies

First, ensure you have the required Analytics Hub library installed:

```bash
uv sync
```

This will install the `google-cloud-bigquery-analyticshub` dependency that was added to `pyproject.toml`.

### 2. Authentication

Ensure you're authenticated with Google Cloud SDK and have the necessary permissions:

```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Required Permissions

The user running the script must have the following IAM roles in the **provider's project**:
- `roles/analyticshub.admin` (to create exchanges and listings)
- `roles/bigquery.dataViewer` (to access the dataset being shared)

### 4. Data Prerequisites

Before running this script, ensure you have already generated the provider's data using:

```bash
uv run python -m dcr_data_generator.main --merchant-project-id your-merchant-project --provider-project-id your-provider-project
```

## Usage

### Basic Command

```bash
uv run python dcr_data_generator/setup_analytics_hub.py \
    --provider-project-id your-provider-project \
    --merchant-project-id your-merchant-project \
    --subscriber-email merchant-user@example.com
```

### All Available Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--provider-project-id` | ✅ | - | The GCP project ID of the data provider (e-wallet provider) |
| `--merchant-project-id` | ✅ | - | The GCP project ID of the data consumer (merchant) |
| `--subscriber-email` | ✅ | - | Email address of the merchant user/group to grant access |
| `--location` | ❌ | `US` | The GCP location for Analytics Hub resources |
| `--exchange-id` | ❌ | `demo_exchange` | Unique ID for the data exchange |
| `--listing-id` | ❌ | `provider_data_listing` | Unique ID for the data listing |

### Example with Custom Parameters

```bash
uv run python dcr_data_generator/setup_analytics_hub.py \
    --provider-project-id ewallet-provider-project \
    --merchant-project-id merchant-analytics-project \
    --location EU \
    --exchange-id production_exchange \
    --listing-id ewallet_dataset_v1 \
    --subscriber-email data-team@merchant.com
```

## What Happens When You Run the Script

### Step 1: Create Data Exchange
```
Creating Data Exchange 'demo_exchange' in projects/your-provider-project/locations/US...
✓ Data Exchange created successfully: projects/your-provider-project/locations/US/dataExchanges/demo_exchange
```

The script creates a private data exchange in the provider's project with:
- **Display Name**: "E-Wallet Provider Data Exchange"
- **Description**: Explains the purpose of the exchange
- **Contact**: Provider admin contact information

### Step 2: Create Listing
```
Creating Listing 'provider_data_listing' in exchange...
✓ Listing created successfully: projects/your-provider-project/locations/US/dataExchanges/demo_exchange/listings/provider_data_listing
```

The script creates a listing that:
- Points to the `ewallet_provider` dataset
- Includes both `provider_users` and `transactions` tables
- Is categorized under Finance and Retail
- Contains comprehensive documentation

### Step 3: Grant Access
```
Granting access to merchant-user@example.com...
✓ Created new subscriber binding for merchant-user@example.com
✓ IAM policy updated successfully
```

The script grants the merchant user the `roles/analyticshub.subscriber` role, allowing them to:
- Discover the listing in Analytics Hub
- Subscribe to create a linked dataset
- Access the shared data directly

## Post-Execution: Merchant Steps

After the script completes successfully, the **merchant** needs to:

### 1. Navigate to Analytics Hub
- Go to the Google Cloud Console
- Switch to the **merchant's project**
- Navigate to **BigQuery** → **Analytics Hub**

### 2. Find the Listing
- Click on **"Browse listings"**
- Look for **"E-Wallet Provider Dataset"**
- The listing should be visible with the provider's project as the source

### 3. Subscribe to the Listing
- Click on the listing to view details
- Click **"Subscribe"**
- Choose a dataset name (e.g., `shared_ewallet_data`)
- Click **"Subscribe"** to create the linked dataset

### 4. Access the Data
Once subscribed, the merchant can query the shared data directly:

```sql
-- Example: Query the shared provider data
SELECT
    account_tier,
    COUNT(*) as user_count
FROM `your-merchant-project.shared_ewallet_data.provider_users`
GROUP BY account_tier
ORDER BY user_count DESC;
```

## Troubleshooting

### Verification

To verify the setup worked correctly:

1. **Check the Exchange**: Go to Analytics Hub in the provider's project and verify the exchange exists
2. **Check the Listing**: Verify the listing appears and shows the correct dataset
3. **Check Permissions**: Verify the merchant user can see the listing when browsing from their project

## Demo Tips

### Cleanup

To clean up after a demo:

```bash
# Delete the listing (this will also revoke access)
gcloud analytics-hub listings delete provider_data_listing \
    --data-exchange=demo_exchange \
    --location=US \
    --project=your-provider-project

# Delete the exchange
gcloud analytics-hub data-exchanges delete demo_exchange \
    --location=US \
    --project=your-provider-project
```

---

**Related Documentation:**
- [Main Project README](README.md) - Data generation and clean room analytics
- [Google Cloud Analytics Hub Documentation](https://cloud.google.com/bigquery/docs/analytics-hub-introduction)
