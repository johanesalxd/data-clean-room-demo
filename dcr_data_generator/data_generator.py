# data_clean_room/data_generator.py

"""
Functions for generating synthetic data for the e-wallet provider.
"""

from datetime import date
from datetime import timedelta
import random
import uuid


def _generate_random_dob(start_year=1950, end_year=2005):
    """Generates a random date of birth."""
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date.isoformat()


def generate_provider_data(base_orders: list):
    """
    Generates synthetic data for the provider_users and transactions tables.

    Args:
        base_orders: A list of dictionaries representing the base order data
                     queried from the merchant's database.

    Returns:
        A tuple containing two lists of dictionaries:
        - provider_users_data
        - transactions_data
    """
    print(f"Received {len(base_orders)} base orders. Applying 50% sampling...")

    # Simulate provider market share by sampling 50% of the orders
    sampled_orders = random.sample(base_orders, k=int(len(base_orders) * 0.5))
    print(f"Sampled {len(sampled_orders)} orders for the provider.")

    provider_users_data = []
    transactions_data = []

    # Create a unique set of users from the sampled orders
    unique_users = {order['email']: order for order in sampled_orders}.values()

    user_email_to_id_map = {}
    provider_user_id_counter = 1

    print(f"Generating user data for {len(unique_users)} unique users...")
    for user in unique_users:
        # Assign a new internal ID for the provider
        user_email_to_id_map[user['email']] = provider_user_id_counter

        provider_users_data.append({
            "provider_user_id": provider_user_id_counter,
            "email": user['email'],
            "date_of_birth": _generate_random_dob(),
            "city": user['city'],
            "account_tier": random.choice(['Free', 'Premium', 'Business']),
            "is_verified_user": random.choice([True, False])
        })
        provider_user_id_counter += 1

    print(f"Generating transaction data for {len(sampled_orders)} orders...")
    for order in sampled_orders:
        provider_user_id = user_email_to_id_map.get(order['email'])
        if provider_user_id:
            transactions_data.append({
                "transaction_id": str(uuid.uuid4()),
                "order_id": order["order_id"],
                "provider_user_id": provider_user_id,
                "transaction_amount": float(order["total_price"]),
                "transaction_timestamp": order["created_at"].isoformat(),
                "status": order["status"]
            })

    return provider_users_data, transactions_data
