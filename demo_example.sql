-- -- dcx bqml
-- uv run python setup_ah_dcx.py \
--     --sharing-project-id merchant-project-id \
--     --subscriber-email provider-email \
--     --dataset-to-share merchant_provider \
--     --listing-id merchant_dataset_listing \
--     --listing-display-name "DCX Merchant Full Dataset" \
--     --exchange-id merchant_dcx_exchange

-- -- dcr analysis
-- uv run python setup_ah_dcr.py \
--     --sharing-project-id provider-project-id \
--     --subscriber-email merchant-email \
--     --dataset-to-share ewallet_provider \
--     --table-to-share provider_users \
--     --listing-id provider_users_listing \
--     --listing-display-name "DCR Provider Users Table" \
--     --exchange-id provider_dcr_exchange

-- uv run python setup_ah_dcr.py \
--     --sharing-project-id provider-project-id \
--     --subscriber-email merchant-email \
--     --dataset-to-share ewallet_provider \
--     --table-to-share transactions \
--     --listing-id transactions_listing \
--     --listing-display-name "DCR Provider Transactions Table" \
--     --exchange-id provider_dcr_exchange

-- uv run python setup_ah_dcr.py \
--     --sharing-project-id provider-project-id \
--     --subscriber-email merchant-email \
--     --dataset-to-share ewallet_provider \
--     --routine-to-share hash_tvf \
--     --listing-id hash_tvf_listing \
--     --listing-display-name "DCR Provider Hash TVF" \
--     --exchange-id provider_dcr_exchange

-- uv run python setup_ah_dcr.py \
--     --sharing-project-id merchant-project-id \
--     --subscriber-email provider-email \
--     --dataset-to-share merchant_provider \
--     --table-to-share users \
--     --listing-id merchant_users_listing \
--     --listing-display-name "DCR Merchant Users Table" \
--     --exchange-id merchant_dcr_exchange

-- Use Case 1 (Merchant POV)
-- This query returns the list of order_ids that exist in both datasets,
-- demonstrating a classic "list overlap" scenario in a data clean room.
SELECT
  *
FROM
  `merchant-project-id.e_wallet_provider_data_clean_room.transactions_listing_view`
LIMIT
  1000;
  -----
SELECT
  DISTINCT m.order_id
FROM
  `merchant-project-id.merchant_provider.orders` AS m
INNER JOIN
  `merchant-project-id.e_wallet_provider_data_clean_room.transactions_listing_view` AS p
ON
  m.order_id = p.order_id;

-- Use Case 4 (Provider POV)
-- This query returns demographic enrichment data for users who exist
-- in both the provider's and merchant's datasets, demonstrating list overlap.
SELECT
  *
FROM
  provider-project-id.merchant_data_clean_room.merchant_users_listing_view
LIMIT
  1000;
  -----
SELECT
  DISTINCT p.provider_user_id,
  m.age,
  m.gender,
  m.country AS merchant_customer_country,
  m.traffic_source
FROM
  `provider-project-id.ewallet_provider.provider_users` AS p
JOIN
  `provider-project-id.merchant_data_clean_room.merchant_users_listing_view` AS m
ON
  p.hashed_email = m.hashed_email;

-- Use Case 2 (Merchant POV)
-- This query segments customers by the provider's account tier
-- and calculates the average order value for each tier.
-- Results will only show tiers with sufficient user counts to meet privacy thresholds.
SELECT
WITH
  AGGREGATION_THRESHOLD OPTIONS(threshold=110) p.account_tier,
  AVG(t.transaction_amount) AS average_order_value,
  COUNT(DISTINCT u.id) AS number_of_customers
FROM
  `merchant-project-id.merchant_provider.users` AS u
JOIN
  `merchant-project-id.e_wallet_provider_data_clean_room.provider_users_listing_view` AS p
ON
  u.hashed_email = p.hashed_email
JOIN
  `merchant-project-id.merchant_provider.orders` AS o
ON
  u.id = o.user_id
JOIN
  `merchant-project-id.e_wallet_provider_data_clean_room.transactions_listing_view` AS t
ON
  o.order_id = t.order_id
GROUP BY
  1
ORDER BY
  2 DESC;

-- Use Case 3a (Merchant POV)
-- This query counts the number of verified vs. unverified users
-- who have made purchases. Results will only show if both groups
-- meet the minimum threshold requirements.
SELECT
  *
FROM
  merchant-project-id.e_wallet_provider_data_clean_room.provider_users_listing_view
LIMIT
  1000;
  -----
SELECT
WITH
  AGGREGATION_THRESHOLD OPTIONS(threshold=110) p.is_verified_user,
  COUNT(DISTINCT u.id) AS number_of_customers
FROM
  `merchant-project-id.merchant_provider.users` AS u
JOIN
  `merchant-project-id.e_wallet_provider_data_clean_room.provider_users_listing_view` AS p
ON
  u.hashed_email = p.hashed_email
GROUP BY
  1

-- Use Case 3b with hash_tvf
-- CREATE OR REPLACE TABLE
--   `merchant-project-id.merchant_provider.users_temp` AS
-- SELECT
--   * EXCEPT (hashed_email)
-- FROM
--   `merchant-project-id.merchant_provider.users`;

SELECT
  u.*,
  hashed.hashed_email
FROM
  `merchant-project-id.merchant_provider.users_temp` AS u
INNER JOIN
  `merchant-project-id.e_wallet_provider_data_clean_room.hash_tvf`( TABLE `merchant-project-id.merchant_provider.users_temp` ) AS hashed
ON
  u.email = hashed.email;
  -----
SELECT
WITH
  AGGREGATION_THRESHOLD OPTIONS(threshold=110) p.is_verified_user,
  COUNT(DISTINCT u.id) AS number_of_customers
FROM
  `merchant-project-id.merchant_provider.users_temp` AS u
CROSS JOIN
  `merchant-project-id.e_wallet_provider_data_clean_room.hash_tvf`( TABLE `merchant-project-id.merchant_provider.users_temp` ) AS hashed
JOIN
  `merchant-project-id.e_wallet_provider_data_clean_room.provider_users_listing_view` AS p
ON
  hashed.hashed_email = p.hashed_email
WHERE
  u.email = hashed.email  -- Match back to original row
GROUP BY
  1

-- Use Case 5a (Provider POV)
CREATE OR REPLACE MODEL
  `provider-project-id.ewallet_provider.account_tier_predictor` OPTIONS(model_type='LOGISTIC_REG',
    input_label_cols=['account_tier']) AS
SELECT
  -- Features from the merchant's rich demographic data
  m.age,
  m.gender,
  m.state,
  m.country,
  m.traffic_source,
  -- Label from the provider's own data
  p.account_tier
FROM
  `provider-project-id.ewallet_provider.provider_users` p
JOIN
  -- `provider-project-id.dcx_merchant_full_dataset.users` m
  `provider-project-id.merchant_data_clean_room.merchant_users_listing_view` m -- data clean room won't work for training due to egress
ON
  p.hashed_email = m.hashed_email;

-- Use Case 5b (Provider POV)
SELECT
  provider_user_id,
  email,
  predicted_account_tier,
  predicted_account_tier_probs
FROM
  ML.PREDICT(MODEL `provider-project-id.ewallet_provider.account_tier_predictor`,
    (
    SELECT
      p.provider_user_id,
      p.email,
      m.age,
      m.gender,
      m.state,
      m.country,
      m.traffic_source
    FROM
      `provider-project-id.ewallet_provider.provider_users_inference` p
    JOIN
      `provider-project-id.merchant_data_clean_room.merchant_users_listing_view` m -- data clean room work just fine for inferencing
      -- `provider-project-id.dcx_merchant_full_dataset.users_inference` m
    ON
      p.hashed_email = m.hashed_email ) );