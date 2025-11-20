# Solana Activity Dashboard Plan

## Overview
A Dune Analytics dashboard to track active onchain participants on Solana blockchain, identifying periods of high and low activity across PumpFun and other popular dapps.

---

## 1. Key Metrics for Active Participant Tracking

### Core Activity Metrics
- **Daily Active Users (DAU)**: Unique addresses interacting per day
- **Weekly Active Users (WAU)**: Unique addresses interacting per week
- **Monthly Active Users (MAU)**: Unique addresses interacting per month
- **DAU/MAU Ratio**: Indicator of user stickiness (higher = more engaged users)

### User Segmentation
- **New Users**: First-time addresses (debut transaction date)
- **Returning Users**: Addresses with prior activity
- **Power Users**: Top percentile by transaction count/volume
- **Inactive Users**: Addresses with no activity for X days

### Transaction Metrics
- **Total Transactions**: Count of all transactions
- **Transactions per User**: Average txns per active address
- **Transaction Volume**: Total SOL transferred
- **Average Transaction Size**: SOL per transaction
- **Gas Fees Paid**: Total fees in SOL

### Activity Pattern Detection
- **Activity Heatmap**: Transactions by day/hour to identify peak times
- **7-Day Moving Average**: Smoothed trend line for DAU
- **Week-over-Week Growth**: % change in active users
- **Engagement Score**: Composite metric (frequency × volume × recency)
- **Churn Rate**: % of users who stop interacting after initial activity

---

## 2. Solana Dapps to Track

### Priority Dapps
1. **PumpFun** - Token launch platform (meme coins)
   - Program ID: `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`
   - Key metrics: Token launches, traders, volume

2. **Jupiter Aggregator** - DEX aggregator
   - Program ID: `JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4`
   - Key metrics: Swap count, unique swappers, volume

3. **Raydium** - AMM DEX
   - Program ID: `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8`
   - Key metrics: Swaps, liquidity providers, volume

4. **Magic Eden** - NFT marketplace
   - Program ID: `M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K`
   - Key metrics: Sales, buyers, sellers, volume

### Secondary Dapps
5. **Orca** - AMM DEX
6. **Marinade Finance** - Liquid staking
7. **Drift Protocol** - Perpetual futures
8. **Phantom/Solflare** - Wallet activity
9. **Pump Portal** - Token trading
10. **Meteora** - Dynamic liquidity pools

---

## 3. Solana Data Structure in Dune

### Main Tables
```sql
-- Core transaction table
solana.transactions
  - block_time
  - block_slot
  - tx_id (signature)
  - signer (fee payer)
  - success
  - fee
  - recent_block_hash

-- Account activity table
solana.account_activity
  - block_time
  - tx_id
  - address
  - tx_index
  - signed
  - writable

-- Instruction calls table
solana.instruction_calls
  - block_time
  - tx_id
  - executing_account (program_id)
  - data
  - account_arguments

-- Token transfers
solana.token_transfers
  - block_time
  - tx_id
  - token_mint_address
  - from_address
  - to_address
  - amount
```

### Program-Specific Tables (if available)
- `jupiter_aggregator_v6.trades`
- `raydium.trades`
- `magic_eden.events`

---

## 4. Dashboard Structure

### Section 1: Network Overview
**Purpose**: High-level Solana activity snapshot

**Visualizations**:
1. **Big Number Cards**:
   - Total Active Users (Last 30d)
   - Total Transactions (Last 30d)
   - Total Volume (SOL)
   - Average Transaction Fee

2. **Time Series Chart**: DAU/WAU/MAU over time (6 months)
3. **Area Chart**: Transaction volume over time
4. **Line Chart**: DAU/MAU ratio (stickiness metric)

---

### Section 2: Activity Pattern Analysis
**Purpose**: Identify on/off periods of blockchain activity

**Visualizations**:
1. **Activity Heatmap**:
   - X-axis: Hour of day (0-23)
   - Y-axis: Day of week
   - Color: Transaction count

2. **7-Day Moving Average Chart**: Smoothed DAU trend
3. **Week-over-Week Growth Chart**: % change in users
4. **Activity Distribution**: Histogram of transactions per user

---

### Section 3: User Segmentation
**Purpose**: Understand user behavior and engagement

**Visualizations**:
1. **Stacked Area Chart**: New vs Returning users over time
2. **Bar Chart**: User segmentation by activity level
   - Whale (>100 txns/month)
   - Power User (20-100 txns)
   - Regular User (5-20 txns)
   - Casual User (1-5 txns)

3. **Cohort Retention Table**:
   - Rows: Sign-up week
   - Columns: Weeks since sign-up
   - Values: % of users still active

4. **Churn Analysis**: Users dropping off by week

---

### Section 4: Dapp-Specific Activity
**Purpose**: Track activity across major Solana protocols

**Visualizations**:
1. **Stacked Bar Chart**: Transactions by dapp over time
2. **Pie Chart**: Current market share (% of transactions)
3. **Multi-line Chart**: DAU by dapp
4. **Table**: Top 10 dapps by unique users (last 7d)

**Per-Dapp Breakdown**:
- PumpFun: Token launches, traders, volume
- Jupiter: Swap count, unique swappers, routing efficiency
- Raydium: Pool activity, LP count, volume
- Magic Eden: NFT sales, buyers, floor prices

---

### Section 5: On/Off Period Detection
**Purpose**: Algorithmically identify activity cycles

**Visualizations**:
1. **Z-Score Chart**: Standardized DAU to identify outliers
2. **Activity State Timeline**:
   - Green: High activity (>1 std dev above mean)
   - Yellow: Normal activity (within 1 std dev)
   - Red: Low activity (>1 std dev below mean)

3. **Correlation Matrix**: Relationship between different metrics
4. **Event Detection Table**: Dates of significant activity spikes/drops

---

## 5. SQL Query Approach

### Query 1: Daily Active Users
```sql
WITH daily_users AS (
  SELECT
    DATE_TRUNC('day', block_time) AS date,
    COUNT(DISTINCT signer) AS dau
  FROM solana.transactions
  WHERE block_time >= NOW() - INTERVAL '90 days'
    AND success = true
  GROUP BY 1
)
SELECT * FROM daily_users
ORDER BY date DESC;
```

### Query 2: Dapp-Specific Activity
```sql
SELECT
  DATE_TRUNC('day', t.block_time) AS date,
  CASE
    WHEN ic.executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P' THEN 'PumpFun'
    WHEN ic.executing_account = 'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4' THEN 'Jupiter'
    WHEN ic.executing_account = '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8' THEN 'Raydium'
    ELSE 'Other'
  END AS dapp,
  COUNT(DISTINCT t.signer) AS unique_users,
  COUNT(*) AS transaction_count
FROM solana.transactions t
JOIN solana.instruction_calls ic ON t.tx_id = ic.tx_id
WHERE t.block_time >= NOW() - INTERVAL '30 days'
  AND t.success = true
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

### Query 3: New vs Returning Users
```sql
WITH first_tx AS (
  SELECT
    signer,
    MIN(DATE_TRUNC('day', block_time)) AS first_seen
  FROM solana.transactions
  WHERE success = true
  GROUP BY 1
),
daily_activity AS (
  SELECT
    DATE_TRUNC('day', t.block_time) AS date,
    t.signer,
    f.first_seen
  FROM solana.transactions t
  JOIN first_tx f ON t.signer = f.signer
  WHERE t.block_time >= NOW() - INTERVAL '90 days'
    AND t.success = true
  GROUP BY 1, 2, 3
)
SELECT
  date,
  COUNT(DISTINCT CASE WHEN date = first_seen THEN signer END) AS new_users,
  COUNT(DISTINCT CASE WHEN date > first_seen THEN signer END) AS returning_users
FROM daily_activity
GROUP BY 1
ORDER BY 1 DESC;
```

### Query 4: Activity Heatmap
```sql
SELECT
  EXTRACT(DOW FROM block_time) AS day_of_week, -- 0=Sunday, 6=Saturday
  EXTRACT(HOUR FROM block_time) AS hour_of_day,
  COUNT(*) AS transaction_count
FROM solana.transactions
WHERE block_time >= NOW() - INTERVAL '30 days'
  AND success = true
GROUP BY 1, 2
ORDER BY 1, 2;
```

### Query 5: User Activity Segmentation
```sql
WITH user_txn_counts AS (
  SELECT
    signer,
    COUNT(*) AS txn_count,
    SUM(fee) / 1e9 AS total_fees_sol,
    MAX(block_time) AS last_active
  FROM solana.transactions
  WHERE block_time >= NOW() - INTERVAL '30 days'
    AND success = true
  GROUP BY 1
)
SELECT
  CASE
    WHEN txn_count >= 100 THEN 'Whale'
    WHEN txn_count >= 20 THEN 'Power User'
    WHEN txn_count >= 5 THEN 'Regular User'
    ELSE 'Casual User'
  END AS user_segment,
  COUNT(*) AS user_count,
  AVG(txn_count) AS avg_transactions,
  AVG(total_fees_sol) AS avg_fees_paid
FROM user_txn_counts
GROUP BY 1
ORDER BY 2 DESC;
```

### Query 6: Activity State Detection (Z-Score)
```sql
WITH daily_stats AS (
  SELECT
    DATE_TRUNC('day', block_time) AS date,
    COUNT(DISTINCT signer) AS dau
  FROM solana.transactions
  WHERE block_time >= NOW() - INTERVAL '90 days'
    AND success = true
  GROUP BY 1
),
stats_summary AS (
  SELECT
    AVG(dau) AS mean_dau,
    STDDEV(dau) AS stddev_dau
  FROM daily_stats
)
SELECT
  d.date,
  d.dau,
  s.mean_dau,
  s.stddev_dau,
  (d.dau - s.mean_dau) / s.stddev_dau AS z_score,
  CASE
    WHEN (d.dau - s.mean_dau) / s.stddev_dau > 1 THEN 'High Activity'
    WHEN (d.dau - s.mean_dau) / s.stddev_dau < -1 THEN 'Low Activity'
    ELSE 'Normal Activity'
  END AS activity_state
FROM daily_stats d
CROSS JOIN stats_summary s
ORDER BY d.date DESC;
```

---

## 6. Implementation Steps

1. **Set up Dune account** and create new dashboard
2. **Write and test core queries** (DAU, transactions, volume)
3. **Create program ID reference table** for dapp tracking
4. **Build visualization panels** following the structure above
5. **Add filters**:
   - Date range selector
   - Dapp selector
   - User segment selector
6. **Set up refresh schedule** (daily recommended)
7. **Add dashboard description** and methodology notes
8. **Share and iterate** based on feedback

---

## 7. Advanced Features (Optional)

### Machine Learning Approaches
- **Anomaly Detection**: Identify unusual activity spikes
- **Predictive Modeling**: Forecast future DAU based on trends
- **Clustering**: Group users by behavior patterns

### Additional Metrics
- **Token-specific tracking**: Top tokens by trading volume
- **Bot detection**: Filter out programmatic activity
- **Geographic analysis**: If location data available
- **Network effects**: User referral chains

### Integration
- **Alerts**: Webhook notifications for activity thresholds
- **API export**: Make data available for external tools
- **Comparative analysis**: Compare Solana to other L1s

---

## 8. Expected Insights

This dashboard will help identify:
1. **Peak activity periods**: Times of day/week with highest engagement
2. **Growth trends**: Is the user base expanding or contracting?
3. **Dapp dominance**: Which protocols drive the most activity?
4. **User retention**: How many users return after first interaction?
5. **Market cycles**: Correlation between price movements and activity
6. **Ecosystem health**: Overall vibrancy of Solana network

---

## Resources

- **Dune Docs**: https://docs.dune.com/
- **Solana Docs**: https://docs.solana.com/
- **Dune Solana Tables**: https://docs.dune.com/data-tables/solana/
- **Example Dashboards**:
  - Solana Overview: https://dune.com/ilemi/solana
  - Jupiter Analytics: https://dune.com/jupiter-exchange/jupiter-overview

---

## Next Steps

1. Validate program IDs for all tracked dapps
2. Test queries on Dune platform
3. Build dashboard incrementally (start with Section 1)
4. Gather feedback and refine
