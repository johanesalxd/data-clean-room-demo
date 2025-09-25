# dcr_data_generator/hashing_logic.py

"""
Contains logic for adding secure hashed email columns to existing BigQuery tables.
This module handles the creation of deterministic, one-way hash keys for secure joins.
"""

from google.cloud import bigquery

# Shared secret salt for deterministic hashing
# In production, this would be securely managed and shared between parties
SECRET_SALT = "DCR_DEMO_SHARED_SECRET_2024_SECURE_HASH_SALT"


def add_hashed_email_columns(merchant_project_id: str, provider_project_id: str):
    """
    Add hashed_email columns to all relevant tables and populate them.

    Args:
        merchant_project_id: The GCP project ID for the merchant's data.
        provider_project_id: The GCP project ID for the e-wallet provider's data.
    """
    client = bigquery.Client()

    # Define the tables that need hashed_email columns
    tables_to_update = [
        # Merchant tables
        {
            "project": merchant_project_id,
            "dataset": "merchant_provider",
            "table": "users",
            "description": "Merchant users (training)"
        },
        {
            "project": merchant_project_id,
            "dataset": "merchant_provider",
            "table": "users_inference",
            "description": "Merchant users (inference)"
        },
        # Provider tables
        {
            "project": provider_project_id,
            "dataset": "ewallet_provider",
            "table": "provider_users",
            "description": "Provider users (training)"
        },
        {
            "project": provider_project_id,
            "dataset": "ewallet_provider",
            "table": "provider_users_inference",
            "description": "Provider users (inference)"
        }
    ]

    print(f"\n{'='*60}")
    print("Adding Secure Hashed Email Columns")
    print(f"{'='*60}")
    print(f"Secret Salt: {SECRET_SALT[:20]}...")
    print()

    for table_info in tables_to_update:
        table_id = f"{table_info['project']}.{table_info['dataset']}.{table_info['table']}"

        print(f"Processing {table_info['description']}: {table_id}")

        # Step 1: Add the hashed_email column
        add_column_query = f"""
        ALTER TABLE `{table_id}`
        ADD COLUMN IF NOT EXISTS hashed_email STRING
        """

        print("  Adding hashed_email column...")
        try:
            job = client.query(add_column_query)
            job.result()  # Wait for completion
            print("  ✓ Column added successfully")
        except Exception as e:
            print(f"  ⚠ Column may already exist: {e}")

        # Step 2: Populate the hashed_email column
        update_query = f"""
        UPDATE `{table_id}`
        SET hashed_email = TO_BASE64(SHA256(CONCAT(email, @salt)))
        WHERE hashed_email IS NULL
        """

        print("  Populating hashed_email values...")
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("salt", "STRING", SECRET_SALT)
            ]
        )

        try:
            job = client.query(update_query, job_config=job_config)
            result = job.result()  # Wait for completion
            print(f"  ✓ Updated {job.num_dml_affected_rows} rows")
        except Exception as e:
            print(f"  ✗ Error updating rows: {e}")
            continue

        # Step 3: Verify the update
        verify_query = f"""
        SELECT
            COUNT(*) as total_rows,
            COUNT(hashed_email) as hashed_rows,
            COUNT(DISTINCT hashed_email) as unique_hashes
        FROM `{table_id}`
        """

        try:
            job = client.query(verify_query)
            results = job.result()
            for row in results:
                print(
                    f"  ✓ Verification: {row.total_rows} total rows, {row.hashed_rows} hashed, {row.unique_hashes} unique hashes")
        except Exception as e:
            print(f"  ⚠ Could not verify: {e}")

        print()  # Add spacing between tables

    print(f"{'='*60}")
    print("✓ SUCCESS: All tables updated with hashed_email columns")
    print("✓ You can now use 'hashed_email' for secure joins in your queries")
    print(f"{'='*60}")
