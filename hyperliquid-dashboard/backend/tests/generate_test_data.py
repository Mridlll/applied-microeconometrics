#!/usr/bin/env python3
"""
Generate realistic test data for HIP-3 Analytics Platform
Populates database with sample trades, snapshots, and user data
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import HIP3Database

# XYZ assets
XYZ_ASSETS = [
    "xyz:XYZ100", "xyz:TSLA", "xyz:NVDA", "xyz:PLTR", "xyz:META",
    "xyz:MSFT", "xyz:GOOGL", "xyz:AMZN", "xyz:AAPL", "xyz:COIN",
    "xyz:GOLD", "xyz:HOOD", "xyz:INTC", "xyz:ORCL", "xyz:AMD", "xyz:MU"
]

# Price ranges for each asset (realistic values)
ASSET_PRICES = {
    "xyz:XYZ100": (180, 220),
    "xyz:TSLA": (200, 300),
    "xyz:NVDA": (450, 550),
    "xyz:PLTR": (15, 25),
    "xyz:META": (450, 550),
    "xyz:MSFT": (400, 450),
    "xyz:GOOGL": (140, 160),
    "xyz:AMZN": (170, 200),
    "xyz:AAPL": (220, 240),
    "xyz:COIN": (200, 250),
    "xyz:GOLD": (2500, 2700),
    "xyz:HOOD": (25, 35),
    "xyz:INTC": (45, 55),
    "xyz:ORCL": (130, 150),
    "xyz:AMD": (150, 180),
    "xyz:MU": (90, 110),
}

def generate_wallet_address():
    """Generate random Ethereum-style address"""
    return f"0x{''.join(random.choices('0123456789abcdef', k=40))}"

def generate_trades(db: HIP3Database, num_trades: int = 10000, days_back: int = 30):
    """Generate realistic trade data"""
    print(f"\n📊 Generating {num_trades} trades over {days_back} days...")

    # Generate some consistent user addresses (100 users)
    users = [generate_wallet_address() for _ in range(100)]

    # Weight users (some are more active)
    user_weights = [1] * 50 + [3] * 30 + [10] * 15 + [50] * 5  # 5 whales

    now = datetime.now()

    for i in range(num_trades):
        # Random time in the past
        hours_ago = random.uniform(0, days_back * 24)
        timestamp = (now - timedelta(hours=hours_ago)).timestamp()

        # Pick asset (weighted towards popular ones)
        if random.random() < 0.3:
            coin = random.choice(["xyz:XYZ100", "xyz:TSLA", "xyz:NVDA"])  # Popular
        else:
            coin = random.choice(XYZ_ASSETS)

        # Pick user (weighted)
        user = random.choices(users, weights=user_weights, k=1)[0]

        # Generate trade details
        price_range = ASSET_PRICES[coin]
        price = random.uniform(*price_range)
        size = random.uniform(0.1, 50)  # Random size

        # Fee (0.03% of volume)
        fee = price * size * 0.0003

        # Random OI and funding
        oi = random.uniform(100, 10000)
        funding_rate = random.uniform(-0.0005, 0.0005)

        trade_data = {
            'timestamp': timestamp,
            'coin': coin,
            'side': random.choice(['buy', 'sell']),
            'price': price,
            'size': size,
            'user': user,
            'fee': fee,
            'oi': oi,
            'funding_rate': funding_rate
        }

        db.record_trade(trade_data)

        if (i + 1) % 1000 == 0:
            print(f"  ✓ Generated {i + 1}/{num_trades} trades")

    print(f"✅ Generated {num_trades} trades")

def generate_market_snapshots(db: HIP3Database, hours_back: int = 168):
    """Generate market snapshots (every hour)"""
    print(f"\n📸 Generating market snapshots for {hours_back} hours...")

    now = datetime.now()
    snapshots_per_asset = hours_back

    for coin in XYZ_ASSETS:
        base_price = sum(ASSET_PRICES[coin]) / 2
        base_oi = random.uniform(1_000_000, 50_000_000)

        for hour in range(snapshots_per_asset):
            timestamp = (now - timedelta(hours=hour))

            # Add some randomness/drift
            price_drift = random.uniform(-0.05, 0.05) * base_price
            mark_price = base_price + price_drift
            oracle_price = mark_price * random.uniform(0.999, 1.001)  # Very tight

            oi_drift = random.uniform(-0.1, 0.1) * base_oi
            oi = max(100_000, base_oi + oi_drift)

            volume_24h = random.uniform(oi * 0.1, oi * 2)

            snapshot_data = {
                'mark_price': mark_price,
                'oracle_price': oracle_price,
                'open_interest': oi / mark_price,
                'open_interest_usd': oi,
                'volume_24h': volume_24h,
                'funding_rate': random.uniform(-0.001, 0.001),
                'premium': mark_price - oracle_price,
                'prev_day_price': mark_price * random.uniform(0.95, 1.05),
                'num_trades_24h': random.randint(50, 500)
            }

            # Manually insert with specific timestamp
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO market_snapshots (
                    timestamp, coin, mark_price, oracle_price, open_interest,
                    open_interest_usd, volume_24h, funding_rate, premium,
                    prev_day_price, num_trades_24h
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp.timestamp(),
                coin,
                snapshot_data['mark_price'],
                snapshot_data['oracle_price'],
                snapshot_data['open_interest'],
                snapshot_data['open_interest_usd'],
                snapshot_data['volume_24h'],
                snapshot_data['funding_rate'],
                snapshot_data['premium'],
                snapshot_data['prev_day_price'],
                snapshot_data['num_trades_24h']
            ))
            conn.commit()

    print(f"✅ Generated {len(XYZ_ASSETS)} × {snapshots_per_asset} = {len(XYZ_ASSETS) * snapshots_per_asset} snapshots")

def generate_oracle_metrics(db: HIP3Database, hours_back: int = 48):
    """Generate oracle metrics"""
    print(f"\n🔮 Generating oracle metrics for {hours_back} hours...")

    now = datetime.now()

    for coin in XYZ_ASSETS:
        base_price = sum(ASSET_PRICES[coin]) / 2

        for hour in range(hours_back):
            timestamp = (now - timedelta(hours=hour))

            mark_price = base_price * random.uniform(0.99, 1.01)
            oracle_price = mark_price * random.uniform(0.9995, 1.0005)  # Very tight spread

            spread = abs(mark_price - oracle_price)
            spread_pct = (spread / oracle_price) * 100
            premium = mark_price - oracle_price

            # Tightness score
            if spread_pct < 0.01:
                tightness_score = 100
            elif spread_pct < 0.1:
                tightness_score = 100 - (spread_pct * 100)
            else:
                tightness_score = max(0, 90 - spread_pct * 10)

            # Manually insert
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO oracle_metrics (
                    timestamp, coin, mark_price, oracle_price, spread,
                    spread_pct, premium, tightness_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp.timestamp(),
                coin,
                mark_price,
                oracle_price,
                spread,
                spread_pct,
                premium,
                tightness_score
            ))
            conn.commit()

    print(f"✅ Generated {len(XYZ_ASSETS)} × {hours_back} = {len(XYZ_ASSETS) * hours_back} oracle metrics")

def generate_market_depth(db: HIP3Database, num_snapshots: int = 100):
    """Generate market depth snapshots"""
    print(f"\n📏 Generating {num_snapshots} market depth snapshots...")

    now = datetime.now()

    for i in range(num_snapshots):
        timestamp = (now - timedelta(minutes=random.randint(0, 1440)))  # Last 24h
        coin = random.choice(XYZ_ASSETS)

        base_price = sum(ASSET_PRICES[coin]) / 2

        # Generate depth metrics
        bid_depth_1pct = random.uniform(10, 500)
        bid_depth_5pct = random.uniform(50, 2000)
        ask_depth_1pct = random.uniform(10, 500)
        ask_depth_5pct = random.uniform(50, 2000)

        spread_bps = random.uniform(1, 20)  # 1-20 basis points
        depth_imbalance = (bid_depth_5pct / ask_depth_5pct) if ask_depth_5pct > 0 else 1

        best_bid = base_price * 0.9998
        best_ask = base_price * 1.0002

        # Manually insert
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO market_depth (
                timestamp, coin, bid_depth_1pct, bid_depth_5pct,
                ask_depth_1pct, ask_depth_5pct, spread_bps,
                depth_imbalance, best_bid, best_ask
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp.timestamp(),
            coin,
            bid_depth_1pct,
            bid_depth_5pct,
            ask_depth_1pct,
            ask_depth_5pct,
            spread_bps,
            depth_imbalance,
            best_bid,
            best_ask
        ))
        conn.commit()

    print(f"✅ Generated {num_snapshots} depth snapshots")

def generate_user_cohorts(db: HIP3Database):
    """Generate user cohort data from trades"""
    print(f"\n👥 Generating user cohort data...")

    conn = db.get_connection()
    cursor = conn.cursor()

    # Get all unique users from trades
    cursor.execute("""
        SELECT DISTINCT user FROM trades
    """)

    users = [row[0] for row in cursor.fetchall()]

    print(f"  Found {len(users)} unique users")

    # For each user, create cohort entry
    for user in users:
        # Get first trade date
        cursor.execute("""
            SELECT MIN(timestamp) as first_trade,
                   MAX(timestamp) as last_trade,
                   COUNT(*) as num_trades,
                   SUM(price * size) as total_volume,
                   SUM(fee) as total_fees
            FROM trades
            WHERE user = ?
        """, (user,))

        row = cursor.fetchone()
        first_timestamp = row[0]
        last_timestamp = row[1]
        num_trades = row[2]
        total_volume = row[3] or 0
        total_fees = row[4] or 0

        first_date = datetime.fromtimestamp(first_timestamp)
        last_date = datetime.fromtimestamp(last_timestamp)

        cohort_week = first_date.strftime("%Y-W%U")

        # Count active days
        cursor.execute("""
            SELECT COUNT(DISTINCT date(timestamp, 'unixepoch')) as days_active
            FROM trades
            WHERE user = ?
        """, (user,))

        days_active = cursor.fetchone()[0]

        # Get favorite asset
        cursor.execute("""
            SELECT coin, COUNT(*) as cnt
            FROM trades
            WHERE user = ?
            GROUP BY coin
            ORDER BY cnt DESC
            LIMIT 1
        """, (user,))

        fav_row = cursor.fetchone()
        favorite_asset = fav_row[0] if fav_row else None

        # Insert or update cohort
        cursor.execute("""
            INSERT OR REPLACE INTO user_cohorts (
                user_address, first_trade_date, cohort_week,
                total_volume, total_trades, total_fees_paid,
                last_active_date, days_active, favorite_asset
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user,
            first_date.strftime("%Y-%m-%d"),
            cohort_week,
            total_volume,
            num_trades,
            total_fees,
            last_date.strftime("%Y-%m-%d"),
            days_active,
            favorite_asset
        ))

    conn.commit()
    print(f"✅ Generated cohort data for {len(users)} users")

def main():
    """Generate all test data"""
    print("="*80)
    print("🧪 HIP-3 Analytics Platform - Test Data Generator")
    print("="*80)

    # Initialize database
    db = HIP3Database("hip3_analytics_test.db")
    print(f"\n✅ Database initialized: hip3_analytics_test.db")

    # Generate data
    generate_trades(db, num_trades=10000, days_back=30)
    generate_market_snapshots(db, hours_back=168)  # 1 week
    generate_oracle_metrics(db, hours_back=48)
    generate_market_depth(db, num_snapshots=200)
    generate_user_cohorts(db)

    # Print summary
    print("\n" + "="*80)
    print("📊 TEST DATA SUMMARY")
    print("="*80)

    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trades")
    print(f"Total Trades:          {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT COUNT(*) FROM market_snapshots")
    print(f"Market Snapshots:      {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT COUNT(*) FROM oracle_metrics")
    print(f"Oracle Metrics:        {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT COUNT(*) FROM market_depth")
    print(f"Depth Snapshots:       {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT COUNT(*) FROM user_cohorts")
    print(f"User Cohorts:          {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT SUM(price * size) FROM trades")
    total_volume = cursor.fetchone()[0] or 0
    print(f"Total Volume:          ${total_volume:,.2f}")

    cursor.execute("SELECT SUM(fee) FROM trades")
    total_fees = cursor.fetchone()[0] or 0
    print(f"Total Fees:            ${total_fees:,.2f}")

    cursor.execute("SELECT COUNT(DISTINCT user) FROM trades")
    print(f"Unique Traders:        {cursor.fetchone()[0]:,}")

    print("\n" + "="*80)
    print("✅ TEST DATA GENERATION COMPLETE!")
    print("="*80)
    print(f"\nDatabase: hip3_analytics_test.db")
    print(f"Ready for testing!")
    print()

if __name__ == "__main__":
    main()
