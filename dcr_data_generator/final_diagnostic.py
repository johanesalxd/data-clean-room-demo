# dcr_data_generator/final_diagnostic.py

from . import bigquery_utils

WRITE_PROJECT_ID = "johanesa-playground-326616"
MERCHANT_PROVIDER_DATASET = "merchant_provider"
EWALLET_PROVIDER_DATASET = "ewallet_provider"


def run_diagnostic():
    """
    Fetches one order_id from the transactions table and checks
    if it exists in the orders snapshot table.
    """
    print("--- Running Final Diagnostic ---")

    # 1. Get a single order_id from the provider's transactions
    get_one_id_query = f"""
    SELECT order_id
    FROM `{WRITE_PROJECT_ID}.{EWALLET_PROVIDER_DATASET}.transactions`
    LIMIT 1
    """
    print("\nFetching a sample order_id from ewallet_provider.transactions...")
    result = bigquery_utils.execute_sql(get_one_id_query)

    if not result:
        print("!!! Could not retrieve any order_id from the transactions table. The table might be empty.")
        return

    sample_order_id = result[0]['order_id']
    print(f"Found sample order_id: {sample_order_id}")

    # 2. Check if that exact order_id exists in the merchant's snapshot
    check_id_query = f"""
    SELECT COUNT(*) as count
    FROM `{WRITE_PROJECT_ID}.{MERCHANT_PROVIDER_DATASET}.orders`
    WHERE order_id = {sample_order_id}
    """
    print(
        f"\nChecking for order_id {sample_order_id} in merchant_provider.orders...")
    count_result = bigquery_utils.execute_sql(check_id_query)

    if count_result and count_result[0]['count'] > 0:
        print(
            f"!!! SUCCESS: Found matching order_id {sample_order_id}. The join should work.")
    else:
        print(
            f"!!! FAILURE: Did not find matching order_id {sample_order_id}. This is the source of the error.")


if __name__ == "__main__":
    run_diagnostic()
