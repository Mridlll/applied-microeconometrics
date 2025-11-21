# HIP-3 Analytics Platform - Complete Refactor Plan

## Current Issues
- ❌ Duplicate analytics modules (analytics.py, advanced_analytics.py vs hip3_*)
- ❌ No oracle tightness/spread metrics
- ❌ No market depth charts
- ❌ Missing platform-level metrics (growth, adoption, health)
- ❌ No user behavior analytics (patterns, cohorts, retention)
- ❌ UI needs complete overhaul
- ❌ No deep query system

## New Architecture

### Backend Structure
```
backend/
├── core/
│   ├── database.py          # Database layer (rename from trade_database.py)
│   ├── hyperliquid_client.py # API client (rename from hyperliquid_api.py)
│   └── models.py             # Data models
│
├── analytics/
│   ├── platform_metrics.py   # Platform-level KPIs (NEW)
│   ├── market_metrics.py     # Per-market oracle, spread, depth (NEW)
│   ├── user_metrics.py       # User behavior analytics (NEW)
│   ├── advanced_queries.py   # Complex analytical queries (NEW)
│   └── realtime.py           # WebSocket real-time analytics (refactor hip3_ws_analytics.py)
│
├── api/
│   └── server.py             # Flask API server (cleaned up)
│
└── tools/
    ├── snapshot_collector.py # Market snapshot collection
    └── volume_tracker.py     # Standalone volume tracker
```

### New Metrics

#### 1. Oracle Tightness & Spread
- **Mark vs Oracle Spread**: `(mark_price - oracle_price) / oracle_price`
- **Spread Volatility**: Standard deviation of spread over time
- **Tightness Score**: How closely mark tracks oracle (0-100)
- **Premium/Discount**: Current mark premium over oracle

#### 2. Market Depth
- **Bid/Ask Depth**: Liquidity at various price levels
- **Depth Imbalance**: Bid vs ask liquidity ratio
- **Orderbook Spread**: Best bid-ask spread
- **Depth Chart**: Visual representation of orderbook

#### 3. Platform Performance
- **Total Value Locked (TVL)**: Sum of all open interest
- **Daily Active Users**: Unique wallets trading per day
- **New User Growth**: Daily/weekly new user acquisition
- **Trade Velocity**: Trades per hour/day
- **Market Count Growth**: New XYZ markets over time
- **Platform Revenue**: Total fees collected

#### 4. User Behavior Metrics
- **User Cohorts**: Group users by signup week
- **Retention Rate**: % of users returning after N days
- **Trading Frequency Distribution**: Light/medium/heavy traders
- **Asset Preference Patterns**: Which assets users trade together
- **Time-of-Day Patterns**: When users are most active
- **User Journey**: First trade → engagement → retention

#### 5. Deep Analytics Queries
- **Whale Tracking**: Identify and track top traders
- **Market Concentration**: Gini coefficient for volume distribution
- **Cross-Market Analysis**: Correlation between asset volumes
- **Predictive Metrics**: Volume momentum, growth trends
- **Anomaly Detection**: Unusual trading patterns

### Database Schema Updates

```sql
-- New tables for platform metrics
CREATE TABLE daily_platform_metrics (
    date TEXT PRIMARY KEY,
    total_volume REAL,
    unique_traders INTEGER,
    new_users INTEGER,
    total_trades INTEGER,
    avg_trade_size REAL,
    total_oi REAL,
    total_revenue REAL
);

CREATE TABLE user_cohorts (
    user_address TEXT,
    first_trade_date TEXT,
    cohort_week TEXT,
    total_volume REAL,
    total_trades INTEGER,
    last_active_date TEXT,
    days_active INTEGER,
    PRIMARY KEY (user_address)
);

CREATE TABLE oracle_metrics (
    timestamp REAL,
    coin TEXT,
    mark_price REAL,
    oracle_price REAL,
    spread REAL,
    spread_pct REAL,
    premium REAL,
    PRIMARY KEY (timestamp, coin)
);

CREATE TABLE market_depth_snapshots (
    timestamp REAL,
    coin TEXT,
    bid_depth_1pct REAL,
    bid_depth_5pct REAL,
    ask_depth_1pct REAL,
    ask_depth_5pct REAL,
    spread_bps REAL,
    PRIMARY KEY (timestamp, coin)
);
```

### Modern UI Design

#### Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│  🎯 XYZ Platform Analytics                    [Timeframe ▼] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 Platform Overview                                        │
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │  TVL     │  DAU     │ Volume   │ Markets  │             │
│  │  $124M   │  2.3K    │ $89M/24h │    16    │             │
│  └──────────┴──────────┴──────────┴──────────┘             │
│                                                               │
│  📈 Growth Metrics (Sparklines)                             │
│  ┌──────────────────────────────────────────┐              │
│  │  Volume: ▁▂▃▅▆▇█▇▆▅ +23% ↑                │              │
│  │  Users:  ▁▂▂▃▄▅▆▇█▇ +45% ↑                │              │
│  │  Trades: ▂▃▄▅▆▅▄▅▆█ +12% ↑                │              │
│  └──────────────────────────────────────────┘              │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  [Markets] [Users] [Oracle] [Depth] [Advanced]              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  🎯 Market Health Matrix                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Asset    │ OI     │ Volume │ Oracle Δ │ Depth │ 🏥 │  │
│  ├──────────┼────────┼────────┼──────────┼───────┼────┤  │
│  │ XYZ100   │ $45M   │ $23M   │  0.01%   │  ████ │ 💚 │  │
│  │ TSLA     │ $12M   │ $8.2M  │  0.03%   │  ███░ │ 💚 │  │
│  │ NVDA     │ $28M   │ $15M   │  0.02%   │  ████ │ 💚 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  📊 Oracle Tightness Chart                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         [Line chart: Mark vs Oracle spread over time] │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  📉 Market Depth Visualization                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    [Interactive depth chart with bid/ask levels]      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Tech Stack for UI
- **Chart.js** → **ApexCharts** (more modern, interactive)
- **Plain CSS** → **Tailwind CSS** (utility-first, clean)
- **Vanilla JS** → **Alpine.js** (lightweight reactivity)
- **Dark theme** with glassmorphism effects
- **Real-time updates** via WebSocket
- **Responsive** mobile-first design

### Implementation Order

1. ✅ **Phase 1: Backend Rationalization** (Day 1)
   - Consolidate analytics files
   - Create new core/ structure
   - Database schema updates

2. ✅ **Phase 2: Oracle & Depth Metrics** (Day 1-2)
   - Implement oracle tightness tracking
   - Add market depth analysis
   - Historical tracking

3. ✅ **Phase 3: Platform Metrics** (Day 2)
   - Daily platform KPIs
   - Growth metrics
   - TVL tracking

4. ✅ **Phase 4: User Analytics** (Day 2-3)
   - Cohort analysis
   - Retention metrics
   - Usage patterns

5. ✅ **Phase 5: Deep Queries** (Day 3)
   - Complex analytics
   - Whale tracking
   - Anomaly detection

6. ✅ **Phase 6: UI Overhaul** (Day 3-4)
   - New dashboard design
   - Modern visualizations
   - Real-time updates

### API Endpoints (New Structure)

```
Platform Metrics:
GET /api/platform/overview
GET /api/platform/growth
GET /api/platform/tvl

Market Metrics:
GET /api/markets/health
GET /api/markets/:coin/oracle
GET /api/markets/:coin/depth
GET /api/markets/:coin/spread-history

User Metrics:
GET /api/users/cohorts
GET /api/users/retention
GET /api/users/patterns
GET /api/users/leaderboard

Advanced Analytics:
GET /api/analytics/whales
GET /api/analytics/concentration
GET /api/analytics/correlations
GET /api/analytics/anomalies
```

## Success Metrics

After refactor:
- ✅ Single source of truth for HIP-3 analytics
- ✅ Oracle tightness tracked for all markets
- ✅ Market depth visualized
- ✅ Platform health dashboard
- ✅ User behavior insights
- ✅ Professional, modern UI
- ✅ Fast, optimized queries
- ✅ Real-time updates

## Timeline

- **Day 1**: Backend rationalization + Oracle/Depth metrics
- **Day 2**: Platform metrics + User analytics
- **Day 3**: Deep queries + UI design
- **Day 4**: UI implementation + Testing

Total: 4 days for complete refactor
