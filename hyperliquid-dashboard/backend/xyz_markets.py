"""
XYZ Markets WebSocket Client
Connects to Hyperliquid WebSocket to fetch HIP-3 XYZ equity perpetuals data
"""

import websocket
import json
import threading
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Callable
from trade_database import TradeDatabase

class XYZMarketsClient:
    """WebSocket client for XYZ HIP-3 equity perpetuals"""

    def __init__(self, use_testnet: bool = False, max_trades_history: int = 10000,
                 use_database: bool = True, db_path: str = "xyz_trades.db"):
        self.api_url = (
            "https://api.hyperliquid-testnet.xyz" if use_testnet
            else "https://api.hyperliquid.xyz"
        )
        self.ws_url = (
            "wss://api.hyperliquid-testnet.xyz/ws" if use_testnet
            else "wss://api.hyperliquid.xyz/ws"
        )
        self.ws = None
        self.connected = False
        self.market_data = {}
        self.callbacks = []
        self.max_trades_history = max_trades_history  # Keep small buffer for quick access

        # Dynamically fetch all XYZ equity perps from API
        self.xyz_assets = self._fetch_xyz_assets()
        print(f"Discovered {len(self.xyz_assets)} XYZ equity perpetuals")

        # In-memory buffer (small, for quick access to recent data)
        self.all_trades_history = []

        # Database for persistent storage (billions of trades)
        self.use_database = use_database
        self.trade_db = None
        if use_database:
            self.trade_db = TradeDatabase(db_path=db_path, batch_size=100, batch_timeout=1.0)
            print(f"Database storage enabled: {db_path}")

    def _fetch_xyz_assets(self) -> List[str]:
        """
        Dynamically fetch all XYZ equity perpetual markets from API
        Returns list of asset names (e.g., ['xyz:XYZ100', 'xyz:NVDA', ...])
        """
        try:
            response = requests.post(
                f"{self.api_url}/info",
                json={"type": "meta", "dex": "xyz"},
                timeout=10
            )

            if response.ok:
                meta = response.json()
                universe = meta.get("universe", [])

                # Extract all asset names (including delisted ones)
                assets = [asset["name"] for asset in universe if "name" in asset]

                # Filter to only active assets (exclude delisted)
                active_assets = [
                    asset["name"] for asset in universe
                    if "name" in asset and not asset.get("isDelisted", False)
                ]

                print(f"Total XYZ markets: {len(assets)} ({len(active_assets)} active, {len(assets) - len(active_assets)} delisted)")

                # Return active assets only for trading data collection
                return active_assets
            else:
                print(f"Failed to fetch XYZ assets: {response.status_code}")
                # Fallback to known assets
                return self._get_fallback_assets()

        except Exception as e:
            print(f"Error fetching XYZ assets: {e}")
            return self._get_fallback_assets()

    def _get_fallback_assets(self) -> List[str]:
        """Fallback list of known XYZ assets if API fetch fails"""
        return [
            "xyz:XYZ100", "xyz:NVDA", "xyz:AAPL", "xyz:AMZN", "xyz:COIN",
            "xyz:GOLD", "xyz:GOOGL", "xyz:HOOD", "xyz:INTC", "xyz:META",
            "xyz:MSFT", "xyz:ORCL", "xyz:PLTR", "xyz:TSLA"
        ]

    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)

            # Check if this is market data for XYZ assets
            if "channel" in data and "data" in data:
                channel = data["channel"]

                # Handle different channel types
                if channel == "allMids":
                    # Update price data
                    mids = data["data"]["mids"]
                    for asset_name, price in mids.items():
                        if asset_name.startswith("xyz:"):
                            if asset_name not in self.market_data:
                                self.market_data[asset_name] = {}
                            self.market_data[asset_name]["mark_price"] = float(price)
                            self.market_data[asset_name]["last_update"] = datetime.now().isoformat()

                elif channel == "trades":
                    # Handle trades data
                    trades_data = data["data"]
                    if isinstance(trades_data, list):
                        for trade in trades_data:
                            coin = trade.get("coin", "")
                            if coin.startswith("xyz:"):
                                if coin not in self.market_data:
                                    self.market_data[coin] = {}
                                if "recent_trades" not in self.market_data[coin]:
                                    self.market_data[coin]["recent_trades"] = []
                                self.market_data[coin]["recent_trades"].append(trade)
                                # Keep only last 50 trades per asset
                                self.market_data[coin]["recent_trades"] = self.market_data[coin]["recent_trades"][-50:]

                                # Store in all_trades_history for analytics
                                trade_with_timestamp = {
                                    **trade,
                                    "received_at": datetime.now().timestamp()
                                }

                                # Add to in-memory buffer (small, for quick access)
                                self.all_trades_history.append(trade_with_timestamp)
                                if len(self.all_trades_history) > self.max_trades_history:
                                    self.all_trades_history = self.all_trades_history[-self.max_trades_history:]

                                # Add to database (async, for billions of trades)
                                if self.trade_db:
                                    self.trade_db.add_trade(trade_with_timestamp)

                                # Update current price from latest trade
                                latest_price = float(trade.get("px", 0))
                                if latest_price > 0:
                                    self.market_data[coin]["mark_price"] = latest_price
                                    self.market_data[coin]["last_update"] = datetime.now().isoformat()

                # Trigger callbacks
                for callback in self.callbacks:
                    callback(self.market_data)

        except Exception as e:
            print(f"Error processing WebSocket message: {e}")

    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"WebSocket error: {error}")
        self.connected = False

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        print(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.connected = False

    def on_open(self, ws):
        """Handle WebSocket open - subscribe to XYZ markets"""
        print("WebSocket connection opened")
        self.connected = True

        # Subscribe to all mids (includes all markets)
        subscribe_msg = {
            "method": "subscribe",
            "subscription": {
                "type": "allMids"
            }
        }
        ws.send(json.dumps(subscribe_msg))
        print("Subscribed to allMids")

        # Subscribe to trades for each XYZ asset
        for asset in self.xyz_assets[:5]:  # Start with top 5 to avoid overwhelming
            trades_msg = {
                "method": "subscribe",
                "subscription": {
                    "type": "trades",
                    "coin": asset
                }
            }
            ws.send(json.dumps(trades_msg))
            print(f"Subscribed to trades for {asset}")

    def connect(self):
        """Establish WebSocket connection"""
        print(f"Connecting to {self.ws_url}...")
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        # Run in a separate thread
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not self.connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if self.connected:
            print("WebSocket connected successfully")
        else:
            print("WebSocket connection timeout")

        return self.connected

    def disconnect(self):
        """Close WebSocket connection and database"""
        if self.ws:
            self.ws.close()
        self.connected = False

        # Close database connection
        if self.trade_db:
            self.trade_db.close()

    def register_callback(self, callback: Callable):
        """Register a callback function to be called when data updates"""
        self.callbacks.append(callback)

    def get_market_data(self) -> Dict:
        """Get current market data for all XYZ assets"""
        return self.market_data.copy()

    def get_asset_data(self, asset_name: str) -> Optional[Dict]:
        """Get market data for a specific XYZ asset"""
        return self.market_data.get(asset_name)

    def get_all_trades_history(self) -> List[Dict]:
        """Get all historical trades collected via WebSocket"""
        return self.all_trades_history.copy()

    def get_trades_since(self, seconds_ago: int) -> List[Dict]:
        """Get trades from the last N seconds"""
        # Use database if available (can handle billions of trades)
        if self.trade_db:
            return self.trade_db.get_trades_since(seconds_ago)

        # Fallback to in-memory buffer (limited to max_trades_history)
        cutoff = datetime.now().timestamp() - seconds_ago
        return [t for t in self.all_trades_history if t.get("received_at", 0) >= cutoff]

    def get_analytics_summary(self) -> Dict:
        """Get quick analytics summary from collected trades"""
        # Use database if available (much faster for large datasets)
        if self.trade_db:
            return self.trade_db.get_summary_stats()

        # Fallback to in-memory calculation
        if not self.all_trades_history:
            return {
                "total_trades": 0,
                "total_volume": 0,
                "unique_wallets": 0,
                "assets_active": 0
            }

        total_volume = 0
        unique_wallets = set()
        assets_active = set()

        for trade in self.all_trades_history:
            price = float(trade.get("px", 0))
            size = abs(float(trade.get("sz", 0)))
            total_volume += price * size

            coin = trade.get("coin", "")
            if coin:
                assets_active.add(coin)

            users = trade.get("users", [])
            for user in users:
                if user and user != "0x0000000000000000000000000000000000000000":
                    unique_wallets.add(user.lower())

        return {
            "total_trades": len(self.all_trades_history),
            "total_volume": total_volume,
            "unique_wallets": len(unique_wallets),
            "assets_active": len(assets_active),
            "oldest_trade_age_seconds": (
                datetime.now().timestamp() - self.all_trades_history[0].get("received_at", datetime.now().timestamp())
                if self.all_trades_history else 0
            )
        }


def test_xyz_websocket():
    """Test XYZ WebSocket connection"""
    print("Testing XYZ Markets WebSocket...")

    client = XYZMarketsClient(use_testnet=False)

    def on_data_update(data):
        print(f"\n=== Market Data Update ===")
        print(f"Total XYZ assets with data: {len(data)}")
        for asset, info in data.items():
            print(f"{asset}: ${info.get('mark_price', 'N/A')}")

    client.register_callback(on_data_update)

    if client.connect():
        print("Connected! Waiting for data...")
        # Keep alive for 30 seconds to receive data
        time.sleep(30)

        print("\n=== Final Market Data ===")
        final_data = client.get_market_data()
        print(json.dumps(final_data, indent=2))

        client.disconnect()
    else:
        print("Failed to connect")


if __name__ == "__main__":
    test_xyz_websocket()
