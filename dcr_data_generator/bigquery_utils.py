# data_clean_room/bigquery_utils.py

"""
Utility functions for interacting with Google BigQuery.
"""

import json
import os

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


def insert_data_from_file(table_id: str, data: list, schema: list):
    """
    Inserts data into a BigQuery table by loading from a temporary JSONL file.
    This method avoids the streaming buffer and makes data immediately available.

    Args:
        table_id: The ID of the table to insert data into.
        data: A list of dictionaries representing the rows to insert.
        schema: The schema of the destination table.
    """
    if not data:
        print(f"No data to insert into {table_id}.")
        return

    temp_file_path = "temp_data.jsonl"
    try:
        # Write data to a temporary JSONL file
        with open(temp_file_path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        )

        print(
            f"Starting load job to insert {len(data)} rows into {table_id}...")
        with open(temp_file_path, "rb") as source_file:
            load_job = client.load_table_from_file(
                source_file, table_id, job_config=job_config
            )

        load_job.result()  # Wait for the job to complete

        destination_table = client.get_table(table_id)
        print(
            f"Load job complete. Loaded {destination_table.num_rows} rows into {table_id}.")

    except Exception as e:
        print(f"An error occurred during the load job for {table_id}: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
