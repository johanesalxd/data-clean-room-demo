#!/usr/bin/env python3
"""
Analytics Hub Setup Script for BigQuery Data Clean Room (DCR) Demo

This script automates the creation of a BigQuery Analytics Hub data exchange
and a DCR-enabled listing. This allows the e-wallet provider to share their
data with the merchant in a privacy-preserving manner.

Usage:
    uv run python dcr_data_generator/setup_ah_dcr.py \
        --provider-project-id your-provider-project \
        --merchant-project-id your-merchant-project \
        --location US \
        --exchange-id dcr_exchange \
        --listing-id dcr_listing \
        --subscriber-email merchant-user@example.com
"""

import argparse
import sys

from google.cloud import bigquery_analyticshub_v1
from google.cloud.bigquery_analyticshub_v1 import types
from google.cloud.exceptions import GoogleCloudError


def get_display_name_from_exchange_id(exchange_id: str) -> str:
    """
    Auto-derive a user-friendly display name from the exchange ID.

    Args:
        exchange_id: The unique ID for the exchange

    Returns:
        A human-readable display name for the DCR
    """
    exchange_lower = exchange_id.lower()

    if "provider" in exchange_lower:
        return "E-Wallet Provider Data Clean Room"
    elif "merchant" in exchange_lower:
        return "Merchant Data Clean Room"
    elif "shared" in exchange_lower:
        return "Shared Data Clean Room"
    else:
        # Fallback for custom exchange IDs
        return "Data Clean Room"


def create_data_clean_room(
    client: bigquery_analyticshub_v1.AnalyticsHubServiceClient,
    project_id: str,
    location: str,
    exchange_id: str
) -> str:
    """
    Create a new Data Clean Room (special data exchange) in the provider's project.

    Args:
        client: The Analytics Hub service client
        project_id: The provider's GCP project ID
        location: The GCP location (e.g., 'US')
        exchange_id: The unique ID for the clean room

    Returns:
        The full resource name of the created clean room
    """
    parent = f"projects/{project_id}/locations/{location}"

    # Auto-derive display name from exchange ID
    display_name = get_display_name_from_exchange_id(exchange_id)

    # Create a Data Clean Room by setting sharing_environment_config to dcr_exchange_config
    exchange = types.DataExchange({
        "display_name": display_name,
        "description": "Privacy-preserving data clean room for collaborative analytics between merchant and e-wallet provider",
        "primary_contact": "data-sharing-admin@example.com",
        "documentation": "This clean room enables secure data collaboration with automatic privacy controls and analysis rules.",
        "sharing_environment_config": {
            "dcr_exchange_config": {}
        }
    })

    print(f"Creating Data Clean Room '{exchange_id}' in {parent}...")

    try:
        request = types.CreateDataExchangeRequest(
            parent=parent,
            data_exchange_id=exchange_id,
            data_exchange=exchange
        )

        operation = client.create_data_exchange(request=request)
        print(f"✓ Data Clean Room created successfully: {operation.name}")
        return operation.name

    except GoogleCloudError as e:
        if "already exists" in str(e).lower():
            exchange_name = f"{parent}/dataExchanges/{exchange_id}"
            print(f"⚠ Data Clean Room already exists: {exchange_name}")
            return exchange_name
        else:
            raise


def create_privacy_view(
    sharing_project_id: str,
    dataset_to_share: str,
    table_to_share: str,
    listing_id: str
) -> str:
    """
    Create a view with analysis rules for DCR sharing.

    Args:
        sharing_project_id: The GCP project ID of the party sharing the data
        dataset_to_share: The name of the dataset containing the table
        table_to_share: The name of the specific table to share
        listing_id: The unique ID for the listing (used as view name)

    Returns:
        The view name created
    """
    from google.cloud import bigquery

    client = bigquery.Client(project=sharing_project_id)
    view_name = f"{listing_id}_view"

    # Define analysis rules based on the dataset and table being shared
    if dataset_to_share == "ewallet_provider":
        if table_to_share == "provider_users":
            # For Use Cases 2 & 3: Aggregation threshold for user analysis
            privacy_policy = {
                "aggregation_threshold_policy": {
                    "threshold": 50,
                    "privacy_unit_column": "hashed_email"
                },
                "join_restriction_policy": {
                    "join_condition": "JOIN_ANY",
                    "join_allowed_columns": ["hashed_email"]
                }
            }
        elif table_to_share == "transactions":
            # For Use Case 1: List overlap for transaction verification
            privacy_policy = {
                "join_restriction_policy": {
                    "join_condition": "JOIN_ANY",
                    "join_allowed_columns": ["order_id"]
                }
            }
        else:
            raise ValueError(f"Unsupported table: {table_to_share}")
    elif dataset_to_share == "merchant_provider":
        if table_to_share == "users":
            # For Use Case 4: List overlap for user enrichment
            privacy_policy = {
                "join_restriction_policy": {
                    "join_condition": "JOIN_ANY",
                    "join_allowed_columns": ["hashed_email"]
                }
            }
        else:
            raise ValueError(f"Unsupported table: {table_to_share}")
    else:
        raise ValueError(f"Unsupported dataset: {dataset_to_share}")

    # Create the view with analysis rules
    import json
    privacy_policy_json = json.dumps(privacy_policy)

    query = f"""
    CREATE OR REPLACE VIEW `{sharing_project_id}.{dataset_to_share}.{view_name}`
    OPTIONS(
        privacy_policy = '{privacy_policy_json}'
    )
    AS SELECT * FROM `{sharing_project_id}.{dataset_to_share}.{table_to_share}`
    """

    print(
        f"Creating privacy-enforced view '{view_name}' for table '{table_to_share}'...")
    client.query(query).result()
    print(f"✓ Privacy view created: {dataset_to_share}.{view_name}")

    return view_name


def create_dcr_listing(
    client: bigquery_analyticshub_v1.AnalyticsHubServiceClient,
    exchange_name: str,
    listing_id: str,
    sharing_project_id: str,
    dataset_to_share: str,
    table_to_share: str,
    listing_display_name: str
) -> str:
    """
    Create a BigQuery view listing with analysis rules within the Data Clean Room.

    Args:
        client: The Analytics Hub service client
        exchange_name: The full resource name of the DCR
        listing_id: The unique ID for the listing
        sharing_project_id: The GCP project ID of the party sharing the data
        dataset_to_share: The name of the dataset containing the table
        table_to_share: The name of the specific table to share
        listing_display_name: The display name for the listing

    Returns:
        The full resource name of the created listing
    """
    print(
        f"Creating DCR listing '{listing_id}' for table '{dataset_to_share}.{table_to_share}'...")

    # Step 1: Create privacy-enforced view
    view_name = create_privacy_view(
        sharing_project_id, dataset_to_share, table_to_share, listing_id)

    # Step 2: Share the view in the DCR listing
    view_resource = f"projects/{sharing_project_id}/datasets/{dataset_to_share}/tables/{view_name}"
    documentation = f"Privacy-enforced view for {table_to_share} table. Analysis rules automatically restrict queries to comply with privacy policies."

    try:
        listing_dict = {
            "display_name": listing_display_name,
            "description": f"DCR listing with analysis rules for {dataset_to_share}.{table_to_share}.",
            "primary_contact": "data-sharing-admin@example.com",
            "documentation": documentation,
            "bigquery_dataset": types.Listing.BigQueryDatasetSource({
                "dataset": f"projects/{sharing_project_id}/datasets/{dataset_to_share}",
                "selected_resources": [
                    types.Listing.BigQueryDatasetSource.SelectedResource({
                        "table": view_resource
                    })
                ]
            }),
            "categories": [
                types.Listing.Category.CATEGORY_FINANCIAL,
                types.Listing.Category.CATEGORY_RETAIL
            ],
            "restricted_export_config": {
                "enabled": True,
                "restrict_query_result": True
            }
        }

        request = types.CreateListingRequest(
            parent=exchange_name,
            listing_id=listing_id,
            listing=listing_dict
        )

        operation = client.create_listing(request=request)
        print(f"✓ DCR listing created successfully: {operation.name}")
        return operation.name

    except GoogleCloudError as e:
        if "already exists" in str(e).lower():
            listing_name = f"{exchange_name}/listings/{listing_id}"
            print(f"⚠ Listing already exists: {listing_name}")
            return listing_name
        else:
            raise


def share_listing_with_merchant(
    client: bigquery_analyticshub_v1.AnalyticsHubServiceClient,
    listing_name: str,
    subscriber_email: str
) -> None:
    """
    Grant the merchant access to the listing by setting IAM policy.

    Args:
        client: The Analytics Hub service client
        listing_name: The full resource name of the listing
        subscriber_email: The email address of the merchant user/group
    """
    from google.iam.v1 import iam_policy_pb2
    from google.iam.v1 import policy_pb2

    print(f"Granting access to {subscriber_email}...")

    try:
        # Get current IAM policy
        get_policy_request = iam_policy_pb2.GetIamPolicyRequest(  # pylint: disable=no-member
            resource=listing_name
        )
        current_policy = client.get_iam_policy(request=get_policy_request)

        # Add the subscriber role binding
        binding = policy_pb2.Binding(  # pylint: disable=no-member
            role="roles/analyticshub.subscriber",
            members=[f"user:{subscriber_email}"]
        )

        # Check if binding already exists
        existing_binding = None
        for b in current_policy.bindings:
            if b.role == "roles/analyticshub.subscriber":
                existing_binding = b
                break

        if existing_binding:
            if f"user:{subscriber_email}" not in existing_binding.members:
                existing_binding.members.append(f"user:{subscriber_email}")
                print(
                    f"✓ Added {subscriber_email} to existing subscriber binding")
            else:
                print(f"⚠ {subscriber_email} already has subscriber access")
                return
        else:
            current_policy.bindings.append(binding)
            print(f"✓ Created new subscriber binding for {subscriber_email}")

        # Set the updated policy
        set_policy_request = iam_policy_pb2.SetIamPolicyRequest(  # pylint: disable=no-member
            resource=listing_name,
            policy=current_policy
        )

        client.set_iam_policy(request=set_policy_request)
        print(f"✓ IAM policy updated successfully")

    except GoogleCloudError as e:
        print(f"✗ Error setting IAM policy: {e}")
        raise


def main():
    """
    Main function to orchestrate the Analytics Hub setup.
    """
    parser = argparse.ArgumentParser(
        description="Set up BigQuery Analytics Hub for a Data Clean Room (DCR) demo"
    )
    parser.add_argument(
        "--sharing-project-id",
        type=str,
        required=True,
        help="The GCP project ID of the party sharing the data."
    )
    parser.add_argument(
        "--subscriber-email",
        type=str,
        required=True,
        help="Email of the data consumer who will be granted subscriber access."
    )
    parser.add_argument(
        "--dataset-to-share",
        type=str,
        required=True,
        choices=['ewallet_provider', 'merchant_provider'],
        help="The name of the dataset containing the table to share."
    )
    parser.add_argument(
        "--table-to-share",
        type=str,
        required=True,
        help="The name of the specific table to share from the dataset."
    )
    parser.add_argument(
        "--listing-display-name",
        type=str,
        required=True,
        help="The display name for the new listing."
    )
    parser.add_argument(
        "--location",
        type=str,
        default="US",
        help="The GCP location for Analytics Hub resources (default: US)"
    )
    parser.add_argument(
        "--exchange-id",
        type=str,
        default="dcr_bi_directional_exchange",
        help="Unique ID for the data exchange (default: dcr_bi_directional_exchange)"
    )
    parser.add_argument(
        "--listing-id",
        type=str,
        required=True,
        help="Unique ID for the DCR listing (e.g., 'provider_to_merchant_listing')."
    )

    args = parser.parse_args()

    print("=" * 70)
    print("BigQuery Analytics Hub Setup - Bi-Directional Data Clean Room (DCR)")
    print("=" * 70)
    print(f"Sharing Project: {args.sharing_project_id}")
    print(f"Subscriber Email: {args.subscriber_email}")
    print(f"Dataset to Share: {args.dataset_to_share}")
    print(f"Table to Share: {args.table_to_share}")
    print(f"Location: {args.location}")
    print(f"Exchange ID: {args.exchange_id}")
    print(f"Listing ID: {args.listing_id}")
    print()

    try:
        # Initialize the Analytics Hub client
        client = bigquery_analyticshub_v1.AnalyticsHubServiceClient()

        # Step 1: Create Data Clean Room
        dcr_name = create_data_clean_room(
            client=client,
            project_id=args.sharing_project_id,
            location=args.location,
            exchange_id=args.exchange_id
        )

        # Step 2: Create Listing in DCR
        listing_name = create_dcr_listing(
            client=client,
            exchange_name=dcr_name,
            listing_id=args.listing_id,
            sharing_project_id=args.sharing_project_id,
            dataset_to_share=args.dataset_to_share,
            table_to_share=args.table_to_share,
            listing_display_name=args.listing_display_name
        )

        # Step 3: Share with Merchant
        share_listing_with_merchant(
            client=client,
            listing_name=listing_name,
            subscriber_email=args.subscriber_email
        )

        print("\n" + "=" * 70)
        print("✓ SUCCESS: Data Clean Room setup completed!")
        print("=" * 70)
        print(f"Data Clean Room: {dcr_name}")
        print(f"Listing: {listing_name}")
        print(f"Subscriber: {args.subscriber_email}")
        print()
        print("Next steps for the subscriber:")
        print(
            f"1. As '{args.subscriber_email}', go to Analytics Hub in the subscriber's GCP project.")
        print(
            f"2. Browse available listings and find '{args.listing_display_name}'.")
        print("3. Subscribe to create a linked dataset.")
        print("4. Run queries that comply with the DCR's privacy policy.")
        print("   Direct access to raw data will be denied.")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
