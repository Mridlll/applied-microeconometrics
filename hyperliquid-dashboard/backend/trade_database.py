"""
Trade Database Module
Efficient SQLite-based storage for billions of HIP-3 XYZ market trades
"""

import sqlite3
import threading
import queue
import time
from datetime import datetime
from typing import Dict, List, Optional
import json


class TradeDatabase:
    """High-performance trade database with asynchronous writes"""

    def __init__(self, db_path: str = "xyz_trades.db", batch_size: int = 100, batch_timeout: float = 1.0):
        """
        Initialize trade database

        Args:
            db_path: Path to SQLite database file
            batch_size: Number of trades to batch before writing
            batch_timeout: Maximum seconds to wait before flushing batch
        """
        self.db_path = db_path
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

        # Write queue for asynchronous inserts
        self.write_queue = queue.Queue()
        self.running = True

        # Initialize database schema
        self._init_database()

        # Start background writer thread
        self.writer_thread = threading.Thread(target=self._batch_writer, daemon=True)
        self.writer_thread.start()

        print(f"Trade database initialized: {db_path}")

    def _init_database(self):
        """Create database schema with optimized indexes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main trades table - optimized for billions of rows
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin TEXT NOT NULL,
                price REAL NOT NULL,
                size REAL NOT NULL,
                volume REAL NOT NULL,
                side TEXT NOT NULL,
                timestamp_ms INTEGER NOT NULL,
                received_at REAL NOT NULL,
                user1 TEXT,
                user2 TEXT,
                trade_data TEXT
            )
        """)

        # Indexes for efficient querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_coin ON trades(coin)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_received_at ON trades(received_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_coin_received ON trades(coin, received_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user1 ON trades(user1)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user2 ON trades(user2)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON trades(timestamp_ms)")

        # Summary statistics table (for quick queries)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                updated_at REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                total_volume REAL NOT NULL,
                unique_wallets INTEGER NOT NULL,
                oldest_trade_timestamp REAL NOT NULL,
                newest_trade_timestamp REAL NOT NULL
            )
        """)

        conn.commit()
        conn.close()

        print("Database schema created with optimized indexes")

    def _batch_writer(self):
        """Background thread for batched database writes"""
        batch = []
        last_flush = time.time()

        while self.running:
            try:
                # Try to get a trade from queue with timeout
                try:
                    trade = self.write_queue.get(timeout=0.1)
                    batch.append(trade)
                except queue.Empty:
                    pass

                # Flush batch if size or timeout reached
                should_flush = (
                    len(batch) >= self.batch_size or
                    (batch and time.time() - last_flush >= self.batch_timeout)
                )

                if should_flush and batch:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = time.time()

            except Exception as e:
                print(f"Error in batch writer: {e}")
                time.sleep(1)

        # Final flush on shutdown
        if batch:
            self._flush_batch(batch)

    def _flush_batch(self, batch: List[Dict]):
        """Write a batch of trades to database"""
        if not batch:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Prepare batch insert
            insert_data = []
            for trade in batch:
                users = trade.get("users", [])
                user1 = users[0] if len(users) > 0 else None
                user2 = users[1] if len(users) > 1 else None

                # Filter out zero addresses
                if user1 == "0x0000000000000000000000000000000000000000":
                    user1 = None
                if user2 == "0x0000000000000000000000000000000000000000":
                    user2 = None

                price = float(trade.get("px", 0))
                size = abs(float(trade.get("sz", 0)))
                volume = price * size

                insert_data.append((
                    trade.get("coin", ""),
                    price,
                    size,
                    volume,
                    trade.get("side", ""),
                    trade.get("time", 0),
                    trade.get("received_at", time.time()),
                    user1,
                    user2,
                    json.dumps(trade)  # Store full trade data as JSON
                ))

            # Batch insert
            cursor.executemany("""
                INSERT INTO trades (coin, price, size, volume, side, timestamp_ms, received_at, user1, user2, trade_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, insert_data)

            conn.commit()

            # Update stats periodically (every 1000 trades)
            if cursor.lastrowid and cursor.lastrowid % 1000 == 0:
                self._update_stats(cursor)
                conn.commit()

        except Exception as e:
            print(f"Error flushing batch: {e}")
            conn.rollback()
        finally:
            conn.close()

    def _update_stats(self, cursor):
        """Update summary statistics table"""
        cursor.execute("""
            SELECT
                COUNT(*) as total_trades,
                SUM(volume) as total_volume,
                MIN(received_at) as oldest,
                MAX(received_at) as newest
            FROM trades
        """)
        row = cursor.fetchone()

        # Count unique wallets (this is expensive, so we do it less frequently)
        cursor.execute("""
            SELECT COUNT(DISTINCT wallet) FROM (
                SELECT user1 as wallet FROM trades WHERE user1 IS NOT NULL
                UNION
                SELECT user2 as wallet FROM trades WHERE user2 IS NOT NULL
            )
        """)
        unique_wallets = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO trade_stats (updated_at, total_trades, total_volume, unique_wallets, oldest_trade_timestamp, newest_trade_timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (time.time(), row[0], row[1] or 0, unique_wallets, row[2] or 0, row[3] or 0))

    def add_trade(self, trade: Dict):
        """Add a trade to the write queue (async)"""
        self.write_queue.put(trade)

    def add_trades_batch(self, trades: List[Dict]):
        """Add multiple trades to the write queue"""
        for trade in trades:
            self.write_queue.put(trade)

    def get_trades_since(self, seconds_ago: int, limit: Optional[int] = None) -> List[Dict]:
        """Get trades from the last N seconds"""
        cutoff = time.time() - seconds_ago

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT coin, price, size, volume, side, timestamp_ms, received_at, user1, user2, trade_data
            FROM trades
            WHERE received_at >= ?
            ORDER BY received_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (cutoff,))
        rows = cursor.fetchall()
        conn.close()

        # Convert to dict format
        trades = []
        for row in rows:
            trade = json.loads(row[9])  # trade_data column
            trades.append(trade)

        return trades

    def get_trades_by_coin(self, coin: str, hours_back: float = 24, limit: Optional[int] = None) -> List[Dict]:
        """Get trades for a specific coin"""
        cutoff = time.time() - (hours_back * 3600)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT trade_data
            FROM trades
            WHERE coin = ? AND received_at >= ?
            ORDER BY received_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (coin, cutoff))
        rows = cursor.fetchall()
        conn.close()

        return [json.loads(row[0]) for row in rows]

    def get_trades_by_wallet(self, wallet: str, hours_back: float = 24) -> List[Dict]:
        """Get all trades involving a specific wallet"""
        cutoff = time.time() - (hours_back * 3600)
        wallet_lower = wallet.lower()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT trade_data
            FROM trades
            WHERE (user1 = ? OR user2 = ?) AND received_at >= ?
            ORDER BY received_at DESC
        """, (wallet_lower, wallet_lower, cutoff))

        rows = cursor.fetchall()
        conn.close()

        return [json.loads(row[0]) for row in rows]

    def get_summary_stats(self) -> Dict:
        """Get quick summary statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get total count and volume
        cursor.execute("SELECT COUNT(*), SUM(volume), MIN(received_at), MAX(received_at) FROM trades")
        row = cursor.fetchone()

        total_trades = row[0] or 0
        total_volume = row[1] or 0
        oldest = row[2] or time.time()
        newest = row[3] or time.time()

        # Get unique wallets (expensive but cached)
        cursor.execute("""
            SELECT COUNT(DISTINCT wallet) FROM (
                SELECT user1 as wallet FROM trades WHERE user1 IS NOT NULL
                UNION
                SELECT user2 as wallet FROM trades WHERE user2 IS NOT NULL
            )
        """)
        unique_wallets = cursor.fetchone()[0]

        # Get asset count
        cursor.execute("SELECT COUNT(DISTINCT coin) FROM trades")
        assets_active = cursor.fetchone()[0]

        # Get queue size
        queue_size = self.write_queue.qsize()

        conn.close()

        return {
            "total_trades": total_trades,
            "total_volume": total_volume,
            "unique_wallets": unique_wallets,
            "assets_active": assets_active,
            "oldest_trade_age_seconds": time.time() - oldest if total_trades > 0 else 0,
            "newest_trade_age_seconds": time.time() - newest if total_trades > 0 else 0,
            "write_queue_size": queue_size,
            "database_path": self.db_path
        }

    def get_database_size(self) -> int:
        """Get database file size in bytes"""
        import os
        try:
            return os.path.getsize(self.db_path)
        except:
            return 0

    def cleanup_old_trades(self, days_to_keep: int = 30):
        """Delete trades older than specified days (for maintenance)"""
        cutoff = time.time() - (days_to_keep * 24 * 3600)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM trades WHERE received_at < ?", (cutoff,))
        deleted = cursor.rowcount

        # Vacuum to reclaim space
        cursor.execute("VACUUM")

        conn.commit()
        conn.close()

        print(f"Cleaned up {deleted} old trades (keeping last {days_to_keep} days)")
        return deleted

    def close(self):
        """Shutdown database and flush remaining writes"""
        print("Shutting down trade database...")
        self.running = False

        # Wait for writer thread to finish
        if self.writer_thread.is_alive():
            self.writer_thread.join(timeout=5)

        print(f"Trade database closed. Queue had {self.write_queue.qsize()} pending writes.")


def test_database():
    """Test trade database functionality"""
    print("Testing Trade Database...")

    # Create test database
    db = TradeDatabase(db_path="test_trades.db", batch_size=10)

    # Add test trades
    for i in range(100):
        trade = {
            "coin": f"xyz:TEST{i % 5}",
            "px": 100 + i,
            "sz": 1.5,
            "side": "B" if i % 2 == 0 else "A",
            "time": int(time.time() * 1000),
            "received_at": time.time(),
            "users": [f"0x{'1' * 40}", f"0x{'2' * 40}"]
        }
        db.add_trade(trade)

    # Wait for writes
    print("Waiting for batch writes...")
    time.sleep(3)

    # Get stats
    stats = db.get_summary_stats()
    print(f"\nDatabase Stats:")
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Total Volume: ${stats['total_volume']:,.2f}")
    print(f"  Unique Wallets: {stats['unique_wallets']}")
    print(f"  Queue Size: {stats['write_queue_size']}")

    # Query recent trades
    recent = db.get_trades_since(60)
    print(f"\nRecent trades (last 60s): {len(recent)}")

    # Query by coin
    coin_trades = db.get_trades_by_coin("xyz:TEST1", hours_back=1)
    print(f"xyz:TEST1 trades: {len(coin_trades)}")

    db.close()
    print("\nTest complete!")


if __name__ == "__main__":
    test_database()
