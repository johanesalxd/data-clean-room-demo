# data_clean_room/bigquery_utils.py

"""
Utility functions for interacting with Google BigQuery.
"""

import functools
import time

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Initialize the BigQuery client
client = bigquery.Client()


def execute_sql(query: str, returns_results=True):
    """
    Executes a SQL statement in BigQuery.

    Args:
        query: The SQL statement to execute.
        returns_results: If True, fetches and returns query results.

    Returns:
        A list of dictionaries representing the query results if returns_results is True,
        otherwise None.
    """
    print(f"Executing SQL...")
    try:
        query_job = client.query(query)
        print("Waiting for query to complete...")
        query_job.result()  # Waits for the job to complete.
        print("Query completed.")

        if returns_results:
            # For SELECT statements, fetch the results.
            destination_table = query_job.destination
            destination_table = client.get_table(destination_table)
            rows = client.list_rows(destination_table)
            return [dict(row) for row in rows]

        return None  # For DDL/DML statements
    except Exception as e:
        print(f"An error occurred during SQL execution: {e}")
        if returns_results:
            return []
        return None


def create_dataset(dataset_id: str):
    """
    Creates a new dataset in BigQuery if it doesn't already exist.

    Args:
        dataset_id: The ID of the dataset to create.
    """
    try:
        client.get_dataset(dataset_id)  # Make an API request.
        print(f"Dataset {dataset_id} already exists.")
    except NotFound:
        print(f"Dataset {dataset_id} not found, creating it.")
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"  # You can change the location if needed
        # Make an API request.
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {client.project}.{dataset.dataset_id}")


def delete_table(table_id: str):
    """
    Deletes a BigQuery table if it exists.

    Args:
        table_id: The ID of the table to delete.
    """
    try:
        client.delete_table(table_id)
        print(f"Table {table_id} deleted.")
    except NotFound:
        print(f"Table {table_id} not found, nothing to delete.")
    except Exception as e:
        print(f"An error occurred while deleting table {table_id}: {e}")


def create_table(table_id: str, schema: list):
    """
    Creates a new table in BigQuery with the specified schema.

    Args:
        table_id: The ID of the table to create.
        schema: A list of SchemaField objects defining the table schema.
    """
    try:
        client.get_table(table_id)
        print(f"Table {table_id} already exists.")
    except NotFound:
        print(f"Table {table_id} not found, creating it.")
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        print(
            f"Created table {table.project}.{table.dataset_id}.{table.table_id}")


def retry_on_not_found(max_retries=3):
    """
    A decorator to retry a function call if a `NotFound` exception is raised.
    Implements exponential backoff.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except NotFound:
                    attempt += 1
                    if attempt >= max_retries:
                        print(
                            f"Operation failed after {max_retries} attempts. Giving up.")
                        raise
                    else:
                        wait_time = 2 ** attempt
                        print(
                            f"NotFound error. Retrying in {wait_time} seconds... (Attempt {attempt}/{max_retries})")
                        time.sleep(wait_time)
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    return
        return wrapper
    return decorator


@retry_on_not_found()
def insert_data(table_id: str, data: list):
    """
    Inserts data into a BigQuery table from a list of dictionaries.
    Retries on NotFound errors to handle table creation race conditions.

    Args:
        table_id: The ID of the table to insert data into.
        data: A list of dictionaries representing the rows to insert.
    """
    if not data:
        print(f"No data to insert into {table_id}.")
        return

    try:
        errors = client.insert_rows_json(table_id, data)
        if not errors:
            print(f"Successfully inserted {len(data)} rows into {table_id}.")
        else:
            print(
                f"Encountered errors while inserting rows into {table_id}: {errors}")
    except Exception as e:
        print(
            f"An unexpected error occurred during data insertion into {table_id}: {e}")
