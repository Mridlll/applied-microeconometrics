"""
XYZ Markets WebSocket Client
Connects to Hyperliquid WebSocket to fetch HIP-3 XYZ equity perpetuals data
"""

import websocket
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable

class XYZMarketsClient:
    """WebSocket client for XYZ HIP-3 equity perpetuals"""

    def __init__(self, use_testnet: bool = False):
        self.ws_url = (
            "wss://api.hyperliquid-testnet.xyz/ws" if use_testnet
            else "wss://api.hyperliquid.xyz/ws"
        )
        self.ws = None
        self.connected = False
        self.market_data = {}
        self.callbacks = []

        # All known XYZ equity perps from perpDexs query
        self.xyz_assets = [
            "xyz:XYZ100",
            "xyz:NVDA",
            "xyz:AAPL",
            "xyz:AMZN",
            "xyz:COIN",
            "xyz:GOLD",
            "xyz:GOOGL",
            "xyz:HOOD",
            "xyz:INTC",
            "xyz:META",
            "xyz:MSFT",
            "xyz:ORCL",
            "xyz:PLTR",
            "xyz:TSLA"
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
                                # Keep only last 50 trades
                                self.market_data[coin]["recent_trades"] = self.market_data[coin]["recent_trades"][-50:]

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
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
        self.connected = False

    def register_callback(self, callback: Callable):
        """Register a callback function to be called when data updates"""
        self.callbacks.append(callback)

    def get_market_data(self) -> Dict:
        """Get current market data for all XYZ assets"""
        return self.market_data.copy()

    def get_asset_data(self, asset_name: str) -> Optional[Dict]:
        """Get market data for a specific XYZ asset"""
        return self.market_data.get(asset_name)


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
