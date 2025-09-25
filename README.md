# BigQuery Data Clean Room Simulation

This project contains a Python script to generate synthetic data for a BigQuery Data Clean Room (DCR) demo. It simulates a realistic data-sharing partnership between an e-commerce merchant and an e-wallet payment provider.

The script first creates a clean, isolated snapshot of source data from `bigquery-public-data.thelook_ecommerce` into your own GCP project. It then uses this clean snapshot to generate the synthetic provider data. This ensures the demo is reproducible and resilient to changes in the public dataset.

## 1. Architecture: A Two-Step Process

The data generation pipeline is a two-step process designed for robustness and data integrity.

**Step 1: Create Merchant Snapshot**
A clean, de-duplicated copy of the merchant's data is created in a new `merchant_provider` dataset within your GCP project. This involves:
1.  Copying `orders` and `order_items` for a specific date.
2.  Identifying the unique users from those orders and copying only their most recent, de-duplicated records into a new `users` table.

**Step 2: Generate E-Wallet Provider Data**
The script then reads from the clean `merchant_provider` snapshot to generate the `ewallet_provider` dataset, which contains the synthetic data for the payment provider.

```mermaid
graph TD
    subgraph PublicData [Source: bigquery-public-data]
        direction LR
        PublicUsers(thelook_ecommerce.users)
        PublicOrders(thelook_ecommerce.orders)
        PublicOrderItems(thelook_ecommerce.order_items)
    end

    subgraph YourProject [Destination: Your GCP Project]
        direction TB

        subgraph SnapshotDS [merchant_provider]
            direction LR
            SnapshotUsers(users)
            SnapshotOrders(orders)
            SnapshotOrderItems(order_items)
        end

        subgraph ProviderDS [ewallet_provider]
            direction LR
            ProviderUsers(provider_users)
            ProviderTransactions(transactions)
        end

        SnapshotDS -- "Read From" --> ProviderDS
    end

    PublicUsers --> SnapshotUsers
    PublicOrders --> SnapshotOrders
    PublicOrderItems --> SnapshotOrderItems
```

## 2. Data Clean Room Use Cases

This simulation enables several powerful use cases. All example queries should be run against the tables created in **your own GCP project**.

---

### Use Case 1: Transaction Verification (Merchant's Goal)

The **merchant** wants to understand which of their sales were processed by this specific e-wallet provider.

*   **Action:** The merchant joins their `orders` table (from the `merchant_provider` snapshot) with the provider's `transactions` table.
*   **Join Key:** `order_id`
*   **Example Query:**
    ```sql
    -- This query, run by the merchant, finds all of their orders
    -- that have a matching transaction record from the payment provider.
    SELECT
        m.order_id,
        m.created_at,
        p.transaction_id,
        p.transaction_amount
    FROM
        `your-gcp-project.merchant_provider.orders` AS m
    INNER JOIN
        `your-gcp-project.ewallet_provider.transactions` AS p
        ON m.order_id = p.order_id
    LIMIT 10;
    ```

---

### Use Case 2: Customer Segmentation (Merchant's Goal)

The **merchant** wants to know if customers with a higher "tier" e-wallet account spend more at their store.

*   **Action:** The merchant joins their `users` data with the provider's `provider_users` data.
*   **Join Key:** `email`
*   **Example Query:**
    ```sql
    -- This query segments customers by the provider's account tier
    -- and calculates the average order value for each tier.
    SELECT
        p.account_tier,
        AVG(t.transaction_amount) AS average_order_value,
        COUNT(DISTINCT u.id) AS number_of_customers
    FROM
        `your-gcp-project.merchant_provider.users` AS u
    JOIN
        `your-gcp-project.ewallet_provider.provider_users` AS p ON u.email = p.email
    JOIN
        `your-gcp-project.ewallet_provider.transactions` AS t ON p.provider_user_id = t.provider_user_id
    GROUP BY 1
    ORDER BY 2 DESC;
    ```

---

### Use Case 3: Trust and Fraud Analysis (Merchant's Goal)

The **merchant** wants to identify high-trust customers.

*   **Action:** The merchant uses the `is_verified_user` flag from the provider's data as a signal of trustworthiness.
*   **Join Key:** `email`
*   **Example Query:**
    ```sql
    -- This query counts the number of verified vs. unverified users
    -- who have made purchases.
    SELECT
        p.is_verified_user,
        COUNT(DISTINCT u.id) AS number_of_customers
    FROM
        `your-gcp-project.merchant_provider.users` AS u
    JOIN
        `your-gcp-project.ewallet_provider.provider_users` AS p ON u.email = p.email
    GROUP BY 1;
    ```

---

### Use Case 4: User Enrichment (Provider's Goal)

The **e-wallet provider** wants to learn more about their customers who shop at this merchant.

*   **Action:** The provider joins their `provider_users` table with the merchant's `users` table.
*   **Join Key:** `email`
*   **Example Query:**
    ```sql
    -- This query, run by the provider, enriches their user data with
    -- the merchant's demographic and location information.
    SELECT
        p.provider_user_id,
        p.email,
        m.age,
        m.gender,
        m.country AS merchant_customer_country
    FROM
        `your-gcp-project.ewallet_provider.provider_users` AS p
    JOIN
        `your-gcp-project.merchant_provider.users` AS m ON p.email = m.email
    LIMIT 10;
    ```

## 3. How to Run

### Prerequisites

*   Python 3.12
*   `uv` package manager installed (`pip install uv`)
*   Authenticated Google Cloud SDK on your local machine.

### Setup

1.  **Set your GCP Project ID:**
    Open `dcr_data_generator/main.py` and update the `WRITE_PROJECT_ID` variable with your Google Cloud project ID.

2.  **Create and Sync the Virtual Environment:**
    From the root of this project directory, run the following command. This will create a local virtual environment (`.venv`) and install the required dependencies.
    ```sh
    uv sync
    ```

### Execution

Once the setup is complete, run the main script from the project's root directory:

```sh
uv run python -m dcr_data_generator.main
```

The script will create both the `merchant_provider` and `ewallet_provider` datasets in your project, overwriting them if they already exist to ensure a clean run every time.

## 4. Generated Schemas

The script will create tables in two datasets within your target GCP project.

### `merchant_provider` (Clean Snapshot)
*   **`orders`**: A direct copy of orders for the target date.
*   **`order_items`**: A direct copy of corresponding order items.
*   **`users`**: A de-duplicated copy of users related to the orders.

### `ewallet_provider` (Synthetic Data)
#### `provider_users`
| Column Name        | Data Type | Description                                                     |
| ------------------ | --------- | --------------------------------------------------------------- |
| `provider_user_id` | `INTEGER` | The provider's unique internal identifier for a user.           |
| `email`            | `STRING`  | The user's email, serving as the join key for enrichment.      |
| `date_of_birth`    | `DATE`    | Synthetically generated date of birth.                          |
| `city`             | `STRING`  | **Sourced directly from the merchant's `users` table.**         |
| `account_tier`     | `STRING`  | The user's account level with the provider (e.g., 'Free', 'Premium'). |
| `is_verified_user` | `BOOLEAN` | Indicates if the user has completed KYC with the provider.      |


#### `transactions`
| Column Name           | Data Type | Description                                                  |
| --------------------- | --------- | ------------------------------------------------------------ |
| `transaction_id`      | `STRING`  | A unique identifier for the payment transaction.             |
| `order_id`            | `INTEGER` | The join key linking back to the merchant's `orders` table.  |
| `provider_user_id`    | `INTEGER` | A foreign key linking to the provider's internal `provider_users` table. |
| `transaction_amount`  | `FLOAT64` | **Sourced from the sum of `sale_price` in `order_items`.**   |
| `transaction_timestamp` | `TIMESTAMP` | **Sourced from the `created_at` field in `orders`.**         |
| `status`              | `STRING`  | **Sourced directly from the `status` field in `orders`.**    |
