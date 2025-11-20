# Quick Start Guide

Get your Hyperliquid dashboard running in 60 seconds!

## 🚀 Quick Setup

### Option 1: Using the Run Script (Recommended)

```bash
cd hyperliquid-dashboard
./run.sh
```

### Option 2: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
cd backend
python3 server.py
```

## 📱 Access the Dashboard

Open your browser and go to:
```
http://localhost:5000
```

## ✅ What You'll See

The dashboard includes:

1. **Market Overview Cards**
   - Total 24h trading volume
   - Total open interest
   - Number of active markets
   - Average funding rate

2. **Interactive Charts**
   - Top markets by volume (bar chart)
   - Market performance rankings

3. **Data Tables**
   - Top gainers (24h)
   - Top losers (24h)
   - Highest volume markets

4. **Real-time Updates**
   - Auto-refreshes every 10 seconds
   - Live price updates
   - Current status indicator

## 🔧 Troubleshooting

### Port 5000 is already in use?

Edit `backend/server.py` and change the port:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port here
```

### Dependencies not installing?

Try using a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### No data showing?

1. Check internet connection (needs to access Hyperliquid API)
2. Check browser console for errors (F12)
3. Verify backend is running (should see "Running on http://0.0.0.0:5000")

## 📊 API Endpoints

If you want to use the API programmatically:

```bash
# Get market statistics
curl http://localhost:5000/api/stats

# Get market summary
curl http://localhost:5000/api/market-summary

# Get list of assets
curl http://localhost:5000/api/universe
```

## 🎨 Customization

### Change refresh interval

Edit `frontend/js/dashboard.js`:
```javascript
const REFRESH_INTERVAL = 5000; // 5 seconds instead of 10
```

### Change theme colors

Edit `frontend/css/styles.css` and modify the `:root` variables:
```css
:root {
    --accent-primary: #3b82f6; /* Change to your preferred color */
}
```

## 📖 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API client in `backend/hyperliquid_api.py`
- Customize the dashboard styling
- Add your own metrics and visualizations

## 🆘 Need Help?

- Check the [Hyperliquid API docs](https://docs.trade.xyz/api/overview)
- Review the main [README.md](README.md)
- Look at the example code in `backend/hyperliquid_api.py`

---

Happy trading! 📈
