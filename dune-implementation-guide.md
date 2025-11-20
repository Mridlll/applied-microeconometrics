# Dune Dashboard Implementation Guide

Follow these steps to build your Solana Activity Dashboard in Dune Analytics.

---

## Step 1: Create Your First Query - Daily Active Users

### In Dune:
1. Go to https://dune.com
2. Click **"New Query"** button (top right)
3. Name it: `Solana Daily Active Users`
4. Copy and paste this SQL:

```sql
WITH daily_users AS (
  SELECT
    DATE_TRUNC('day', block_time) AS date,
    COUNT(DISTINCT signer) AS dau,
    COUNT(*) AS total_transactions,
    SUM(fee) / 1e9 AS total_fees_sol
  FROM solana.transactions
  WHERE block_time >= NOW() - INTERVAL '90' day
    AND success = true
  GROUP BY 1
)
SELECT
  date,
  dau,
  total_transactions,
  total_fees_sol,
  AVG(dau) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS dau_7day_ma
FROM daily_users
ORDER BY date DESC;
```

5. Click **"Run"** button
6. Wait for results (may take 30-60 seconds)

### Expected Output:
- You should see columns: `date`, `dau`, `total_transactions`, `total_fees_sol`, `dau_7day_ma`
- Most recent dates at the top
- DAU values typically in the 100k-300k range for Solana

### Create Visualization:
1. Click **"New visualization"** button
2. Select **"Line chart"**
3. Configure:
   - **X-axis**: `date`
   - **Y-axis**: `dau` and `dau_7day_ma`
   - **Title**: "Daily Active Users (90 days)"
4. Click **"Save"**

---

## Step 2: Create Dashboard

1. Click your profile icon → **"New Dashboard"**
2. Name it: `Solana Activity & Engagement Tracker`
3. Add description:
   ```
   Tracking active onchain participants across Solana blockchain,
   identifying on/off periods of activity via PumpFun, Jupiter,
   Raydium, Magic Eden, and other popular dapps.
   ```
4. Click **"Create"**

### Add Your First Query:
1. Click **"Add visualization"**
2. Search for your "Solana Daily Active Users" query
3. Select the line chart you created
4. Resize and position it at the top
5. Click **"Save"**

---

## Step 3: Add Big Number Cards

### Query: Current 30-Day Metrics
1. Create new query: `Solana 30D Overview Stats`
2. Paste this SQL:

```sql
WITH last_30d AS (
  SELECT
    COUNT(DISTINCT signer) AS total_active_users,
    COUNT(*) AS total_transactions,
    SUM(fee) / 1e9 AS total_fees_sol,
    AVG(fee) / 1e9 AS avg_fee_sol
  FROM solana.transactions
  WHERE block_time >= NOW() - INTERVAL '30' day
    AND success = true
)
SELECT * FROM last_30d;
```

3. Run the query
4. Create 4 separate **"Counter"** visualizations:
   - Counter 1: `total_active_users` → Title: "Active Users (30d)"
   - Counter 2: `total_transactions` → Title: "Total Transactions (30d)"
   - Counter 3: `total_fees_sol` → Title: "Total Fees Paid (SOL)"
   - Counter 4: `avg_fee_sol` → Title: "Avg Transaction Fee (SOL)"

5. Add all 4 to your dashboard at the top

---

## Step 4: New vs Returning Users

### Query: User Cohort Analysis
1. Create new query: `Solana New vs Returning Users`
2. Paste this SQL:

```sql
WITH first_tx AS (
  SELECT
    signer,
    MIN(DATE_TRUNC('day', block_time)) AS first_seen
  FROM solana.transactions
  WHERE success = true
    AND block_time >= NOW() - INTERVAL '180' day
  GROUP BY 1
),
daily_activity AS (
  SELECT
    DATE_TRUNC('day', t.block_time) AS date,
    t.signer,
    f.first_seen
  FROM solana.transactions t
  JOIN first_tx f ON t.signer = f.signer
  WHERE t.block_time >= NOW() - INTERVAL '90' day
    AND t.success = true
  GROUP BY 1, 2, 3
)
SELECT
  date,
  COUNT(DISTINCT CASE WHEN date = first_seen THEN signer END) AS new_users,
  COUNT(DISTINCT CASE WHEN date > first_seen THEN signer END) AS returning_users,
  COUNT(DISTINCT signer) AS total_users
FROM daily_activity
GROUP BY 1
ORDER BY 1 DESC;
```

3. Run query
4. Create **"Stacked area chart"**:
   - X-axis: `date`
   - Y-axis: `new_users`, `returning_users`
   - Title: "New vs Returning Users"
5. Add to dashboard

---

## Step 5: Dapp-Specific Activity

### Query: Activity by Protocol
1. Create new query: `Solana Activity by Dapp`
2. Paste this SQL:

```sql
WITH dapp_mapping AS (
  SELECT
    DATE_TRUNC('day', t.block_time) AS date,
    CASE
      WHEN ic.executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P' THEN 'PumpFun'
      WHEN ic.executing_account = 'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4' THEN 'Jupiter'
      WHEN ic.executing_account = '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8' THEN 'Raydium'
      WHEN ic.executing_account = 'M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K' THEN 'Magic Eden'
      WHEN ic.executing_account = 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc' THEN 'Orca'
      WHEN ic.executing_account = 'MarBmsSgKXdrN1egZf5sqe1TMai9K1rChYNDJgjq7aD' THEN 'Marinade'
      ELSE 'Other'
    END AS dapp,
    t.signer
  FROM solana.transactions t
  INNER JOIN solana.instruction_calls ic
    ON t.tx_id = ic.tx_id
    AND t.block_slot = ic.block_slot
  WHERE t.block_time >= NOW() - INTERVAL '30' day
    AND t.success = true
)
SELECT
  date,
  dapp,
  COUNT(DISTINCT signer) AS unique_users,
  COUNT(*) AS transaction_count
FROM dapp_mapping
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

3. Run query
4. Create **"Bar chart"** (or stacked area):
   - X-axis: `date`
   - Y-axis: `unique_users`
   - Group by: `dapp`
   - Title: "Daily Active Users by Dapp"
5. Add to dashboard

---

## Step 6: User Activity Segmentation

### Query: User Tiers
1. Create new query: `Solana User Segmentation`
2. Paste this SQL:

```sql
WITH user_txn_counts AS (
  SELECT
    signer,
    COUNT(*) AS txn_count,
    SUM(fee) / 1e9 AS total_fees_sol,
    MAX(block_time) AS last_active,
    MIN(block_time) AS first_active
  FROM solana.transactions
  WHERE block_time >= NOW() - INTERVAL '30' day
    AND success = true
  GROUP BY 1
)
SELECT
  CASE
    WHEN txn_count >= 100 THEN '1. Whale (100+ txns)'
    WHEN txn_count >= 20 THEN '2. Power User (20-99 txns)'
    WHEN txn_count >= 5 THEN '3. Regular User (5-19 txns)'
    ELSE '4. Casual User (1-4 txns)'
  END AS user_segment,
  COUNT(*) AS user_count,
  ROUND(AVG(txn_count), 2) AS avg_transactions,
  ROUND(AVG(total_fees_sol), 4) AS avg_fees_paid_sol,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_users
FROM user_txn_counts
GROUP BY 1
ORDER BY 1;
```

3. Run query
4. Create **"Bar chart"** or **"Pie chart"**:
   - For bar: X=`user_segment`, Y=`user_count`
   - Title: "User Distribution by Activity Level"
5. Add to dashboard

---

## Step 7: Activity Heatmap

### Query: Hour × Day Activity Pattern
1. Create new query: `Solana Activity Heatmap`
2. Paste this SQL:

```sql
WITH hourly_data AS (
  SELECT
    CASE EXTRACT(DOW FROM block_time)
      WHEN 0 THEN '0-Sunday'
      WHEN 1 THEN '1-Monday'
      WHEN 2 THEN '2-Tuesday'
      WHEN 3 THEN '3-Wednesday'
      WHEN 4 THEN '4-Thursday'
      WHEN 5 THEN '5-Friday'
      WHEN 6 THEN '6-Saturday'
    END AS day_of_week,
    EXTRACT(HOUR FROM block_time) AS hour_of_day,
    COUNT(*) AS transaction_count
  FROM solana.transactions
  WHERE block_time >= NOW() - INTERVAL '30' day
    AND success = true
  GROUP BY 1, 2
)
SELECT
  day_of_week,
  hour_of_day,
  transaction_count,
  transaction_count * 1.0 / MAX(transaction_count) OVER () AS normalized_activity
FROM hourly_data
ORDER BY 1, 2;
```

3. Run query
4. Create **"Heatmap"** visualization:
   - X-axis: `hour_of_day`
   - Y-axis: `day_of_week`
   - Color/Value: `transaction_count`
   - Title: "Activity Heatmap: Hour × Day"
5. Add to dashboard

---

## Step 8: Activity State Detection

### Query: On/Off Period Identification
1. Create new query: `Solana Activity States (Z-Score)`
2. Paste this SQL:

```sql
WITH daily_stats AS (
  SELECT
    DATE_TRUNC('day', block_time) AS date,
    COUNT(DISTINCT signer) AS dau,
    COUNT(*) AS transaction_count
  FROM solana.transactions
  WHERE block_time >= NOW() - INTERVAL '90' day
    AND success = true
  GROUP BY 1
),
stats_summary AS (
  SELECT
    AVG(dau) AS mean_dau,
    STDDEV(dau) AS stddev_dau,
    AVG(transaction_count) AS mean_txns,
    STDDEV(transaction_count) AS stddev_txns
  FROM daily_stats
)
SELECT
  d.date,
  d.dau,
  d.transaction_count,
  ROUND(s.mean_dau, 0) AS mean_dau,
  ROUND(s.stddev_dau, 0) AS stddev_dau,
  ROUND((d.dau - s.mean_dau) / NULLIF(s.stddev_dau, 0), 2) AS z_score,
  CASE
    WHEN (d.dau - s.mean_dau) / NULLIF(s.stddev_dau, 0) > 1 THEN 'High Activity'
    WHEN (d.dau - s.mean_dau) / NULLIF(s.stddev_dau, 0) < -1 THEN 'Low Activity'
    ELSE 'Normal Activity'
  END AS activity_state
FROM daily_stats d
CROSS JOIN stats_summary s
ORDER BY d.date DESC;
```

3. Run query
4. Create **"Line chart"** with color coding:
   - X-axis: `date`
   - Y-axis: `dau`
   - Color by: `activity_state`
   - Title: "Activity States (Statistical Detection)"
5. Add to dashboard

---

## Step 9: Dashboard Organization

### Arrange Your Dashboard Sections:

**Section 1: Overview (Top)**
- Row 1: 4 big number cards (users, transactions, fees, avg fee)
- Row 2: DAU line chart (full width)

**Section 2: User Behavior**
- Row 3: New vs Returning users (stacked area)
- Row 4: User segmentation (bar/pie chart)

**Section 3: Dapp Activity**
- Row 5: Activity by dapp (stacked chart)

**Section 4: Activity Patterns**
- Row 6: Activity heatmap
- Row 7: Activity state detection (z-score chart)

### Add Text Boxes:
1. Click **"Add text"** between sections
2. Use markdown for headers:
   ```markdown
   ## 📊 Network Overview

   ## 👥 User Behavior & Cohorts

   ## 🎯 Dapp-Specific Activity

   ## 🔥 Activity Pattern Analysis
   ```

---

## Step 10: Add Filters (Optional)

1. Click **"Add parameter"**
2. Create date range filter:
   - Name: `time_range`
   - Type: `Date range`
   - Default: Last 90 days

3. Update queries to use parameter:
   ```sql
   WHERE block_time >= {{time_range.start}}
     AND block_time <= {{time_range.end}}
   ```

---

## Step 11: Publish & Share

1. Click **"Save"** (top right)
2. Click **"Make public"** to share
3. Get shareable link
4. Optional: Add to Dune community dashboards

---

## Troubleshooting

### Common Issues:

**Query takes too long:**
- Reduce time range (use 30 days instead of 90)
- Add more specific WHERE filters
- Use indexed columns (block_time, block_slot)

**No results returned:**
- Check program IDs are correct
- Verify table names: `solana.transactions`, `solana.instruction_calls`
- Check date filters aren't too restrictive

**Visualization doesn't look right:**
- Check column names match exactly
- Try different chart types
- Verify data types (dates, numbers)

**Program ID not found:**
- Some program IDs may change or be incorrect
- Use Dune's `solana.decoded_instructions` for popular programs
- Check Solana Explorer for correct addresses

---

## Next Steps After Basic Dashboard

1. **Add more dapps**: Drift, Orca, Phantom, Tensor
2. **Token-specific tracking**: Top tokens by volume
3. **Whale watching**: Track large transactions
4. **Bot detection**: Filter programmatic activity
5. **Comparison metrics**: WoW/MoM growth rates
6. **Alerts**: Set up notifications for activity spikes

---

## Resources

- **Dune Docs**: https://docs.dune.com/
- **Solana Tables**: https://docs.dune.com/data-tables/solana
- **SQL Reference**: https://docs.dune.com/query-engine/dune-sql-reference
- **Community Dashboards**: https://dune.com/browse/dashboards/chain/solana

Good luck building your dashboard! 🚀
