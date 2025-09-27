# BigQuery Analytics Hub Setup - Data Clean Room (DCR) Configurations

This document explains how to use the flexible `setup_ah_dcr.py` script to automate the creation of Data Clean Room (DCR) environments for collaborative analytics between two parties (a data provider and a merchant).

## Overview

The script supports **two different architectural approaches** for DCR setup, each with distinct advantages:

### **Option A: Single Shared DCR** (True Bi-Directional)
- **One DCR** hosted in a single project (provider, merchant, or dedicated DCR project)
- **Both parties** add their listings to the same DCR instance
- **True collaboration** in one shared, governed space
- **Best for**: Organizations with strong partnership agreements

### **Option B: Separate Party DCRs** (Data Sovereignty)
- **Two separate DCRs**, one in each party's project
- **Each party** maintains control over their own DCR
- **Independent governance** while enabling cross-party analytics
- **Best for**: Organizations requiring data sovereignty

This document provides commands for both approaches.

### What the Script Does

-   Creates a shared Data Clean Room in the sharing party's project.
-   **Creates privacy-enforced views** with analysis rules based on the specific table being shared.
-   Creates DCR-enabled listings that share the privacy-enforced views (not raw tables).
-   **Automatically applies the correct analysis rules** based on the use cases each table supports:
    - **List Overlap Rules** for transaction verification and user enrichment
    - **Aggregation Threshold Rules** for customer segmentation and fraud analysis
-   Grants subscriber access to the other party.

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

To create the full bi-directional DCR, **both parties must run commands** since each DCR listing can only contain one table.

### Summary
- **E-Wallet Provider**: Runs 2 commands (shares 2 tables)
- **Merchant**: Runs 1 command (shares 1 table)
- **Total**: 3 script executions required

---

## Usage: Choose Your DCR Architecture

### **Option A: Single Shared DCR** (Recommended for Strong Partnerships)

Use the **same sharing project** and **same exchange-id** for all commands:

#### Commands for E-Wallet Provider
```bash
# Command 1: Share provider_users table
uv run python dcr_data_generator/setup_ah_dcr.py \
    --sharing-project-id shared-dcr-project \
    --subscriber-email merchant-user@example.com \
    --dataset-to-share ewallet_provider \
    --table-to-share provider_users \
    --listing-id provider_users_listing \
    --listing-display-name "DCR Provider Users Table" \
    --exchange-id shared_dcr_exchange

# Command 2: Share transactions table
uv run python dcr_data_generator/setup_ah_dcr.py \
    --sharing-project-id shared-dcr-project \
    --subscriber-email merchant-user@example.com \
    --dataset-to-share ewallet_provider \
    --table-to-share transactions \
    --listing-id provider_transactions_listing \
    --listing-display-name "DCR Provider Transactions Table" \
    --exchange-id shared_dcr_exchange
```

#### Commands for Merchant
```bash
# Command 1: Share users table
uv run python dcr_data_generator/setup_ah_dcr.py \
    --sharing-project-id shared-dcr-project \
    --subscriber-email data-sharing-admin@example.com \
    --dataset-to-share merchant_provider \
    --table-to-share users \
    --listing-id merchant_users_listing \
    --listing-display-name "DCR Merchant Users Table" \
    --exchange-id shared_dcr_exchange
```

---

### **Option B: Separate Party DCRs** (Data Sovereignty)

Each party creates their own DCR with **different exchange names**:

#### Commands for E-Wallet Provider (Creates Provider DCR)
```bash
# Command 1: Share provider_users table
uv run python dcr_data_generator/setup_ah_dcr.py \
    --sharing-project-id your-provider-project \
    --subscriber-email merchant-user@example.com \
    --dataset-to-share ewallet_provider \
    --table-to-share provider_users \
    --listing-id provider_users_listing \
    --listing-display-name "DCR Provider Users Table" \
    --exchange-id provider_dcr_exchange

# Command 2: Share transactions table
uv run python dcr_data_generator/setup_ah_dcr.py \
    --sharing-project-id your-provider-project \
    --subscriber-email merchant-user@example.com \
    --dataset-to-share ewallet_provider \
    --table-to-share transactions \
    --listing-id provider_transactions_listing \
    --listing-display-name "DCR Provider Transactions Table" \
    --exchange-id provider_dcr_exchange
```

#### Commands for Merchant (Creates Merchant DCR)
```bash
# Command 1: Share users table
uv run python dcr_data_generator/setup_ah_dcr.py \
    --sharing-project-id your-merchant-project \
    --subscriber-email data-sharing-admin@example.com \
    --dataset-to-share merchant_provider \
    --table-to-share users \
    --listing-id merchant_users_listing \
    --listing-display-name "DCR Merchant Users Table" \
    --exchange-id merchant_dcr_exchange
```

### All Available Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--sharing-project-id` | ✅ | The GCP project ID of the party sharing the data. |
| `--subscriber-email` | ✅ | Email of the data consumer who will be granted subscriber access. |
| `--dataset-to-share` | ✅ | The dataset containing the table (`ewallet_provider` or `merchant_provider`). |
| `--table-to-share` | ✅ | The specific table to share (e.g., `users`, `transactions`, `provider_users`). |
| `--listing-id` | ✅ | A unique ID for the listing (e.g., `provider_users_listing`). |
| `--listing-display-name` | ✅ | The user-friendly display name for the listing. |
| `--location` | ❌ | The GCP location for Analytics Hub resources (default: `US`). |
| `--exchange-id` | ❌ | Unique ID for the data exchange. Choose based on your architecture: Option A (same for all), Option B (different per party). Default: `dcr_bi_directional_exchange` |
| `--allow-egress` | ❌ | If set, allows query results to be saved. **Required for BQML `CREATE MODEL` jobs.** Defaults to `False`. |

## What Happens When You Run the Script

Each time the script runs, it performs these four steps in the context of the `--sharing-project-id`:

1.  **Create Data Clean Room**: It creates a common DCR where listings can be published. If it already exists, it reuses it.
2.  **Create Privacy-Enforced View**: This is the **key privacy step**. The script creates a BigQuery view with analysis rules that enforce:
    - **Aggregation thresholds** (minimum 50 users for Use Cases 2 & 3)
    - **List overlap restrictions** (only joined data visible for Use Cases 1 & 4)
    - **Join restrictions** (queries must join on specific columns)
3.  **Create DCR Listing**: The script creates a listing that shares the privacy-enforced view (not the raw table).
4.  **Grant Access**: It grants the `--subscriber-email` the `roles/analyticshub.subscriber` role, allowing them to discover and use the listing according to the DCR rules.

## Understanding the Dynamic Analysis Rules

The script automatically applies the correct analysis rules based on the specific table being shared, implementing the exact privacy policies needed for each use case:

### Provider Users Table (`ewallet_provider.provider_users`):
**Analysis Rules Applied**:
-   **Aggregation Threshold**: Minimum 50 distinct users (`hashed_email`) required
-   **Join Restriction**: Must join on `hashed_email` column
-   **Enables**: Use Cases 2 & 3 (Customer Segmentation, Fraud Analysis)

### Provider Transactions Table (`ewallet_provider.transactions`):
**Analysis Rules Applied**:
-   **List Overlap**: Must join on `order_id` column
-   **Enables**: Use Case 1 (Transaction Verification)

### Merchant Users Table (`merchant_provider.users`):
**Analysis Rules Applied**:
-   **List Overlap**: Must join on `hashed_email` column
-   **Enables**: Use Case 4 (User Enrichment) and BQML training

---

### Special Note on BQML Training

To allow a `CREATE MODEL` job to run on data from a DCR, the listing must be created with data egress enabled. This is a security consideration, as it allows the results of a query (the training data) to be materialized into a model object.

To enable this for the BQML use case, you must add the `--allow-egress` flag when creating the listing for the merchant's `users` table.

**Example Command for BQML-enabled Listing:**
```bash
# When sharing the merchant's data for the BQML use case, add --allow-egress
uv run python dcr_data_generator/setup_ah_dcr.py \
    --sharing-project-id your-merchant-project \
    --subscriber-email provider-user@example.com \
    --dataset-to-share merchant_provider \
    --table-to-share users \
    --listing-id merchant_users_listing_for_bqml \
    --listing-display-name "DCR Merchant Users for BQML" \
    --exchange-id your_dcr_exchange \
    --allow-egress
```

**Key Privacy Protection**: Raw `SELECT *` queries are **blocked**. Only queries that comply with the analysis rules will succeed.

## Post-Execution: Subscriber Steps

After both script runs are complete, each party can subscribe to the other's listing.

### 1. Navigate to Analytics Hub and Subscribe
- As the **Merchant**, go to Analytics Hub and subscribe to both provider listings:
  - **"DCR Provider Users Table"**
  - **"DCR Provider Transactions Table"**
- As the **Provider**, go to Analytics Hub and subscribe to the merchant listing:
  - **"DCR Merchant Users Table"**

### 2. Run Privacy-Compliant Queries

Subscribers **cannot** see the raw data. The analysis rules enforce strict privacy controls:

- **❌ Blocked**: `SELECT *` queries (no analysis rules satisfied)
- **❌ Blocked**: Non-aggregated queries on provider_users (threshold not met)
- **❌ Blocked**: Queries without required joins (list overlap not satisfied)
- **✅ Allowed**: Aggregated queries with 50+ users grouped by account_tier
- **✅ Allowed**: Join queries using the allowed columns (hashed_email, order_id)

*The query examples from the main `README.md` will now work correctly **only when** they comply with the analysis rules. Queries that don't follow the rules will be automatically blocked by BigQuery.*

**Example of Real Privacy Protection**:
```sql
-- ❌ This will FAIL - violates aggregation threshold
SELECT account_tier, COUNT(*) FROM linked_dataset.provider_users_view GROUP BY 1;

-- ✅ This will SUCCEED - meets 50+ user threshold
SELECT account_tier, COUNT(*) FROM linked_dataset.provider_users_view
WHERE account_tier IN ('Premium', 'Business') GROUP BY 1;
```

## Troubleshooting

### Verification

To verify the setup worked correctly:

1. **Check the Exchange**: Go to Analytics Hub in the provider's project and verify the exchange exists
2. **Check the Listing**: Verify the listing appears and shows the correct dataset
3. **Check Permissions**: Verify the merchant user can see the listing when browsing from their project

## Demo Tips

### Cleanup Commands

**Option A: Single Shared DCR**
```bash
# Delete all listings from shared DCR
gcloud analytics-hub listings delete provider_users_listing \
    --data-exchange=shared_dcr_exchange \
    --location=US \
    --project=shared-dcr-project

gcloud analytics-hub listings delete provider_transactions_listing \
    --data-exchange=shared_dcr_exchange \
    --location=US \
    --project=shared-dcr-project

gcloud analytics-hub listings delete merchant_users_listing \
    --data-exchange=shared_dcr_exchange \
    --location=US \
    --project=shared-dcr-project

# Delete the shared exchange
gcloud analytics-hub data-exchanges delete shared_dcr_exchange \
    --location=US \
    --project=shared-dcr-project
```

**Option B: Separate Party DCRs**
```bash
# Delete provider DCR
gcloud analytics-hub listings delete provider_users_listing \
    --data-exchange=provider_dcr_exchange \
    --location=US \
    --project=your-provider-project

gcloud analytics-hub listings delete provider_transactions_listing \
    --data-exchange=provider_dcr_exchange \
    --location=US \
    --project=your-provider-project

gcloud analytics-hub data-exchanges delete provider_dcr_exchange \
    --location=US \
    --project=your-provider-project

# Delete merchant DCR
gcloud analytics-hub listings delete merchant_users_listing \
    --data-exchange=merchant_dcr_exchange \
    --location=US \
    --project=your-merchant-project

gcloud analytics-hub data-exchanges delete merchant_dcr_exchange \
    --location=US \
    --project=your-merchant-project
```

---

**Related Documentation:**
- [Main Project README](README.md) - Data generation and clean room analytics
- [Google Cloud Analytics Hub Documentation](https://cloud.google.com/bigquery/docs/analytics-hub-introduction)
