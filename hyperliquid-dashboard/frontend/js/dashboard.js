/**
 * Hyperliquid Analytics Dashboard
 * Real-time data integration with granular timeframes and user analytics
 */

// API Configuration
const API_BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
    ? 'http://localhost:5000'
    : '';

const REFRESH_INTERVAL = 10000; // 10 seconds

// State
let currentAsset = 'BTC';
let currentInterval = '15m';
let currentUserAddress = null;

// Chart instances
let priceChart = null;
let volumeChart = null;
let portfolioChart = null;
let pnlChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Hyperliquid Analytics Dashboard Loading...');
    initializeCharts();
    loadPlatformData();
    setupEventListeners();

    // Auto-refresh platform data
    setInterval(loadPlatformData, REFRESH_INTERVAL);

    // Load leaderboard data after a short delay
    setTimeout(() => {
        loadLeaderboardData();
    }, 2000);
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Timeframe buttons
    document.querySelectorAll('.timeframe-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentInterval = e.target.dataset.interval;
            loadGranularData();
        });
    });

    // Asset selector
    document.getElementById('assetSelect').addEventListener('change', (e) => {
        currentAsset = e.target.value;
        loadGranularData();
    });

    // Load user data button
    document.getElementById('loadUserData').addEventListener('click', loadUserAnalytics);

    // Enter key in wallet address input
    document.getElementById('walletAddress').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadUserAnalytics();
        }
    });

    // Load leaderboard data button
    document.getElementById('loadLeaderboardData').addEventListener('click', loadLeaderboardData);
}

/**
 * Initialize all charts
 */
function initializeCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: {
                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                ticks: { color: '#a0aec0' }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#a0aec0' }
            }
        }
    };

    // Price Chart (Candlestick line chart)
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Price',
                data: [],
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: chartOptions
    });

    // Volume Chart
    const volumeCtx = document.getElementById('volumeChart').getContext('2d');
    volumeChart = new Chart(volumeCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Volume',
                data: [],
                backgroundColor: 'rgba(139, 92, 246, 0.6)',
                borderWidth: 0
            }]
        },
        options: chartOptions
    });

    // Portfolio Chart
    const portfolioCtx = document.getElementById('portfolioChart').getContext('2d');
    portfolioChart = new Chart(portfolioCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Portfolio Value',
                data: [],
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                borderColor: 'rgba(16, 185, 129, 1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: chartOptions
    });

    // PnL Chart
    const pnlCtx = document.getElementById('pnlChart').getContext('2d');
    pnlChart = new Chart(pnlCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'PnL',
                data: [],
                backgroundColor: [],
                borderWidth: 0
            }]
        },
        options: chartOptions
    });
}

/**
 * Load platform-wide data
 */
async function loadPlatformData() {
    try {
        updateStatus('Loading...', false);

        // Fetch platform metrics and market stats in parallel
        const [platformMetrics, marketStats] = await Promise.all([
            fetchPlatformMetrics(),
            fetchMarketStats()
        ]);

        if (platformMetrics) {
            updatePlatformMetrics(platformMetrics);
        }

        if (marketStats) {
            updateMarketStats(marketStats);
        }

        updateLastUpdateTime();
        updateStatus('Live', true);
    } catch (error) {
        console.error('Error loading platform data:', error);
        updateStatus('Error', false);
    }
}

/**
 * Fetch platform metrics with real fee calculations
 */
async function fetchPlatformMetrics() {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/platform-metrics`);
        return response.data;
    } catch (error) {
        console.error('Platform Metrics API Error:', error);
        return null;
    }
}

/**
 * Fetch market statistics
 */
async function fetchMarketStats() {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/stats`);
        return response.data;
    } catch (error) {
        console.error('Market Stats API Error:', error);
        return null;
    }
}

/**
 * Update platform metrics display
 */
function updatePlatformMetrics(data) {
    // Platform Overview
    document.getElementById('totalVolume').textContent = formatCurrency(data.total_volume_24h || 0);
    document.getElementById('totalOI').textContent = formatCurrency(data.total_open_interest || 0);
    document.getElementById('platformRevenue').textContent = formatCurrency(data.platform_revenue_24h || 0);

    // Asset Categories - Crypto Perps
    const cryptoPerps = data.crypto_perps || {};
    document.getElementById('cryptoPerpsCount').textContent = cryptoPerps.count || 0;
    document.getElementById('cryptoPerpsVolume').textContent = formatCurrency(cryptoPerps.total_volume || 0);
    document.getElementById('cryptoPerpsOI').textContent = formatCurrency(cryptoPerps.total_oi || 0);

    // Asset Categories - TradFi Perps
    const tradfiPerps = data.tradfi_perps || {};
    document.getElementById('tradfiPerpsCount').textContent = tradfiPerps.count || 0;
    document.getElementById('tradfiPerpsVolume').textContent = formatCurrency(tradfiPerps.total_volume || 0);
    document.getElementById('tradfiPerpsOI').textContent = formatCurrency(tradfiPerps.total_oi || 0);

    // Load detailed TradFi analytics
    loadTradFiDetailedAnalytics();
}

/**
 * Update market statistics
 */
function updateMarketStats(data) {
    document.getElementById('activeMarkets').textContent = data.total_assets || 0;

    // Update top markets table
    updateTopMarketsTable(data.top_by_volume || []);

    // Populate asset selector with top assets
    populateAssetSelector(data.top_by_volume || []);
}

/**
 * Populate asset selector with top trading assets
 */
function populateAssetSelector(markets) {
    const select = document.getElementById('assetSelect');
    const currentValue = select.value;

    // Clear existing options
    select.innerHTML = '';

    // Add top 20 markets by volume
    markets.slice(0, 20).forEach(market => {
        const option = document.createElement('option');
        option.value = market.name;
        option.textContent = market.name;
        select.appendChild(option);
    });

    // Restore previous selection if it still exists
    if (currentValue && Array.from(select.options).some(opt => opt.value === currentValue)) {
        select.value = currentValue;
    } else if (select.options.length > 0) {
        // Otherwise select first option and update currentAsset
        currentAsset = select.options[0].value;
        select.value = currentAsset;
    }
}

/**
 * Update top markets table
 */
function updateTopMarketsTable(markets) {
    const tbody = document.getElementById('topMarketsTable');
    tbody.innerHTML = '';

    markets.slice(0, 10).forEach((market, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>#${index + 1}</strong></td>
            <td class="asset-name">${market.name}</td>
            <td class="price">${formatCurrency(market.mark_price)}</td>
            <td class="${market.change_24h >= 0 ? 'change-positive' : 'change-negative'}">
                ${market.change_24h >= 0 ? '+' : ''}${formatPercent(market.change_24h)}
            </td>
            <td class="volume">${formatCurrency(market.day_ntl_vlm)}</td>
            <td class="volume">${formatCurrency(market.open_interest)}</td>
            <td class="${market.funding_rate >= 0 ? 'change-positive' : 'change-negative'}">
                ${formatPercent(market.funding_rate * 100)}
            </td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Load granular market data for selected asset and timeframe
 */
async function loadGranularData() {
    try {
        const hoursMap = {
            '15m': 24,
            '1h': 48,
            '4h': 168,
            '1d': 720
        };
        const hoursBack = hoursMap[currentInterval] || 24;

        const response = await axios.get(
            `${API_BASE_URL}/api/granular/candles/${currentAsset}/${currentInterval}?hours_back=${hoursBack}`
        );

        const candles = response.data;

        if (!candles || candles.length === 0) {
            console.warn('No candle data received');
            return;
        }

        // Update price chart
        priceChart.data.labels = candles.map(c => formatTimestamp(c.t));
        priceChart.data.datasets[0].data = candles.map(c => parseFloat(c.c)); // Close prices
        priceChart.update();

        // Update volume chart
        volumeChart.data.labels = candles.map(c => formatTimestamp(c.t));
        volumeChart.data.datasets[0].data = candles.map(c => parseFloat(c.v || 0)); // Volume
        volumeChart.update();

    } catch (error) {
        console.error('Error loading granular data:', error);
    }
}

/**
 * Load user analytics data
 */
async function loadUserAnalytics() {
    const address = document.getElementById('walletAddress').value.trim();

    if (!address) {
        alert('Please enter a wallet address');
        return;
    }

    currentUserAddress = address;
    const window = document.getElementById('windowSelect').value;

    try {
        // Fetch user data in parallel
        const [pnlData, portfolioData, volumeData, fillsData] = await Promise.all([
            fetchUserPnL(address, window),
            fetchPortfolioValue(address, window),
            fetchUserVolume(address, 24),
            fetchUserFills(address)
        ]);

        // Show user sections
        document.getElementById('userMetricsSection').style.display = 'grid';
        document.getElementById('userChartsSection').style.display = 'grid';
        document.getElementById('userFillsSection').style.display = 'block';

        // Update metrics
        if (pnlData) {
            updateUserMetrics(pnlData, volumeData);
        }

        // Update charts
        if (portfolioData) {
            updatePortfolioChart(portfolioData);
            updatePnLChart(portfolioData);
        }

        // Update fills table
        if (fillsData) {
            updateUserFillsTable(fillsData);
        }

    } catch (error) {
        console.error('Error loading user analytics:', error);
        alert('Failed to load user data. Please check the wallet address.');
    }
}

/**
 * Fetch user PnL data
 */
async function fetchUserPnL(address, window) {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/user/pnl/${address}?window=${window}`);
        return response.data;
    } catch (error) {
        console.error('User PnL API Error:', error);
        return null;
    }
}

/**
 * Fetch portfolio value history
 */
async function fetchPortfolioValue(address, window) {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/portfolio/${address}?window=${window}`);
        return response.data;
    } catch (error) {
        console.error('Portfolio API Error:', error);
        return null;
    }
}

/**
 * Fetch user volume breakdown
 */
async function fetchUserVolume(address, hoursBack) {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/user/volume/${address}?hours_back=${hoursBack}`);
        return response.data;
    } catch (error) {
        console.error('User Volume API Error:', error);
        return null;
    }
}

/**
 * Fetch user fills
 */
async function fetchUserFills(address) {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/user/fills/${address}`);
        return response.data;
    } catch (error) {
        console.error('User Fills API Error:', error);
        return null;
    }
}

/**
 * Update user metrics display
 */
function updateUserMetrics(pnlData, volumeData) {
    document.getElementById('userAccountValue').textContent = formatCurrency(pnlData.account_value || 0);

    const cumulativePnL = pnlData.cumulative_pnl || 0;
    const pnlElement = document.getElementById('userCumulativePnL');
    pnlElement.textContent = formatCurrency(cumulativePnL);
    pnlElement.className = 'metric-value';
    if (cumulativePnL > 0) {
        pnlElement.style.color = 'var(--success)';
    } else if (cumulativePnL < 0) {
        pnlElement.style.color = 'var(--danger)';
    }

    if (volumeData) {
        document.getElementById('userTotalVolume').textContent = formatCurrency(volumeData.total_volume || 0);
        document.getElementById('userFeesPaid').textContent = formatCurrency(volumeData.total_fees_paid || 0);
    }
}

/**
 * Update portfolio value chart
 */
function updatePortfolioChart(data) {
    if (!Array.isArray(data) || data.length === 0) {
        console.warn('No portfolio data to display');
        return;
    }

    portfolioChart.data.labels = data.map(d => formatTimestamp(d[0]));
    portfolioChart.data.datasets[0].data = data.map(d => parseFloat(d[1]));
    portfolioChart.update();
}

/**
 * Update PnL chart (bar chart with positive/negative colors)
 */
function updatePnLChart(data) {
    if (!Array.isArray(data) || data.length === 0) {
        console.warn('No PnL data to display');
        return;
    }

    // Calculate PnL changes between consecutive points
    const pnlChanges = [];
    const labels = [];

    for (let i = 1; i < data.length; i++) {
        const change = parseFloat(data[i][1]) - parseFloat(data[i-1][1]);
        pnlChanges.push(change);
        labels.push(formatTimestamp(data[i][0]));
    }

    pnlChart.data.labels = labels;
    pnlChart.data.datasets[0].data = pnlChanges;
    pnlChart.data.datasets[0].backgroundColor = pnlChanges.map(val =>
        val >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'
    );
    pnlChart.update();
}

/**
 * Update user fills table
 */
function updateUserFillsTable(fills) {
    const tbody = document.getElementById('userFillsTable');
    tbody.innerHTML = '';

    if (!fills || fills.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No fills found</td></tr>';
        return;
    }

    // Show recent 50 fills
    fills.slice(0, 50).forEach(fill => {
        const price = parseFloat(fill.px || 0);
        const size = Math.abs(parseFloat(fill.sz || 0));
        const value = price * size;
        const fee = parseFloat(fill.fee || 0);
        const closedPnl = parseFloat(fill.closedPnl || 0);

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatTimestamp(fill.time)}</td>
            <td class="asset-name">${fill.coin || '-'}</td>
            <td class="${fill.side === 'B' ? 'change-positive' : 'change-negative'}">
                ${fill.side === 'B' ? 'BUY' : 'SELL'}
            </td>
            <td class="price">${formatCurrency(price)}</td>
            <td>${size.toFixed(4)}</td>
            <td class="volume">${formatCurrency(value)}</td>
            <td class="${fee < 0 ? 'change-positive' : 'change-negative'}">
                ${formatCurrency(Math.abs(fee))}
            </td>
            <td class="${closedPnl >= 0 ? 'change-positive' : 'change-negative'}">
                ${closedPnl !== 0 ? formatCurrency(closedPnl) : '-'}
            </td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Load all leaderboard and advanced analytics data
 */
async function loadLeaderboardData() {
    console.log('Loading leaderboard and analytics data...');
    const hoursBack = parseInt(document.getElementById('leaderboardWindow').value);

    try {
        await Promise.all([
            loadTopTraders(hoursBack),
            loadLargeTradesAnalytics(),
            loadTradeSizeAnalytics()
        ]);
        console.log('Leaderboard data loaded successfully');
    } catch (error) {
        console.error('Error loading leaderboard data:', error);
    }
}

/**
 * Load top traders leaderboard
 */
async function loadTopTraders(hoursBack = 24) {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/leaderboard/top-traders?hours_back=${hoursBack}&limit=50`);
        const traders = response.data;

        const tableBody = document.getElementById('topTradersTable');
        if (!traders || traders.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="loading">No leaderboard data available</td></tr>';
            return;
        }

        tableBody.innerHTML = traders.map(trader => {
            const shortAddress = trader.user.length > 10
                ? `${trader.user.slice(0, 6)}...${trader.user.slice(-4)}`
                : trader.user;

            const pnlClass = trader.pnl >= 0 ? 'positive' : 'negative';
            const pnlSign = trader.pnl >= 0 ? '+' : '';

            return `
                <tr>
                    <td><strong>${trader.rank}</strong></td>
                    <td><code>${shortAddress}</code></td>
                    <td>${formatCurrency(trader.account_value)}</td>
                    <td class="${pnlClass}">${pnlSign}${formatCurrency(trader.pnl)}</td>
                    <td class="${pnlClass}">${pnlSign}${trader.pnl_pct.toFixed(2)}%</td>
                    <td>${formatCurrency(trader.vlm)}</td>
                    <td>${trader.n_trades.toLocaleString()}</td>
                </tr>
            `;
        }).join('');

        console.log(`Loaded ${traders.length} top traders`);
    } catch (error) {
        console.error('Error loading top traders:', error);
        document.getElementById('topTradersTable').innerHTML =
            '<tr><td colspan="7" class="error">Error loading leaderboard data</td></tr>';
    }
}

/**
 * Load large and interesting trades across markets
 */
async function loadLargeTradesAnalytics() {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/leaderboard/platform-analytics`);
        const data = response.data;

        const largeTradesTable = document.getElementById('largeTradesTable');
        if (!data || !data.largest_trades || data.largest_trades.length === 0) {
            largeTradesTable.innerHTML = '<tr><td colspan="6" class="loading">No large trades found</td></tr>';
            return;
        }

        const trades = data.largest_trades.slice(0, 20); // Top 20 largest
        largeTradesTable.innerHTML = trades.map(trade => {
            const sideClass = trade.side === 'BUY' ? 'positive' : 'negative';
            const timeAgo = formatTimestamp(new Date(trade.time).getTime());

            return `
                <tr>
                    <td>${timeAgo}</td>
                    <td><strong>${trade.coin}</strong></td>
                    <td class="${sideClass}">${trade.side}</td>
                    <td>$${trade.price.toLocaleString()}</td>
                    <td>${trade.size.toFixed(4)}</td>
                    <td><strong>${formatCurrency(trade.value_usd)}</strong></td>
                </tr>
            `;
        }).join('');

        console.log(`Loaded ${trades.length} large trades`);
    } catch (error) {
        console.error('Error loading large trades:', error);
        document.getElementById('largeTradesTable').innerHTML =
            '<tr><td colspan="6" class="error">Error loading large trades</td></tr>';
    }
}

/**
 * Load trade size analytics across top markets
 */
async function loadTradeSizeAnalytics() {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/leaderboard/trade-sizes`);
        const data = response.data;

        const tradeSizeTable = document.getElementById('tradeSizeTable');
        if (!data || data.length === 0) {
            tradeSizeTable.innerHTML = '<tr><td colspan="7" class="loading">No trade size data available</td></tr>';
            return;
        }

        tradeSizeTable.innerHTML = data.map(stats => {
            return `
                <tr>
                    <td><strong>${stats.coin}</strong></td>
                    <td>${stats.total_trades.toLocaleString()}</td>
                    <td>${formatCurrency(stats.avg_trade_size_usd)}</td>
                    <td>${formatCurrency(stats.median_trade_size_usd)}</td>
                    <td>${stats.small_trades_pct.toFixed(1)}%</td>
                    <td>${stats.medium_trades_pct.toFixed(1)}%</td>
                    <td>${stats.large_trades_pct.toFixed(1)}%</td>
                </tr>
            `;
        }).join('');

        console.log(`Loaded trade size analytics for ${data.length} assets`);
    } catch (error) {
        console.error('Error loading trade size analytics:', error);
        document.getElementById('tradeSizeTable').innerHTML =
            '<tr><td colspan="7" class="error">Error loading trade size data</td></tr>';
    }
}

/**
 * Load detailed TradFi/Equity perpetuals analytics
 */
async function loadTradFiDetailedAnalytics() {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/tradfi/detailed-analytics`);
        const data = response.data;

        // Update overview cards
        document.getElementById('tradfiAssetsCount').textContent = data.total_count || 0;
        document.getElementById('tradfiTotalVolume').textContent = formatCurrency(data.total_volume_24h || 0);
        document.getElementById('tradfiTotalOI').textContent = formatCurrency(data.total_open_interest || 0);

        // Update percentages
        const comparison = data.crypto_comparison || {};
        document.getElementById('tradfiVolumePct').textContent = `${(comparison.tradfi_volume_pct || 0).toFixed(2)}%`;
        document.getElementById('tradfiOIPct').textContent = `${(comparison.tradfi_oi_pct || 0).toFixed(2)}%`;

        // Update assets table
        const tradfiAssetsTable = document.getElementById('tradfiAssetsTable');
        const assets = data.assets || [];

        if (assets.length === 0) {
            tradfiAssetsTable.innerHTML = '<tr><td colspan="8" class="loading">No TradFi assets found</td></tr>';
            return;
        }

        tradfiAssetsTable.innerHTML = assets.map(asset => {
            const changeClass = asset.change_24h >= 0 ? 'positive' : 'negative';
            const changeSign = asset.change_24h >= 0 ? '+' : '';
            const fundingClass = asset.funding_rate >= 0 ? 'positive' : 'negative';

            return `
                <tr>
                    <td><strong>${asset.name}</strong></td>
                    <td>$${asset.mark_price.toLocaleString()}</td>
                    <td class="${changeClass}">${changeSign}${asset.change_24h.toFixed(2)}%</td>
                    <td>${formatCurrency(asset.day_ntl_vlm)}</td>
                    <td>${asset.volume_pct.toFixed(1)}%</td>
                    <td>${formatCurrency(asset.open_interest)}</td>
                    <td>${asset.oi_pct.toFixed(1)}%</td>
                    <td class="${fundingClass}">${(asset.funding_rate * 100).toFixed(4)}%</td>
                </tr>
            `;
        }).join('');

        console.log(`Loaded ${assets.length} TradFi assets with detailed analytics`);
    } catch (error) {
        console.error('Error loading TradFi analytics:', error);
        document.getElementById('tradfiAssetsTable').innerHTML =
            '<tr><td colspan="8" class="error">Error loading TradFi data</td></tr>';
    }
}

/**
 * Update status indicator
 */
function updateStatus(text, isLive) {
    const statusEl = document.getElementById('status');
    statusEl.innerHTML = `<span class="pulse"></span> ${text}`;

    if (isLive) {
        statusEl.style.color = 'var(--success)';
        statusEl.querySelector('.pulse').style.background = 'var(--success)';
    } else {
        statusEl.style.color = 'var(--text-secondary)';
        if (statusEl.querySelector('.pulse')) {
            statusEl.querySelector('.pulse').style.background = 'var(--text-secondary)';
        }
    }
}

/**
 * Update last update timestamp
 */
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('lastUpdate').textContent = timeString;
}

/**
 * Format timestamp to readable string
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays < 1) {
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays < 7) {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
}

/**
 * Format number as currency
 */
function formatCurrency(value) {
    if (value === undefined || value === null) return '$0';

    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : '';

    if (absValue >= 1e9) {
        return `${sign}$${(absValue / 1e9).toFixed(2)}B`;
    } else if (absValue >= 1e6) {
        return `${sign}$${(absValue / 1e6).toFixed(2)}M`;
    } else if (absValue >= 1e3) {
        return `${sign}$${(absValue / 1e3).toFixed(2)}K`;
    } else {
        return `${sign}$${absValue.toFixed(2)}`;
    }
}

/**
 * Format number as percentage
 */
function formatPercent(value) {
    if (value === undefined || value === null) return '0%';
    return `${value.toFixed(2)}%`;
}

// Initialize granular data on load
setTimeout(() => {
    loadGranularData();
}, 1000);
