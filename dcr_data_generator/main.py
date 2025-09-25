# dcr_data_generator/main.py

"""
Main orchestrator script to generate both training and inference datasets
for the BigQuery Data Clean Room simulation.
"""

import argparse

from . import data_generation_logic
from . import hashing_logic

# --- Configuration ---
TRAINING_DATE = "2025-09-23"
INFERENCE_DATE = "2025-09-24"


def main():
    """
    Parses command-line arguments and runs the data generation for both
    training and inference datasets.
    """
    parser = argparse.ArgumentParser(
        description="DCR Data Generation Orchestrator")
    parser.add_argument(
        "--merchant-project-id",
        type=str,
        required=True,
        help="The GCP project ID for the merchant's data."
    )
    parser.add_argument(
        "--provider-project-id",
        type=str,
        required=True,
        help="The GCP project ID for the e-wallet provider's data."
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["all", "generate", "hash"],
        default="all",
        help="Which step to execute: 'all' (default), 'generate' (data only), or 'hash' (hashing only)."
    )
    args = parser.parse_args()

    if args.step in ["all", "generate"]:
        # --- Generate Training Data ---
        data_generation_logic.generate_dataset(
            merchant_project_id=args.merchant_project_id,
            provider_project_id=args.provider_project_id,
            target_date=TRAINING_DATE,
            table_suffix=""  # No suffix for the main training tables
        )

        # --- Generate Inference Data ---
        data_generation_logic.generate_dataset(
            merchant_project_id=args.merchant_project_id,
            provider_project_id=args.provider_project_id,
            target_date=INFERENCE_DATE,
            table_suffix="_inference"  # Suffix for inference tables
        )

    if args.step in ["all", "hash"]:
        # --- Add Secure Hashed Email Columns ---
        hashing_logic.add_hashed_email_columns(
            merchant_project_id=args.merchant_project_id,
            provider_project_id=args.provider_project_id
        )


if __name__ == "__main__":
    main()
