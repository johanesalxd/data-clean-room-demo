# BigQuery Analytics Hub Setup Guide

This document provides a comprehensive guide to setting up both **Data Clean Rooms (DCRs)** and standard **Data Exchanges (DCXs)** using the provided automation scripts.

## 1. Overview: DCR vs. DCX

Before setting up, it's crucial to understand the difference between the two sharing mechanisms available in BigQuery Analytics Hub.

### Data Clean Room (DCR)
-   **Purpose**: For sharing sensitive data with **privacy-preserving controls**.
-   **Mechanism**: Subscribers **cannot** access the raw data. They can only run queries that comply with pre-defined **analysis rules** (e.g., aggregation thresholds, join restrictions).
-   **Use Case**: Collaborative analytics where trust is limited or data is highly sensitive. Ideal for customer segmentation, and fraud analysis without revealing underlying user-level data.
-   **Script**: `setup_ah_dcr.py`

### Data Exchange (DCX)
-   **Purpose**: For sharing data directly with **trusted partners**.
-   **Mechanism**: Subscribers get **direct, read-only access** to the entire shared dataset. There are no analysis rules enforced.
-   **Use Case**: Collaborative projects where direct data access is required, such as training a joint Machine Learning model.
-   **Script**: `setup_ah_dcx.py`

---

## 2. Prerequisites

These steps are required before running either setup script.

### 1. Install Dependencies
Ensure you have the required Python packages installed:
```bash
uv sync
```

### 2. Authenticate with Google Cloud
Make sure your local SDK is authenticated and has the necessary permissions:
```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Required IAM Permissions
The user or service account running the scripts must have the following IAM roles in the project where the data is being shared from:
-   `roles/analyticshub.admin` (to create exchanges and listings)
-   `roles/bigquery.dataEditor` (to create the necessary authorized views for DCRs)

### 4. Generate Demo Data
Before setting up sharing, you must first generate the synthetic datasets:
```bash
uv run python -m dcr_data_generator.main --merchant-project-id your-merchant-project --provider-project-id your-provider-project
```

---

## 3. Setup Instructions & Examples

Both scripts are flexible and allow either the merchant or the provider to be the data sharer.

### A. Data Clean Room (DCR) Setup

Use the `setup_ah_dcr.py` script to create a listing with privacy controls. Each listing can only contain a single table (view).

#### All Available DCR Arguments
| Argument | Required | Description |
|----------|----------|-------------|
| `--sharing-project-id` | ✅ | The GCP project ID of the party sharing the data. |
| `--subscriber-email` | ✅ | Email of the data consumer. |
| `--dataset-to-share` | ✅ | The dataset containing the table (`ewallet_provider` or `merchant_provider`). |
| `--table-to-share` | ✅ | The specific table to share (e.g., `users`, `transactions`). |
| `--listing-id` | ✅ | A unique ID for the listing (e.g., `provider_users_listing`). |
| `--listing-display-name` | ✅ | The user-friendly display name for the listing. |
| `--exchange-id` | ✅ | Unique ID for the data clean room (e.g., `provider_dcr_exchange`). |
| `--location` | ❌ | The GCP location for resources (default: `US`). |

#### DCR Example Commands

**Example 1: Provider shares the `provider_users` table with the Merchant**
```bash
uv run python dcr_data_generator/setup_ah_dcr.py \
    --sharing-project-id your-provider-project-id \
    --subscriber-email merchant-subscriber-email@example.com \
    --dataset-to-share ewallet_provider \
    --table-to-share provider_users \
    --listing-id provider_users_listing \
    --listing-display-name "DCR Provider Users Table" \
    --exchange-id provider_dcr_exchange
```

**Example 2: Merchant shares the `users` table with the Provider**
```bash
uv run python dcr_data_generator/setup_ah_dcr.py \
    --sharing-project-id your-merchant-project-id \
    --subscriber-email provider-subscriber-email@example.com \
    --dataset-to-share merchant_provider \
    --table-to-share users \
    --listing-id merchant_users_listing \
    --listing-display-name "DCR Merchant Users Table" \
    --exchange-id merchant_dcr_exchange
```

---

### B. Data Exchange (DCX) Setup

Use the `setup_ah_dcx.py` script to share a **full dataset** directly. This is required for use cases like BQML training where data egress is necessary.

#### All Available DCX Arguments
| Argument | Required | Description |
|----------|----------|-------------|
| `--sharing-project-id` | ✅ | The GCP project ID of the party sharing the data. |
| `--subscriber-email` | ✅ | Email address of the data consumer. |
| `--dataset-to-share` | ✅ | The name of the dataset to share (`ewallet_provider` or `merchant_provider`). |
| `--listing-display-name`| ✅ | The user-friendly display name for the listing. |
| `--exchange-id` | ✅ | Unique ID for the data exchange (e.g., `provider_dcx_exchange`). |
| `--listing-id` | ✅ | Unique ID for the data listing (e.g., `provider_full_dataset_listing`). |
| `--location` | ❌ | The GCP location for resources (default: `US`). |

#### DCX Example Commands

**Example 1: Provider shares the `ewallet_provider` dataset with the Merchant**
```bash
uv run python dcr_data_generator/setup_ah_dcx.py \
    --sharing-project-id your-provider-project-id \
    --subscriber-email merchant-subscriber-email@example.com \
    --dataset-to-share ewallet_provider \
    --listing-id provider_ewallet_dataset_listing \
    --listing-display-name "DCX E-Wallet Provider Full Dataset" \
    --exchange-id provider_dcx_exchange
```

**Example 2: Merchant shares the `merchant_provider` dataset with the Provider**
This enables the BQML use case where the provider needs to join their data with the merchant's data to train a model.
```bash
uv run python dcr_data_generator/setup_ah_dcx.py \
    --sharing-project-id your-merchant-project-id \
    --subscriber-email provider-subscriber-email@example.com \
    --dataset-to-share merchant_provider \
    --listing-id merchant_dataset_listing \
    --listing-display-name "DCX Merchant Full Dataset" \
    --exchange-id merchant_dcx_exchange
```

---

## 4. Post-Setup: Subscribing and Querying

After a listing is created (either DCR or DCX), the subscriber must perform the following steps:

1.  **Navigate to Analytics Hub**: In the Google Cloud Console, go to **BigQuery -> Analytics Hub**.
2.  **Find the Listing**: Browse the listings you have access to. You can filter by exchange name.
3.  **Subscribe**: Click on the desired listing and subscribe to it. This will create a new **linked dataset** in your project.
4.  **Query the Data**: You can now write queries against the tables in the newly created linked dataset.
    *   For **DCR listings**, your queries must comply with the analysis rules (e.g., use `SELECT WITH AGGREGATION_THRESHOLD`).
    *   For **DCX listings**, you can query the data directly without restrictions.

## 5. Cleanup

To remove the resources created by these scripts, use the `gcloud` CLI.

### Delete a Listing
```bash
# Example for a DCR listing
gcloud analytics-hub listings delete provider_users_listing \
    --data-exchange=provider_dcr_exchange \
    --location=US \
    --project=your-provider-project-id

# Example for a DCX listing
gcloud analytics-hub listings delete provider_ewallet_dataset_listing \
    --data-exchange=provider_dcx_exchange \
    --location=US \
    --project=your-provider-project-id
```

### Delete an Exchange
**Note:** You must delete all listings within an exchange before you can delete the exchange itself.
```bash
# Example for a DCR
gcloud analytics-hub data-exchanges delete provider_dcr_exchange \
    --location=US \
    --project=your-provider-project-id

# Example for a DCX
gcloud analytics-hub data-exchanges delete merchant_dcx_exchange \
    --location=US \
    --project=your-merchant-project-id
