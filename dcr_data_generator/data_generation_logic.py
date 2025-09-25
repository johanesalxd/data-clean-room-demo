# dcr_data_generator/data_generation_logic.py

"""
Contains the core logic for generating the DCR datasets.
This is designed to be called by an orchestrator script.
"""

from google.cloud import bigquery

from . import bigquery_utils
from . import data_generator

# --- Static Configuration ---
SOURCE_PROJECT_ID = "bigquery-public-data"
SOURCE_DATASET = "thelook_ecommerce"
MERCHANT_PROVIDER_DATASET = "merchant_provider"
EWALLET_PROVIDER_DATASET = "ewallet_provider"


def generate_dataset(merchant_project_id: str, provider_project_id: str, target_date: str, table_suffix: str = ""):
    """
    Generates a full set of DCR data for a specific date.

    Args:
        merchant_project_id: The GCP project to write the merchant's datasets to.
        provider_project_id: The GCP project to write the provider's datasets to.
        target_date: The date to snapshot data for (e.g., "2024-01-15").
        table_suffix: An optional suffix to append to the generated table names
                      (e.g., "_inference").
    """
    print(f"\n{'='*50}")
    print(
        f"STARTING DATA GENERATION FOR DATE: {target_date} | SUFFIX: '{table_suffix}'")
    print(f"{'='*50}")

    # Define table names with optional suffix
    provider_users_table = f"{EWALLET_PROVIDER_DATASET}.provider_users{table_suffix}"
    provider_transactions_table = f"{EWALLET_PROVIDER_DATASET}.transactions{table_suffix}"

    # 1. Create a clean, isolated snapshot of the merchant data
    _create_merchant_snapshot(merchant_project_id, target_date, table_suffix)

    # 2. Define the query to get base orders from our new snapshot
    base_query = f"""
    SELECT
        a.order_id, a.user_id, u.email, u.city, a.status,
        SUM(b.sale_price) AS total_price, a.created_at
    FROM `{merchant_project_id}.{MERCHANT_PROVIDER_DATASET}.orders{table_suffix}` AS a
    JOIN `{merchant_project_id}.{MERCHANT_PROVIDER_DATASET}.order_items{table_suffix}` AS b ON a.order_id = b.order_id
    JOIN `{merchant_project_id}.{MERCHANT_PROVIDER_DATASET}.users{table_suffix}` AS u ON a.user_id = u.id
    WHERE a.status NOT IN ('Cancelled', 'Returned')
    GROUP BY a.order_id, a.user_id, u.email, u.city, a.status, a.created_at
    """

    # 3. Execute the query to get base data
    print("\nStep 2: Fetching base order data from snapshot...")
    base_orders = bigquery_utils.execute_sql(base_query)

    # 4. Generate the provider's data
    print("\nStep 3: Generating synthetic data for e-wallet provider...")
    if base_orders is None:
        base_orders = []
    provider_users, transactions = data_generator.generate_provider_data(
        base_orders)

    # 5. Recreate e-wallet provider tables
    print(
        f"\nStep 4: Preparing dataset and tables in '{EWALLET_PROVIDER_DATASET}'...")
    bigquery_utils.create_dataset(
        f"{provider_project_id}.{EWALLET_PROVIDER_DATASET}")

    bigquery_utils.delete_table(
        f"{provider_project_id}.{provider_users_table}")
    bigquery_utils.delete_table(
        f"{provider_project_id}.{provider_transactions_table}")

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

    print(f"Creating table '{provider_users_table}'...")
    bigquery_utils.create_table(
        f"{provider_project_id}.{provider_users_table}", provider_users_schema)
    print(f"Creating table '{provider_transactions_table}'...")
    bigquery_utils.create_table(
        f"{provider_project_id}.{provider_transactions_table}", transactions_schema)

    # 6. Insert the generated data
    print("\nStep 5: Inserting generated data into new tables...")
    bigquery_utils.insert_data_from_file(
        f"{provider_project_id}.{provider_users_table}", provider_users, provider_users_schema)
    bigquery_utils.insert_data_from_file(
        f"{provider_project_id}.{provider_transactions_table}", transactions, transactions_schema)

    print(f"\n--- Data Generation Complete for Suffix: '{table_suffix}' ---")


def _create_merchant_snapshot(merchant_project_id: str, target_date: str, table_suffix: str = ""):
    """
    Internal function to create the merchant data snapshot.
    """
    print(
        f"\n--- Creating or Replacing Merchant Snapshot for Date: {target_date} ---")
    bigquery_utils.create_dataset(
        f"{merchant_project_id}.{MERCHANT_PROVIDER_DATASET}")

    orders_snapshot_query = f"""
    CREATE OR REPLACE TABLE `{merchant_project_id}.{MERCHANT_PROVIDER_DATASET}.orders{table_suffix}` AS
    SELECT * FROM `{SOURCE_PROJECT_ID}.{SOURCE_DATASET}.orders`
    WHERE DATE(created_at) = DATE('{target_date}');
    """
    print(f"\nStep 1.1: Creating snapshot of 'orders{table_suffix}' table...")
    bigquery_utils.execute_sql(orders_snapshot_query, returns_results=False)

    order_items_snapshot_query = f"""
    CREATE OR REPLACE TABLE `{merchant_project_id}.{MERCHANT_PROVIDER_DATASET}.order_items{table_suffix}` AS
    SELECT t2.* FROM `{merchant_project_id}.{MERCHANT_PROVIDER_DATASET}.orders{table_suffix}` AS t1
    JOIN `{SOURCE_PROJECT_ID}.{SOURCE_DATASET}.order_items` AS t2 ON t1.order_id = t2.order_id;
    """
    print(
        f"\nStep 1.2: Creating snapshot of 'order_items{table_suffix}' table...")
    bigquery_utils.execute_sql(
        order_items_snapshot_query, returns_results=False)

    users_snapshot_query = f"""
    CREATE OR REPLACE TABLE `{merchant_project_id}.{MERCHANT_PROVIDER_DATASET}.users{table_suffix}` AS
    WITH RankedUsers AS (
        SELECT u.*, ROW_NUMBER() OVER(PARTITION BY u.id ORDER BY u.created_at DESC) as rn
        FROM `{SOURCE_PROJECT_ID}.{SOURCE_DATASET}.users` AS u
        WHERE u.id IN (SELECT DISTINCT user_id FROM `{merchant_project_id}.{MERCHANT_PROVIDER_DATASET}.orders{table_suffix}`)
    )
    SELECT * EXCEPT(rn) FROM RankedUsers WHERE rn = 1;
    """
    print("\nStep 1.3: Creating de-duplicated snapshot of 'users' table...")
    bigquery_utils.execute_sql(users_snapshot_query, returns_results=False)
    print("\n--- Merchant Snapshot Complete ---")
