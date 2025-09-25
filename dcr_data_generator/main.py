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
WRITE_PROJECT_ID = "johanesa-playground-326616"
SOURCE_PROJECT_ID = "bigquery-public-data"
SOURCE_DATASET = "thelook_ecommerce"
MERCHANT_PROVIDER_DATASET = "merchant_provider"  # Snapshot dataset
EWALLET_PROVIDER_DATASET = "ewallet_provider"
TARGET_DATE = "2025-09-23"  # Using a more recent date for public data

PROVIDER_USERS_TABLE = f"{EWALLET_PROVIDER_DATASET}.provider_users"
PROVIDER_TRANSACTIONS_TABLE = f"{EWALLET_PROVIDER_DATASET}.transactions"


def create_merchant_snapshot():
    """
    Creates a clean, isolated snapshot of the merchant's data from the
    public dataset into the `merchant_provider` dataset.
    """
    print(
        f"\n--- Creating or Replacing Merchant Snapshot in Dataset: {MERCHANT_PROVIDER_DATASET} ---")
    bigquery_utils.create_dataset(
        f"{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}")

    # 1. Create a snapshot of the orders table for the target date
    orders_snapshot_query = f"""
    CREATE OR REPLACE TABLE `{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}.orders` AS
    SELECT *
    FROM `{SOURCE_PROJECT_ID}.{SOURCE_DATASET}.orders`
    WHERE DATE(created_at) = DATE('{TARGET_DATE}');
    """
    print("\nStep 1.1: Creating snapshot of 'orders' table...")
    bigquery_utils.execute_sql(orders_snapshot_query, returns_results=False)

    # 2. Create a snapshot of the order_items table
    order_items_snapshot_query = f"""
    CREATE OR REPLACE TABLE `{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}.order_items` AS
    SELECT t2.*
    FROM `{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}.orders` AS t1
    JOIN `{SOURCE_PROJECT_ID}.{SOURCE_DATASET}.order_items` AS t2
        ON t1.order_id = t2.order_id;
    """
    print("\nStep 1.2: Creating snapshot of 'order_items' table...")
    bigquery_utils.execute_sql(
        order_items_snapshot_query, returns_results=False)

    # 3. Create a de-duplicated snapshot of the users table
    users_snapshot_query = f"""
    CREATE OR REPLACE TABLE `{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}.users` AS
    WITH RankedUsers AS (
        SELECT
            u.*,
            ROW_NUMBER() OVER(PARTITION BY u.id ORDER BY u.created_at DESC) as rn
        FROM `{SOURCE_PROJECT_ID}.{SOURCE_DATASET}.users` AS u
        WHERE u.id IN (SELECT DISTINCT user_id FROM `{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}.orders`)
    )
    SELECT * EXCEPT(rn)
    FROM RankedUsers
    WHERE rn = 1;
    """
    print("\nStep 1.3: Creating de-duplicated snapshot of 'users' table...")
    bigquery_utils.execute_sql(users_snapshot_query, returns_results=False)
    print("\n--- Merchant Snapshot Complete ---")


def main():
    """
    Main function to execute the data generation pipeline.
    """
    print("--- Starting Data Clean Room Simulation Data Generation ---")

    # 1. Create a clean, isolated snapshot of the merchant data
    create_merchant_snapshot()

    # 2. Define the query to get base orders from our new snapshot
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
        `{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}.orders` AS a
    JOIN
        `{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}.order_items` AS b ON a.order_id = b.order_id
    JOIN
        `{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}.users` AS u ON a.user_id = u.id
    WHERE
        a.status NOT IN ('Cancelled', 'Returned')
    GROUP BY
        a.order_id, a.user_id, u.email, u.city, a.status, a.created_at
    """

    # 3. Execute the query to get base data
    print("\nStep 2: Fetching base order data from snapshot...")
    base_orders = bigquery_utils.execute_sql(base_query)

    # 4. Generate the provider's data
    print("\nStep 2: Generating synthetic data for e-wallet provider...")
    provider_users, transactions = data_generator.generate_provider_data(
        base_orders)

    # 5. Recreate e-wallet provider tables
    print(
        f"\nStep 4: Preparing dataset and tables in '{EWALLET_PROVIDER_DATASET}'...")
    bigquery_utils.create_dataset(
        f"{WRITE_PROJECT_ID}.{EWALLET_PROVIDER_DATASET}")

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

    # 6. Insert the generated data
    print("\nStep 5: Inserting generated data into new tables...")
    bigquery_utils.insert_data(
        f"{WRITE_PROJECT_ID}.{PROVIDER_USERS_TABLE}", provider_users)
    bigquery_utils.insert_data(
        f"{WRITE_PROJECT_ID}.{PROVIDER_TRANSACTIONS_TABLE}", transactions)

    print("\n--- Data Generation Complete ---")


if __name__ == "__main__":
    main()
