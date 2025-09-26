#!/usr/bin/env python3
"""
Analytics Hub Setup Script for BigQuery Data Clean Room Demo

This script automates the creation of a BigQuery Analytics Hub data exchange
and listing, enabling the e-wallet provider to share their data with the merchant
through a normal data exchange (not a clean room).

Usage:
    uv run python dcr_data_generator/setup_ah_dcx.py \
        --provider-project-id your-provider-project \
        --merchant-project-id your-merchant-project \
        --location US \
        --exchange-id demo_exchange \
        --listing-id provider_data_listing \
        --subscriber-email merchant-user@example.com
"""

import argparse
import sys

from google.cloud import bigquery_analyticshub_v1
from google.cloud.bigquery_analyticshub_v1 import types
from google.cloud.exceptions import GoogleCloudError


def create_data_exchange(
    client: bigquery_analyticshub_v1.AnalyticsHubServiceClient,
    project_id: str,
    location: str,
    exchange_id: str
) -> str:
    """
    Create a new Data Exchange in the provider's project.

    Args:
        client: The Analytics Hub service client
        project_id: The provider's GCP project ID
        location: The GCP location (e.g., 'US')
        exchange_id: The unique ID for the exchange

    Returns:
        The full resource name of the created exchange
    """
    parent = f"projects/{project_id}/locations/{location}"

    exchange = types.DataExchange({
        "display_name": "E-Wallet Provider Data Exchange",
        "description": "Data exchange for sharing e-wallet provider data with merchant partners",
        "primary_contact": "provider-admin@example.com",
        "documentation": "This exchange contains e-wallet transaction and user data for collaborative analytics."
    })

    print(f"Creating Data Exchange '{exchange_id}' in {parent}...")

    try:
        request = types.CreateDataExchangeRequest(
            parent=parent,
            data_exchange_id=exchange_id,
            data_exchange=exchange
        )

        operation = client.create_data_exchange(request=request)
        print(f"✓ Data Exchange created successfully: {operation.name}")
        return operation.name

    except GoogleCloudError as e:
        if "already exists" in str(e).lower():
            exchange_name = f"{parent}/dataExchanges/{exchange_id}"
            print(f"⚠ Data Exchange already exists: {exchange_name}")
            return exchange_name
        else:
            raise


def create_listing(
    client: bigquery_analyticshub_v1.AnalyticsHubServiceClient,
    exchange_name: str,
    listing_id: str,
    provider_project_id: str
) -> str:
    """
    Create a new Listing within the Data Exchange.

    Args:
        client: The Analytics Hub service client
        exchange_name: The full resource name of the exchange
        listing_id: The unique ID for the listing
        provider_project_id: The provider's GCP project ID

    Returns:
        The full resource name of the created listing
    """
    print(f"Creating Listing '{listing_id}' in exchange...")

    try:
        # Create the listing using the proper request object
        request = types.CreateListingRequest(
            parent=exchange_name,
            listing_id=listing_id,
            listing={
                "display_name": "E-Wallet Provider Dataset",
                "description": "Complete e-wallet provider dataset including user profiles and transaction data",
                "primary_contact": "provider-admin@example.com",
                "documentation": "This listing provides access to the ewallet_provider dataset containing provider_users and transactions tables.",
                "bigquery_dataset": types.Listing.BigQueryDatasetSource({
                    "dataset": f"projects/{provider_project_id}/datasets/ewallet_provider"
                }),
                "categories": [
                    types.Listing.Category.CATEGORY_FINANCIAL,
                    types.Listing.Category.CATEGORY_RETAIL
                ]
            }
        )

        operation = client.create_listing(request=request)
        print(f"✓ Listing created successfully: {operation.name}")
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
        description="Set up BigQuery Analytics Hub for data sharing demo"
    )
    parser.add_argument(
        "--provider-project-id",
        type=str,
        required=True,
        help="The GCP project ID of the data provider (e-wallet provider)"
    )
    parser.add_argument(
        "--merchant-project-id",
        type=str,
        required=True,
        help="The GCP project ID of the data consumer (merchant)"
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
        default="demo_exchange",
        help="Unique ID for the data exchange (default: demo_exchange)"
    )
    parser.add_argument(
        "--listing-id",
        type=str,
        default="provider_data_listing",
        help="Unique ID for the data listing (default: provider_data_listing)"
    )
    parser.add_argument(
        "--subscriber-email",
        type=str,
        required=True,
        help="Email address of the merchant user/group to grant access"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("BigQuery Analytics Hub Setup - Normal Data Exchange")
    print("=" * 70)
    print(f"Provider Project: {args.provider_project_id}")
    print(f"Merchant Project: {args.merchant_project_id}")
    print(f"Location: {args.location}")
    print(f"Exchange ID: {args.exchange_id}")
    print(f"Listing ID: {args.listing_id}")
    print(f"Subscriber Email: {args.subscriber_email}")
    print()

    try:
        # Initialize the Analytics Hub client
        client = bigquery_analyticshub_v1.AnalyticsHubServiceClient()

        # Step 1: Create Data Exchange
        exchange_name = create_data_exchange(
            client=client,
            project_id=args.provider_project_id,
            location=args.location,
            exchange_id=args.exchange_id
        )

        # Step 2: Create Listing
        listing_name = create_listing(
            client=client,
            exchange_name=exchange_name,
            listing_id=args.listing_id,
            provider_project_id=args.provider_project_id
        )

        # Step 3: Share with Merchant
        share_listing_with_merchant(
            client=client,
            listing_name=listing_name,
            subscriber_email=args.subscriber_email
        )

        print("\n" + "=" * 70)
        print("✓ SUCCESS: Analytics Hub setup completed!")
        print("=" * 70)
        print(f"Exchange: {exchange_name}")
        print(f"Listing: {listing_name}")
        print(f"Subscriber: {args.subscriber_email}")
        print()
        print("Next steps for the merchant:")
        print(
            f"1. Go to Analytics Hub in the {args.merchant_project_id} project")
        print("2. Browse available listings and find the 'E-Wallet Provider Dataset'")
        print("3. Subscribe to create a linked dataset in their project")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
