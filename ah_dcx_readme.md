# BigQuery Analytics Hub Setup - Normal Data Exchange (DCX)

This document explains how to use the `setup_ah_dcx.py` script to automate the creation of a BigQuery Analytics Hub data exchange for normal data sharing (not a clean room). This provides direct access to the full dataset without privacy restrictions.

## Overview

The `setup_ah_dcx.py` script automates the complete setup of a BigQuery Analytics Hub data exchange where the **e-wallet provider** shares their data with the **merchant** through a normal data exchange. This enables collaborative analytics between merchant and e-wallet provider with full dataset access.

### What the Script Does

1. **Creates a Data Exchange** in the sharing party's project
2. **Creates a DCX Listing** within that exchange, pointing to the `ewallet_provider` dataset
3. **Grants Access** to the subscriber by setting appropriate IAM policies

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

The user running the script must have the following IAM roles in the **sharing party's project**:
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
uv run python dcr_data_generator/setup_ah_dcx.py \
    --sharing-project-id your-provider-project \
    --subscriber-email merchant-user@example.com
```

### All Available Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--sharing-project-id` | ✅ | - | The GCP project ID of the party sharing the data (e-wallet provider) |
| `--subscriber-email` | ✅ | - | Email address of the data consumer who will be granted subscriber access |
| `--location` | ❌ | `US` | The GCP location for Analytics Hub resources |
| `--exchange-id` | ❌ | `provider_dcx_exchange` | Unique ID for the data exchange |
| `--listing-id` | ❌ | `provider_data_listing` | Unique ID for the data listing |

### Example with Custom Parameters

```bash
uv run python dcr_data_generator/setup_ah_dcx.py \
    --sharing-project-id ewallet-provider-project \
    --location EU \
    --exchange-id production_dcx_exchange \
    --listing-id ewallet_dataset_v1 \
    --subscriber-email data-team@merchant.com
```

## What Happens When You Run the Script

Each time the script runs, it performs these three steps in the context of the `--sharing-project-id`:

### Step 1: Create Data Exchange
```
Creating Data Exchange 'provider_dcx_exchange' in projects/your-provider-project/locations/US...
✓ Data Exchange created successfully: projects/your-provider-project/locations/US/dataExchanges/provider_dcx_exchange
```

The script creates a normal data exchange in the sharing party's project with:
- **Display Name**: "E-Wallet Provider Data Exchange"
- **Description**: "Normal data exchange for collaborative analytics between merchant and e-wallet provider"
- **Contact**: "data-sharing-admin@example.com"

### Step 2: Create DCX Listing
```
Creating DCX listing 'provider_data_listing' in exchange...
✓ DCX listing created successfully: projects/your-provider-project/locations/US/dataExchanges/provider_dcx_exchange/listings/provider_data_listing
```

The script creates a listing that:
- **Display Name**: "DCX E-Wallet Provider Dataset"
- Points to the `ewallet_provider` dataset
- Includes both `provider_users` and `transactions` tables
- Is categorized under Finance and Retail
- Provides direct access to the full dataset

### Step 3: Grant Access
```
Granting access to merchant-user@example.com...
✓ Created new subscriber binding for merchant-user@example.com
✓ IAM policy updated successfully
```

The script grants the subscriber the `roles/analyticshub.subscriber` role, allowing them to:
- Discover the listing in Analytics Hub
- Subscribe to create a linked dataset
- Access the shared data directly without privacy restrictions

## Post-Execution: Subscriber Steps

After the script completes successfully, the **subscriber** needs to:

### Success Message
```
✓ SUCCESS: Normal Data Exchange (DCX) setup completed!
Data Exchange: projects/your-provider-project/locations/US/dataExchanges/provider_dcx_exchange
Listing: projects/your-provider-project/locations/US/dataExchanges/provider_dcx_exchange/listings/provider_data_listing
Subscriber: merchant-user@example.com

Next steps for the subscriber:
1. Go to Analytics Hub in the subscriber's project
2. Browse available listings and find 'DCX E-Wallet Provider Dataset'
3. Subscribe to create a linked dataset in their project
4. Query the full dataset directly without privacy restrictions
```

### 1. Navigate to Analytics Hub
- Go to the Google Cloud Console
- Switch to the **subscriber's project**
- Navigate to **BigQuery** → **Analytics Hub**

### 2. Find the Listing
- Click on **"Browse listings"**
- Look for **"DCX E-Wallet Provider Dataset"**
- The listing should be visible with the sharing party's project as the source

### 3. Subscribe to the Listing
- Click on the listing to view details
- Click **"Subscribe"**
- Choose a dataset name (e.g., `shared_ewallet_data`)
- Click **"Subscribe"** to create the linked dataset

### 4. Access the Data
Once subscribed, the subscriber can query the shared data directly:

```sql
-- Example: Query the shared provider data (no privacy restrictions)
SELECT
    account_tier,
    COUNT(*) as user_count
FROM `your-subscriber-project.shared_ewallet_data.provider_users`
GROUP BY account_tier
ORDER BY user_count DESC;
```

## Troubleshooting

### Verification

To verify the setup worked correctly:

1. **Check the Exchange**: Go to Analytics Hub in the sharing party's project and verify the exchange exists
2. **Check the Listing**: Verify the listing appears and shows the correct dataset
3. **Check Permissions**: Verify the subscriber user can see the listing when browsing from their project

## Demo Tips

### Cleanup

To clean up after a demo:

```bash
# Delete the listing (this will also revoke access)
gcloud analytics-hub listings delete provider_data_listing \
    --data-exchange=provider_dcx_exchange \
    --location=US \
    --project=your-sharing-project

# Delete the exchange
gcloud analytics-hub data-exchanges delete provider_dcx_exchange \
    --location=US \
    --project=your-sharing-project
```

---

**Related Documentation:**
- [Main Project README](README.md) - Data generation and clean room analytics
- [Google Cloud Analytics Hub Documentation](https://cloud.google.com/bigquery/docs/analytics-hub-introduction)
