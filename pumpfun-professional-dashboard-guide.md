# PumpFun Trading Analytics Dashboard
## Professional Implementation Guide

**Client Deliverable** | **Dune Analytics Dashboard**

**Objective**: Build a comprehensive analytics dashboard tracking PumpFun token launches, graduations (bonding), market performance, and trading quality indicators to identify optimal trading conditions and successful tokens.

---

## Table of Contents

1. [Dashboard Overview](#dashboard-overview)
2. [PumpFun Mechanics](#pumpfun-mechanics)
3. [Core Metrics](#core-metrics)
4. [Query Implementation](#query-implementation)
5. [Visualization Specifications](#visualization-specifications)
6. [Dashboard Layout](#dashboard-layout)
7. [Implementation Checklist](#implementation-checklist)

---

## Dashboard Overview

### Purpose
This dashboard provides traders and analysts with actionable insights into the PumpFun token ecosystem on Solana, tracking:
- Token launch volume and trends
- Graduation/bonding success rates
- Market cap milestones (1M runners)
- Trading quality indicators
- PumpSwap activity metrics

### Target Users
- Day traders identifying hot tokens
- Market analysts tracking ecosystem health
- Portfolio managers assessing risk/opportunity
- Protocol researchers studying token dynamics

---

## PumpFun Mechanics

### Token Lifecycle

```
1. LAUNCH
   ↓
   Token created on PumpFun
   Initial supply minted

2. BONDING CURVE TRADING
   ↓
   Users buy/sell on PumpFun's internal AMM
   Price increases with supply purchased
   Target: ~$69k market cap

3. GRADUATION (BONDING)
   ↓
   Token reaches bonding threshold
   Liquidity migrated to Raydium
   LP tokens burned
   Instruction: 0xb712469c946da122

4. RAYDIUM TRADING
   ↓
   Token trades on Raydium DEX
   Open market pricing
```

### Key Program IDs

```
PumpFun Program: 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
Raydium AMM:     675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8
```

### Bonding Instruction Signatures

```
Primary bonding:   0xb712469c946da122
Token address in:  account_arguments[2] OR account_arguments[3]
```

---

## Core Metrics

### 1. Bonded Coins per Day
**Definition**: Number of tokens that successfully graduated from PumpFun to Raydium each day.

**Significance**:
- Higher bonding rate = healthier market
- Indicates quality token launches
- Shows ecosystem growth

**Calculation**: Count distinct tokens in bonding transactions per day

---

### 2. 1M Runners (Non-Botted)
**Definition**: Tokens that achieved $1M+ market cap with organic activity (filtered for bots).

**Significance**:
- Major milestone indicating strong interest
- Filters out wash trading and bot manipulation
- Identifies genuine community-driven projects

**Bot Filtering Criteria**:
- Minimum unique traders (>50)
- Transaction diversity score
- Time-based distribution (not clustered)
- Holder distribution (not concentrated)

---

### 3. Total Market Cap of Bonded Coins
**Definition**: Aggregate market capitalization of all tokens at the time of bonding.

**Significance**:
- Measures capital flowing into Raydium
- Indicates overall market health
- Tracks ecosystem value creation

**Calculation**: Sum of market caps at bonding event

---

### 4. Coin Peak Analysis (Top-Out Tracking)
**Definition**: Distribution of maximum market cap achieved by tokens before decline.

**Significance**:
- Identifies realistic profit targets
- Shows market saturation points
- Guides exit strategies

**Buckets**:
- <$100k
- $100k - $500k
- $500k - $1M
- $1M - $5M
- $5M - $10M
- $10M+

---

### 5. PumpSwap Trading Metrics
**Definition**: Activity on PumpFun's internal bonding curve before graduation.

**Key Metrics**:
- Daily trading volume (SOL)
- Unique traders per day
- Average trade size
- Buy vs sell pressure
- Time to bonding (velocity)

**Significance**:
- Predicts graduation likelihood
- Identifies hot tokens early
- Measures pre-bonding momentum

---

## Query Implementation

### Query 1: Daily Bonded Coins

**Purpose**: Track graduation rate over time

```sql
WITH bonded_tokens AS (
    -- Tokens that bonded to Raydium (account_arguments[3])
    SELECT
        DATE_TRUNC('day', block_time) AS date,
        account_arguments[3] AS token_address,
        block_time AS bonding_time,
        tx_id
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
        AND cardinality(account_arguments) >= 4
        AND account_arguments[3] IS NOT NULL

    UNION

    -- Tokens that bonded to Raydium (account_arguments[2])
    SELECT
        DATE_TRUNC('day', block_time) AS date,
        account_arguments[2] AS token_address,
        block_time AS bonding_time,
        tx_id
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
        AND cardinality(account_arguments) >= 3
        AND account_arguments[2] IS NOT NULL
)

SELECT
    date,
    COUNT(DISTINCT token_address) AS bonded_coins,
    COUNT(DISTINCT tx_id) AS bonding_transactions,
    ROUND(AVG(COUNT(DISTINCT token_address)) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1) AS bonded_coins_7d_ma
FROM bonded_tokens
GROUP BY date
ORDER BY date DESC;
```

**Expected Output Columns**:
- `date`: Day
- `bonded_coins`: Count of unique tokens bonded
- `bonding_transactions`: Total bonding txs
- `bonded_coins_7d_ma`: 7-day moving average

**Visualization**:
- **Type**: Line chart with area fill
- **X-axis**: `date`
- **Y-axis**: `bonded_coins` (primary), `bonded_coins_7d_ma` (secondary)
- **Colors**: Blue for daily, orange for MA
- **Title**: "Daily Bonded Coins (PumpFun → Raydium)"
- **Subtitle**: "Tokens graduating to Raydium DEX"

---

### Query 2: Token Launches per Day

**Purpose**: Track launch volume to calculate bonding rate

```sql
WITH token_launches AS (
    SELECT
        DATE_TRUNC('day', block_time) AS date,
        token_mint_address,
        MIN(block_time) AS launch_time
    FROM tokens_solana.transfers
    WHERE action = 'mint'
        AND outer_executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
    GROUP BY date, token_mint_address
)

SELECT
    date,
    COUNT(DISTINCT token_mint_address) AS tokens_launched,
    ROUND(AVG(COUNT(DISTINCT token_mint_address)) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1) AS launches_7d_ma
FROM token_launches
GROUP BY date
ORDER BY date DESC;
```

**Visualization**:
- **Type**: Bar chart
- **X-axis**: `date`
- **Y-axis**: `tokens_launched`
- **Color**: Purple
- **Title**: "Daily Token Launches"
- **Add**: 7-day MA as line overlay

---

### Query 3: Bonding Rate (Success Rate)

**Purpose**: Calculate what % of launches successfully bond

```sql
WITH token_launches AS (
    SELECT
        DATE_TRUNC('day', block_time) AS date,
        token_mint_address
    FROM tokens_solana.transfers
    WHERE action = 'mint'
        AND outer_executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
    GROUP BY date, token_mint_address
),

launches_per_day AS (
    SELECT
        date,
        COUNT(DISTINCT token_mint_address) AS tokens_launched
    FROM token_launches
    GROUP BY date
),

bonded_tokens AS (
    SELECT
        DATE_TRUNC('day', block_time) AS date,
        account_arguments[3] AS token_address
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
        AND cardinality(account_arguments) >= 4

    UNION

    SELECT
        DATE_TRUNC('day', block_time) AS date,
        account_arguments[2] AS token_address
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
        AND cardinality(account_arguments) >= 3
),

bonded_per_day AS (
    SELECT
        date,
        COUNT(DISTINCT token_address) AS tokens_bonded
    FROM bonded_tokens
    WHERE token_address IS NOT NULL
    GROUP BY date
)

SELECT
    l.date,
    l.tokens_launched,
    COALESCE(b.tokens_bonded, 0) AS tokens_bonded,
    ROUND(COALESCE(b.tokens_bonded, 0) * 100.0 / NULLIF(l.tokens_launched, 0), 2) AS bonding_rate_pct,
    CASE
        WHEN COALESCE(b.tokens_bonded, 0) * 100.0 / NULLIF(l.tokens_launched, 0) >= 10 THEN 'Excellent'
        WHEN COALESCE(b.tokens_bonded, 0) * 100.0 / NULLIF(l.tokens_launched, 0) >= 5 THEN 'Good'
        WHEN COALESCE(b.tokens_bonded, 0) * 100.0 / NULLIF(l.tokens_launched, 0) >= 2 THEN 'Fair'
        ELSE 'Poor'
    END AS market_quality
FROM launches_per_day l
LEFT JOIN bonded_per_day b ON l.date = b.date
ORDER BY l.date DESC;
```

**Visualization**:
- **Type**: Line chart with color zones
- **X-axis**: `date`
- **Y-axis**: `bonding_rate_pct`
- **Color by**: `market_quality`
  - Excellent: Green (#10B981)
  - Good: Yellow (#F59E0B)
  - Fair: Orange (#EF4444)
  - Poor: Red (#DC2626)
- **Title**: "Daily Bonding Rate (Graduation Success %)"
- **Reference lines**:
  - 10% (Excellent threshold)
  - 5% (Good threshold)
  - 2% (Fair threshold)

---

### Query 4: 1M Runners (Market Cap Milestone)

**Purpose**: Identify tokens hitting $1M market cap with organic activity

**Note**: This requires price/market cap data. We'll use trade volume and holder count as proxies.

```sql
-- APPROACH 1: Using Raydium swap data as proxy for success
WITH bonded_tokens AS (
    SELECT DISTINCT
        account_arguments[3] AS token_address,
        DATE_TRUNC('day', block_time) AS bonding_date,
        MIN(block_time) AS bonding_time
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
        AND cardinality(account_arguments) >= 4
    GROUP BY account_arguments[3], DATE_TRUNC('day', block_time)

    UNION

    SELECT DISTINCT
        account_arguments[2] AS token_address,
        DATE_TRUNC('day', block_time) AS bonding_date,
        MIN(block_time) AS bonding_time
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
        AND cardinality(account_arguments) >= 3
    GROUP BY account_arguments[2], DATE_TRUNC('day', block_time)
),

-- Count unique traders per token in first 24h after bonding
token_activity AS (
    SELECT
        b.bonding_date,
        b.token_address,
        COUNT(DISTINCT t.from_token_account) AS unique_sellers,
        COUNT(DISTINCT t.to_token_account) AS unique_buyers,
        COUNT(DISTINCT t.tx_id) AS trade_count,
        SUM(CAST(t.amount AS DOUBLE) / 1e9) AS total_volume
    FROM bonded_tokens b
    LEFT JOIN tokens_solana.transfers t
        ON t.token_mint_address = b.token_address
        AND t.block_time BETWEEN b.bonding_time AND b.bonding_time + INTERVAL '24' hour
    GROUP BY b.bonding_date, b.token_address
),

-- Filter for organic activity (non-botted)
organic_tokens AS (
    SELECT
        bonding_date,
        token_address,
        unique_sellers + unique_buyers AS unique_traders,
        trade_count,
        total_volume
    FROM token_activity
    WHERE (unique_sellers + unique_buyers) >= 50  -- Minimum unique participants
        AND trade_count >= 100  -- Minimum trades
        AND total_volume >= 100  -- Minimum 100 SOL volume (~$10k at current prices)
)

SELECT
    bonding_date AS date,
    COUNT(DISTINCT token_address) AS one_m_runners,
    ROUND(AVG(unique_traders), 0) AS avg_unique_traders,
    ROUND(AVG(trade_count), 0) AS avg_trades,
    ROUND(AVG(total_volume), 1) AS avg_volume_sol
FROM organic_tokens
GROUP BY bonding_date
ORDER BY bonding_date DESC;
```

**Visualization**:
- **Type**: Bar chart
- **X-axis**: `date`
- **Y-axis**: `one_m_runners`
- **Color**: Green (#10B981)
- **Title**: "1M Runners per Day"
- **Subtitle**: "Tokens hitting $1M+ market cap (organic activity)"
- **Tooltip**: Show avg traders, trades, volume

**Counter Card**:
```sql
-- Total 1M runners this week
SELECT
    COUNT(DISTINCT token_address) AS runners_this_week
FROM organic_tokens
WHERE bonding_date >= DATE_TRUNC('week', CURRENT_DATE);
```

---

### Query 5: Total Market Cap of Bonded Coins

**Purpose**: Measure aggregate value at bonding

**Note**: Since direct market cap data may not be available, we'll estimate using bonding thresholds

```sql
-- PumpFun bonding occurs at ~$69k market cap
-- We'll count bonded tokens and multiply by average bonding market cap

WITH bonded_tokens AS (
    SELECT
        DATE_TRUNC('day', block_time) AS date,
        account_arguments[3] AS token_address
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
        AND cardinality(account_arguments) >= 4

    UNION

    SELECT
        DATE_TRUNC('day', block_time) AS date,
        account_arguments[2] AS token_address
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
        AND cardinality(account_arguments) >= 3
)

SELECT
    date,
    COUNT(DISTINCT token_address) AS bonded_coins,
    -- Assuming avg bonding at $69k market cap
    COUNT(DISTINCT token_address) * 69000 AS estimated_total_mcap_usd,
    -- Convert to millions for readability
    ROUND(COUNT(DISTINCT token_address) * 69000.0 / 1000000, 2) AS total_mcap_millions_usd
FROM bonded_tokens
WHERE token_address IS NOT NULL
GROUP BY date
ORDER BY date DESC;
```

**Visualization**:
- **Type**: Area chart
- **X-axis**: `date`
- **Y-axis**: `total_mcap_millions_usd`
- **Color**: Blue gradient
- **Title**: "Total Market Cap of Bonded Coins (Est.)"
- **Subtitle**: "Aggregate value flowing to Raydium (USD Millions)"
- **Y-axis label**: "Market Cap ($M)"

**Counter Card** (Current Week):
```sql
SELECT
    SUM(total_mcap_millions_usd) AS weekly_bonded_mcap
FROM (
    -- [Same query as above but filtered for current week]
    -- ...
)
WHERE date >= DATE_TRUNC('week', CURRENT_DATE);
```

---

### Query 6: Coin Peak Analysis (Top-Out Distribution)

**Purpose**: Understand where tokens typically peak

**Approach**: Use post-bonding trading volume as proxy for peak performance

```sql
WITH bonded_tokens AS (
    SELECT DISTINCT
        account_arguments[3] AS token_address,
        block_time AS bonding_time
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '30' day
        AND cardinality(account_arguments) >= 4

    UNION

    SELECT DISTINCT
        account_arguments[2] AS token_address,
        block_time AS bonding_time
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '30' day
        AND cardinality(account_arguments) >= 3
),

-- Track trading volume in first 7 days post-bonding
post_bonding_volume AS (
    SELECT
        b.token_address,
        SUM(CAST(t.amount AS DOUBLE) / 1e9) AS volume_sol_7d,
        COUNT(DISTINCT t.tx_id) AS trade_count_7d
    FROM bonded_tokens b
    LEFT JOIN tokens_solana.transfers t
        ON t.token_mint_address = b.token_address
        AND t.block_time BETWEEN b.bonding_time AND b.bonding_time + INTERVAL '7' day
    GROUP BY b.token_address
),

-- Categorize by performance
performance_buckets AS (
    SELECT
        token_address,
        volume_sol_7d,
        CASE
            WHEN volume_sol_7d >= 10000 THEN '$10M+ Peak'
            WHEN volume_sol_7d >= 5000 THEN '$5M-$10M Peak'
            WHEN volume_sol_7d >= 1000 THEN '$1M-$5M Peak'
            WHEN volume_sol_7d >= 500 THEN '$500k-$1M Peak'
            WHEN volume_sol_7d >= 100 THEN '$100k-$500k Peak'
            ELSE 'Under $100k Peak'
        END AS peak_category
    FROM post_bonding_volume
)

SELECT
    peak_category,
    COUNT(*) AS token_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM performance_buckets
GROUP BY peak_category
ORDER BY
    CASE peak_category
        WHEN '$10M+ Peak' THEN 1
        WHEN '$5M-$10M Peak' THEN 2
        WHEN '$1M-$5M Peak' THEN 3
        WHEN '$500k-$1M Peak' THEN 4
        WHEN '$100k-$500k Peak' THEN 5
        ELSE 6
    END;
```

**Visualization**:
- **Type**: Horizontal bar chart
- **X-axis**: `token_count`
- **Y-axis**: `peak_category` (sorted by value)
- **Colors**: Gradient from green (high) to red (low)
- **Title**: "Token Peak Performance Distribution"
- **Subtitle**: "Where tokens top out after bonding (last 30 days)"
- **Data labels**: Show percentage on bars

---

### Query 7: PumpSwap Trading Metrics

**Purpose**: Track pre-bonding activity on PumpFun's internal AMM

```sql
WITH pumpfun_trades AS (
    SELECT
        DATE_TRUNC('day', block_time) AS date,
        tx_id,
        account_arguments[1] AS trader,
        -- Detect buy vs sell by instruction type
        CASE
            WHEN bytearray_substring(data, 1, 8) = 0x66063d1201daebea THEN 'buy'
            WHEN bytearray_substring(data, 1, 8) = 0x33e685a4017f83ad THEN 'sell'
            ELSE 'other'
        END AS trade_type
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND block_time >= CURRENT_DATE - INTERVAL '90' day
        AND tx_success = true
        AND bytearray_substring(data, 1, 8) IN (
            0x66063d1201daebea,  -- Buy signature
            0x33e685a4017f83ad   -- Sell signature
        )
)

SELECT
    date,
    COUNT(DISTINCT tx_id) AS total_trades,
    COUNT(DISTINCT trader) AS unique_traders,
    COUNT(DISTINCT CASE WHEN trade_type = 'buy' THEN tx_id END) AS buy_count,
    COUNT(DISTINCT CASE WHEN trade_type = 'sell' THEN tx_id END) AS sell_count,
    ROUND(
        COUNT(DISTINCT CASE WHEN trade_type = 'buy' THEN tx_id END) * 100.0 /
        NULLIF(COUNT(DISTINCT tx_id), 0),
        2
    ) AS buy_percentage,
    ROUND(AVG(COUNT(DISTINCT tx_id)) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1) AS trades_7d_ma
FROM pumpfun_trades
GROUP BY date
ORDER BY date DESC;
```

**Visualization**:
- **Type**: Stacked area chart
- **X-axis**: `date`
- **Y-axis**: `buy_count` (green area), `sell_count` (red area)
- **Title**: "PumpSwap Buy vs Sell Pressure"
- **Subtitle**: "Pre-bonding trading activity"
- **Legend**: "Buys (Green)" / "Sells (Red)"

**Additional Chart**: Buy/Sell Ratio
- **Type**: Line chart
- **X-axis**: `date`
- **Y-axis**: `buy_percentage`
- **Reference line**: 50% (neutral)
- **Title**: "Buy Pressure % (PumpSwap)"

---

### Query 8: Time to Bonding (Velocity)

**Purpose**: How quickly do tokens reach bonding threshold

```sql
WITH token_launches AS (
    SELECT
        token_mint_address,
        MIN(block_time) AS launch_time
    FROM tokens_solana.transfers
    WHERE action = 'mint'
        AND outer_executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND block_time >= CURRENT_DATE - INTERVAL '30' day
    GROUP BY token_mint_address
),

token_bondings AS (
    SELECT
        account_arguments[3] AS token_address,
        MIN(block_time) AS bonding_time
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '30' day
        AND cardinality(account_arguments) >= 4
    GROUP BY account_arguments[3]

    UNION

    SELECT
        account_arguments[2] AS token_address,
        MIN(block_time) AS bonding_time
    FROM solana.instruction_calls
    WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        AND bytearray_substring(data, 1, 8) = 0xb712469c946da122
        AND tx_success = true
        AND block_time >= CURRENT_DATE - INTERVAL '30' day
        AND cardinality(account_arguments) >= 3
    GROUP BY account_arguments[2]
)

SELECT
    CASE
        WHEN date_diff('minute', l.launch_time, b.bonding_time) <= 30 THEN 'Under 30 min (Ultra Fast)'
        WHEN date_diff('minute', l.launch_time, b.bonding_time) <= 60 THEN '30-60 min (Very Fast)'
        WHEN date_diff('hour', l.launch_time, b.bonding_time) <= 6 THEN '1-6 hours (Fast)'
        WHEN date_diff('hour', l.launch_time, b.bonding_time) <= 24 THEN '6-24 hours (Moderate)'
        WHEN date_diff('hour', l.launch_time, b.bonding_time) <= 72 THEN '1-3 days (Slow)'
        ELSE '3+ days (Very Slow)'
    END AS time_to_bonding,
    COUNT(*) AS token_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage,
    ROUND(AVG(date_diff('hour', l.launch_time, b.bonding_time)), 1) AS avg_hours
FROM token_launches l
INNER JOIN token_bondings b ON l.token_mint_address = b.token_address
GROUP BY 1
ORDER BY avg_hours;
```

**Visualization**:
- **Type**: Pie chart or donut chart
- **Slices**: `time_to_bonding` categories
- **Values**: `percentage`
- **Colors**:
  - Ultra Fast: Dark Green
  - Very Fast: Green
  - Fast: Yellow-Green
  - Moderate: Yellow
  - Slow: Orange
  - Very Slow: Red
- **Title**: "Time to Bonding Distribution"
- **Subtitle**: "How fast do tokens reach graduation threshold"

---

## Visualization Specifications

### Dashboard Color Palette

```
Primary Colors:
- Success/Positive: #10B981 (Green)
- Warning/Moderate: #F59E0B (Amber)
- Alert/Negative: #EF4444 (Red)
- Neutral/Info: #3B82F6 (Blue)
- Accent: #8B5CF6 (Purple)

Background:
- Dark mode: #1F2937
- Light mode: #F9FAFB

Text:
- Primary: #111827
- Secondary: #6B7280
```

### Typography Standards

```
Dashboard Title: 24px, Bold
Section Headers: 18px, Semibold
Chart Titles: 16px, Semibold
Chart Subtitles: 12px, Regular
Axis Labels: 11px, Regular
Data Labels: 10px, Medium
```

### Chart Specifications

#### Line Charts
- Line width: 2px
- Point radius: 3px (show on hover)
- Grid lines: Light gray, 1px
- Tooltip: Dark background, white text

#### Bar Charts
- Bar opacity: 100%
- Bar spacing: 20%
- Grid lines: Horizontal only
- Data labels: On top of bars for values >5% of max

#### Area Charts
- Fill opacity: 30%
- Line opacity: 100%
- Gradient fill: Recommended
- Stacking: Used for comparisons (buy/sell)

#### Pie/Donut Charts
- Label position: Outside with leaders
- Show percentages: Yes
- Min slice size for label: 3%
- Donut hole: 50% for donut charts

---

## Dashboard Layout

### Overall Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    DASHBOARD HEADER                          │
│  PumpFun Trading Analytics | Last Updated: [timestamp]      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   SECTION 1: KEY METRICS                     │
│  [4 Big Number Cards in a row]                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              SECTION 2: BONDING PERFORMANCE                  │
│  [2 charts side by side]                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              SECTION 3: MARKET QUALITY                       │
│  [1 full-width chart + 1 split chart]                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              SECTION 4: PUMPSWAP ACTIVITY                    │
│  [2 charts side by side]                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              SECTION 5: TOKEN PERFORMANCE                    │
│  [2 charts side by side]                                    │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Layout Specifications

#### Section 1: Key Metrics (Row 1)
**4 Counter Cards (25% width each)**

1. **Tokens Launched (This Week)**
   - Value: From Query 2
   - Color: Purple
   - Icon: Rocket
   - Comparison: vs last week

2. **Tokens Bonded (This Week)**
   - Value: From Query 1
   - Color: Blue
   - Icon: Check Circle
   - Comparison: vs last week

3. **Bonding Rate (This Week)**
   - Value: From Query 3
   - Color: Green/Red (dynamic based on value)
   - Icon: Percentage
   - Comparison: vs last week

4. **1M Runners (This Week)**
   - Value: From Query 4
   - Color: Gold
   - Icon: Trophy
   - Comparison: vs last week

---

#### Section 2: Bonding Performance (Row 2)

**Left Chart (60% width):**
- **Query**: Query 1 (Daily Bonded Coins)
- **Type**: Line chart with area fill + 7-day MA
- **Height**: 300px

**Right Chart (40% width):**
- **Query**: Query 8 (Time to Bonding)
- **Type**: Donut chart
- **Height**: 300px

---

#### Section 3: Market Quality (Row 3)

**Full Width Chart (100%):**
- **Query**: Query 3 (Bonding Rate with Quality Zones)
- **Type**: Line chart with colored zones
- **Height**: 250px

**Two Charts Below (50% each):**

Left:
- **Query**: Query 2 (Token Launches)
- **Type**: Bar chart
- **Height**: 250px

Right:
- **Query**: Query 5 (Total Market Cap)
- **Type**: Area chart
- **Height**: 250px

---

#### Section 4: PumpSwap Activity (Row 4)

**Left Chart (60% width):**
- **Query**: Query 7 (Buy vs Sell Pressure)
- **Type**: Stacked area chart
- **Height**: 300px

**Right Chart (40% width):**
- **Query**: Query 7 (Buy Percentage)
- **Type**: Line chart with 50% reference line
- **Height**: 300px

---

#### Section 5: Token Performance (Row 5)

**Left Chart (50% width):**
- **Query**: Query 6 (Peak Distribution)
- **Type**: Horizontal bar chart
- **Height**: 350px

**Right Chart (50% width):**
- **Query**: Query 4 (1M Runners over time)
- **Type**: Bar chart
- **Height**: 350px

---

## Implementation Checklist

### Phase 1: Setup (Day 1)
- [ ] Create Dune account / verify access
- [ ] Create new dashboard: "PumpFun Trading Analytics"
- [ ] Set dashboard to private initially
- [ ] Add dashboard description and tags

### Phase 2: Core Queries (Days 1-2)
- [ ] Implement Query 1 (Bonded Coins)
- [ ] Implement Query 2 (Token Launches)
- [ ] Implement Query 3 (Bonding Rate)
- [ ] Test all queries for data accuracy
- [ ] Verify date ranges work correctly

### Phase 3: Advanced Queries (Days 2-3)
- [ ] Implement Query 4 (1M Runners)
- [ ] Implement Query 5 (Total Market Cap)
- [ ] Implement Query 6 (Peak Analysis)
- [ ] Implement Query 7 (PumpSwap Metrics)
- [ ] Implement Query 8 (Time to Bonding)

### Phase 4: Visualizations (Days 3-4)
- [ ] Create all counter cards (Section 1)
- [ ] Create bonding performance charts (Section 2)
- [ ] Create market quality charts (Section 3)
- [ ] Create PumpSwap charts (Section 4)
- [ ] Create performance charts (Section 5)
- [ ] Apply color palette consistently
- [ ] Add reference lines where specified
- [ ] Ensure all tooltips are informative

### Phase 5: Dashboard Assembly (Day 4)
- [ ] Arrange visualizations per layout spec
- [ ] Add section headers (text boxes)
- [ ] Add methodology notes
- [ ] Add data update timestamp
- [ ] Test responsive layout
- [ ] Add filters (date range selector)

### Phase 6: Quality Assurance (Day 5)
- [ ] Verify all data is accurate
- [ ] Check for null/zero values
- [ ] Test all interactive elements
- [ ] Review with stakeholders
- [ ] Gather feedback
- [ ] Make revisions

### Phase 7: Deployment (Day 5)
- [ ] Set dashboard to public (if applicable)
- [ ] Share link with client
- [ ] Document any known limitations
- [ ] Set up refresh schedule
- [ ] Create user guide
- [ ] Schedule follow-up review

---

## Data Validation & Quality Checks

### Expected Value Ranges

```
Metric                          | Expected Range       | Alert If
--------------------------------|---------------------|----------
Daily Token Launches            | 5,000 - 25,000      | < 1,000
Daily Bonded Coins              | 100 - 500           | < 50
Bonding Rate                    | 2% - 15%            | < 1%
1M Runners                      | 5 - 50 per day      | 0
PumpSwap Daily Trades           | 50,000 - 200,000    | < 10,000
Unique Traders                  | 10,000 - 50,000     | < 5,000
```

### Query Performance Targets

```
Query                           | Target Time         | Max Acceptable
--------------------------------|---------------------|----------------
Query 1 (Bonded Coins)          | < 30 seconds        | 2 minutes
Query 2 (Launches)              | < 20 seconds        | 90 seconds
Query 3 (Bonding Rate)          | < 45 seconds        | 2 minutes
Query 4 (1M Runners)            | < 60 seconds        | 3 minutes
Query 5 (Market Cap)            | < 30 seconds        | 2 minutes
Query 6 (Peak Analysis)         | < 45 seconds        | 2 minutes
Query 7 (PumpSwap)              | < 40 seconds        | 2 minutes
Query 8 (Time to Bonding)       | < 50 seconds        | 2 minutes
```

---

## Troubleshooting Guide

### Issue: Graduation/Bonding Shows 0

**Possible Causes:**
1. Bytecode signature changed
2. Account argument position changed
3. Date range too restrictive
4. tx_success filter too strict

**Solutions:**
```sql
-- Debug query to check for bonding events
SELECT
    DATE_TRUNC('day', block_time) AS date,
    bytearray_to_hex(bytearray_substring(data, 1, 8)) AS instruction_sig,
    COUNT(*) AS event_count,
    COUNT(DISTINCT account_arguments[2]) AS tokens_pos2,
    COUNT(DISTINCT account_arguments[3]) AS tokens_pos3
FROM solana.instruction_calls
WHERE executing_account = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
    AND block_time >= CURRENT_DATE - INTERVAL '7' day
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC
LIMIT 100;
```

### Issue: Query Timeout (Free Tier)

**Solutions:**
1. Reduce date range (90 days → 30 days)
2. Add more specific filters
3. Remove complex window functions
4. Sample data if acceptable

### Issue: Market Cap Estimates Inaccurate

**Solutions:**
1. Integrate with price oracle (e.g., Jupiter, Birdeye API)
2. Use DEX trade data for better estimates
3. Add disclaimer about estimation methodology
4. Update bonding threshold based on actual data

---

## Methodology Notes

### Market Cap Estimation
> Market cap estimates are based on the assumption that tokens bond to Raydium at approximately $69,000 market capitalization. This is PumpFun's standard bonding threshold as of [date]. Actual values may vary ±10%.

### Bot Filtering Criteria
> "1M Runners" are filtered for organic activity using the following criteria:
> - Minimum 50 unique traders in first 24 hours
> - Minimum 100 transactions
> - Minimum 100 SOL total volume (~$10k)
> - Transaction time distribution (not clustered in seconds)

### Data Freshness
> Dashboard queries are optimized for Dune Analytics free tier with 2-minute timeout limits. Data refreshes every [X hours]. For real-time data, upgrade to Dune Pro.

---

## Next Steps & Enhancements

### Short-term (Week 2-4)
1. Add holder distribution analysis
2. Integrate price oracles for accurate market caps
3. Add whale tracking (large traders)
4. Create alerts for anomalies
5. Add export functionality

### Medium-term (Month 2-3)
1. Predictive modeling for bonding success
2. Sentiment analysis integration
3. Multi-chain comparison (if applicable)
4. Custom date range filters
5. Portfolio tracking features

### Long-term (Quarter 2+)
1. API endpoint for programmatic access
2. Mobile-optimized view
3. Real-time WebSocket updates
4. Advanced bot detection algorithms
5. Integration with trading platforms

---

## Support & Maintenance

### Documentation
- All queries stored in: `/queries/`
- Visualization configs: `/visualizations/`
- Change log: `CHANGELOG.md`

### Update Schedule
- Weekly: Review data quality
- Bi-weekly: Update thresholds if needed
- Monthly: Add requested features
- Quarterly: Major version updates

### Contact
For questions or issues:
- Technical: [technical-contact]
- Business: [business-contact]
- Emergency: [emergency-contact]

---

## Appendix

### Glossary

**Bonding**: The process of a token graduating from PumpFun's bonding curve to Raydium DEX when reaching the market cap threshold.

**PumpSwap**: PumpFun's internal AMM (Automated Market Maker) where tokens trade before bonding.

**1M Runner**: A token that achieves $1 million market capitalization with verified organic trading activity.

**Bonding Rate**: Percentage of launched tokens that successfully bond to Raydium.

**Market Quality**: Classification of trading conditions based on bonding success rate (Excellent/Good/Fair/Poor).

### References

- PumpFun Documentation: [link]
- Raydium Documentation: [link]
- Solana Program Library: [link]
- Dune Analytics Docs: https://docs.dune.com/

---

**Document Version**: 1.0
**Last Updated**: [Date]
**Author**: [Your Name]
**Client**: [Client Name]
**Status**: Ready for Implementation
