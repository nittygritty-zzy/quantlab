"""
Test what data yfinance provides via download() and other methods
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

print('=' * 80)
print('TESTING YFINANCE DATA AVAILABILITY')
print('=' * 80)

# Define the ticker and date range
ticker = 'MSFT'
start_date = '2023-01-01'
end_date = datetime.now().strftime('%Y-%m-%d')

print(f'\nTicker: {ticker}')
print(f'Date Range: {start_date} to {end_date}')

# Fetch the data
print('\n📊 Downloading historical data...')
data = yf.download(ticker, start=start_date, end=end_date, progress=False)

print(f'\n✅ Downloaded {len(data)} trading days of data')

print('\n' + '=' * 80)
print('AVAILABLE COLUMNS IN HISTORICAL DATA')
print('=' * 80)
for col in data.columns:
    print(f'  • {col}')

print('\n' + '=' * 80)
print('SAMPLE DATA (First 5 rows)')
print('=' * 80)
print(data.head())

print('\n' + '=' * 80)
print('SAMPLE DATA (Last 5 rows)')
print('=' * 80)
print(data.tail())

print('\n' + '=' * 80)
print('DATA STATISTICS')
print('=' * 80)
print(data.describe())

# Save to CSV
csv_filename = f'{ticker}_data.csv'
data.to_csv(csv_filename)
print(f'\n✅ Data saved to: {csv_filename}')

print('\n' + '=' * 80)
print('ADDITIONAL DATA FROM .info DICTIONARY')
print('=' * 80)
stock = yf.Ticker(ticker)
info = stock.info

# Show key fields
key_fields = {
    'currentPrice': 'Current Price',
    'previousClose': 'Previous Close',
    'open': 'Open',
    'dayHigh': 'Day High',
    'dayLow': 'Day Low',
    'volume': 'Volume',
    'averageVolume': 'Average Volume',
    'marketCap': 'Market Cap',
    'beta': 'Beta',
    'trailingPE': 'P/E Ratio (TTM)',
    'forwardPE': 'Forward P/E',
    'dividendYield': 'Dividend Yield',
    'trailingEps': 'EPS (TTM)',
    'forwardEps': 'Forward EPS',
    'fiftyTwoWeekHigh': '52-Week High',
    'fiftyTwoWeekLow': '52-Week Low',
    'fiftyDayAverage': '50-Day Avg',
    'twoHundredDayAverage': '200-Day Avg',
    'profitMargins': 'Profit Margin',
    'operatingMargins': 'Operating Margin',
    'returnOnEquity': 'ROE',
    'returnOnAssets': 'ROA',
    'revenueGrowth': 'Revenue Growth',
    'earningsGrowth': 'Earnings Growth',
    'debtToEquity': 'Debt/Equity',
    'currentRatio': 'Current Ratio',
    'quickRatio': 'Quick Ratio',
    'freeCashflow': 'Free Cash Flow',
    'operatingCashflow': 'Operating Cash Flow',
    'targetMeanPrice': 'Target Price',
    'recommendationKey': 'Recommendation',
    'numberOfAnalystOpinions': 'Analyst Count'
}

print('\nKey fundamental data available:')
for field, label in key_fields.items():
    value = info.get(field)
    if value is not None:
        if isinstance(value, float):
            if field in ['marketCap', 'freeCashflow', 'operatingCashflow', 'volume', 'averageVolume']:
                print(f'  • {label:25s}: {value:,.0f}')
            elif field in ['dividendYield', 'profitMargins', 'operatingMargins', 'returnOnEquity', 'returnOnAssets', 'revenueGrowth', 'earningsGrowth']:
                print(f'  • {label:25s}: {value*100:.2f}%')
            else:
                print(f'  • {label:25s}: {value:.2f}')
        elif isinstance(value, int):
            print(f'  • {label:25s}: {value:,}')
        else:
            print(f'  • {label:25s}: {value}')

print('\n' + '=' * 80)
print('OTHER AVAILABLE DATA METHODS')
print('=' * 80)
print('  • stock.history()           - Historical price data (what we just used)')
print('  • stock.info                - 165+ company info fields')
print('  • stock.income_stmt         - Income statement')
print('  • stock.balance_sheet       - Balance sheet')
print('  • stock.cashflow            - Cash flow statement')
print('  • stock.quarterly_income_stmt - Quarterly income statement')
print('  • stock.quarterly_balance_sheet - Quarterly balance sheet')
print('  • stock.quarterly_cashflow  - Quarterly cash flow')
print('  • stock.dividends           - Dividend history')
print('  • stock.splits              - Stock split history')
print('  • stock.actions             - All corporate actions')
print('  • stock.recommendations     - Analyst recommendations')
print('  • stock.analyst_price_target - Price targets')
print('  • stock.earnings_dates      - Upcoming earnings dates')
print('  • stock.news()              - Recent news articles')
print('  • stock.options             - Available option expiration dates')
print('  • stock.option_chain(date)  - Options chain for specific date')

print('\n' + '=' * 80)
print('TESTING FINANCIAL STATEMENTS')
print('=' * 80)

# Income Statement
income_stmt = stock.income_stmt
if not income_stmt.empty:
    print(f'\n✅ Income Statement available with {len(income_stmt)} rows')
    print(f'   Latest period: {income_stmt.columns[0]}')
    print(f'   Available metrics: {len(income_stmt.index)} items')
    print('\n   Sample metrics:')
    for metric in ['Total Revenue', 'Net Income', 'Gross Profit', 'Operating Income', 'EBITDA']:
        if metric in income_stmt.index:
            value = income_stmt.loc[metric].iloc[0]
            print(f'     • {metric:20s}: {value:,.0f}')

# Balance Sheet
balance_sheet = stock.balance_sheet
if not balance_sheet.empty:
    print(f'\n✅ Balance Sheet available with {len(balance_sheet)} rows')
    print(f'   Latest period: {balance_sheet.columns[0]}')
    print(f'   Available metrics: {len(balance_sheet.index)} items')

# Cash Flow
cashflow = stock.cashflow
if not cashflow.empty:
    print(f'\n✅ Cash Flow Statement available with {len(cashflow)} rows')
    print(f'   Latest period: {cashflow.columns[0]}')
    print(f'   Available metrics: {len(cashflow.index)} items')

# Test dividends
dividends = stock.dividends
if not dividends.empty:
    print(f'\n✅ Dividend History available')
    print(f'   Total dividends: {len(dividends)}')
    print(f'   Latest dividend: ${dividends.iloc[-1]:.2f} on {dividends.index[-1].date()}')

# Test recommendations
recommendations = stock.recommendations
if recommendations is not None and not recommendations.empty:
    print(f'\n✅ Analyst Recommendations available')
    print(f'   Total recommendations: {len(recommendations)}')

print('\n' + '=' * 80)
print('SUMMARY: WHAT DATA CAN YOU GET?')
print('=' * 80)
print('''
FROM yf.download() - HISTORICAL PRICE DATA:
  ✅ Open, High, Low, Close prices
  ✅ Adjusted Close (accounts for splits/dividends)
  ✅ Volume
  ✅ Date-indexed time series
  ✅ Any date range you specify
  ✅ Intraday data (1m, 5m, 15m, 30m, 1h intervals)

FROM stock.info - COMPANY FUNDAMENTALS:
  ✅ 165+ fields including:
    • Current price data (bid, ask, open, close)
    • Valuation metrics (P/E, P/B, P/S, PEG, market cap)
    • Profitability (margins, ROE, ROA)
    • Growth (revenue growth, earnings growth)
    • Balance sheet (cash, debt, ratios)
    • Dividends & analyst data

FROM FINANCIAL STATEMENTS:
  ✅ Complete income statements (annual & quarterly)
  ✅ Complete balance sheets (annual & quarterly)
  ✅ Complete cash flow statements (annual & quarterly)
  ✅ Multi-year historical data

OTHER DATA:
  ✅ Dividend history
  ✅ Stock splits
  ✅ Analyst recommendations & price targets
  ✅ News articles
  ✅ Options chains (all expirations + full chain data)
  ✅ Earnings dates
  ✅ Institutional & insider holdings

INTERVALS AVAILABLE FOR history():
  • 1m, 2m, 5m, 15m, 30m (intraday - limited to recent data)
  • 60m, 90m, 1h (hourly)
  • 1d (daily - default)
  • 5d, 1wk, 1mo, 3mo (weekly/monthly)

PERIODS AVAILABLE:
  • 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
''')

print('=' * 80)
print('CSV FILE STRUCTURE')
print('=' * 80)
print(f'\nThe CSV file "{csv_filename}" contains:')
print('  • Date column (index)')
print('  • Open - Opening price')
print('  • High - Highest price of the day')
print('  • Low - Lowest price of the day')
print('  • Close - Closing price')
print('  • Adj Close - Adjusted closing price (accounts for dividends/splits)')
print('  • Volume - Number of shares traded')
print('\nThis is perfect for:')
print('  • Technical analysis (moving averages, RSI, MACD, etc.)')
print('  • Backtesting trading strategies')
print('  • Price trend analysis')
print('  • Volatility calculations')
print('  • Volume analysis')

print('\n' + '=' * 80)
