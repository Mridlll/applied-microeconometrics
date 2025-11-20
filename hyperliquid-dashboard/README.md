# Hyperliquid Trading Dashboard

A real-time trading analytics dashboard for Hyperliquid (trade.xyz), built to visualize perpetual futures markets data similar to Dune Analytics dashboards.

![Dashboard Preview](https://img.shields.io/badge/Status-Live-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Real-time Market Data**: Live updates every 10 seconds from Hyperliquid API
- **Comprehensive Metrics**:
  - Total 24h trading volume across all markets
  - Total open interest for all perpetuals
  - Average funding rates
  - Active market count

- **Platform Analytics** (NEW! 🎉):
  - Estimated user counts and activity metrics
  - Growth tracking (7d and 30d periods)
  - Historical data storage (up to 90 days)
  - Time-series charts for volume and OI trends
  - Platform activity estimates
  - See [ANALYTICS_GUIDE.md](ANALYTICS_GUIDE.md) for details

- **Interactive Visualizations**:
  - Top 10 markets by trading volume (bar chart)
  - Market performance rankings (24h change %)
  - 30-day volume trend (line chart)
  - 30-day open interest trend (line chart)
  - Top gainers and losers tables
  - Highest volume markets with detailed stats

- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Clean UI**: Dark theme optimized for trading data visualization
- **Data Persistence**: Automatic historical data tracking with JSON storage

## Tech Stack

### Backend
- **Python 3.8+**: Core language
- **Flask**: Web server and API endpoints
- **Requests**: HTTP client for Hyperliquid API calls
- **Flask-CORS**: Cross-origin resource sharing support

### Frontend
- **HTML5/CSS3**: Structure and styling
- **Vanilla JavaScript**: Dashboard logic and updates
- **Chart.js**: Interactive data visualizations
- **Axios**: HTTP client for API calls

## Project Structure

```
hyperliquid-dashboard/
├── backend/
│   ├── hyperliquid_api.py    # Hyperliquid API client
│   └── server.py              # Flask server
├── frontend/
│   ├── index.html             # Main dashboard page
│   ├── css/
│   │   └── styles.css         # Dashboard styles
│   └── js/
│       └── dashboard.js       # Dashboard logic
├── data/                      # Data cache (if needed)
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or navigate to the repository**:
   ```bash
   cd hyperliquid-dashboard
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the backend server**:
   ```bash
   cd backend
   python server.py
   ```

4. **Access the dashboard**:
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Running the Dashboard

```bash
# From the hyperliquid-dashboard/backend directory
python server.py
```

The server will start on `http://localhost:5000` and the dashboard will automatically load.

### Using the API Client Directly

You can also use the Hyperliquid API client independently:

```python
from hyperliquid_api import HyperliquidAPI

# Initialize the API client
api = HyperliquidAPI(use_testnet=False)

# Get market summary
summary = api.get_market_summary()
print(f"Total assets: {len(summary['assets'])}")

# Get data for a specific asset
trades = api.get_recent_trades("BTC")
candles = api.get_candles("BTC", interval="1h")
```

## API Endpoints

The Flask server provides the following REST API endpoints:

- `GET /` - Serves the dashboard HTML
- `GET /api/health` - Health check endpoint
- `GET /api/market-summary` - Get comprehensive market summary
- `GET /api/universe` - Get list of all tradable assets
- `GET /api/asset/<coin>` - Get detailed data for a specific asset
- `GET /api/candles/<coin>/<interval>` - Get candlestick data
- `GET /api/funding/<coin>` - Get funding rate history
- `GET /api/stats` - Get aggregated market statistics

## Dashboard Components

### Metric Cards
- **Total 24h Volume**: Aggregate trading volume across all markets
- **Total Open Interest**: Sum of open interest for all perpetuals
- **Active Markets**: Number of trading pairs available
- **Average Funding Rate**: Mean funding rate across top markets

### Charts
- **Volume Chart**: Bar chart showing top 10 markets by 24h volume
- **Performance Chart**: Bar chart of top performers by 24h change percentage

### Tables
- **Top Gainers**: Assets with highest positive 24h change
- **Top Losers**: Assets with largest negative 24h change
- **Highest Volume**: Detailed ranking of markets by trading volume

## Configuration

### API Settings

Edit `backend/hyperliquid_api.py` to configure:
- **Testnet vs Mainnet**: Set `use_testnet=True` for testnet
- **Cache duration**: Modify `CACHE_DURATION` in `server.py` (default: 10 seconds)

### Frontend Settings

Edit `frontend/js/dashboard.js` to configure:
- **Refresh interval**: Modify `REFRESH_INTERVAL` (default: 10000ms)
- **API base URL**: Modify `API_BASE_URL` if deploying to production

## Data Source

This dashboard uses the official Hyperliquid API (accessed via trade.xyz):
- **API Base URL**: `https://api.hyperliquid.xyz`
- **Documentation**: [https://docs.trade.xyz/api/overview](https://docs.trade.xyz/api/overview)

## Features in Detail

### Real-time Updates
The dashboard automatically refreshes every 10 seconds to display the latest market data. The refresh interval can be adjusted in the configuration.

### Responsive Design
The dashboard uses CSS Grid and Flexbox to provide a responsive layout that adapts to different screen sizes:
- Desktop: Multi-column layout with full tables
- Tablet: Adjusted column counts
- Mobile: Single-column stacked layout

### Color Coding
- **Green**: Positive changes, gains
- **Red**: Negative changes, losses
- **Blue/Purple**: Accent colors for branding and highlights

## Troubleshooting

### Server won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if port 5000 is already in use
- Verify Python version is 3.8+

### No data appearing
- Check internet connection (API requires external access)
- Verify the Hyperliquid API is accessible
- Check browser console for JavaScript errors

### CORS errors
- Ensure Flask-CORS is installed
- Check that the backend server is running
- Verify API_BASE_URL in dashboard.js matches server address

## Development

### Adding New Features

1. **New API endpoint**: Add to `backend/server.py`
2. **New visualization**: Update `frontend/js/dashboard.js` and add Chart.js config
3. **New metrics**: Modify `hyperliquid_api.py` to fetch additional data

### Testing

Test the API client:
```bash
cd backend
python hyperliquid_api.py
```

This will fetch and display current market data in the console.

## Performance Optimization

- Data is cached on the backend for 10 seconds to reduce API calls
- Frontend only updates changed DOM elements
- Charts use Chart.js update() method instead of full re-renders

## Future Enhancements

Potential features for future versions:
- [ ] User portfolio tracking
- [ ] Price alerts and notifications
- [ ] Historical data analysis
- [ ] Advanced charting with TradingView
- [ ] Liquidation tracking
- [ ] Market depth visualization
- [ ] WebSocket integration for real-time updates
- [ ] Export data to CSV/Excel
- [ ] Mobile app version

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Acknowledgments

- **Hyperliquid**: For providing the trading infrastructure and API
- **trade.xyz**: Platform documentation
- **Dune Analytics**: Inspiration for dashboard design
- **Chart.js**: Charting library

## Support

For issues or questions:
1. Check the [Hyperliquid API documentation](https://docs.trade.xyz/api/overview)
2. Review the troubleshooting section above
3. Open an issue in the repository

## Disclaimer

This dashboard is for informational purposes only. It is not financial advice. Always do your own research before trading.

---

**Built with ❤️ for the Hyperliquid community**
