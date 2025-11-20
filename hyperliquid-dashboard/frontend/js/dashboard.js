/**
 * Hyperliquid Dashboard - Main JavaScript
 * Handles data fetching, UI updates, and chart rendering
 */

// API Configuration
const API_BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
    ? 'http://localhost:5000'
    : '';

const REFRESH_INTERVAL = 10000; // 10 seconds

// Chart instances
let volumeChart = null;
let performanceChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Hyperliquid Dashboard Loading...');
    initializeCharts();
    loadDashboardData();

    // Auto-refresh
    setInterval(loadDashboardData, REFRESH_INTERVAL);
});

/**
 * Initialize Chart.js charts
 */
function initializeCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: '#a0aec0'
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    color: '#a0aec0'
                }
            }
        }
    };

    // Volume Chart
    const volumeCtx = document.getElementById('volumeChart').getContext('2d');
    volumeChart = new Chart(volumeCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: '24h Volume',
                data: [],
                backgroundColor: 'rgba(59, 130, 246, 0.6)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1
            }]
        },
        options: chartOptions
    });

    // Performance Chart
    const performanceCtx = document.getElementById('performanceChart').getContext('2d');
    performanceChart = new Chart(performanceCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: '24h Change %',
                data: [],
                backgroundColor: [],
                borderWidth: 1
            }]
        },
        options: chartOptions
    });
}

/**
 * Main data loading function
 */
async function loadDashboardData() {
    try {
        updateStatus('Loading...', false);

        const stats = await fetchMarketStats();

        if (stats) {
            updateMetrics(stats);
            updateCharts(stats);
            updateTables(stats);
            updateLastUpdateTime();
            updateStatus('Live', true);
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        updateStatus('Error', false);
    }
}

/**
 * Fetch market statistics from API
 */
async function fetchMarketStats() {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/stats`);
        return response.data;
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

/**
 * Update metric cards
 */
function updateMetrics(stats) {
    document.getElementById('totalVolume').textContent = formatCurrency(stats.total_volume_24h);
    document.getElementById('totalOI').textContent = formatCurrency(stats.total_open_interest);
    document.getElementById('activeMarkets').textContent = stats.total_assets;

    // Calculate average funding rate
    const avgFunding = stats.top_by_volume.reduce((acc, asset) => acc + asset.funding_rate, 0) / stats.top_by_volume.length;
    document.getElementById('avgFunding').textContent = formatPercent(avgFunding * 100);
}

/**
 * Update charts with new data
 */
function updateCharts(stats) {
    // Update Volume Chart (Top 10)
    const topVolume = stats.top_by_volume;
    volumeChart.data.labels = topVolume.map(a => a.name);
    volumeChart.data.datasets[0].data = topVolume.map(a => a.day_ntl_vlm);
    volumeChart.update();

    // Update Performance Chart (Top 10 by absolute change)
    const topPerformers = [...stats.top_gainers, ...stats.top_losers]
        .sort((a, b) => Math.abs(b.change_24h) - Math.abs(a.change_24h))
        .slice(0, 10);

    performanceChart.data.labels = topPerformers.map(a => a.name);
    performanceChart.data.datasets[0].data = topPerformers.map(a => a.change_24h);
    performanceChart.data.datasets[0].backgroundColor = topPerformers.map(a =>
        a.change_24h >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'
    );
    performanceChart.update();
}

/**
 * Update market tables
 */
function updateTables(stats) {
    updateMarketTable('gainersTable', stats.top_gainers);
    updateMarketTable('losersTable', stats.top_losers);
    updateVolumeTable(stats.top_by_volume);
}

/**
 * Update a market table (gainers/losers)
 */
function updateMarketTable(tableId, data) {
    const tbody = document.getElementById(tableId);
    tbody.innerHTML = '';

    data.forEach(asset => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="asset-name">${asset.name}</td>
            <td class="price">${formatCurrency(asset.mark_price)}</td>
            <td class="${asset.change_24h >= 0 ? 'change-positive' : 'change-negative'}">
                ${asset.change_24h >= 0 ? '+' : ''}${formatPercent(asset.change_24h)}
            </td>
            <td class="volume">${formatCurrency(asset.day_ntl_vlm)}</td>
            <td class="${asset.funding_rate >= 0 ? 'change-positive' : 'change-negative'}">
                ${formatPercent(asset.funding_rate * 100)}
            </td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Update volume table with ranking
 */
function updateVolumeTable(data) {
    const tbody = document.getElementById('volumeTable');
    tbody.innerHTML = '';

    data.forEach((asset, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>#${index + 1}</strong></td>
            <td class="asset-name">${asset.name}</td>
            <td class="price">${formatCurrency(asset.mark_price)}</td>
            <td class="${asset.change_24h >= 0 ? 'change-positive' : 'change-negative'}">
                ${asset.change_24h >= 0 ? '+' : ''}${formatPercent(asset.change_24h)}
            </td>
            <td class="volume">${formatCurrency(asset.day_ntl_vlm)}</td>
            <td class="volume">${formatCurrency(asset.open_interest)}</td>
            <td class="${asset.funding_rate >= 0 ? 'change-positive' : 'change-negative'}">
                ${formatPercent(asset.funding_rate * 100)}
            </td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Update status indicator
 */
function updateStatus(text, isLive) {
    const statusEl = document.getElementById('status');
    const pulseEl = statusEl.querySelector('.pulse');

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
 * Format number as currency
 */
function formatCurrency(value) {
    if (value === undefined || value === null) return '$0';

    if (value >= 1e9) {
        return `$${(value / 1e9).toFixed(2)}B`;
    } else if (value >= 1e6) {
        return `$${(value / 1e6).toFixed(2)}M`;
    } else if (value >= 1e3) {
        return `$${(value / 1e3).toFixed(2)}K`;
    } else {
        return `$${value.toFixed(2)}`;
    }
}

/**
 * Format number as percentage
 */
function formatPercent(value) {
    if (value === undefined || value === null) return '0%';
    return `${value.toFixed(2)}%`;
}

/**
 * Format large numbers with K/M/B suffixes
 */
function formatNumber(value) {
    if (value >= 1e9) {
        return `${(value / 1e9).toFixed(2)}B`;
    } else if (value >= 1e6) {
        return `${(value / 1e6).toFixed(2)}M`;
    } else if (value >= 1e3) {
        return `${(value / 1e3).toFixed(2)}K`;
    } else {
        return value.toFixed(0);
    }
}
