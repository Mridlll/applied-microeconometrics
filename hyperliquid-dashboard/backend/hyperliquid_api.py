"""
Hyperliquid API Client
Fetches trading data from Hyperliquid exchange via trade.xyz API
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class HyperliquidAPI:
    """Client for interacting with Hyperliquid API"""

    def __init__(self, use_testnet: bool = False):
        self.base_url = (
            "https://api.hyperliquid-testnet.xyz" if use_testnet
            else "https://api.hyperliquid.xyz"
        )
        self.info_url = f"{self.base_url}/info"

    def _post_request(self, endpoint: str, data: Dict) -> Dict:
        """Make POST request to API"""
        try:
            response = requests.post(
                endpoint,
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {}

    def get_all_mids(self) -> Dict:
        """Get current mid prices for all assets"""
        return self._post_request(
            self.info_url,
            {"type": "allMids"}
        )

    def get_user_state(self, user_address: str) -> Dict:
        """Get user's current state (positions, balances)"""
        return self._post_request(
            self.info_url,
            {"type": "clearinghouseState", "user": user_address}
        )

    def get_meta(self) -> Dict:
        """Get exchange metadata (available assets, universe info)"""
        return self._post_request(
            self.info_url,
            {"type": "meta"}
        )

    def get_meta_and_asset_ctxs(self) -> Dict:
        """Get asset contexts including funding rates, open interest, etc."""
        return self._post_request(
            self.info_url,
            {"type": "metaAndAssetCtxs"}
        )

    def get_l2_snapshot(self, coin: str) -> Dict:
        """Get L2 order book snapshot for a coin"""
        return self._post_request(
            self.info_url,
            {"type": "l2Book", "coin": coin}
        )

    def get_recent_trades(self, coin: str, limit: int = 100) -> List[Dict]:
        """Get recent trades for a coin"""
        result = self._post_request(
            self.info_url,
            {"type": "trades", "coin": coin}
        )
        if isinstance(result, list):
            return result[:limit]
        return []

    def get_candles(self, coin: str, interval: str = "1h",
                    start_time: Optional[int] = None,
                    end_time: Optional[int] = None) -> List[Dict]:
        """
        Get candlestick data
        interval: "1m", "15m", "1h", "4h", "1d"
        """
        if not start_time:
            start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
        if not end_time:
            end_time = int(datetime.now().timestamp() * 1000)

        result = self._post_request(
            self.info_url,
            {
                "type": "candleSnapshot",
                "req": {
                    "coin": coin,
                    "interval": interval,
                    "startTime": start_time,
                    "endTime": end_time
                }
            }
        )
        return result if isinstance(result, list) else []

    def get_funding_history(self, coin: str, start_time: Optional[int] = None) -> List[Dict]:
        """Get funding rate history"""
        if not start_time:
            start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)

        result = self._post_request(
            self.info_url,
            {
                "type": "fundingHistory",
                "coin": coin,
                "startTime": start_time
            }
        )
        return result if isinstance(result, list) else []

    def get_user_fills(self, user_address: str) -> List[Dict]:
        """Get user's trade fills"""
        result = self._post_request(
            self.info_url,
            {"type": "userFills", "user": user_address}
        )
        return result if isinstance(result, list) else []

    def get_user_funding(self, user_address: str, start_time: Optional[int] = None) -> List[Dict]:
        """Get user's funding payment history"""
        if not start_time:
            start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)

        result = self._post_request(
            self.info_url,
            {
                "type": "userFunding",
                "user": user_address,
                "startTime": start_time
            }
        )
        return result if isinstance(result, list) else []

    def get_open_orders(self, user_address: str) -> List[Dict]:
        """Get user's open orders"""
        result = self._post_request(
            self.info_url,
            {"type": "openOrders", "user": user_address}
        )
        return result if isinstance(result, list) else []

    def get_frontend_open_orders(self, user_address: str) -> List[Dict]:
        """Get user's frontend open orders"""
        result = self._post_request(
            self.info_url,
            {"type": "frontendOpenOrders", "user": user_address}
        )
        return result if isinstance(result, list) else []

    def get_universe(self) -> List[str]:
        """Get list of all tradable coins"""
        meta = self.get_meta()
        if meta and "universe" in meta:
            return [asset["name"] for asset in meta["universe"]]
        return []

    def get_market_summary(self) -> Dict:
        """Get comprehensive market summary"""
        # Get metadata and asset contexts
        meta_data = self.get_meta_and_asset_ctxs()

        summary = {
            "timestamp": datetime.now().isoformat(),
            "assets": []
        }

        # Handle if API returns unexpected format
        if not meta_data:
            return summary

        # Check if response is a list (alternative API response format)
        if isinstance(meta_data, list):
            # API returns [universe_data, asset_contexts]
            if len(meta_data) < 2:
                return summary

            universe = meta_data[0].get("universe", [])
            asset_ctxs = meta_data[1] if len(meta_data) > 1 else []

            # Build summary from universe and asset contexts
            for i, asset in enumerate(universe):
                asset_name = asset.get("name", "")

                # Get corresponding asset context
                asset_ctx = asset_ctxs[i] if i < len(asset_ctxs) else {}

                mark_price = float(asset_ctx.get("markPx", 0))
                prev_day_px = float(asset_ctx.get("prevDayPx", 0))

                asset_summary = {
                    "name": asset_name,
                    "mark_price": mark_price,
                    "funding_rate": float(asset_ctx.get("funding", 0)),
                    "open_interest": float(asset_ctx.get("openInterest", 0)),
                    "prev_day_px": prev_day_px,
                    "day_ntl_vlm": float(asset_ctx.get("dayNtlVlm", 0)),
                    "premium": float(asset_ctx.get("premium", 0) or 0),
                    "change_24h": 0
                }

                # Calculate 24h change
                if prev_day_px > 0:
                    asset_summary["change_24h"] = (
                        (mark_price - prev_day_px) / prev_day_px * 100
                    )

                summary["assets"].append(asset_summary)

            return summary

        # Original logic for dict response
        universe = meta_data.get("universe", [])

        for i, asset_ctx in enumerate(meta_data.get("assetCtxs", [])):
            if i < len(universe):
                asset_info = universe[i]
                asset_summary = {
                    "name": asset_info.get("name"),
                    "mark_price": float(asset_ctx.get("markPx", 0)),
                    "funding_rate": float(asset_ctx.get("funding", 0)),
                    "open_interest": float(asset_ctx.get("openInterest", 0)),
                    "prev_day_px": float(asset_ctx.get("prevDayPx", 0)),
                    "day_ntl_vlm": float(asset_ctx.get("dayNtlVlm", 0)),
                    "premium": float(asset_ctx.get("premium", 0))
                }

                # Calculate 24h change
                if asset_summary["prev_day_px"] > 0:
                    asset_summary["change_24h"] = (
                        (asset_summary["mark_price"] - asset_summary["prev_day_px"])
                        / asset_summary["prev_day_px"] * 100
                    )
                else:
                    asset_summary["change_24h"] = 0

                summary["assets"].append(asset_summary)

        return summary


def main():
    """Example usage"""
    api = HyperliquidAPI()

    print("Fetching Hyperliquid market data...\n")

    # Get market summary
    summary = api.get_market_summary()
    print(f"Market Summary ({summary['timestamp']}):")
    print(f"Total assets: {len(summary['assets'])}\n")

    # Display top 10 by volume
    sorted_assets = sorted(
        summary['assets'],
        key=lambda x: x['day_ntl_vlm'],
        reverse=True
    )[:10]

    print("Top 10 by 24h Volume:")
    print(f"{'Asset':<10} {'Price':<12} {'24h Change':<12} {'Volume (24h)':<15} {'Funding %':<12}")
    print("-" * 75)

    for asset in sorted_assets:
        print(
            f"{asset['name']:<10} "
            f"${asset['mark_price']:<11,.2f} "
            f"{asset['change_24h']:>+10.2f}% "
            f"${asset['day_ntl_vlm']:<14,.0f} "
            f"{asset['funding_rate']*100:>10.4f}%"
        )


if __name__ == "__main__":
    main()
