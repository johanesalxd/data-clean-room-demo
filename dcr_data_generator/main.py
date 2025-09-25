# dcr_data_generator/main.py

"""
Main orchestrator script to generate both training and inference datasets
for the BigQuery Data Clean Room simulation.
"""

import argparse

from . import data_generation_logic

# --- Configuration ---
# This is the default project ID, can be overridden with --project-id
DEFAULT_WRITE_PROJECT_ID = "your-gcp-project"
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
        "--project-id",
        type=str,
        default=DEFAULT_WRITE_PROJECT_ID,
        help="The GCP project ID to write the datasets to."
    )
    args = parser.parse_args()

    # --- Generate Training Data ---
    data_generation_logic.generate_dataset(
        write_project_id=args.project_id,
        target_date=TRAINING_DATE,
        table_suffix=""  # No suffix for the main training tables
    )

    # --- Generate Inference Data ---
    data_generation_logic.generate_dataset(
        write_project_id=args.project_id,
        target_date=INFERENCE_DATE,
        table_suffix="_inference"  # Suffix for inference tables
    )


if __name__ == "__main__":
    main()
