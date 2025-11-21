"""
Advanced HIP-3 Analytics Module
Comprehensive analytics for all HIP-3 deployed markets (XYZ, FLX, VNTL)
Includes: deployer economics, oracle metrics, correlations, trader behavior, and more
"""

import requests
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from trade_database import TradeDatabase
import statistics


class HIP3AdvancedAnalytics:
    """Advanced analytics for HIP-3 ecosystem"""

    def __init__(self, use_testnet: bool = False):
        self.api_url = (
            "https://api.hyperliquid-testnet.xyz" if use_testnet
            else "https://api.hyperliquid.xyz"
        )
        self.trade_db = None

        # Fee structure
        self.TAKER_FEE = 0.00045  # 0.045%
        self.MAKER_REBATE = 0.00015  # 0.015%

    def set_trade_database(self, trade_db: TradeDatabase):
        """Connect to trade database for historical analysis"""
        self.trade_db = trade_db

    def get_all_hip3_deployers(self) -> List[Dict]:
        """Fetch all HIP-3 deployer information"""
        try:
            response = requests.post(
                f"{self.api_url}/info",
                json={"type": "perpDexs"},
                timeout=10
            )

            if response.ok:
                dexs = response.json()
                # Filter out None entries
                return [dex for dex in dexs if dex is not None]
            return []

        except Exception as e:
            print(f"Error fetching HIP-3 deployers: {e}")
            return []

    def get_deployer_economics(self, hours_back: float = 24) -> Dict:
        """
        Track deployer economics and revenue
        Returns revenue breakdown for each HIP-3 deployer
        """
        deployers = self.get_all_hip3_deployers()

        result = {
            "timestamp": datetime.now().isoformat(),
            "timeframe_hours": hours_back,
            "deployers": []
        }

        for dex in deployers:
            name = dex.get("name", "unknown")

            # Get trades for this dex's markets
            if self.trade_db:
                trades = self._get_dex_trades(name, hours_back)
            else:
                trades = []

            # Calculate revenue
            total_volume = sum(
                float(t.get("px", 0)) * abs(float(t.get("sz", 0)))
                for t in trades
            )

            # Estimate taker/maker split (70% taker, 30% maker)
            taker_volume = total_volume * 0.7
            maker_volume = total_volume * 0.3

            taker_fees = taker_volume * self.TAKER_FEE
            maker_rebates = maker_volume * self.MAKER_REBATE
            platform_revenue = taker_fees - maker_rebates

            # Deployer gets portion based on deployerFeeScale
            deployer_fee_scale = float(dex.get("deployerFeeScale", 1.0))
            deployer_revenue = platform_revenue * deployer_fee_scale

            result["deployers"].append({
                "name": name,
                "full_name": dex.get("fullName", ""),
                "deployer_address": dex.get("deployer", ""),
                "fee_recipient": dex.get("feeRecipient", ""),
                "total_markets": len(dex.get("assetToStreamingOiCap", [])),
                "deployer_fee_scale": deployer_fee_scale,
                "total_volume": total_volume,
                "taker_fees": taker_fees,
                "maker_rebates": maker_rebates,
                "platform_revenue": platform_revenue,
                "deployer_revenue": deployer_revenue,
                "total_trades": len(trades)
            })

        # Add totals
        result["total_hip3_volume"] = sum(d["total_volume"] for d in result["deployers"])
        result["total_hip3_revenue"] = sum(d["platform_revenue"] for d in result["deployers"])
        result["total_deployer_revenue"] = sum(d["deployer_revenue"] for d in result["deployers"])

        # Calculate actual data collection window
        if self.trade_db:
            db_stats = self.trade_db.get_summary_stats()
            actual_hours = db_stats.get('oldest_trade_age_seconds', 0) / 3600
            result["actual_data_hours"] = round(actual_hours, 2)
            result["is_full_24h"] = actual_hours >= 24
            result["disclaimer"] = f"Data from last {round(actual_hours, 1)} hours (not full 24h)" if actual_hours < 24 else "Full 24h data"

        return result

    def get_oracle_performance(self, dex: str = "xyz") -> Dict:
        """
        Analyze oracle performance: update frequency, price deviations
        """
        try:
            # Get current market data with oracle prices
            response = requests.post(
                f"{self.api_url}/info",
                json={"type": "metaAndAssetCtxs", "dex": dex},
                timeout=10
            )

            if not response.ok:
                return {"error": "Failed to fetch oracle data"}

            data = response.json()
            meta = data[0] if len(data) > 0 else {}
            asset_ctxs = data[1] if len(data) > 1 else []

            deployers = self.get_all_hip3_deployers()
            dex_info = next((d for d in deployers if d and d.get("name") == dex), {})

            oracle_metrics = {
                "dex": dex,
                "oracle_updater": dex_info.get("oracleUpdater", "N/A"),
                "timestamp": datetime.now().isoformat(),
                "assets": []
            }

            total_deviation = 0
            total_premium = 0

            for ctx in asset_ctxs:
                oracle_px = float(ctx.get("oraclePx", 0))
                mark_px = float(ctx.get("markPx", 0))
                mid_px = float(ctx.get("midPx", 0))

                # Calculate deviations
                oracle_to_mark_dev = ((mark_px - oracle_px) / oracle_px * 100) if oracle_px > 0 else 0
                oracle_to_mid_dev = ((mid_px - oracle_px) / oracle_px * 100) if oracle_px > 0 else 0

                premium = float(ctx.get("premium", 0))

                total_deviation += abs(oracle_to_mark_dev)
                total_premium += premium

                # Get asset name from meta
                asset_name = "unknown"
                universe = meta.get("universe", [])
                if asset_ctxs.index(ctx) < len(universe):
                    asset_name = universe[asset_ctxs.index(ctx)].get("name", "unknown")

                oracle_metrics["assets"].append({
                    "asset": asset_name,
                    "oracle_price": oracle_px,
                    "mark_price": mark_px,
                    "mid_price": mid_px,
                    "oracle_to_mark_deviation_pct": round(oracle_to_mark_dev, 4),
                    "oracle_to_mid_deviation_pct": round(oracle_to_mid_dev, 4),
                    "premium": premium,
                    "funding_rate": float(ctx.get("funding", 0))
                })

            oracle_metrics["avg_deviation_pct"] = total_deviation / len(asset_ctxs) if asset_ctxs else 0
            oracle_metrics["avg_premium"] = total_premium / len(asset_ctxs) if asset_ctxs else 0

            return oracle_metrics

        except Exception as e:
            print(f"Error analyzing oracle performance: {e}")
            return {"error": str(e)}

    def get_market_maturity_analysis(self, dex: str = "xyz") -> Dict:
        """
        Analyze market lifecycle and maturity
        Track volume growth, OI growth, delisted markets
        """
        try:
            # Get meta to see delisted markets
            response = requests.post(
                f"{self.api_url}/info",
                json={"type": "meta", "dex": dex},
                timeout=10
            )

            if not response.ok:
                return {"error": "Failed to fetch market data"}

            meta = response.json()
            universe = meta.get("universe", [])

            # Get current market contexts
            ctx_response = requests.post(
                f"{self.api_url}/info",
                json={"type": "metaAndAssetCtxs", "dex": dex},
                timeout=10
            )

            asset_ctxs = []
            if ctx_response.ok:
                ctx_data = ctx_response.json()
                asset_ctxs = ctx_data[1] if len(ctx_data) > 1 else []

            result = {
                "dex": dex,
                "timestamp": datetime.now().isoformat(),
                "total_markets": len(universe),
                "active_markets": [],
                "delisted_markets": []
            }

            for i, asset in enumerate(universe):
                asset_name = asset.get("name", "unknown")
                is_delisted = asset.get("isDelisted", False)

                # Get current metrics if available
                ctx = asset_ctxs[i] if i < len(asset_ctxs) else {}

                market_info = {
                    "asset": asset_name,
                    "max_leverage": asset.get("maxLeverage", 0),
                    "margin_mode": asset.get("marginMode", ""),
                    "day_volume": float(ctx.get("dayNtlVlm", 0)) if ctx else 0,
                    "open_interest": float(ctx.get("openInterest", 0)) if ctx else 0,
                    "funding_rate": float(ctx.get("funding", 0)) if ctx else 0,
                    "mark_price": float(ctx.get("markPx", 0)) if ctx else 0
                }

                # Get trade history from database
                if self.trade_db:
                    trades_24h = self._get_asset_trades(asset_name, 24)
                    trades_7d = self._get_asset_trades(asset_name, 168)

                    market_info["trades_24h"] = len(trades_24h)
                    market_info["trades_7d"] = len(trades_7d)
                    market_info["volume_24h"] = sum(
                        float(t.get("px", 0)) * abs(float(t.get("sz", 0)))
                        for t in trades_24h
                    )
                    market_info["volume_7d"] = sum(
                        float(t.get("px", 0)) * abs(float(t.get("sz", 0)))
                        for t in trades_7d
                    )

                    # Growth rate
                    if market_info["trades_7d"] > 0:
                        market_info["volume_growth_rate"] = (
                            market_info["volume_24h"] / (market_info["volume_7d"] / 7) - 1
                        ) * 100

                if is_delisted:
                    result["delisted_markets"].append(market_info)
                else:
                    result["active_markets"].append(market_info)

            # Sort active markets by volume
            result["active_markets"].sort(key=lambda x: x.get("day_volume", 0), reverse=True)

            return result

        except Exception as e:
            print(f"Error analyzing market maturity: {e}")
            return {"error": str(e)}

    def get_trader_leaderboard(self, hours_back: float = 24, limit: int = 50, dex: str = "xyz") -> Dict:
        """
        Top traders leaderboard for HIP-3 markets
        Ranked by volume, trade count, and estimated PnL
        """
        if not self.trade_db:
            return {"error": "Database not connected"}

        try:
            seconds_back = int(hours_back * 3600)
            trades = self.trade_db.get_trades_since(seconds_back)

            # Filter to specific dex
            dex_trades = [t for t in trades if t.get("coin", "").startswith(f"{dex}:")]

            # Aggregate by wallet
            wallet_stats = defaultdict(lambda: {
                "volume": 0,
                "trades": 0,
                "assets_traded": set(),
                "buy_volume": 0,
                "sell_volume": 0,
                "fees_paid": 0
            })

            for trade in dex_trades:
                users = trade.get("users", [])
                price = float(trade.get("px", 0))
                size = abs(float(trade.get("sz", 0)))
                volume = price * size
                side = trade.get("side", "")
                coin = trade.get("coin", "")

                for user in users:
                    if user and user != "0x0000000000000000000000000000000000000000":
                        wallet = user.lower()
                        wallet_stats[wallet]["volume"] += volume
                        wallet_stats[wallet]["trades"] += 1
                        wallet_stats[wallet]["assets_traded"].add(coin)

                        if side == "B":
                            wallet_stats[wallet]["buy_volume"] += volume
                        else:
                            wallet_stats[wallet]["sell_volume"] += volume

                        # Estimate fees (assume 70% taker)
                        wallet_stats[wallet]["fees_paid"] += volume * 0.7 * self.TAKER_FEE

            # Convert to list and calculate metrics
            leaderboard = []
            for wallet, stats in wallet_stats.items():
                leaderboard.append({
                    "wallet": wallet,
                    "total_volume": stats["volume"],
                    "trade_count": stats["trades"],
                    "assets_traded_count": len(stats["assets_traded"]),
                    "assets_traded": list(stats["assets_traded"]),
                    "buy_volume": stats["buy_volume"],
                    "sell_volume": stats["sell_volume"],
                    "buy_sell_ratio": stats["buy_volume"] / stats["sell_volume"] if stats["sell_volume"] > 0 else 0,
                    "avg_trade_size": stats["volume"] / stats["trades"] if stats["trades"] > 0 else 0,
                    "fees_paid": stats["fees_paid"],
                    "market_share_pct": 0  # Will calculate after sorting
                })

            # Sort by volume
            leaderboard.sort(key=lambda x: x["total_volume"], reverse=True)

            # Calculate market share
            total_volume = sum(t["total_volume"] for t in leaderboard)
            for trader in leaderboard:
                trader["market_share_pct"] = (trader["total_volume"] / total_volume * 100) if total_volume > 0 else 0

            return {
                "dex": dex,
                "timeframe_hours": hours_back,
                "timestamp": datetime.now().isoformat(),
                "total_traders": len(leaderboard),
                "total_volume": total_volume,
                "leaderboard": leaderboard[:limit]
            }

        except Exception as e:
            print(f"Error generating trader leaderboard: {e}")
            return {"error": str(e)}

    def get_cross_market_correlations(self, hours_back: float = 24, dex: str = "xyz") -> Dict:
        """
        Calculate price correlations between HIP-3 assets
        """
        if not self.trade_db:
            return {"error": "Database not connected"}

        try:
            seconds_back = int(hours_back * 3600)
            trades = self.trade_db.get_trades_since(seconds_back)

            # Filter to dex
            dex_trades = [t for t in trades if t.get("coin", "").startswith(f"{dex}:")]

            # Group trades by asset and create price series
            asset_prices = defaultdict(list)

            for trade in sorted(dex_trades, key=lambda x: x.get("received_at", 0)):
                coin = trade.get("coin", "")
                price = float(trade.get("px", 0))
                asset_prices[coin].append(price)

            # Calculate correlations
            assets = list(asset_prices.keys())
            correlation_matrix = []

            for asset1 in assets:
                row = []
                for asset2 in assets:
                    if len(asset_prices[asset1]) > 1 and len(asset_prices[asset2]) > 1:
                        # Resample to same length (take last N points)
                        min_len = min(len(asset_prices[asset1]), len(asset_prices[asset2]))
                        prices1 = asset_prices[asset1][-min_len:]
                        prices2 = asset_prices[asset2][-min_len:]

                        if min_len > 2:
                            correlation = np.corrcoef(prices1, prices2)[0, 1]
                            row.append(round(float(correlation), 4))
                        else:
                            row.append(0)
                    else:
                        row.append(0 if asset1 != asset2 else 1)

                correlation_matrix.append(row)

            return {
                "dex": dex,
                "timeframe_hours": hours_back,
                "timestamp": datetime.now().isoformat(),
                "assets": assets,
                "correlation_matrix": correlation_matrix
            }

        except Exception as e:
            print(f"Error calculating correlations: {e}")
            return {"error": str(e)}

    def get_growth_metrics(self, dex: str = "xyz") -> Dict:
        """
        Track HIP-3 growth and adoption metrics
        """
        if not self.trade_db:
            return {"error": "Database not connected"}

        try:
            # Get metrics for different time windows
            trades_1h = self.trade_db.get_trades_since(3600)
            trades_24h = self.trade_db.get_trades_since(86400)
            trades_7d = self.trade_db.get_trades_since(604800)

            # Filter to dex
            dex_trades_1h = [t for t in trades_1h if t.get("coin", "").startswith(f"{dex}:")]
            dex_trades_24h = [t for t in trades_24h if t.get("coin", "").startswith(f"{dex}:")]
            dex_trades_7d = [t for t in trades_7d if t.get("coin", "").startswith(f"{dex}:")]

            # Calculate volumes
            volume_1h = sum(float(t.get("px", 0)) * abs(float(t.get("sz", 0))) for t in dex_trades_1h)
            volume_24h = sum(float(t.get("px", 0)) * abs(float(t.get("sz", 0))) for t in dex_trades_24h)
            volume_7d = sum(float(t.get("px", 0)) * abs(float(t.get("sz", 0))) for t in dex_trades_7d)

            # Unique wallets
            wallets_1h = self._extract_unique_wallets(dex_trades_1h)
            wallets_24h = self._extract_unique_wallets(dex_trades_24h)
            wallets_7d = self._extract_unique_wallets(dex_trades_7d)

            # New vs returning
            new_wallets_24h = wallets_24h - wallets_7d

            return {
                "dex": dex,
                "timestamp": datetime.now().isoformat(),
                "last_hour": {
                    "trades": len(dex_trades_1h),
                    "volume": volume_1h,
                    "unique_wallets": len(wallets_1h),
                    "avg_trade_size": volume_1h / len(dex_trades_1h) if dex_trades_1h else 0
                },
                "last_24h": {
                    "trades": len(dex_trades_24h),
                    "volume": volume_24h,
                    "unique_wallets": len(wallets_24h),
                    "new_wallets": len(new_wallets_24h),
                    "avg_trade_size": volume_24h / len(dex_trades_24h) if dex_trades_24h else 0
                },
                "last_7d": {
                    "trades": len(dex_trades_7d),
                    "volume": volume_7d,
                    "unique_wallets": len(wallets_7d),
                    "avg_trade_size": volume_7d / len(dex_trades_7d) if dex_trades_7d else 0
                },
                "growth_rates": {
                    "volume_24h_vs_7d_avg": ((volume_24h / (volume_7d / 7)) - 1) * 100 if volume_7d > 0 else 0,
                    "trades_24h_vs_7d_avg": ((len(dex_trades_24h) / (len(dex_trades_7d) / 7)) - 1) * 100 if dex_trades_7d else 0,
                    "wallet_retention_rate": (len(wallets_24h - new_wallets_24h) / len(wallets_24h) * 100) if wallets_24h else 0
                }
            }

        except Exception as e:
            print(f"Error calculating growth metrics: {e}")
            return {"error": str(e)}

    def get_trade_size_distribution(self, hours_back: float = 24, dex: str = "xyz") -> Dict:
        """
        Analyze trade size distribution (microstructure analysis)
        """
        if not self.trade_db:
            return {"error": "Database not connected"}

        try:
            seconds_back = int(hours_back * 3600)
            trades = self.trade_db.get_trades_since(seconds_back)

            # Filter to dex
            dex_trades = [t for t in trades if t.get("coin", "").startswith(f"{dex}:")]

            # Extract trade sizes
            trade_sizes = [
                float(t.get("px", 0)) * abs(float(t.get("sz", 0)))
                for t in dex_trades
            ]

            if not trade_sizes:
                return {"error": "No trades found"}

            # Calculate distribution metrics
            trade_sizes_sorted = sorted(trade_sizes)

            # Percentiles
            percentiles = {
                "p10": np.percentile(trade_sizes_sorted, 10),
                "p25": np.percentile(trade_sizes_sorted, 25),
                "p50": np.percentile(trade_sizes_sorted, 50),
                "p75": np.percentile(trade_sizes_sorted, 75),
                "p90": np.percentile(trade_sizes_sorted, 90),
                "p95": np.percentile(trade_sizes_sorted, 95),
                "p99": np.percentile(trade_sizes_sorted, 99)
            }

            # Histogram bins
            bins = [0, 100, 500, 1000, 5000, 10000, 50000, 100000, float('inf')]
            bin_labels = ["<$100", "$100-500", "$500-1k", "$1k-5k", "$5k-10k", "$10k-50k", "$50k-100k", ">$100k"]
            histogram = [0] * len(bin_labels)

            for size in trade_sizes:
                for i, bin_max in enumerate(bins[1:]):
                    if size < bin_max:
                        histogram[i] += 1
                        break

            return {
                "dex": dex,
                "timeframe_hours": hours_back,
                "timestamp": datetime.now().isoformat(),
                "total_trades": len(trade_sizes),
                "mean": statistics.mean(trade_sizes),
                "median": statistics.median(trade_sizes),
                "std_dev": statistics.stdev(trade_sizes) if len(trade_sizes) > 1 else 0,
                "min": min(trade_sizes),
                "max": max(trade_sizes),
                "percentiles": percentiles,
                "histogram": {
                    "labels": bin_labels,
                    "counts": histogram
                }
            }

        except Exception as e:
            print(f"Error analyzing trade size distribution: {e}")
            return {"error": str(e)}

    # Helper methods
    def _get_dex_trades(self, dex_name: str, hours_back: float) -> List[Dict]:
        """Get trades for a specific dex from database"""
        if not self.trade_db:
            return []

        seconds_back = int(hours_back * 3600)
        all_trades = self.trade_db.get_trades_since(seconds_back)
        return [t for t in all_trades if t.get("coin", "").startswith(f"{dex_name}:")]

    def _get_asset_trades(self, asset_name: str, hours_back: float) -> List[Dict]:
        """Get trades for a specific asset from database"""
        if not self.trade_db:
            return []

        return self.trade_db.get_trades_by_coin(asset_name, hours_back)

    def _extract_unique_wallets(self, trades: List[Dict]) -> set:
        """Extract unique wallet addresses from trades"""
        wallets = set()
        for trade in trades:
            users = trade.get("users", [])
            for user in users:
                if user and user != "0x0000000000000000000000000000000000000000":
                    wallets.add(user.lower())
        return wallets
