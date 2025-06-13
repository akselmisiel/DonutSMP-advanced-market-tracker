# DonutSMP Market Tracker

A comprehensive web application for tracking and analyzing market transactions on the DonutSMP Minecraft server. This tool provides real-time market cap analysis, price tracking, and transaction monitoring with interactive charts and detailed statistics.

## Features

### 📊 Market Cap Analysis
- **Price Range Filtering**: Track items within specific price ranges
- **Market Cap Ranking**: Items sorted by total sales volume
- **Seller Analysis**: Detailed breakdown of sellers for each item
- **Time Window Controls**: Filter data by 1h, 6h, 1d, 1w, or custom timeframes
- **Interactive Charts**: Click on items to view price history graphs

### 📈 Price Tracking
- **Individual Item Tracking**: Monitor specific items or shulker box contents
- **High-Value Sales**: Track transactions above custom price thresholds
- **Shulker Box Support**: Full tracking of shulker box contents with stack size validation
- **Historical Data**: Persistent storage of all transaction history

### 🎯 Advanced Features
- **Real-time Polling**: Automatic updates from DonutSMP API
- **Blacklist System**: Filter out unwanted items from analysis
- **Interactive Legends**: Toggle chart datasets by clicking legend items
- **Zoom & Pan**: Mouse wheel zoom and drag-to-pan chart navigation
- **Transaction Details**: Click chart points to view detailed transaction information

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript with Chart.js
- **API**: DonutSMP Auction API integration
- **Storage**: JSON file-based persistence
- **Charts**: Chart.js with zoom/pan functionality

## Installation & Local Development

### Prerequisites
- Python 3.7+
- DonutSMP API token

### Setup
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd market-tracker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

5. Enter your DonutSMP API token and start tracking!

## Deployment

### Render.com (Recommended)
1. Push your code to GitHub
2. Connect your GitHub repository to Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python app.py`
5. Deploy!

### Other Hosting Options
- **Railway.app**: Auto-detects Python and deploys automatically
- **Fly.io**: Use `fly launch` and `fly deploy`
- **Vercel + PythonAnywhere**: Frontend on Vercel, API on PythonAnywhere

## Usage Guide

### Adding Trackers
1. **Item Tracker**: Track individual items or shulker box contents
2. **Price Tracker**: Monitor high-value sales above a threshold
3. **Market Cap Tracker**: Analyze items within a price range by market volume

### Market Cap Analysis
- Items are grouped by identical properties (ID, count, enchantments, trim, contents)
- Sorted by total sales volume (market cap)
- Shows total value, unique sellers, and median price
- Click "Show Graph" to view price history
- Click "Sellers" to see seller breakdown

### Navigation
- **Tabs**: Switch between different trackers
- **Time Windows**: Filter data by timeframe
- **Charts**: Zoom with mouse wheel, pan by dragging
- **Stats Button**: View summary statistics for active tracker

## API Integration

The application integrates with the DonutSMP API:
- `/v1/auction/transactions/` - Historical transaction data
- `/v1/auction/list/` - Active listings (deprecated in this version)
- `/v1/stats/` - Player statistics

## Data Storage

- **market_history.json**: Persistent transaction history
- **localStorage**: User preferences and legend visibility states

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the console for error messages
2. Ensure your API token is valid
3. Verify internet connectivity for API access
4. Create an issue on GitHub with details

## Version History

- **v1.0**: Initial release with market cap tracking
- **v1.1**: Enhanced UI and chart interactions
- **v1.2**: Added seller analysis and time filtering

---

Built with ❤️ for the DonutSMP community
