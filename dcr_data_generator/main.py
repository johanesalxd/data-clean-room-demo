# data_clean_room/main.py

"""
Main script to orchestrate the data generation process for the
BigQuery data clean room simulation.
"""

import time

from google.cloud import bigquery

from . import bigquery_utils
from . import data_generator

# --- Configuration ---
# <-- UPDATE THIS WITH YOUR GCP PROJECT ID
WRITE_PROJECT_ID = "your-gcp-project"
SOURCE_PROJECT_ID = "bigquery-public-data"
MERCHANT_DATASET = "thelook_ecommerce"
PROVIDER_DATASET = "ewallet_provider"
TARGET_DATE = "2025-09-23"  # Using a more recent date for public data

PROVIDER_USERS_TABLE = f"{PROVIDER_DATASET}.provider_users"
PROVIDER_TRANSACTIONS_TABLE = f"{PROVIDER_DATASET}.transactions"


def main():
    """
    Main function to execute the data generation pipeline.
    """
    print("--- Starting Data Clean Room Simulation Data Generation ---")

    # 1. Define the query to get base orders from the public dataset
    base_query = f"""
    SELECT
        a.order_id,
        a.user_id,
        u.email,
        u.city,
        a.status,
        SUM(b.sale_price) AS total_price,
        a.created_at
    FROM
        `{SOURCE_PROJECT_ID}.{MERCHANT_DATASET}.orders` AS a
    JOIN
        `{SOURCE_PROJECT_ID}.{MERCHANT_DATASET}.order_items` AS b ON a.order_id = b.order_id
    JOIN
        `{SOURCE_PROJECT_ID}.{MERCHANT_DATASET}.users` AS u ON a.user_id = u.id
    WHERE
        DATE(a.created_at) = DATE('{TARGET_DATE}')
        AND a.status NOT IN ('Cancelled', 'Returned')
    GROUP BY
        a.order_id, a.user_id, u.email, u.city, a.status, a.created_at
    """

    # 2. Execute the query to get base data
    print("\nStep 1: Fetching base order data from merchant...")
    base_orders = bigquery_utils.execute_query(base_query)

    # 3. Generate the provider's data
    print("\nStep 2: Generating synthetic data for e-wallet provider...")
    provider_users, transactions = data_generator.generate_provider_data(
        base_orders)

    # 4. Recreate tables to ensure schema is up-to-date
    print(f"\nStep 3: Preparing dataset and tables in '{PROVIDER_DATASET}'...")
    bigquery_utils.create_dataset(f"{WRITE_PROJECT_ID}.{PROVIDER_DATASET}")

    # Delete tables first to ensure clean creation with correct schema
    bigquery_utils.delete_table(f"{WRITE_PROJECT_ID}.{PROVIDER_USERS_TABLE}")
    bigquery_utils.delete_table(
        f"{WRITE_PROJECT_ID}.{PROVIDER_TRANSACTIONS_TABLE}")

    provider_users_schema = [
        bigquery.SchemaField("provider_user_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("date_of_birth", "DATE"),
        bigquery.SchemaField("city", "STRING"),
        bigquery.SchemaField("account_tier", "STRING"),
        bigquery.SchemaField("is_verified_user", "BOOLEAN"),
    ]

    transactions_schema = [
        bigquery.SchemaField("transaction_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("order_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("provider_user_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("transaction_amount", "FLOAT64"),
        bigquery.SchemaField("transaction_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("status", "STRING"),
    ]

    print(f"Creating table '{PROVIDER_USERS_TABLE}'...")
    bigquery_utils.create_table(
        f"{WRITE_PROJECT_ID}.{PROVIDER_USERS_TABLE}", provider_users_schema)

    print(f"Creating table '{PROVIDER_TRANSACTIONS_TABLE}'...")
    bigquery_utils.create_table(
        f"{WRITE_PROJECT_ID}.{PROVIDER_TRANSACTIONS_TABLE}", transactions_schema)

    # 5. Insert the generated data
    print("\nStep 4: Inserting generated data into new tables...")
    bigquery_utils.insert_data(
        f"{WRITE_PROJECT_ID}.{PROVIDER_USERS_TABLE}", provider_users)
    bigquery_utils.insert_data(
        f"{WRITE_PROJECT_ID}.{PROVIDER_TRANSACTIONS_TABLE}", transactions)

    print("\n--- Data Generation Complete ---")


if __name__ == "__main__":
    main()
