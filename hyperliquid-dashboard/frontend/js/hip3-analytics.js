/**
 * HIP-3 Advanced Analytics Dashboard
 * Powers all visualizations and data for the comprehensive HIP-3 analytics page
 */

const API_BASE = 'http://localhost:5000/api';
let charts = {}; // Store all chart instances

// ============================================================================
// TAB SWITCHING
// ============================================================================

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Load tab-specific data
    switch(tabName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'leaderboard':
            loadLeaderboardData();
            break;
        case 'markets':
            loadMarketsData();
            break;
        case 'analytics':
            loadAnalyticsData();
            break;
        case 'deployers':
            loadDeployersData();
            break;
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatNumber(num) {
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toFixed(2);
}

function formatCurrency(num) {
    return '$' + formatNumber(num);
}

function formatPercent(num) {
    return num.toFixed(2) + '%';
}

function formatAddress(address) {
    if (!address) return '';
    return address.substring(0, 6) + '...' + address.substring(address.length - 4);
}

function getChangeClass(value) {
    return value >= 0 ? 'positive' : 'negative';
}

function getRankBadgeClass(rank) {
    if (rank === 1) return 'rank-1';
    if (rank === 2) return 'rank-2';
    if (rank === 3) return 'rank-3';
    return 'rank-other';
}

// ============================================================================
// OVERVIEW TAB
// ============================================================================

async function loadOverviewData() {
    try {
        // Fetch all HIP-3 markets
        const response = await axios.get(`${API_BASE}/hip3/all-markets`);
        const data = response.data;

        // Update top metrics
        document.getElementById('totalHip3Volume').textContent = formatCurrency(data.total_volume_24h);
        document.getElementById('totalHip3OI').textContent = formatCurrency(data.total_open_interest_usd);
        document.getElementById('totalHip3Markets').textContent = data.total_markets;

        // Get deployer economics for revenue
        const economicsResponse = await axios.get(`${API_BASE}/hip3/deployer-economics`);
        const economics = economicsResponse.data;
        document.getElementById('totalHip3Revenue').textContent = formatCurrency(economics.total_hip3_revenue);

        // Populate markets table
        populateAllMarketsTable(data.markets);

        // Create deployer charts
        createVolumeByDeployerChart(data.summary_by_dex);
        createMarketsByDeployerChart(data.summary_by_dex);

    } catch (error) {
        console.error('Error loading overview data:', error);
    }
}

function populateAllMarketsTable(markets) {
    const tbody = document.getElementById('allMarketsTable');

    if (!markets || markets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No active markets found</td></tr>';
        return;
    }

    tbody.innerHTML = markets.map(market => {
        const changeClass = market.price_change_24h_pct >= 0 ? 'positive' : 'negative';
        const changeIcon = market.price_change_24h_pct >= 0 ? '▲' : '▼';

        return `
            <tr>
                <td><span class="badge badge-primary">${market.dex.toUpperCase()}</span></td>
                <td><strong>${market.market}</strong></td>
                <td>${formatCurrency(market.mark_price)}</td>
                <td class="metric-change ${changeClass}">
                    ${changeIcon} ${formatPercent(Math.abs(market.price_change_24h_pct))}
                </td>
                <td>${formatCurrency(market.volume_24h)}</td>
                <td>${formatCurrency(market.open_interest_usd)}</td>
                <td>${(market.funding_rate * 100).toFixed(4)}%</td>
                <td>${market.max_leverage}x</td>
            </tr>
        `;
    }).join('');
}

function createVolumeByDeployerChart(summary) {
    const ctx = document.getElementById('volumeByDeployerChart');

    if (charts.volumeByDeployer) {
        charts.volumeByDeployer.destroy();
    }

    const labels = [];
    const data = [];
    const colors = ['#667eea', '#764ba2', '#f093fb'];

    Object.keys(summary).forEach((dex, index) => {
        labels.push(dex.toUpperCase());
        data.push(summary[dex].total_volume_24h);
    });

    charts.volumeByDeployer = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#a8b2d1',
                        padding: 20,
                        font: {
                            size: 13,
                            weight: 'bold'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + formatCurrency(context.parsed);
                        }
                    }
                }
            }
        }
    });
}

function createMarketsByDeployerChart(summary) {
    const ctx = document.getElementById('marketsByDeployerChart');

    if (charts.marketsByDeployer) {
        charts.marketsByDeployer.destroy();
    }

    const labels = [];
    const data = [];

    Object.keys(summary).forEach(dex => {
        labels.push(dex.toUpperCase());
        data.push(summary[dex].total_markets);
    });

    charts.marketsByDeployer = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Active Markets',
                data: data,
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: '#667eea',
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#a8b2d1',
                        stepSize: 1
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        color: '#a8b2d1'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ============================================================================
// LEADERBOARD TAB
// ============================================================================

async function loadLeaderboardData() {
    try {
        // Fetch leaderboard
        const response = await axios.get(`${API_BASE}/hip3/leaderboard?limit=50`);
        const data = response.data;

        // Update metrics
        document.getElementById('totalTraders').textContent = data.total_traders;

        if (data.leaderboard && data.leaderboard.length > 0) {
            const avgSize = data.total_volume / data.leaderboard.reduce((sum, t) => sum + t.trade_count, 0);
            document.getElementById('avgTradeSize').textContent = formatCurrency(avgSize);
            document.getElementById('topTraderShare').textContent = formatPercent(data.leaderboard[0].market_share_pct);
        }

        // Populate leaderboard table
        populateLeaderboardTable(data.leaderboard);

        // Fetch and display trade size distribution
        const distResponse = await axios.get(`${API_BASE}/hip3/trade-size-distribution`);
        createTradeSizeDistributionChart(distResponse.data);

    } catch (error) {
        console.error('Error loading leaderboard data:', error);
    }
}

function populateLeaderboardTable(leaderboard) {
    const tbody = document.getElementById('leaderboardTable');

    if (!leaderboard || leaderboard.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No trader data available</td></tr>';
        return;
    }

    tbody.innerHTML = leaderboard.map((trader, index) => {
        const rank = index + 1;
        const rankBadgeClass = getRankBadgeClass(rank);

        return `
            <tr>
                <td><span class="rank-badge ${rankBadgeClass}">${rank}</span></td>
                <td><span class="wallet-address">${formatAddress(trader.wallet)}</span></td>
                <td><strong>${formatCurrency(trader.total_volume)}</strong></td>
                <td>${trader.trade_count.toLocaleString()}</td>
                <td>${trader.assets_traded_count}</td>
                <td>${formatCurrency(trader.avg_trade_size)}</td>
                <td>${trader.buy_sell_ratio.toFixed(2)}x</td>
                <td>${formatCurrency(trader.fees_paid)}</td>
                <td>
                    <div>${formatPercent(trader.market_share_pct)}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${trader.market_share_pct}%"></div>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function createTradeSizeDistributionChart(data) {
    const ctx = document.getElementById('tradeSizeDistChart');

    if (charts.tradeSizeDist) {
        charts.tradeSizeDist.destroy();
    }

    if (!data.histogram) {
        return;
    }

    charts.tradeSizeDist = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.histogram.labels,
            datasets: [{
                label: 'Number of Trades',
                data: data.histogram.counts,
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: '#667eea',
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#a8b2d1'
                    }
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Trade Size: ' + context[0].label;
                        },
                        label: function(context) {
                            return 'Trades: ' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#a8b2d1'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    title: {
                        display: true,
                        text: 'Number of Trades',
                        color: '#a8b2d1'
                    }
                },
                x: {
                    ticks: {
                        color: '#a8b2d1'
                    },
                    grid: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Trade Size Range',
                        color: '#a8b2d1'
                    }
                }
            }
        }
    });
}

// ============================================================================
// MARKETS TAB
// ============================================================================

async function loadMarketsData() {
    try {
        // Load market maturity
        const maturityResponse = await axios.get(`${API_BASE}/hip3/market-maturity`);
        populateMaturityTable(maturityResponse.data);

        // Load oracle performance
        const oracleResponse = await axios.get(`${API_BASE}/hip3/oracle-performance`);
        displayOraclePerformance(oracleResponse.data);

        // Load correlations
        const corrResponse = await axios.get(`${API_BASE}/hip3/correlations`);
        displayCorrelationHeatmap(corrResponse.data);

    } catch (error) {
        console.error('Error loading markets data:', error);
    }
}

function populateMaturityTable(data) {
    const tbody = document.getElementById('maturityTableBody');

    if (!data.active_markets || data.active_markets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No market data available</td></tr>';
        return;
    }

    tbody.innerHTML = data.active_markets.map(market => {
        const growthRate = market.volume_growth_rate || 0;
        const growthClass = getChangeClass(growthRate);
        const statusBadge = market.day_volume > 1000000 ? 'badge-success' :
                           market.day_volume > 100000 ? 'badge-warning' : 'badge-danger';

        return `
            <tr>
                <td><strong>${market.asset}</strong></td>
                <td>${formatCurrency(market.volume_24h || market.day_volume)}</td>
                <td>${formatCurrency(market.volume_7d || 0)}</td>
                <td class="metric-change ${growthClass}">
                    ${growthRate >= 0 ? '▲' : '▼'} ${formatPercent(Math.abs(growthRate))}
                </td>
                <td>${formatCurrency(market.open_interest || 0)}</td>
                <td>${(market.trades_24h || 0).toLocaleString()}</td>
                <td>${market.max_leverage}x</td>
                <td><span class="badge ${statusBadge}">Active</span></td>
            </tr>
        `;
    }).join('');
}

function displayOraclePerformance(data) {
    const container = document.getElementById('oracleMetrics');

    if (!data.assets || data.assets.length === 0) {
        container.innerHTML = '<div class="loading">No oracle data available</div>';
        return;
    }

    const avgDev = data.avg_deviation_pct || 0;
    const avgDevClass = avgDev < 0.1 ? 'badge-success' : avgDev < 0.5 ? 'badge-warning' : 'badge-danger';

    let html = `
        <div class="grid grid-3" style="margin-bottom: 24px;">
            <div class="stat-row">
                <span class="label">Oracle Updater:</span>
                <span class="value wallet-address">${formatAddress(data.oracle_updater)}</span>
            </div>
            <div class="stat-row">
                <span class="label">Average Deviation:</span>
                <span class="value"><span class="badge ${avgDevClass}">${avgDev.toFixed(4)}%</span></span>
            </div>
            <div class="stat-row">
                <span class="label">Average Premium:</span>
                <span class="value">${(data.avg_premium || 0).toFixed(6)}</span>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Asset</th>
                    <th>Oracle Price</th>
                    <th>Mark Price</th>
                    <th>Mid Price</th>
                    <th>Oracle→Mark Dev</th>
                    <th>Premium</th>
                    <th>Funding Rate</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.assets.forEach(asset => {
        const devClass = Math.abs(asset.oracle_to_mark_deviation_pct) < 0.1 ? 'metric-change positive' :
                        Math.abs(asset.oracle_to_mark_deviation_pct) < 0.5 ? 'metric-change' : 'metric-change negative';

        html += `
            <tr>
                <td><strong>${asset.asset}</strong></td>
                <td>${formatCurrency(asset.oracle_price)}</td>
                <td>${formatCurrency(asset.mark_price)}</td>
                <td>${formatCurrency(asset.mid_price)}</td>
                <td class="${devClass}">${asset.oracle_to_mark_deviation_pct.toFixed(4)}%</td>
                <td>${asset.premium.toFixed(6)}</td>
                <td>${(asset.funding_rate * 100).toFixed(4)}%</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

function displayCorrelationHeatmap(data) {
    const container = document.getElementById('correlationHeatmap');

    if (!data.correlation_matrix || data.correlation_matrix.length === 0) {
        container.innerHTML = '<div class="loading">Not enough data for correlations</div>';
        return;
    }

    const assets = data.assets;
    const matrix = data.correlation_matrix;

    let html = '<div class="heatmap-grid" style="grid-template-columns: repeat(' + assets.length + ', 1fr);">';

    matrix.forEach((row, i) => {
        row.forEach((value, j) => {
            const intensity = Math.abs(value);
            const isPositive = value >= 0;
            const color = isPositive
                ? `rgba(74, 222, 128, ${intensity})`
                : `rgba(248, 113, 113, ${intensity})`;

            const tooltip = `${assets[i]} vs ${assets[j]}: ${value.toFixed(3)}`;

            html += `
                <div class="heatmap-cell" style="background: ${color};" title="${tooltip}">
                    ${value.toFixed(2)}
                </div>
            `;
        });
    });

    html += '</div>';
    html += '<div style="margin-top: 20px; display: flex; justify-content: center; gap: 30px;">';
    html += '<div style="display: flex; align-items: center; gap: 10px;"><div style="width: 30px; height: 30px; background: rgba(74, 222, 128, 0.8); border-radius: 4px;"></div><span style="color: #a8b2d1;">Positive Correlation</span></div>';
    html += '<div style="display: flex; align-items: center; gap: 10px;"><div style="width: 30px; height: 30px; background: rgba(248, 113, 113, 0.8); border-radius: 4px;"></div><span style="color: #a8b2d1;">Negative Correlation</span></div>';
    html += '</div>';

    container.innerHTML = html;
}

// ============================================================================
// ANALYTICS TAB
// ============================================================================

async function loadAnalyticsData() {
    try {
        const response = await axios.get(`${API_BASE}/hip3/growth-metrics`);
        const data = response.data;

        // Display growth metrics for each time period
        displayGrowthMetrics('growth1h', data.last_hour);
        displayGrowthMetrics('growth24h', data.last_24h);
        displayGrowthMetrics('growth7d', data.last_7d);

        // Create growth trends chart
        createGrowthTrendsChart(data);

    } catch (error) {
        console.error('Error loading analytics data:', error);
    }
}

function displayGrowthMetrics(elementId, metrics) {
    const container = document.getElementById(elementId);

    if (!metrics) {
        container.innerHTML = '<div class="loading">No data</div>';
        return;
    }

    container.innerHTML = `
        <div class="stat-row">
            <span class="label">Trades:</span>
            <span class="value">${metrics.trades.toLocaleString()}</span>
        </div>
        <div class="stat-row">
            <span class="label">Volume:</span>
            <span class="value">${formatCurrency(metrics.volume)}</span>
        </div>
        <div class="stat-row">
            <span class="label">Unique Wallets:</span>
            <span class="value">${metrics.unique_wallets.toLocaleString()}</span>
        </div>
        <div class="stat-row">
            <span class="label">Avg Trade Size:</span>
            <span class="value">${formatCurrency(metrics.avg_trade_size)}</span>
        </div>
        ${metrics.new_wallets !== undefined ? `
        <div class="stat-row">
            <span class="label">New Wallets:</span>
            <span class="value">${metrics.new_wallets.toLocaleString()}</span>
        </div>
        ` : ''}
    `;
}

function createGrowthTrendsChart(data) {
    const ctx = document.getElementById('growthTrendsChart');

    if (charts.growthTrends) {
        charts.growthTrends.destroy();
    }

    const labels = ['Last Hour', 'Last 24h', 'Last 7d'];
    const volumes = [
        data.last_hour.volume,
        data.last_24h.volume,
        data.last_7d.volume
    ];
    const trades = [
        data.last_hour.trades,
        data.last_24h.trades,
        data.last_7d.trades
    ];

    charts.growthTrends = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Volume',
                    data: volumes,
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 2,
                    borderRadius: 8,
                    yAxisID: 'y'
                },
                {
                    label: 'Trades',
                    data: trades,
                    backgroundColor: 'rgba(118, 75, 162, 0.8)',
                    borderColor: '#764ba2',
                    borderWidth: 2,
                    borderRadius: 8,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#a8b2d1',
                        padding: 20,
                        font: {
                            size: 13,
                            weight: 'bold'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.dataset.label === 'Volume'
                                ? formatCurrency(context.parsed.y)
                                : context.parsed.y.toLocaleString();
                            return label + ': ' + value;
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: {
                        color: '#a8b2d1',
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    title: {
                        display: true,
                        text: 'Volume',
                        color: '#667eea'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    ticks: {
                        color: '#a8b2d1'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    title: {
                        display: true,
                        text: 'Trades',
                        color: '#764ba2'
                    }
                },
                x: {
                    ticks: {
                        color: '#a8b2d1'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ============================================================================
// DEPLOYERS TAB
// ============================================================================

async function loadDeployersData() {
    try {
        const response = await axios.get(`${API_BASE}/hip3/deployer-economics`);
        const data = response.data;

        // Display deployer cards
        displayDeployerCards(data.deployers);

        // Create revenue chart
        createRevenueByDeployerChart(data.deployers);

    } catch (error) {
        console.error('Error loading deployers data:', error);
    }
}

function displayDeployerCards(deployers) {
    const container = document.getElementById('deployerCards');

    if (!deployers || deployers.length === 0) {
        container.innerHTML = '<div class="loading">No deployer data available</div>';
        return;
    }

    container.innerHTML = deployers.map(deployer => `
        <div class="card deployer-card">
            <div class="card-header">
                <h3>${deployer.full_name} (${deployer.name.toUpperCase()})</h3>
            </div>
            <div class="stat-row">
                <span class="label">Total Markets:</span>
                <span class="value">${deployer.total_markets}</span>
            </div>
            <div class="stat-row">
                <span class="label">24h Volume:</span>
                <span class="value">${formatCurrency(deployer.total_volume)}</span>
            </div>
            <div class="stat-row">
                <span class="label">Total Trades:</span>
                <span class="value">${deployer.total_trades.toLocaleString()}</span>
            </div>
            <div class="stat-row">
                <span class="label">Taker Fees:</span>
                <span class="value">${formatCurrency(deployer.taker_fees)}</span>
            </div>
            <div class="stat-row">
                <span class="label">Maker Rebates:</span>
                <span class="value">${formatCurrency(deployer.maker_rebates)}</span>
            </div>
            <div class="stat-row">
                <span class="label">Platform Revenue:</span>
                <span class="value"><strong>${formatCurrency(deployer.platform_revenue)}</strong></span>
            </div>
            <div class="stat-row">
                <span class="label">Deployer Revenue:</span>
                <span class="value"><strong>${formatCurrency(deployer.deployer_revenue)}</strong></span>
            </div>
            <div class="stat-row">
                <span class="label">Fee Scale:</span>
                <span class="value">${deployer.deployer_fee_scale}x</span>
            </div>
            <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.1);">
                <div class="stat-row">
                    <span class="label">Deployer Address:</span>
                </div>
                <div class="wallet-address" style="font-size: 11px; word-break: break-all; margin-top: 4px;">
                    ${deployer.deployer_address}
                </div>
            </div>
        </div>
    `).join('');
}

function createRevenueByDeployerChart(deployers) {
    const ctx = document.getElementById('revenueByDeployerChart');

    if (charts.revenueByDeployer) {
        charts.revenueByDeployer.destroy();
    }

    const labels = deployers.map(d => d.name.toUpperCase());
    const data = deployers.map(d => d.platform_revenue);

    charts.revenueByDeployer = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#667eea', '#764ba2', '#f093fb'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#a8b2d1',
                        padding: 20,
                        font: {
                            size: 13,
                            weight: 'bold'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + formatCurrency(context.parsed);
                        }
                    }
                }
            }
        }
    });
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('HIP-3 Advanced Analytics Dashboard Initialized');

    // Load initial data for overview tab
    loadOverviewData();

    // Auto-refresh every 30 seconds
    setInterval(() => {
        const activeTab = document.querySelector('.tab.active');
        if (activeTab) {
            const tabText = activeTab.textContent.toLowerCase();
            if (tabText.includes('overview')) loadOverviewData();
            else if (tabText.includes('leaderboard')) loadLeaderboardData();
            else if (tabText.includes('markets')) loadMarketsData();
            else if (tabText.includes('analytics')) loadAnalyticsData();
            else if (tabText.includes('deployers')) loadDeployersData();
        }
    }, 30000);
});
