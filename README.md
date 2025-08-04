# Financial Tracker

A comprehensive personal financial tracking application built with Python, Flask, and SQLAlchemy. Track your accounts, transactions, investments, and get insights into your financial health with a clean, responsive web interface.

## Features

### 🏦 Account Management
- Support for multiple account types (Checking, Savings, Brokerage, Credit Card, etc.)
- Real-time balance tracking and transaction history
- Account categorization and institution management
- Active/inactive account status management

### 💰 Transaction Tracking
- Comprehensive transaction management with categorization
- Support for income, expenses, transfers, and investment transactions
- Advanced filtering and search capabilities
- CSV import/export functionality with flexible column mapping
- Recurring transaction support
- Tag-based organization system

### 📈 Investment Portfolio
- Stock tracking with real-time price updates via yfinance API
- Portfolio holdings management with cost basis tracking
- Buy/sell transaction recording with automatic holding updates
- Portfolio performance analytics and gain/loss calculations
- Historical price data visualization

### 📊 Analytics & Reporting
- Interactive financial dashboard with key metrics
- Spending analysis by category with visual charts
- Balance trend tracking over time
- Net worth calculation and monitoring
- Monthly/yearly financial summaries

### 🎨 User Experience
- Clean, responsive web interface
- Light/dark theme support with system preference detection
- Real-time search across accounts, transactions, and stocks
- Mobile-friendly responsive design
- Keyboard shortcuts for power users

### ⚙️ Technical Features
- SQLite database for local data storage
- RESTful API endpoints for data access
- Comprehensive error handling and logging
- Extensible architecture for additional financial data providers
- Full test coverage with unit, integration, and UI tests

## Installation

### Prerequisites
- Python 3.9 or higher
- pip or Poetry for package management

### Method 1: Using Poetry (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd financial-tracker
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies:**
   ```bash
   poetry install
   ```

4. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

### Method 2: Using pip

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd financial-tracker
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Environment Configuration

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your configuration:
   ```env
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   DATABASE_URL=sqlite:///financial_tracker.db
   DEFAULT_THEME=light
   DEFAULT_CURRENCY=$
   ```

## Usage

### Starting the Application

1. **Using Poetry:**
   ```bash
   poetry run python main.py
   ```

2. **Using pip:**
   ```bash
   python main.py
   ```

3. **Access the application:**
   Open your web browser and navigate to `http://localhost:5000`

### First Steps

1. **Add Your First Account:**
   - Click "Accounts" in the navigation menu
   - Click "Add Account"
   - Fill in your account details (name, type, initial balance)
   - Save the account

2. **Record Transactions:**
   - Navigate to "Transactions"
   - Click "Add Transaction"
   - Select the account, enter amount, description, and category
   - Save the transaction

3. **Track Investments:**
   - Go to "Stocks" section
   - Add stocks you want to track
   - Record buy/sell transactions
   - Monitor your portfolio performance

4. **Customize Settings:**
   - Visit "Settings" to configure:
     - Theme preference (light/dark)
     - Default currency
     - Display preferences
     - Pagination settings

## Development

### Project Structure
```
financial-tracker/
├── src/
│   ├── models/          # SQLAlchemy ORM definitions
│   ├── services/        # Business logic and API integrations
│   ├── web/            # Flask routes and web components
│   ├── templates/      # Jinja2 HTML templates
│   ├── static/         # CSS, JavaScript, images
│   ├── utils/          # Common helper functions
│   └── config.py       # Application configuration
├── tests/              # Test suite
├── main.py            # Application entry point
├── pyproject.toml     # Poetry configuration
└── requirements.txt   # pip requirements
```

### Running Tests

1. **Run all tests:**
   ```bash
   poetry run pytest
   # or with pip:
   python -m pytest
   ```

2. **Run with coverage:**
   ```bash
   poetry run pytest --cov=src --cov-report=html
   ```

3. **Run specific test types:**
   ```bash
   # Unit tests only
   pytest tests/test_*_service.py
   
   # Integration tests
   pytest tests/test_integration.py
   
   # UI tests (requires Chrome WebDriver)
   pytest tests/test_ui.py
   ```

### Code Quality

1. **Format code with Black:**
   ```bash
   poetry run black src/ tests/
   ```

2. **Lint with Flake8:**
   ```bash
   poetry run flake8 src/ tests/
   ```

3. **Run all quality checks:**
   ```bash
   poetry run black src/ tests/ && poetry run flake8 src/ tests/ && poetry run pytest
   ```

### Database Management

The application automatically creates the SQLite database on first run. To reset the database:

1. **Stop the application**
2. **Delete the database file:**
   ```bash
   rm financial_tracker.db
   ```
3. **Restart the application** (database will be recreated)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key-change-in-production` |
| `FLASK_ENV` | Flask environment | `development` |
| `DATABASE_URL` | Database connection string | `sqlite:///financial_tracker.db` |
| `DEFAULT_THEME` | Default UI theme | `light` |
| `DEFAULT_CURRENCY` | Default currency symbol | `$` |
| `YFINANCE_TIMEOUT` | Timeout for yfinance API calls | `10` |
| `STOCKDX_API_KEY` | Optional Stockdx API key | None |

### Financial Data APIs

The application uses yfinance as the primary data source for stock prices and information. For extended functionality, you can optionally configure:

- **Stockdx API**: Add your API key to `.env` for additional dividend data
- **Future APIs**: The architecture supports easy addition of new financial data providers

## Contributing

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes and add tests**
4. **Run the test suite:**
   ```bash
   poetry run pytest
   ```
5. **Format and lint your code:**
   ```bash
   poetry run black src/ tests/
   poetry run flake8 src/ tests/
   ```
6. **Commit your changes:**
   ```bash
   git commit -am "Add your feature description"
   ```
7. **Push to your fork and submit a pull request**

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or feature requests:

1. **Check the documentation** in this README
2. **Search existing issues** in the repository
3. **Create a new issue** with detailed information about your problem or suggestion

## Roadmap

### Planned Features
- [ ] Multi-user support with authentication
- [ ] Advanced reporting and analytics
- [ ] Budget planning and tracking
- [ ] Mobile application
- [ ] Additional financial data providers
- [ ] Automated transaction categorization
- [ ] Data backup and sync capabilities
- [ ] Advanced portfolio analytics
- [ ] Goal tracking and financial planning tools

### Technical Improvements
- [ ] API rate limiting and caching
- [ ] Database migration system
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Performance optimizations
- [ ] Enhanced security features
